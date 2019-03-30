from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import database_mqtt as db
import time
import datetime
 
app = Flask(__name__)
 
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

 
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
