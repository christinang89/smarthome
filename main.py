from flask import *
from light import *
from lock import *
import requests
import random
import simplejson as json

app = Flask(__name__)

global lights
lights = {}

global locks
locks = {}


@app.route("/")
def hello():
    return "Hello aWorld!"

@app.route("/lights", methods=['GET'])
def listLights():
	p = {'rand': random.random()}
	response = requests.get("http://192.168.1.88/port_3480/data_request?id=user_data", params = p)
	lst = []
	devices = json.loads(response.__dict__['_content'])['devices']

	for i in devices:
		if "device_type" in i:
			if "Light" in i["device_type"] and "Sensor" not in i["device_type"]:
				for n in i["states"]:
					if n["variable"] == "Status":
						lights[i["id"]] = Light(i["id"],i["name"],i["room"],n["value"]).__dict__

	return jsonify(**lights)

@app.route("/lights/<int:id>", methods=['GET'])
def getLight(id):
	if lights == {}:
		listLights()
	
	p = {'DeviceNum': id, 'rand': random.random() }
	response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
	states = json.loads(response.__dict__['_content'])['Device_Num_'+str(id)]['states']
	for state in states:
		if state["variable"] == "Status":
			lights[str(id)]['status'] = state["value"]

	return jsonify(**lights[str(id)])

@app.route("/lights/<int:id>", methods=['PUT'])
def putLight(id):
	if lights == {}:
		listLights()

	if str(id) in lights:
		if "state" in request.get_json():
			p = {'DeviceNum': id, 'newTargetValue': request.get_json()['state'], 'rand': random.random() }
			response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&serviceId=urn:upnp-org:serviceId:SwitchPower1&action=SetTarget", params = p)
			
			if "ERROR" not in response.__dict__['_content']:
				return jsonify(result = "ok", state = request.get_json()['state'])	
			else:
				return jsonify(result = "error", message = response.__dict__['_content'])
		else:
			return jsonify(result = "error", message = "state not specified")
	else:
		return jsonify(result = "error", message = "not a light")

@app.route("/locks", methods=['GET'])
def listLocks():
	p = {'rand': random.random()}
	response = requests.get("http://192.168.1.88/port_3480/data_request?id=user_data", params = p)
	lst = []
	devices = json.loads(response.__dict__['_content'])['devices']

	for i in devices:
		if "device_type" in i:
			if "DoorLock" in i["device_type"]:
				for n in i["states"]:
					if n["variable"] == "Status" and "DoorLock" in n["service"]:
						locks[i["id"]] = Lock(i["id"],i["name"],i["room"],n["value"]).__dict__

	return jsonify(**locks)

@app.route("/locks/<int:id>", methods=['GET'])
def getLock(id):
	if locks == {}:
		listLocks()
	
	p = {'DeviceNum': id, 'rand': random.random() }

	response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
	states = json.loads(response.__dict__['_content'])['Device_Num_'+str(id)]['states']
	for state in states:
		if state["variable"] == "Status" and "DoorLock" in state["service"]:
			locks[str(id)]['status'] = state["value"]

	return jsonify(**locks[str(id)])

@app.route("/locks/<int:id>", methods=['PUT'])
def putLock(id):
	if locks == {}:
		listLocks()

	if str(id) in locks:
		if "state" in request.get_json():
			p = {'DeviceNum': id, 'newTargetValue': request.get_json()['state'], 'rand': random.random() }
			response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&serviceId=urn:micasaverde-com:serviceId:DoorLock1&action=SetTarget", params = p)
			
			if "ERROR" not in response.__dict__['_content']:
				return jsonify(result = "ok", state = request.get_json()['state'])	
			else:
				return jsonify(result = "error", message = response.__dict__['_content'])
		else:
			return jsonify(result = "error", message = "state not specified")
	else:
		return jsonify(result = "error", message = "not a lock")

if __name__ == "__main__":
    app.run(debug = True)
