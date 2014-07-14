import flask

# super class modal for devices

class Device():
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

class Light(Device):
    pass

class Lock(Device):
    pass

class Nest(Device):
    currentTemperature = 0
    maxTemp = 78
    minTemp = 70
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
        return jsonify({"id": self.id, "name": self.name, "room": self.room, "currentTemperature": self.currentTemperature, "maxTemp": self.maxTemp, "minTemp": self.minTemp, "controllerId": self.controllerId, "state": self.state})
