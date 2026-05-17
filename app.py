from flask import Flask, request, jsonify, send_from_directory, send_file
from supabase import create_client
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# ---------------- SUPABASE ----------------

SUPABASE_URL = "https://zonfcubbjwqugxfspvxv.supabase.co/rest/v1/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvbmZjdWJiandxdWd4ZnNwdnh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwMzAxNDcsImV4cCI6MjA5NDYwNjE0N30.ODenipIuIUZSi9la68Xrrd3C7Ib72NQtaGmJyGuNpN0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- USERS ----------------

USERS = {
    "manager": {
        "password": "9999",
        "role": "manager"
    },
    "operator1": {
        "password": "2222",
        "role": "operator"
    },
    "operator2": {
        "password": "3333",
        "role": "operator"
    },
    "operator3": {
        "password": "4444",
        "role": "operator"
    }
}

# ---------------- HOME ----------------

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

# ---------------- LOGIN ----------------

@app.route("/login", methods=["POST"])
def login():

    data = request.json

    username = data["username"].strip()
    password = data["password"].strip()

    if username in USERS:

        if USERS[username]["password"] == password:

            return jsonify({
                "success": True,
                "role": USERS[username]["role"]
            })

    return jsonify({"success": False})

# ---------------- ADD ORDER ----------------

@app.route("/add_order", methods=["POST"])
def add_order():

    data = request.json

    now = datetime.now().strftime("%Y-%m-%d")

    try:

        supabase.table("orders").insert({
            "order_id": data["order_id"],
            "status": data["status"],
            "location": data["location"],
            "updated_by": data["updated_by"],
            "last_updated": now
        }).execute()
app.run(host="0.0.0.0", port=5000)
