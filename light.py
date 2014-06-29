import flask

class Light():
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