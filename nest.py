import flask

# modal class for nest
class Nest():
    id = 0
    name = ""
    room = ""
    currentTemperature = 0
    maxTemp = 78
    minTemp = 70
    state = 0 # 0 for away, 1 for home
    controllerId = 0


    def __init__(self, id, name, room, currentTemperature, maxTemp, minTemp, controllerId, state):
        self.id = id
        self.name = name
        self.room = room
        self.state = state
        self.currentTemperature = currentTemperature
        self.maxTemp = maxTemp
        self.minTemp = minTemp
        self.controllerId = controllerId
        
    def __repr__(self):
        return jsonify({"id": self.id, "name": self.name, "room": self.room, "state": self.state})


