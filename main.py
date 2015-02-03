from flask import *
from flask.json import JSONEncoder
from device import *
from scene import *
import requests
import random
import simplejson as json
import os
import time
import redis

redis = redis.Redis("localhost")

class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            if isinstance(obj, Device):
                deviceDict = obj.__dict__
                deviceDict['_type'] = obj.__class__.__name__
                return deviceDict
            iterable = iter(obj)
        except TypeError:
            print type(obj)
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)

def deviceDecoder(dct):
    if '_type' in dct:
        if dct['_type'] == "Light":
            return Light(dct["id"],dct["name"],dct["room"],dct["state"])
        elif dct['_type'] == "Lock":
            return Lock(dct["id"],dct["name"],dct["room"],dct["state"])
        elif dct['_type'] == "Nest":
            return Nest(dct["id"],dct["name"],dct["room"], dct["currentTemp"], dct["maxTemp"], dct["minTemp"], dct["controllerId"], dct["state"])
    return dct

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

global lights
lights = {}

global scenes
scenes = {}

global locks
locks = {}

global nests
nests = {}

global verdeDevices
verdeDevices = {}

global smarthomeState 
smarthomeState = "smarthome_state_"

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/lights", methods = ['GET'])
def listLights():
    p = { 'rand': random.random() }
    response = requests.get("http://192.168.1.88/port_3480/data_request?id=user_data", params = p)
    responseContent = json.loads(response.__dict__['_content'])
    devices = responseContent['devices']
    rooms = responseContent['rooms']
    availableScenes = responseContent['scenes']
    roomNames = {}

    for room in rooms:
        if room["id"] not in roomNames:
            roomNames[room["id"]] = room["name"]
            
    for scene in availableScenes:
        # add scene to dictionary (except it doesn't seem to really work like a dictionary)
        scenes[str(scene["id"])] = Scene(unicode(str(scene["id"])),scene["name"])
        # uncomment the below to have your scenes printed to stdout because of the problem with listScenes()
        # print vars(scenes[str(scene["id"])])

    for device in devices:
        if "device_type" in device:
            if ("Light" in device["device_type"] or "WeMoControllee" in device["device_type"]) and "Sensor" not in device["device_type"]:
                # get room name
                if int(device["room"]) not in roomNames:
                    roomName = "Room not found"
                else:
                    roomName = roomNames[int(device["room"])]

                # get device state
                brightness = 0
                hasBrightness = False
                for state in device["states"]:
                    if state["variable"] == "Status":
                        deviceState = state["value"]
                    if state["variable"] == "LoadLevelStatus":
                        brightness = state["value"]
                        hasBrightness = True

                # add light to dictionary
                lights[device["id"]] = Light(device["id"],device["name"],roomName,deviceState,hasBrightness,brightness)

    return jsonify(**lights)

@app.route("/scenes", methods = ['GET'])
def listScenes():
    if lights == {}:
        listLights()
    # this function does not work because scenes is not JSON serializable. I could not figure out what to do about it
    return jsonify(**scenes)    
    
@app.route("/lights/<int:id>", methods = ['GET'])
def getLight(id):
    if lights == {}:
        listLights()
    p = { 'DeviceNum': id, 'rand': random.random() }
    response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
    states = json.loads(response.__dict__['_content'])['Device_Num_'+str(id)]['states']
    
    for state in states:
        if state["variable"] == "Status":
            lights[str(id)].updateState(state["value"])

    return jsonify(**lights[str(id)].__dict__)

@app.route("/lights/<int:id>", methods = ['PUT'])
def putLight(id):
    if lights == {}:
        listLights()

    # check inputs
    if str(id) not in lights:
        return jsonify(result = "Error", message = "Not a light")

    if "state" not in request.get_json():
        return jsonify(result = "Error", message = "State not specified")

    change = lights[str(id)].setState(request.get_json()['state'], "urn:upnp-org:serviceId:SwitchPower1")

    if change is not True:
        return change
    else:
        return jsonify(result = "OK", state = request.get_json()['state'])
        

@app.route("/lights/brightness/<int:id>", methods = ['PUT'])
def putLightBrightness(id):
    if lights == {}:
        listLights()

    # check inputs
    if str(id) not in lights:
        return jsonify(result = "Error", message = "Not a light")

    if "brightness" not in request.get_json():
        return jsonify(result = "Error", message = "Brightness not specified")

    change = lights[str(id)].setBrightness(request.get_json()['brightness'], "urn:upnp-org:serviceId:Dimming1")

    if change is not True:
        return change
    else:
        return jsonify(result = "OK", state = request.get_json()['brightness'])        
        
@app.route("/scenes/<int:id>", methods = ['PUT'])
def putScene(id):
    if scenes == {}:
        listLights()

    # check inputs
    if str(id) not in scenes:
        return jsonify(result = "Error", message = "Not a scene")

    change = scenes[str(id)].activate("urn:micasaverde-com:serviceId:HomeAutomationGateway1")

    if change is not True:
        return change
    else:
        return jsonify(result = "OK")

@app.route("/locks", methods = ['GET'])
def listLocks():
    p = { 'rand': random.random() }
    response = requests.get("http://192.168.1.88/port_3480/data_request?id=user_data", params = p)
    responseContent = json.loads(response.__dict__['_content'])
    devices = responseContent['devices']
    rooms = responseContent['rooms']
    roomNames = {}

    for room in rooms:
        if room["id"] not in roomNames:
            roomNames[room["id"]] = room["name"]

    for device in devices:
        if "device_type" in device:
            if "DoorLock" in device["device_type"]:
                # get room name
                if int(device["room"]) not in roomNames:
                    roomName = "Room not found"
                else:
                    roomName = roomNames[int(device["room"])]

                # get device state
                for state in device["states"]:
                    if state["variable"] == "Status" and "DoorLock" in state["service"]:
                        deviceState = state["value"]

                # add lock to dictionary
                locks[device["id"]] = Lock(device["id"],device["name"],roomName,deviceState)

    return jsonify(**locks)

@app.route("/locks/<int:id>", methods = ['GET'])
def getLock(id):
    if locks == {}:
        listLocks()
    
    p = { 'DeviceNum': id, 'rand': random.random() }
    response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
    states = json.loads(response.__dict__['_content'])['Device_Num_'+str(id)]['states']
    
    for state in states:
        if state["variable"] == "Status" and "DoorLock" in state["service"]:
            locks[str(id)].updateState(state["value"])

    return jsonify(**locks[str(id)].__dict__)

@app.route("/locks/<int:id>", methods = ['PUT'])
def putLock(id):
    # check inputs
    if str(id) not in locks:
        return jsonify(result = "Error", message = "Not a lock")

    if "state" not in request.get_json():
        return jsonify(result = "Error", message = "State not specified")

    if "password" not in request.get_json():
        return jsonify(result = "Error", message = "Password not specified")

    if request.get_json()['password'] != os.environ['LOCKSECRET']:
        return jsonify(result = "Error", message = "Wrong password")

    change = locks[str(id)].setState(request.get_json()['state'], "urn:micasaverde-com:serviceId:DoorLock1")

    if change is not True:
        return change
    else:
        return jsonify(result = "OK", state = request.get_json()['state'])


@app.route("/nests", methods = ['GET'])
def listNests():
    p = { 'rand': random.random() }
    response = requests.get("http://192.168.1.88/port_3480/data_request?id=user_data", params = p)
    responseContent = json.loads(response.__dict__['_content'])
    devices = responseContent['devices']
    rooms = responseContent['rooms']
    roomNames = {}

    for room in rooms:
        if room["id"] not in roomNames:
            roomNames[room["id"]] = room["name"]

    for device in devices:
        if "device_type" in device:
            if "HVAC" in device["device_type"] or "NestStructure" in device["device_type"]:
                if "HVAC" in device["device_type"]:
                    deviceId = device["id"]
                    deviceName = device["name"]
                    # get room name
                    if int(device["room"]) not in roomNames:
                        roomName = "Room not found"
                    else:
                        roomName = roomNames[int(device["room"])]

                    # get device state
                    for state in device["states"]:
                        if state["variable"] == "CurrentTemperature":
                            currentTemperature = state["value"]
                        if "TemperatureSetpoint1_Cool" in state["service"] and state["variable"] == "CurrentSetpoint":
                            maxTemp = state["value"]
                        if "TemperatureSetpoint1_Heat" in state["service"] and state["variable"] == "CurrentSetpoint":
                            minTemp = state["value"]

                else:    
                    # get home/ away mode and id of controller 
                    if "NestStructure" in device["device_type"]:
                        controllerId = device["id"]
                        for state in device["states"]:
                            if state["variable"] == "OccupancyState":
                                if state["value"] == "Occupied":
                                    deviceState = "1"
                                elif state["value"] == "Unoccupied":
                                    deviceState = "0"

    # add nest to dictionary
    if deviceId is not None and controllerId is not None:
        nests[deviceId] = Nest(deviceId,deviceName,roomName,currentTemperature,maxTemp,minTemp, controllerId, deviceState)
    else:
        raise Exception('Problem with Nest API')

    return jsonify(**nests)

@app.route("/nests/<int:id>", methods = ['GET'])
def getNest(id):
    if nests == {}:
        listNests()
    
    p = { 'DeviceNum': id, 'rand': random.random() }
    response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
    states = json.loads(response.__dict__['_content'])['Device_Num_'+str(id)]['states']
    
    for state in states:
        if state["variable"] == "CurrentTemperature":
            nests[str(id)].updateCurrentTemp(state["value"])
        if "TemperatureSetpoint1_Cool" in state["service"] and state["variable"] == "CurrentSetpoint":
            nests[str(id)].updateMaxTemp(state["value"])
        if "TemperatureSetpoint1_Heat" in state["service"] and state["variable"] == "CurrentSetpoint":
            nests[str(id)].updateMinTemp(state["value"])
        
    # get state for controller
    controllerId = nests[str(id)].getControllerId()

    p = { 'DeviceNum': controllerId, 'rand': random.random() }
    response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
    controllerStates = json.loads(response.__dict__['_content'])['Device_Num_'+str(controllerId)]['states']
    for state in controllerStates:
        if state["variable"] == "OccupancyState":
            if state["value"] == "Occupied":
                nests[str(id)].updateState("1")
            elif state["value"] == "Unoccupied":
                nests[str(id)].updateState("0")

    return jsonify(**nests[str(id)].__dict__)

@app.route("/nests/<int:id>", methods = ['PUT'])
def putNest(id):
    # check inputs
    if str(id) not in nests:
        return jsonify(result = "Error", message = "Not a Nest")

    if "maxTemp" not in request.get_json() and "minTemp" not in request.get_json() and "state" not in request.get_json():
        return jsonify(result = "Error", message = "No change specified")

    if "maxTemp" in request.get_json() and "minTemp" in request.get_json():
        if request.get_json()['maxTemp'] < request.get_json()['minTemp']:
            return jsonify(result = "Error", message = "Max temp cannot be lower than min temp")

    if "password" not in request.get_json():
        return jsonify(result = "Error", message = "Password not specified")

    if request.get_json()['password'] != os.environ['LOCKSECRET']:
        return jsonify(result = "Error", message = "Wrong password")

    # make the changes
    if "minTemp" in request.get_json() and "maxTemp" in request.get_json():
        change = nests[str(id)].setTemp(request.get_json()['minTemp'], request.get_json()['maxTemp'])
        if change is not True:
            return change
    elif "minTemp" in request.get_json() and "maxTemp" not in request.get_json():
        change = nests[str(id)].setTemp(request.get_json()['minTemp'], nests[str(id)].getMaxTemp())
        if change is not True:
            return change
    elif "minTemp" not in request.get_json() and "maxTemp" in request.get_json():
        change = nests[str(id)].setTemp(nests[str(id)].getMinTemp(), request.get_json()['maxTemp'])
        if change is not True:
            return change

    if "state" in request.get_json():
        if request.get_json()['state'] == "0":
            change = nests[str(id)].setState("Unoccupied", "urn:upnp-org:serviceId:HouseStatus1")
        elif request.get_json()['state'] == "1":
            change = nests[str(id)].setState("Occupied", "urn:upnp-org:serviceId:HouseStatus1")
        if change is not True:
            return change

    return jsonify(result = "OK", message = "All changes made")

@app.route("/states", methods = ['GET'])
def listStates():
    keys = redis.keys(smarthomeState+"*")
    result = []
    for key in keys:
        result.append(key[len(smarthomeState):])
    return json.dumps(result)

@app.route("/states/<string:slot>", methods = ['GET'])
def getState(slot):
    slot = smarthomeState + slot
    return jsonify(json.loads(redis.get(slot), object_hook=deviceDecoder))

@app.route("/states/<string:slot>", methods = ['PUT'])
def saveCurrentState(slot):
    slot = smarthomeState + slot
    if "password" not in request.get_json():
        return jsonify(result = "Error", message = "Password not specified")

    if request.get_json()['password'] != os.environ['LOCKSECRET']:
        return jsonify(result = "Error", message = "Wrong password")

    listLights()
    listLocks()
    listNests()

    for light in lights:
        verdeDevices[light] = lights[light]
    for lock in locks:
        verdeDevices[lock] = locks[lock]
    for nest in nests:
        verdeDevices[nest] = nests[nest]

    redis.set(slot,json.dumps(verdeDevices, cls=CustomJSONEncoder))

    return jsonify(result = "OK", message = slot + " state saved")


@app.route("/states/load/<string:slot>", methods = ['PUT'])
def loadState(slot):
    slot = smarthomeState + slot
    if "password" not in request.get_json():
        return jsonify(result = "Error", message = "Password not specified")

    if request.get_json()['password'] != os.environ['LOCKSECRET']:
        return jsonify(result = "Error", message = "Wrong password")

    listLights()
    listLocks()
    listNests()

    savedStates = json.loads(redis.get(slot), object_hook=deviceDecoder)

    for savedState in savedStates:
        if isinstance(savedStates[savedState], Light):
            if savedStates[savedState].getState() != lights[savedStates[savedState].getId()].getState():
                change = lights[savedStates[savedState].getId()].setState(savedStates[savedState].getState(), "urn:upnp-org:serviceId:SwitchPower1")
                if change is not True:
                    return change
        elif isinstance(savedStates[savedState], Lock):
            if savedStates[savedState].getState() != locks[savedStates[savedState].getId()].getState():
                change = locks[savedStates[savedState].getId()].setState(savedStates[savedState].getState(), "urn:micasaverde-com:serviceId:DoorLock1")
                if change is not True:
                    return change
        elif isinstance(savedStates[savedState], Nest):
            if savedStates[savedState].getMinTemp() != nests[savedStates[savedState].getId()].getMinTemp() or savedStates[savedState].getMaxTemp() != nests[savedStates[savedState].getId()].getMaxTemp():
                change = nests[savedStates[savedState].getId()].setTemp(savedStates[savedState].getMinTemp(), savedStates[savedState].getMaxTemp())
                if change is not True:
                    return change
            if savedStates[savedState].getState() != nests[savedStates[savedState].getId()].getState():
                if savedStates[savedState].getState() == "0":
                    change = nests[savedStates[savedState].getId()].setState("Unoccupied", "urn:upnp-org:serviceId:HouseStatus1")
                    if change is not True:
                        return change
                elif savedStates[savedState].getState() == "1":
                    change = nests[savedStates[savedState].getId()].setState("Occupied", "urn:upnp-org:serviceId:HouseStatus1")
                    if change is not True:
                        return change

    return jsonify(result = "OK", message = "All states restored")

# gunicorn stuff here
from werkzeug.contrib.fixers import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config.from_pyfile('config.py')

import logging
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler('flask.log', maxBytes=1024 * 1024 * 100, backupCount=20)
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)

if __name__ == "__main__":
    app.run(debug = True, host='0.0.0.0')