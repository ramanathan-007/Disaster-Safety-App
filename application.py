from datetime import datetime, timedelta
import os

from flask import Flask, flash, redirect, render_template, request, session, jsonify
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import json
from math import *
import urllib3
import requests
import pygame


import sqlite3

conn = sqlite3.connect('alerts (1).db', check_same_thread=False)
db = conn.cursor()

urllib3.disable_warnings()
# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

pygame.mixer.init()

epicenter = {"lat": 33.4, "lng": -75.5}


def dist(lat1, lon1, lat2, lon2):
    R = 6371e3
    toRad = pi / 180
    lat1, lat2, lon1, lon2 = [float(x) for x in [lat1, lat2, lon1, lon2]]
    phi_1 = lat1 * toRad
    phi_2 = lat2 * toRad
    delta_phi = (lat2-lat1) * toRad
    delta_lambda = (lon2-lon1) * toRad

    a = sin(delta_phi/2) * sin(delta_phi/2) + cos(phi_1) * \
        cos(phi_2) * sin(delta_lambda/2) * sin(delta_lambda/2)
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    d = R * c
    return d


def updateDistances():
    for p in ZONE_ARR:
        p['distance'] = dist(p['lat'], p['long'],
                             epicenter['lat'], epicenter['lng'])


try:
    with open('data.json') as f:
        ZONE_ARR = json.load(f)
except:
    ZONE_ARR = []

try:
    data = requests.get(
        "https://weather.terrapin.com/wx/storm_show.jsp?area=ATL&storm=06A&dtype=ASCII", verify=False)
    _, _, lat, lon, _, _ = [x for x in data.text.splitlines(
    ) if '<' not in x and '>' not in x and len(x) > 5][-1].split(', ')
    epicenter = {"lat": float(lat), "lng": float(lon)}
    print("Got em coordinates!")
except:
    pass

updateDistances()


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def menu():
    return render_template("menu.html")


@app.route("/govtalerts", methods=["GET", "POST"])
def govtalerts():

    if request.method == "POST":
        if not request.form.get("username"):
            return "Must enter a username"
        elif not request.form.get("password"):
            return "Must enter the password"
        elif not request.form.get("calamity"):
            return "Must enter the calamity"
        elif not request.form.get("location"):
            return "Must enter the location"
        elif not request.form.get("description"):
            return "Must enter the description"

        username = request.form.get("username")
        password = request.form.get("password")
        rows = db.execute(
            "SELECT * FROM govtids WHERE username = ?", (username,))
        row = rows.fetchone()
        if row is None or not check_password_hash(row[2], request.form.get("password")):
            return "Invalid username and/or password"

        # username = request.form.get("username")
        # password = request.form.get("password")
        # rows = db.execute(
        #     "SELECT * FROM govtids WHERE username = ?", (username,))
        # row = rows.fetchone()  # Changed to rows.fetchone()

        # if row is None:
        #     return "Invalid username"

        # # Make sure the index matches the password hash's location in the row
        # stored_password_hash = row[2]
        # if not check_password_hash(stored_password_hash, password):
        #     return "Invalid password"

        c = request.form.get("calamity")
        l = request.form.get("location")
        d = request.form.get("description")
        s = {"success": "yes"}

        db.execute("INSERT INTO govtalerts (calamity,location,description) VALUES (?,?,?)",
                   (c, l, d))
        conn.commit()
        return "Alert Issued Successfully.", 200
    else:
        return render_template("govtalerts.html")


@app.route("/getgovtalerts")
def getgovtalerts():

    alerts = []
    w = db.execute("SELECT * FROM govtalerts ORDER BY id DESC ")
    for w1 in w:
        s = {"datetime": w1[1], "location": w1[3],
             "calamity": w1[2], "description": w1[4]}
        alerts.append(s)

    return jsonify(alerts)


# @app.route("/generateids")
# def generateids():
#     usernames = ["earthquakeagencyofasia", "hurricaneagencyofasia",
#                  "floodagencyofasia", "disastermanagementagencyofasia", "malaysiangovt"]
#     passwords = ["eaoi", "haoi", "faoi", "dmaoi", "mgt"]

#     for i in range(5):
#         db.execute("INSERT INTO govtids (username,password) VALUES (?,?)",
#                    (usernames[i], generate_password_hash(passwords[i])))
#     print("Successfully entered")


@app.route("/viewgovtalerts")
def viewgovtalerts():

    alerts = []
    w = db.execute("SELECT * FROM govtalerts ORDER BY id DESC ")
    for w1 in w:
        s = {"datetime": w1[1], "location": w1[3],
             "calamity": w1[2], "description": w1[4]}
        alerts.append(s)

    pygame.mixer.music.load('./templates/alarm.mp3')
    pygame.mixer.music.play()
    return render_template("view.html", rows=alerts, alert="Government Issued Alerts")

# @app.route("/viewgovtalerts")
# def viewgovtalerts():
#     alerts = []


#     w = db.execute("SELECT * FROM govtalerts ORDER BY id DESC ")
#     for w1 in w:
#         alert_time = datetime.strptime(w1[1], '%Y-%m-%d %H:%M:%S')  # Assuming datetime is in the format 'YYYY-MM-DD HH:MM:SS'

#         time_difference = alert_time - current_time

#         if timedelta(hours=-5) <= time_difference <= timedelta(hours=0):
#             # Trigger alarm as the alert is within 5 hours
#             alarm_path = os.path.join("static", "audio", "alarm.mp3")
#             os.system(f"start {alarm_path}")  # This assumes Windows OS for playing the alarm. Adjust for other OS.

#         s = {
#             "datetime": w1[1],
#             "location": w1[3],
#             "calamity": w1[2],
#             "description": w1[4]
#         }
#         alerts.append(s)

#     return render_template("view.html", rows=alerts, alert="Government Issued Alerts")
# @app.route("/viewcommonalerts")
# def viewcommonalerts():

#     alerts = []
#     w = db.execute("SELECT * FROM commonalerts ORDER BY id DESC ")
#     for w1 in w:
#         s = {"datetime": w1[1], "location": w1[3],
#              "calamity": w1[2], "description": w1[4]}
#         alerts.append(s)

#     return render_template("view.html", rows=alerts, alert="Common Alerts")
@app.route("/zonealerts")
def zonealerts():
    return render_template('index.html')


@app.route('/submitData', methods=['POST'])
def submitData():
    obj = {
        "name": request.form["name"],     # Label
        "status": request.form["status"],  # Label
        "lat": request.form["lat"],               # Location
        "long": request.form["long"],             # Location
        "food": request.form["food"],             # Numerical
        "water": request.form["water"],           # Numerical
        "capacity": request.form["capacity"],     # Numerical
        "occupancy": request.form["occupancy"],   # Numerical
        "electricity": request.form["electricity"],  # Boolean
    }
    obj['distance'] = dist(obj['lat'], obj['long'],
                           epicenter['lat'], epicenter['lng'])
    added = 0
    i = 0
    for p in ZONE_ARR:
        if p['name'] == request.form["name"]:
            ZONE_ARR[i] = obj
            added = 1
            break
        i = i+1
    if not added:
        ZONE_ARR.append(obj)
    with open('data.json', 'w') as outfile:
        json.dump(ZONE_ARR, outfile)
    return redirect('/addData')


@app.route('/addData')
def addData():
    return render_template('addData.html')


@app.route('/api/listZones')
def listZones():
    return json.dumps(ZONE_ARR)


@app.route('/api/getEpicenter')
def getEpicenter():
    return json.dumps(epicenter)


@app.route('/manufacturing-plant', methods=['GET'])
def manufacturing_plant_management():
    return render_template('plant.html')


app.run(debug=True)
