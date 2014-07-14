import flask

# modal class for nest
class Nest():
    id = 0
    name = ""
    room = ""
    state = 0   # 0 for off, 1 for AutoChangeOver
    currentTemperature = 0
    targetTemperatureCool = 77
    targetTemperatureHeat = 70
    occupancyState = 0 # 0 for away, 1 for home
    controllerId = 0


    def __init__(self, id, name, room, state, currentTemperature, targetTemperatureCool, targetTemperatureHeat, occupancyState, controllerId):
        self.id = id
        self.name = name
        self.room = room
        self.state = state
        self.currentTemperature = currentTemperature
        self.targetTemperatureCool = targetTemperatureCool
        self.targetTemperatureHeat = targetTemperatureHeat
        self.occupancyState = occupancyState
        self.controllerId = controllerId
        
    def __repr__(self):
        return jsonify({"id": self.id, "name": self.name, "room": self.room, "state": self.state})


