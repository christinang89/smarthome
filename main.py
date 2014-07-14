from flask import *
from light import *
from lock import *
from nest import *
import requests
import random
import simplejson as json
import os
import time

app = Flask(__name__)

global lights
lights = {}

global locks
locks = {}

global nests
nests = {}

def verifyLightState(id, targetState):
	for i in range(50):
		p = { 'DeviceNum': int(id), 'rand': random.random() }
		response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
		states = json.loads(response.__dict__['_content'])['Device_Num_'+str(id)]['states']
		
		for state in states:
			if state["variable"] == "Status":
				lights[str(id)]['state'] = state["value"]
		if lights[str(id)]['state'] == str(targetState):
			return True
		else:
			time.sleep(0.1)
	return False

def verifyLockState(id, targetState):
	for i in range(50):
		p = { 'DeviceNum': int(id), 'rand': random.random() }
		response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
		states = json.loads(response.__dict__['_content'])['Device_Num_'+str(id)]['states']
		
		for state in states:
			if state["variable"] == "Status":
				locks[str(id)]['state'] = state["value"]
		if locks[str(id)]['state'] == str(targetState):
			return True
		else:
			time.sleep(0.5)
	return False

def changeAllState(targetLightState, targetLockState):
	if lights == {}:
		listLights()
	if locks == {}:
		listLocks()

	# check inputs
	if "password" not in request.get_json():
		return jsonify(result = "error", message = "password not specified")

	if request.get_json()['password'] != os.environ['LOCKSECRET']:
		return jsonify(result = "error", message = "wrong password")
	
	for light in lights:
		if lights[light]["state"] == str((targetLightState+1)%2):
			p = { 'DeviceNum': int(light), 'newTargetValue': targetLightState, 'rand': random.random() }
			response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&serviceId=urn:upnp-org:serviceId:SwitchPower1&action=SetTarget", params = p)
			if "ERROR" in response.__dict__['_content']:
				return jsonify(result = "error", message = response.__dict__['_content'])
			if not verifyLightState(light, targetLightState):
				return jsonify(result = "error", message = "changing state of " + str(light) + " has timed out")

	for lock in locks:
		if locks[lock]["state"] == str((targetLockState+1)%2):
			p = { 'DeviceNum': int(lock), 'newTargetValue': targetLockState, 'rand': random.random() }
			response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&serviceId=urn:micasaverde-com:serviceId:DoorLock1&action=SetTarget", params = p)
			if "ERROR" in response.__dict__['_content']:
				return jsonify(result = "error", message = response.__dict__['_content'])
			if not verifyLockState(lock, targetLockState):
				return jsonify(result = "error", message = "changing state of " + str(lock) + " has timed out")

	if targetLightState == 1:
		message = "Lights switched on"
	else:
		message = "Lights switched off"

	if targetLockState == 0:
		message += " and doors unlocked"
	else:
		message += " and doors locked"

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
				lights[device["id"]] = Light(device["id"],device["name"],roomName,deviceState).__dict__

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
			lights[str(id)]['state'] = state["value"]

	return jsonify(**lights[str(id)])

@app.route("/lights/<int:id>", methods = ['PUT'])
def putLight(id):
	if lights == {}:
		listLights()

	# check inputs
	if str(id) not in lights:
		return jsonify(result = "error", message = "not a light")

	if "state" not in request.get_json():
		return jsonify(result = "error", message = "state not specified")

	# do the real shizz
	p = { 'DeviceNum': id, 'newTargetValue': request.get_json()['state'], 'rand': random.random() }
	response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&serviceId=urn:upnp-org:serviceId:SwitchPower1&action=SetTarget", params = p)
	
	# return response
	if "ERROR" not in response.__dict__['_content']:
		if verifyLightState(id, request.get_json()['state']):
			return jsonify(result = "ok", state = request.get_json()['state'])	
		else:
			return jsonify(result = "error", message = "switching state of " + str(id) + " has timed out")
	else:
		return jsonify(result = "error", message = response.__dict__['_content'])
		

@app.route("/locks", methods = ['GET'])
def listLocks():
	p = { 'rand': random.random() }
	response = requests.get("http://192.168.1.88/port_3480/data_request?id=user_data", params = p)
	responseContent = json.loads(response.__dict__['_content'])
	devices = responseContent['devices']
	rooms = responseContent['rooms']
	roomNames = {}
	#devices = json.loads(response.__dict__['_content'])['devices']

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
				locks[device["id"]] = Lock(device["id"],device["name"],roomName,deviceState).__dict__

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
			locks[str(id)]['state'] = state["value"]

	return jsonify(**locks[str(id)])

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
	
	# do real stuff
	p = { 'DeviceNum': id, 'newTargetValue': request.get_json()['state'], 'rand': random.random() }
	response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&serviceId=urn:micasaverde-com:serviceId:DoorLock1&action=SetTarget", params = p)
	
	# return response
	if "ERROR" not in response.__dict__['_content']:
		if verifyLockState(id, request.get_json()['state']):
			return jsonify(result = "ok", state = request.get_json()['state'])	
		else:
			return jsonify(result = "error", message = "switching state of " + str(id) + " has timed out")
	else:
		return jsonify(result = "error", message = response.__dict__['_content'])


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

	# devices = json.loads(response.__dict__['_content'])['devices']

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
		nests[deviceId] = Nest(deviceId,deviceName,roomName,currentTemperature,maxTemp,minTemp, controllerId, deviceState).__dict__
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
			nests[str(id)]['currentTemperature'] = state["value"]
		if "TemperatureSetpoint1_Cool" in state["service"] and state["variable"] == "CurrentSetpoint":
			nests[str(id)]['maxTemp'] = state["value"]
		if "TemperatureSetpoint1_Heat" in state["service"] and state["variable"] == "CurrentSetpoint":
			nests[str(id)]['minTemp'] = state["value"]
		
	# get state for controller
	controllerId = nests[str(id)]['controllerId']
	p = { 'DeviceNum': controllerId, 'rand': random.random() }
	response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
	controllerStates = json.loads(response.__dict__['_content'])['Device_Num_'+str(controllerId)]['states']
	for state in controllerStates:
		if state["variable"] == "OccupancyState":
			if state["value"] == "Occupied":
				nests[str(id)]['state'] = "1"
			elif state["value"] == "Unoccupied":
				nests[str(id)]['state'] = "0" 

	return jsonify(**nests[str(id)])

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

	if "minTemp" in request.get_json():
		p = { 'DeviceNum': id, 'NewCurrentSetpoint': request.get_json()['minTemp'], 'rand': random.random() }
		response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&serviceId=urn:upnp-org:serviceId:TemperatureSetpoint1_Heat&action=SetCurrentSetpoint", params = p)
		
		if "ERROR" in response.__dict__['_content']:
			return jsonify(result = "error", message = response.__dict__['_content'])

	if "maxTemp" in request.get_json():
		p = { 'DeviceNum': id, 'NewCurrentSetpoint': request.get_json()['maxTemp'], 'rand': random.random() }
		response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&serviceId=urn:upnp-org:serviceId:TemperatureSetpoint1_Cool&action=SetCurrentSetpoint", params = p)

		if "ERROR" in response.__dict__['_content']:
			return jsonify(result = "error", message = response.__dict__['_content'])

	if "state" in request.get_json():
		if request.get_json()['state'] == 0:
			p = { 'DeviceNum': int(nests[str(id)]['controllerId']) , 'NewOccupancyState': 'Unoccupied', 'rand': random.random() }
			response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&serviceId=urn:upnp-org:serviceId:HouseStatus1&action=SetOccupancyState", params = p)
		elif request.get_json()['state'] == 1:
			p = { 'DeviceNum': int(nests[str(id)]['controllerId']), 'NewOccupancyState': 'Occupied', 'rand': random.random() }
			response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&serviceId=urn:upnp-org:serviceId:HouseStatus1&action=SetOccupancyState", params = p)

		if "ERROR" in response.__dict__['_content']:
			return jsonify(result = "error", message = response.__dict__['_content'])

	return jsonify(result = "ok", message = "All changes made")

@app.route("/away", methods = ['PUT'])
def switchAway():
	return changeAllState(0,1)

@app.route("/home", methods = ['PUT'])
def switchHome():
	return changeAllState(1,0)


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

