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

app = Flask(__name__)
socketio = SocketIO(app)

class CMD:
    GET_WIFI_LIST = 0x01
    CHECK_WIFI_CONNECT = 0x02
    SAVE = 0x03
    CONNECT_MQTT = 0x04

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


@socketio.on('request')
def reguest(value):
    print(json)
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

        # if(value["data"]["connect"]):


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
                json_file.close()
                response["data"]["status"] = 0

            emit('response', response)
        elif(value["data"]["type"]==SAVE_VALUE.MQTT_DATA):
            response["data"] = {"type":SAVE_VALUE.MQTT_DATA, "status":1}

            with open("data.json","r+") as json_file:
                data = json.load(json_file)
                data["serwer"] = value["data"]["serwer"]
                data["port"] = value["data"]["port"]
                data["user_mqtt"] = value["data"]["user"]
                data["password_mqtt"] = value["data"]["password"]
                json_file.seek(0)
                json.dump(data, json_file)
                json_file.close()
                response["data"]["status"] = 0

            emit('response', response)


@app.route('/')
def home():
    sensor_list = []
    db_sensors = db.sensor_get()

    if session.get('logged_in') == "Admin" or session.get('logged_in') == "User":
        #Pobranie wszystkich sensorów z bazy danych oraz najnowszych danych
        for sensor in db_sensors:
            db_last_measured = db.last_record(sensor)
            sensor_list.append([sensor, db_last_measured[0], db_last_measured[1], db_last_measured[2] ])
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
