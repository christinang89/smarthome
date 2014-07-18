from flask import *
from flask.json import JSONEncoder
from device import *
import requests
import random
import simplejson as json
import os
import time

class CustomJSONEncoder(JSONEncoder):
	def default(self, obj):
		try:
			if isinstance(obj, Device):
				return obj.__dict__
			iterable = iter(obj)
		except TypeError:
			print type(obj)
		else:
			return list(iterable)
		return JSONEncoder.default(self, obj)

app = Flask(__name__)
app.json_encoder = CustomJSONEncoder

global lights
lights = {}

global locks
locks = {}

global nests
nests = {}


def changeAllState(targetLightState, targetLockState, targetNestState):
	if lights == {}:
		listLights()
	if locks == {}:
		listLocks()
	if nests == {}:
		listNests()

	# check inputs
	if "password" not in request.get_json():
		return jsonify(result = "error", message = "password not specified")

	if request.get_json()['password'] != os.environ['LOCKSECRET']:
		return jsonify(result = "error", message = "wrong password")
	
	for light in lights:
		if lights[light].getState() != targetLightState:
			change = lights[light].setState(targetLightState,"urn:upnp-org:serviceId:SwitchPower1")
			if change is not True:
				return change

	for lock in locks:
		if locks[lock].getState() != targetLockState:
			change = locks[lock].setState(targetLockState,"urn:micasaverde-com:serviceId:DoorLock1")
			if change is not True:
				return change

	for nest in nests:
		if nests[nest].getState() != targetNestState:
			if targetNestState == "1":
				change = nests[nest].setState("NewOccupancyState", "Occupied", "urn:upnp-org:serviceId:HouseStatus1")
			elif targetNestState == "0":
				change = nests[nest].setState("NewOccupancyState", "Unoccupied", "urn:upnp-org:serviceId:HouseStatus1")
			if change is not True:
				return change

	if targetLightState == "1":
		message = "Lights switched on, "
	else:
		message = "Lights switched off, "

	if targetLockState == "0":
		message += "Doors unlocked, "
	else:
		message += "Doors locked, "

	if targetNestState == "1":
		message += "and Nest set to Home mode."
	else:
		message += "and Nest set to Away mode."

	return jsonify(result = "ok", message = message)
	

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
	roomNames = {}

	for room in rooms:
		if room["id"] not in roomNames:
			roomNames[room["id"]] = room["name"]

	# devices = json.loads(response.__dict__['_content'])['devices']

	for device in devices:
		if "device_type" in device:
			if ("Light" in device["device_type"] or "WeMoControllee" in device["device_type"]) and "Sensor" not in device["device_type"]:
				# get room name
				if int(device["room"]) not in roomNames:
					roomName = "Room not found"
				else:
					roomName = roomNames[int(device["room"])]

				# get device state
				for state in device["states"]:
					if state["variable"] == "Status":
						deviceState = state["value"]

				# add light to dictionary
				lights[device["id"]] = Light(device["id"],device["name"],roomName,deviceState)

	return jsonify(**lights)

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
		return jsonify(result = "error", message = "not a light")

	if "state" not in request.get_json():
		return jsonify(result = "error", message = "state not specified")

	change = lights[str(id)].setState(request.get_json()['state'],"urn:upnp-org:serviceId:SwitchPower1")

	if change is not True:
		return change
	else:
		return jsonify(result = "ok", state = request.get_json()['state'])
		

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
	if locks == {}:
		listLocks()
		
	# check inputs
	if str(id) not in locks:
		return jsonify(result = "error", message = "not a lock")

	if "state" not in request.get_json():
		return jsonify(result = "error", message = "state not specified")

	if "password" not in request.get_json():
		return jsonify(result = "error", message = "password not specified")

	if request.get_json()['password'] != os.environ['LOCKSECRET']:
		return jsonify(result = "error", message = "wrong password")

	change = locks[str(id)].setState(request.get_json()['state'],"urn:micasaverde-com:serviceId:DoorLock1")

	if change is not True:
		return change
	else:
		return jsonify(result = "ok", state = request.get_json()['state'])


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
	if nests == {}:
		listNests()

	# check inputs
	if str(id) not in nests:
		return jsonify(result = "error", message = "not a Nest")

	if "maxTemp" not in request.get_json() and "minTemp" not in request.get_json() and "state" not in request.get_json():
		return jsonify(result = "error", message = "no change specified")

	if "maxTemp" in request.get_json() and "minTemp" in request.get_json():
		if request.get_json()['maxTemp'] < request.get_json()['minTemp']:
			return jsonify(result = "error", message = "Max temp cannot be lower than min temp")

	if "password" not in request.get_json():
		return jsonify(result = "error", message = "password not specified")

	if request.get_json()['password'] != os.environ['LOCKSECRET']:
		return jsonify(result = "error", message = "wrong password")

	# make the changes
	if "minTemp" in request.get_json():
		change = nests[str(id)].setTemp(request.get_json()['minTemp'],"urn:upnp-org:serviceId:TemperatureSetpoint1_Heat")
		if change is not True:
			return change

	if "maxTemp" in request.get_json():
		change = nests[str(id)].setTemp(request.get_json()['maxTemp'],"urn:upnp-org:serviceId:TemperatureSetpoint1_Cool")
		if change is not True:
			return change

	if "state" in request.get_json():
		if request.get_json()['state'] == "0":
			change = nests[str(id)].setState("NewOccupancyState", "Unoccupied", "urn:upnp-org:serviceId:HouseStatus1")
		elif request.get_json()['state'] == "1":
			change = nests[str(id)].setState("NewOccupancyState", "Occupied", "urn:upnp-org:serviceId:HouseStatus1")
		if change is not True:
			return change

	return jsonify(result = "ok", message = "All changes made")

@app.route("/away", methods = ['PUT'])
def switchAway():
	return changeAllState("0","1","0")

@app.route("/home", methods = ['PUT'])
def switchHome():
	return changeAllState("1","0","1")

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

