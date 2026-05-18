# app.py

from flask import Flask, request, jsonify, send_from_directory, send_file
from supabase import create_client
from datetime import datetime
import pandas as pd

# PDF
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import (
    getSampleStyleSheet
)

# QR
import qrcode

# BARCODE
import barcode
from barcode.writer import ImageWriter

# SOCKETS
from flask_socketio import SocketIO

# ---------------- APP ----------------

app = Flask(__name__)

socketio = SocketIO(app)

# ---------------- SUPABASE ----------------

SUPABASE_URL = "https://zonfcubbjwqugxfspvxv.supabase.co/rest/v1/"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpvbmZjdWJiandxdWd4ZnNwdnh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkwMzAxNDcsImV4cCI6MjA5NDYwNjE0N30.ODenipIuIUZSi9la68Xrrd3C7Ib72NQtaGmJyGuNpN0"
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# ---------------- USERS ----------------

USERS = {

    "manager": {
        "password": "9999",
        "role": "manager"
    },

    "supervisor": {
        "password": "3333",
        "role": "supervisor"
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

# ---------------- ORDER ID ----------------

def generate_order_id():

    year = datetime.now().year

    response = supabase.table(
        "orders"
    ).select(
        "order_id"
    ).execute()

    count = len(response.data) + 1

    return f"ORD-{year}-{count:04}"

# ---------------- HOME ----------------

@app.route("/")
def home():

    return send_from_directory(
        ".",
        "index.html"
    )

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

                "role":
                USERS[username]["role"]

            })

    return jsonify({
        "success": False
    })

# ---------------- CREATE ORDER ----------------

@app.route("/create_order", methods=["POST"])
def create_order():

    data = request.json

    order_id = generate_order_id()

    now = datetime.now().strftime(
        "%Y-%m-%d"
    )

    supabase.table("orders").insert({

        "order_id": order_id,

        "assigned_operator":
        data["assigned_operator"],

        "status": "Order Received",

        "location":
        data["location"],

        "updated_by": "manager",

        "last_updated": now

    }).execute()

    supabase.table("activity_logs").insert({

        "operator_name": "manager",

        "action": "Created Order",

        "order_id": order_id,

        "time": now

    }).execute()

    socketio.emit(
        "new_order",
        {"order_id": order_id}
    )

    return jsonify({

        "msg": "created",

        "order_id": order_id

    })

# ---------------- UPDATE ORDER ----------------

@app.route("/update_order", methods=["POST"])
def update_order():

    data = request.json

    now = datetime.now().strftime(
        "%Y-%m-%d"
    )

    supabase.table("orders").update({

        "status":
        data["status"],

        "location":
        data["location"],

        "updated_by":
        data["updated_by"],

        "last_updated":
        now

    }).eq(

        "order_id",
        data["order_id"]

    ).execute()

    supabase.table("activity_logs").insert({

        "operator_name":
        data["updated_by"],

        "action":
        f"Updated to {data['status']}",

        "order_id":
        data["order_id"],

        "time":
        now

    }).execute()

    socketio.emit(
        "order_updated",
        {"order_id": data["order_id"]}
    )

    return jsonify({
        "msg": "updated"
    })

# ---------------- GET ORDERS ----------------

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

# ---------------- GET LOGS ----------------

@app.route("/get_logs")
def get_logs():

    response = supabase.table(
        "activity_logs"
    ).select("*").execute()

    return jsonify(response.data)

# ---------------- EXCEL REPORT ----------------

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

# ---------------- PDF REPORT ----------------

@app.route("/download_pdf")
def download_pdf():

    response = supabase.table(
        "orders"
    ).select("*").execute()

    orders = response.data

    file_name = "report.pdf"

    doc = SimpleDocTemplate(
        file_name
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(

        Paragraph(
            "Order Tracker Report",
            styles['Title']
        )

    )

    elements.append(
        Spacer(1, 12)
    )

    for o in orders:

        text = f'''

        Order ID:
        {o['order_id']}<br/>

        Assigned Operator:
        {o['assigned_operator']}<br/>

        Status:
        {o['status']}<br/>

        Location:
        {o['location']}<br/>

        Last Updated:
        {o['last_updated']}<br/><br/>

        '''

        elements.append(

            Paragraph(
                text,
                styles['BodyText']
            )

        )

        elements.append(
            Spacer(1, 12)
        )

    doc.build(elements)

    return send_file(
        file_name,
        as_attachment=True
    )

# ---------------- PDF INVOICE ----------------

@app.route("/invoice/<order_id>")
def invoice(order_id):

    response = supabase.table(
        "orders"
    ).select("*").eq(
        "order_id",
        order_id
    ).execute()

    order = response.data[0]

    file_name = f"invoice_{order_id}.pdf"

    doc = SimpleDocTemplate(
        file_name
    )

    styles = getSampleStyleSheet()

    elements = []

    elements.append(

        Paragraph(
            "Order Invoice",
            styles['Title']
        )

    )

    text = f'''

    Order ID:
    {order['order_id']}<br/>

    Assigned Operator:
    {order['assigned_operator']}<br/>

    Status:
    {order['status']}<br/>

    Location:
    {order['location']}<br/>

    '''

    elements.append(

        Paragraph(
            text,
            styles['BodyText']
        )

    )

    doc.build(elements)

    return send_file(
        file_name,
        as_attachment=True
    )

# ---------------- QR CODE ----------------

@app.route("/generate_qr/<order_id>")
def generate_qr(order_id):

    url = (
        f"https://YOUR-RENDER-LINK.onrender.com/"
        f"track/{order_id}"
    )

    img = qrcode.make(url)

    file_name = f"{order_id}.png"

    img.save(file_name)

    return send_file(
        file_name,
        as_attachment=True
    )

# ---------------- BARCODE ----------------

@app.route("/generate_barcode/<order_id>")
def generate_barcode(order_id):

    code128 = barcode.get(

        'code128',

        order_id,

        writer=ImageWriter()

    )

    file_name = code128.save(order_id)

    return send_file(
        file_name,
        as_attachment=True
    )

# ---------------- TRACK ORDER ----------------

@app.route("/track/<order_id>")
def track_order(order_id):

    response = supabase.table(
        "orders"
    ).select("*").eq(
        "order_id",
        order_id
    ).execute()

    if len(response.data) == 0:

        return jsonify({
            "error": "Order Not Found"
        })

    return jsonify(response.data[0])

# ---------------- RUN ----------------

socketio.run(

    app,

    host="0.0.0.0",

    port=5000

)
