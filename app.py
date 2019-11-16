from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify, Response
import os
import database_mqtt as db
import scan_wifi as wifi
import time
import datetime
import json
import iwlist
from subprocess import check_output
from flask_socketio import SocketIO, send, emit
import threading
from subscribe_mqtt import MqttServer, mqtt
import math
import numpy as np

app = Flask(__name__)
socketio = SocketIO(app)

def PMV(Temp):

    Ti = Temp
    M = 100.00                                  # poziom metabolizmu [W/m3]
    W = 10.0                                    # praca zewnetrzna [W/m3]
    Pa = 1800.0                                 # czastkowe cisnienie pary wodnej [Pa]
    Tr = 20.0                                   # sr. temperatura promieniowania
    Tcl = 15.0                                  # temp. powierzchni odziezy
    Fcl = 0.7                                   # stosunek pola powierzchni ciala odkrytego do ciala zakrytego odzieza
    Hcl = 7                                     # wsplczynnik przejmowania ciepla prze konwekcje [W/m2]
    PMV = 0
    # Icl = 0.23                                # opor cieplny odziezy

    a1 = 0.303 * math.exp(-0.036 * M + 0.028)
    a2 = (M - W)
    # Tcl= 35.7 -0.028*a2 -Icl*(3.96*pow(10,-8)*Fcl)*(((Tcl+273)*4-(Tr+274)*4))+Fcl*Hcl*(Tcl-Ti)
    a3 = 3.05 * pow(10, -3) * (5733 - 6.99 * (M - W) - Pa)
    a4 = 0.42 * ((M - W) - 58.15)
    a5 = 1.7 * pow(10, -5) * M * (5867 - Pa)
    a6 = 0.001 * 4 * M * (34 - Ti)
    a7 = 3.96 * pow(10, -8) * Fcl * ((Tcl + 273) * 4 - (Tr + 274) * 4)
    a8 = Fcl * Hcl * (Tcl - Ti)
    PMV = (a1) * (a2 - a3 - a4 - a5 - a6 - a7 - a8)
    return PMV

def PMV_RGB(PMV):

    # PMV has value from -3 to 3 - create list
    PMVrange = np.arange(-3, 3, 0.1)

    # match closest PMV value tovalue from created list
    index = closest(PMVrange, PMV)

    #generate list of color from red to green with lenght the same as PMVrange
    #red = Color("red")
    #colors = list(red.range_to(Color("green"), len(PMVrange)))

    # or gradient from blue via green to red
    col=list(["#0054E5", "#0061E4", "#006EE3", "#007BE3", "#0088E2", "#0095E1", "#00A2E1", "#00AFE0", "#00BCE0", "#00C8DF", "#00D5DE", "#00DEDA", "#00DDCD", "#00DDBF", "#00DCB2", "#00DBA4", "#00DB97", "#00DA89", "#00DA7C", "#00D96F", "#00D862", "#00D855", "#00D748", "#00D73B", "#00D62E", "#00D521", "#00D515", "#00D408", "#03D400", "#10D300", "#1CD200", "#29D200", "#35D100","#41D100", "#4DD000", "#59CF00", "#65CF00", "#71CE00", "#7DCE00", "#89CD00", "#94CC00", "#A0CC00","#ACCB00", "#B7CB00", "#C2CA00", "#C9C500", "#C9B800", "#C8AC00", "#C8A000", "#C79400", "#C68700", "#C67B00", "#C56F00", "#C56300", "#C45700", "#C34C00","#C34000", "#C23400", "#C22800", "#C11D00", "#C01100", "#C00600", "#BF0004", "#BF000F"])

    # len(PMVrange) = len(colorse) -> so we can take the same value from color list
    PMVcolor = col[index]

    #return background color in hex
    return PMVcolor

def closest(list, Number):
    aux = []
    for valor in list:
        aux.append(abs(Number-valor))

    return aux.index(min(aux))

class CMD:
    GET_WIFI_LIST = 0x01
    CHECK_WIFI_CONNECT = 0x02
    SAVE = 0x03
    CONNECT_MQTT = 0x04
    START_PAIRING = 0x05

class SAVE_VALUE:
    WIFI_DATA = 0x01
    MQTT_DATA = 0x02

class WiFiThread(threading.Thread):
    def __init__(self, ssid, password, response):
        threading.Thread.__init__(self)
        self.ssid = ssid
        self.password = password
        self.response = response

    def CheckConnect(self):
        if(wifi.wifi_connect(self.ssid,self.password)==0):
            print("Connected")
            self.response["data"] = 1
        else:
            print("Problem with Connected")
            self.response["data"] = 0
        socketio.emit('response', self.response)

    def run(self):
        self.CheckConnect()


def connect(client, userdata, flags, rc):
    print("Server: " + mqtt.connack_string(rc))

def message(client, obj, msg):
    print("Otrzymana wiadomosc: " + "\nTopic: " + msg.topic + "\nWiadomosc: "+ str(msg.payload))
    message = str(msg.payload, 'utf-8')
    rs = message.split(" ")

    if msg.topic == 'sensor/+':
        db.sensor_data_entry(rs[0], rs[1], rs[2], rs[3])

def subscribe(client, obj, mid, granted_qos):
    print("Subskrypcja z oczekiwaniem na topic: " + topic)

#mqtt_sensor = MqttServer("m24.cloudmqtt.com", 15966, "wnztitmo", "0qytqhgzfa9A", message, connect, subscribe)

@socketio.on('request')
def reguest(value):
    print(value)
    response = {"cmd" : None, "data" : None}

    if(value["cmd"]==CMD.GET_WIFI_LIST):
        content = iwlist.scan(interface='wlp2s0')
        cells = iwlist.parse(content)

        response["cmd"] = CMD.GET_WIFI_LIST
        response["data"] = cells
        emit('response', response)
    elif(value["cmd"]==CMD.CHECK_WIFI_CONNECT):
        response["cmd"] = CMD.CHECK_WIFI_CONNECT
        thread = WiFiThread(value['data']['ssid'],value['data']['password'], response)
        thread.start()
    elif(value["cmd"]==CMD.CONNECT_MQTT):
        response["cmd"] = CMD.CONNECT_MQTT
        response["data"] = 1

        print("reconnect")
        mqtt_sensor.ChangeDataToConnect(value["data"]["serwer"], int(value["data"]["port"]), value["data"]["user"], value["data"]["password"])
        mqtt_sensor.Reconnect()
        if not mqtt_sensor.is_alive():
            mqtt_sensor.start()

        with open("data.json","r+") as json_file:
            data = json.load(json_file)
            data["serwer"] = value["data"]["serwer"]
            data["port"] = value["data"]["port"]
            data["user_mqtt"] = value["data"]["user"]
            data["password_mqtt"] = value["data"]["password"]
            json_file.seek(0)
            json.dump(data, json_file)

        emit('response', response)
    elif(value["cmd"]==CMD.SAVE):
        response["cmd"] = CMD.SAVE

        if(value["data"]["type"]==SAVE_VALUE.WIFI_DATA):
            response["data"] = {"type":SAVE_VALUE.WIFI_DATA, "status":1}

            with open("data.json","r+") as json_file:
                data = json.load(json_file)
                data["ssid"] = value["data"]["ssid"]
                data["password_ssid"] = value["data"]["password"]
                json_file.seek(0)
                json.dump(data, json_file)
                response["data"]["status"] = 0

            emit('response', response)
    elif(value["cmd"]==CMD.START_PAIRING):
        with open("data.json","r") as json_file:
            data = json.load(json_file)
        print("Pairnig")
        wifi.wifi_request("/paired?ssid={}&password_ssid={}".format(data["ssid"],data["password_ssid"]))

@app.route('/')
def home():
    sensor_list = []
    db_sensors = db.sensor_get()

    if session.get('logged_in') == "Admin" or session.get('logged_in') == "User":
        #Pobranie wszystkich sensorów z bazy danych oraz najnowszych danych
        for sensor in db_sensors:
            db_last_measured = db.last_record(sensor)
            temp = float(db_last_measured[0])
            sensor_list.append([sensor, db_last_measured[0], db_last_measured[1], db_last_measured[2], round(PMV(temp),3), PMV_RGB(PMV(temp))])
        print(sensor_list)

        return render_template('index.html', list = sensor_list)
    else:
        return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'admin' and request.form['username'] == 'admin':
        session['logged_in'] = "Admin"
    elif request.form['password'] == 'user' and request.form['username'] == 'user':
        session['logged_in'] = "User"
    else:
        flash('wrong password!')
    return home()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

@app.route("/charts", methods=['GET'])
def show_charts():
    if not(session.get('logged_in') == "Admin" or session.get('logged_in') == "User"):
        return render_template('login.html')

    select_list = db.sensor_get()
    db_sensors = []
    db_sensors_value = {}

    from_date_str 	= request.args.get('from',time.strftime("%Y-%m-%d 00:00:00")) #Get the from date value from the URL
    to_date_str 	= request.args.get('to',time.strftime("%Y-%m-%d %H:%M:%S"))   #Get the to date value from the URL
    select      	= request.args.get('select','all')   #Get select sensor from the URL

    if(select == "all"):
        db_sensors = db.sensor_get()
    else:
        db_sensors.append(select)

    for sensor in db_sensors:
        db_sensors_value.update({sensor:db.sensor_data_get(sensor,from_date_str,to_date_str)});

    print(db_sensors_value)
    return render_template('charts.html', list = db_sensors, value = db_sensors_value, sensor_select = select_list, from_date = from_date_str, to_date = to_date_str, select_sensor = select)

@app.route("/settings")
def settings():
    if not(session.get('logged_in') == "Admin" or session.get('logged_in') == "User"):
        return render_template('login.html')

    db_sensors = db.sensor_get()
    with open("data.json") as json_file:
        data = json.load(json_file)

    return render_template('settings.html', list = db_sensors, settings=data)


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    socketio.run(app)
