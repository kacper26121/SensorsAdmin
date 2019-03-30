import sqlite3
import time
import datetime
import random


#Tworzenie tabel w bazie danych.
def sensor_create_table():
	conn = sqlite3.connect('mqtt.db')
	c = conn.cursor()
	c.execute('CREATE TABLE IF NOT EXISTS sensor_id(id_wpisu INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id TEXT)')
	c.execute('CREATE TABLE IF NOT EXISTS sensor_data(id_wpisu INTEGER PRIMARY KEY AUTOINCREMENT, sensor_id TEXT, temp_value TEXT, hum_value TEXT, press_value TEXT, ts DATE)')
	c.close()
	conn.close()

#Funkcja sprawdzajaca czy podany sensor jest w bazie danych.
def sensor_check(sensor_id): 
	conn = sqlite3.connect('mqtt.db')
	c = conn.cursor()
	c.execute('SELECT * FROM sensor_id WHERE sensor_id = (?)', [sensor_id])
	data = c.fetchall()
	c.close()
	conn.close()
	return not data


#Tworzenie nowego sensora w bazie danych, tylko gdy nie ma takiego w bazie danych.
def sensor_create_entry(sensor_id):
	wartosc = sensor_check(sensor_id)
	if wartosc:
		conn = sqlite3.connect('mqtt.db')
		c = conn.cursor()
		c.execute("INSERT INTO sensor_id (sensor_id) VALUES (?)", [sensor_id])
		conn.commit()
		c.close()
		conn.close()

#Wyswietlenie wszystkich sensorow z bazy danych - lista.
def sensor_get():
	conn = sqlite3.connect('mqtt.db')
	c = conn.cursor()
	c.execute('SELECT sensor_id FROM sensor_id')
	sensor_list = []
	for row in c.fetchall():
		sensor_list.append(str(row[0]))
	c.close()
	conn.close()
	return sensor_list
	

#Dodanie nowego wpisu z pomiarami do bazy danych tylko wtedy, gdy sensor jest w bazie danych.
def sensor_data_entry(sensor_id, temp_value, hum_value, press_value): 
	wartosc = sensor_check(sensor_id)
	if not wartosc:
		conn = sqlite3.connect('mqtt.db')
		c = conn.cursor()
		czas_wpisu = int(time.time())
		data_wpisu = datetime.datetime.fromtimestamp(czas_wpisu).strftime('%Y-%m-%d %H:%M:%S')
		c.execute("INSERT INTO sensor_data (sensor_id, temp_value, hum_value, press_value, ts) VALUES (?, ?, ?, ?, ?)", 
		(sensor_id, temp_value, hum_value, press_value, data_wpisu))
		conn.commit()
		c.close()
		conn.close()

#Pobranie wszystkich danych z wybranego sensora
def sensor_data_get_all(sensor_id):
	conn = sqlite3.connect('mqtt.db')
	c = conn.cursor()
	c.execute('SELECT temp_value, hum_value, press_value, ts FROM sensor_data WHERE sensor_id=:sensor_id', {"sensor_id": sensor_id})
	sensor_data_list = []
	for row in c.fetchall():
		sensor_data_list.append([str(row[0]), str(row[1]), str(row[2]), str(row[3])])
#		print row[0], row[1], row[2], row[3]
	c.close()
	conn.close()
	return sensor_data_list

#Pobranie wszystkich danych z jednego sensora w podanym zakresie
def sensor_data_get(sensor_id, date_begin, date_end):
	conn = sqlite3.connect('mqtt.db')
	c = conn.cursor()
	#c.execute('SELECT temp_value, hum_value, press_value, ts FROM sensor_data WHERE sensor_id=:sensor_id AND ts BETWEEN "2019-03-24 00:00:00" AND "2019-03-24 13:40:05" ', {"sensor_id": sensor_id})
	c.execute("SELECT temp_value, hum_value, press_value, ts FROM sensor_data WHERE sensor_id=:sensor_id AND ts BETWEEN \"" + date_begin + "\" AND \"" + date_end + "\"", {"sensor_id": sensor_id})
	sensor_data_date_list = []
	for row in c.fetchall():
		sensor_data_date_list.append([row[0],row[1],row[2],row[3]])
#		print row[0], row[1], row[2], row[3]
	c.close()
	conn.close()
	return sensor_data_date_list
	
def last_record(sensor_id):
	conn = sqlite3.connect('mqtt.db')
	c = conn.cursor()
	c.execute('SELECT temp_value, hum_value, press_value, ts FROM sensor_data WHERE sensor_id=:sensor_id ORDER BY id_wpisu DESC LIMIT 1', {"sensor_id":sensor_id})
	last_record = []
	for row in c.fetchall():
		last_record.append(row[0])
		last_record.append(row[1])
		last_record.append(row[2])
		last_record.append(row[3])
#		print row[0], row[1], row[2], row[3]
	c.close()
	conn.close()
	return last_record
		
#---------------------------------------------------------
#Tworzenie kolumn w bazie danych (jesli nie sa stworzone).
#sensor_create_table()
#---------------------------------------------------------

#Pobranie ostataniego rekordu z bazy danych dla podanego sensora
#last_record('sensor_0000')

#Pobranie wszystkich danych pomiarowych z bazy danych dla sensora
#sensor_data_get_all('sensor_0000')

#---------------------------------------------------------
#Test odpytania bazy danych o pomiary w przedziale czasowym
#sensor_data_get('sensor_0000', '2019-03-24 13:40:00', '2019-03-24 13:50:05')
#---------------------------------------------------------

#---------------------------------------------------------
#Szybkie stworzenie sensora w bazie danych:
#sensor_create_entry('sensor_0000')
#---------------------------------------------------------

#---------------------------------------------------------
#Szybkie stworzenie 5 wpisow pomairow z sensora do bazy danych:
#sensor_data_entry('sensor_0000', '0', '45', '1005')
#sensor_data_entry('sensor_0000', '21', '65', '1001')
#sensor_data_entry('sensor_0000', '12', '32', '989')
#sensor_data_entry('sensor_0000', '33', '21', '1023')
#sensor_data_entry('sensor_0000', '45', '78', '997')
#---------------------------------------------------------

