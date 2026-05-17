# =========================
# app.py
# =========================

from flask import Flask, request, jsonify, send_from_directory, send_file
from supabase import create_client
from datetime import datetime
import pandas as pd

app = Flask(__name__)

# =========================
# SUPABASE
# =========================

SUPABASE_URL = "https://zonfcubbjwqugxfspvxv.supabase.co/rest/v1/"
SUPABASE_KEY = "sb_publishable_O3jRqRa2ZxVLSv2Unfhvtg_1pN1aVWY"

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# =========================
# USERS
# =========================

USERS = {

    "manager": {
        "password": "9999",
        "role": "manager"
    },

    "operator1": {
        "password": "5555",
        "role": "operator"
    },

    "operator2": {
        "password": "7777",
        "role": "operator"
    },

    "operator3": {
        "password": "8888",
        "role": "operator"
    }

}

# =========================
# HOME
# =========================

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

# =========================
# LOGIN
# =========================

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

    return jsonify({
        "success": False
    })

# =========================
# ADD ORDER
# =========================

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

        supabase.table("activity_logs").insert({

            "operator_name": data["updated_by"],
            "action": "Added Order",
            "order_id": data["order_id"],
            "time": now

        }).execute()

    except:
        pass

    return jsonify({
        "msg": "added"
    })

# =========================
# UPDATE ORDER
# =========================

@app.route("/update_order", methods=["POST"])
def update_order():

    data = request.json

    now = datetime.now().strftime("%Y-%m-%d")

    supabase.table("orders").update({

        "status": data["status"],
        "location": data["location"],
        "updated_by": data["updated_by"],
        "last_updated": now

    }).eq(
        "order_id",
        data["order_id"]
    ).execute()

    supabase.table("activity_logs").insert({

        "operator_name": data["updated_by"],
        "action": f"Updated to {data['status']}",
        "order_id": data["order_id"],
        "time": now

    }).execute()

    return jsonify({
        "msg": "updated"
    })

# =========================
# GET ORDERS
# =========================

@app.route("/get_orders")
def get_orders():

    response = supabase.table(
        "orders"
    ).select("*").execute()

    orders = response.data

    today = datetime.now()

    for o in orders:

        last = datetime.strptime(
            o["last_updated"],
            "%Y-%m-%d"
        )

        days = (today - last).days

        if days > 7 and o["status"] != "Delivered":
            o["delayed"] = True
        else:
            o["delayed"] = False

    return jsonify(orders)

# =========================
# GET LOGS
# =========================

@app.route("/get_logs")
def get_logs():

    response = supabase.table(
        "activity_logs"
    ).select("*").execute()

    return jsonify(response.data)

# =========================
# DOWNLOAD REPORT
# =========================

@app.route("/download_report")
def download_report():

    response = supabase.table(
        "orders"
    ).select("*").execute()

    df = pd.DataFrame(response.data)

    file_name = "report.xlsx"

    df.to_excel(
        file_name,
        index=False
    )

    return send_file(
        file_name,
        as_attachment=True
    )

# =========================
# RUN
# =========================

app.run(
    host="0.0.0.0",
    port=5000
)
