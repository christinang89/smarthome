import flask

class Lock():
	id = 0
	name = ""
	room = ""
	status = 0

	def __init__(self, id, name, room, status):
		self.id = id
		self.name = name
		self.room = room
		self.status = status
		
	def __repr__(self):
		return jsonify({"id": self.id, "name": self.name, "room": self.room, "status": self.status})


"""http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&DeviceNum=34&serviceId=urn:micasaverde-com:serviceId:DoorLock1&action=SetTarget&newTargetValue=0&rand=0.28891129908151925"""