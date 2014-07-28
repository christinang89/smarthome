from flask import *
import requests
import simplejson as json
import random
import time

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
        return json.dumps({"id": self.id, "name": self.name, "room": self.room, "state": self.state})

    def getState(self):
        return self.state

    def getId(self):
        return self.id

    def updateState(self, newState):
        self.state = newState

    def verifyState(self, targetState):
        for i in range(500):
            p = { 'DeviceNum': self.id, 'rand': random.random() }
            response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
            states = json.loads(response.__dict__['_content'])['Device_Num_'+str(self.id)]['states']
            
            for state in states:
                if state["variable"] == "Status":
                    self.state = state["value"]
            if self.state == str(targetState):
                return True
            else:
                time.sleep(0.3)
        return False

    def setState(self, targetState, serviceName):
        # set state
        p = { 'serviceId': serviceName, 'DeviceNum': self.id, 'newTargetValue': targetState, 'rand': random.random()}
        response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&action=SetTarget", params = p)

        # return response
        if "ERROR" not in response.__dict__['_content']:
            if self.verifyState(targetState):
                return True
            else:
                return jsonify(result = "Error", message = "Switching state of " + str(self.id) + " has timed out")
        else:
            return jsonify(result = "Error", message = response.__dict__['_content'])

# class light inherits from device
class Light(Device):
    pass

# class lock inherits from device
class Lock(Device):
    pass

# class nest inherits from device and contains additional variables
class Nest(Device):
    currentTemp = 0
    maxTemp = 78
    minTemp = 70
    controllerId = 0

    def __init__(self, id, name, room, currentTemp, maxTemp, minTemp, controllerId, state):
        self.id = id
        self.name = name
        self.room = room
        self.state = state
        self.currentTemp = currentTemp
        self.maxTemp = maxTemp
        self.minTemp = minTemp
        self.controllerId = controllerId

    def __repr__(self):
        return json.dumps({"id": self.id, "name": self.name, "room": self.room, "currentTemp": self.currentTemp, "maxTemp": self.maxTemp, "minTemp": self.minTemp, "controllerId": self.controllerId, "state": self.state})

    def updateCurrentTemp(self, newCurrentTemp):
        self.currentTemp = newCurrentTemp

    def updateMaxTemp(self, newMaxTemp):
        self.maxTemp = newMaxTemp

    def updateMinTemp(self, newMinTemp):
        self.minTemp = newMinTemp

    def getControllerId(self):
        return self.controllerId

    def getMinTemp(self):
        return self.minTemp

    def getMaxTemp(self):
        return self.maxTemp

    def verifyTemp(self, targetTemp, varType):
        for i in range(500):
            p = { 'DeviceNum': self.id, 'rand': random.random() }
            response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
            states = json.loads(response.__dict__['_content'])['Device_Num_'+str(self.id)]['states']
            
            for state in states:
                if state["variable"] == "CurrentTemperature":
                    self.currentTemp = state["value"]
                if "TemperatureSetpoint1_Heat" in state["service"] and state["variable"] == "CurrentSetpoint":
                    self.minTemp = state["value"]
                if "TemperatureSetpoint1_Cool" in state["service"] and state["variable"] == "CurrentSetpoint":
                    self.maxTemp = state["value"]

            if varType == "Heat":
                if self.minTemp == str(targetTemp):
                    return True
                else:
                    time.sleep(0.3)
            elif varType == "Cool":
                if self.maxTemp == str(targetTemp):
                    return True
                else:
                    time.sleep(0.3)
        return False

    def setTemp(self, targetState, serviceName):
        # set state
        p = { 'serviceId': serviceName, 'DeviceNum': self.id, 'NewCurrentSetpoint': targetState, 'rand': random.random() }
        response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&action=SetCurrentSetpoint", params = p)

        # return response
        if "ERROR" not in response.__dict__['_content']:
            if "Heat" in serviceName:
                if self.verifyTemp(targetState, "Heat"):
                    return True
                else:
                    return jsonify(result = "Error", message = "Switching temp of " + str(self.id) + " has timed out")
            elif "Cool" in serviceName:
                if self.verifyTemp(targetState, "Cool"):
                    return True
                else:
                    return jsonify(result = "Error", message = "Switching temp of " + str(self.id) + " has timed out")
        else:
            return jsonify(result = "Error", message = response.__dict__['_content'])

    def verifyState(self, targetState):
        for i in range(500):
            p = { 'DeviceNum': self.controllerId, 'rand': random.random() }
            response = requests.get("http://192.168.1.88/port_3480/data_request?id=status&output_format=json", params = p)
            states = json.loads(response.__dict__['_content'])['Device_Num_'+str(self.controllerId)]['states']
            
            for state in states:
                if state["variable"] == "OccupancyState":
                    if state["value"] == "Occupied":
                        self.state = "1"
                    elif state["value"] == "Unoccupied":
                        self.state = "0"

            if targetState == "Occupied":
                if self.state == "1":
                    return True
                else:
                    time.sleep(0.3)
            elif targetState == "Unoccupied":
                if self.state == "0":
                    return True
                else:
                    time.sleep(0.3)

        return False

    def setState(self, targetState, serviceName):
        # set state
        p = { 'serviceId': serviceName, 'DeviceNum': self.controllerId, 'NewOccupancyState': targetState, 'rand': random.random() }
        response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&action=SetOccupancyState", params = p)

        # return response
        if "ERROR" not in response.__dict__['_content']:
            if self.verifyState(targetState):
                return True
            else:
                return jsonify(result = "Error", message = "Switching state of " + str(self.id) + " has timed out")
        else:
            return jsonify(result = "Error", message = response.__dict__['_content'])
