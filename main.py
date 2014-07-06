from flask import *
from light import *
from lock import *
import requests
import random
import simplejson as json
import os

app = Flask(__name__)

global lights
lights = {}

global locks
locks = {}

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
		return jsonify(result = "ok", state = request.get_json()['state'])	
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
	
	# return the response
	if "ERROR" not in response.__dict__['_content']:
		return jsonify(result = "ok", state = request.get_json()['state'])	
	else:
		return jsonify(result = "error", message = response.__dict__['_content'])	

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

