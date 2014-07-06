import flask

# modal class for lock
class Lock():
	id = 0
	name = ""
	room = ""
	state = 0

	def __init__(self, id, name, room, state):
		self.id = id
		self.name = name
		self.room = room
		self.state = state
		
	def __repr__(self):
		return jsonify({"id": self.id, "name": self.name, "room": self.room, "state": self.state})


