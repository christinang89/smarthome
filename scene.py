#!/usr/bin/env python
from flask import *
import requests
import simplejson as json
import random
import time

# super class modal for devices
class Scene():
    id = 0
    name = ""

    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
         return json.dumps({"id": self.id, "name": self.name})

    def getId(self):
        return self.id
        
    def getName(self):
        return self.name

    def activate(self, serviceName):
        # set state
        p = { 'serviceId': serviceName, 'SceneNum': self.id, 'rand': random.random()}
        response = requests.get("http://192.168.1.88/port_3480/data_request?id=lu_action&output_format=json&action=RunScene", params = p)

        # return response
        if "ERROR" not in response.__dict__['_content']:
            return True
        else:
            return jsonify(result = "Error from Vera", message = response.__dict__['_content'])
