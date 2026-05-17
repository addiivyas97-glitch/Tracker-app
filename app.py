from flask import Flask, request, jsonify, send_file
import json
import os
import time

app = Flask(__name__)

DATA_FILE = "data.json"

# Load data
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Save data
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
def home():
    return send_file("index.html")

@app.route("/update", methods=["POST"])
def update():
    data = load_data()

    oid = request.json["order_id"]
    status = request.json["status"]

    data[oid] = {
        "status": status,
        "time": time.strftime("%H:%M:%S")
    }

    save_data(data)
    return jsonify({"message": "updated"})

@app.route("/get")
def get_data():
    return jsonify(load_data())

app.run(host="0.0.0.0", port=5000)