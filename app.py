# app.py

from flask import Flask, request, jsonify, send_from_directory, send_file
import sqlite3
from datetime import datetime
import csv

app = Flask(__name__)

# ---------------- DATABASE ----------------

def init_db():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )
    """)

    # ORDERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        status TEXT,
        location TEXT,
        updated_by TEXT,
        last_updated TEXT
    )
    """)

    # RESET USERS
    c.execute("DELETE FROM users")

    users = [

        ("manager", "9999", "manager"),

        ("operator1", "1111", "operator"),

        ("operator2", "2222", "operator"),

        ("operator3", "3333", "operator")

    ]

    c.executemany(
        "INSERT INTO users VALUES (?, ?, ?)",
        users
    )

    conn.commit()
    conn.close()

init_db()

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

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT role FROM users WHERE username=? AND password=?",
        (username, password)
    )

    result = c.fetchone()

    conn.close()

    if result:

        return jsonify({
            "success": True,
            "role": result[0]
        })

    return jsonify({
        "success": False
    })

# ---------------- ADD ORDER ----------------

@app.route("/add_order", methods=["POST"])
def add_order():

    data = request.json

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d")

    try:

        c.execute("""
        INSERT INTO orders VALUES (?, ?, ?, ?, ?)
        """, (

            data["order_id"],
            data["status"],
            data["location"],
            data["updated_by"],
            now

        ))

        conn.commit()

    except:
        pass

    conn.close()

    return jsonify({
        "msg": "added"
    })

# ---------------- UPDATE ORDER ----------------

@app.route("/update_order", methods=["POST"])
def update_order():

    data = request.json

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d")

    c.execute("""

    UPDATE orders

    SET
    status=?,
    location=?,
    updated_by=?,
    last_updated=?

    WHERE order_id=?

    """, (

        data["status"],
        data["location"],
        data["updated_by"],
        now,
        data["order_id"]

    ))

    conn.commit()

    conn.close()

    return jsonify({
        "msg": "updated"
    })

# ---------------- GET ORDERS ----------------

@app.route("/get_orders")
def get_orders():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM orders")

    rows = c.fetchall()

    conn.close()

    orders = []

    today = datetime.now()

    for r in rows:

        last = datetime.strptime(r[4], "%Y-%m-%d")

        days = (today - last).days

        delayed = False

        if days > 7 and r[1] != "Delivered":
            delayed = True

        orders.append({

            "order_id": r[0],
            "status": r[1],
            "location": r[2],
            "updated_by": r[3],
            "last_updated": r[4],
            "delayed": delayed

        })

    return jsonify(orders)

# ---------------- DOWNLOAD REPORT ----------------

@app.route("/download_report")
def download_report():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM orders")

    rows = c.fetchall()

    conn.close()

    with open("report.csv", "w", newline="") as f:

        writer = csv.writer(f)

        writer.writerow([

            "Order ID",
            "Status",
            "Location",
            "Updated By",
            "Last Updated"

        ])

        writer.writerows(rows)

    return send_file(
        "report.csv",
        as_attachment=True
    )

# ---------------- RUN ----------------

app.run(
    host="0.0.0.0",
    port=5000
)
