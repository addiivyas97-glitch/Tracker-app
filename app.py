from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        status TEXT,
        location TEXT,
        updated_by TEXT,
        last_updated TEXT
    )''')

    # Reset users (safe for now)
    c.execute("DELETE FROM users")

    users = [
        ("manager", "9999", "manager"),
        ("operator1", "1111", "worker"),
        ("operator2", "2222", "worker"),
        ("operator3", "3333", "worker")
    ]

    c.executemany("INSERT INTO users VALUES (?, ?, ?)", users)

    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES ----------
@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    u = data["username"].strip()
    p = data["password"].strip()

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT role FROM users WHERE username=? AND password=?", (u, p))
    result = c.fetchone()
    conn.close()

    if result:
        return jsonify({"success": True, "role": result[0]})
    return jsonify({"success": False})

@app.route("/add_order", methods=["POST"])
def add_order():
    d = request.json
    now = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    try:
        c.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
                  (d["order_id"], d["status"], d["location"], d["user"], now))
        conn.commit()
        msg = "Added"
    except:
        msg = "Exists"

    conn.close()
    return jsonify({"msg": msg})

@app.route("/update_order", methods=["POST"])
def update_order():
    d = request.json
    now = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE orders SET status=?, location=?, updated_by=?, last_updated=? WHERE order_id=?",
              (d["status"], d["location"], d["user"], now, d["order_id"]))

    conn.commit()
    conn.close()

    return jsonify({"msg": "Updated"})

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

        delay = days > 7 and r[1] != "Delivered"

        orders.append({
            "order_id": r[0],
            "status": r[1],
            "location": r[2],
            "updated_by": r[3],
            "last_updated": r[4],
            "delay": delay
        })

    return jsonify(orders)

app.run(host="0.0.0.0", port=5000)
