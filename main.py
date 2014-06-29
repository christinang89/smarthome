from flask import *
from light import *

app = Flask(__name__)

lights = {}

a = Light(1,"ceiling","mine")
b = Light(2,"ceiling","master")

lights["1"] = a.__dict__
lights["2"] = b.__dict__

@app.route("/")
def hello():
    return "Hello aWorld!"

@app.route("/lights", methods=['GET'])
def list():
	return jsonify(**lights)

@app.route("/lights/<int:id>", methods=['GET'])
def get(id):
	return jsonify(**lights[str(id)])

@app.route("/lights/<int:id>", methods=['PUT'])
def put(id):
	if "state" in request.get_json():
		return jsonify(result = "ok", state = request.get_json()['state'])
	else:
		return jsonify(result = "error", message = "state not specified")

if __name__ == "__main__":
    app.run(debug = True)
