from flask import *
from light import *

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello aWorld!"

@app.route("/lights")
def list():
	lights = {}

	a = Light(1,"ceiling","mine")
	b = Light(2,"ceiling","master")
	
	lights["1"] = a.__dict__
	lights["2"] = b.__dict__

	return jsonify(**lights)

if __name__ == "__main__":
    app.run(debug = True)
