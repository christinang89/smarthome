import flask

class Light():
	id = 0
	name = ""
	room = ""

	def __init__(self, id, name, room):
		self.id = id
		self.name = name
		self.room = room
		
	def __repr__(self):
		return jsonify({"id": self.id, "name": self.name, "room": self.room})