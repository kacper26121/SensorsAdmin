import sys
sys.path.insert(0, '/home/adi/mqtt')
import database_mqtt as db_mqtt

import paho.mqtt.client as mqtt

#Dane servera MQTT
server = "m24.cloudmqtt.com"
port = 15966

#Dane do logowania
username = "wnztitmo"
password = "pcPKdXRULLdf"
topic = 'sensor/+'
message = "0"

def on_connect(client, userdata, flags, rc):
    print("Server: " + mqtt.connack_string(rc))

def on_message(client, obj, msg):
	print("Otrzymana wiadomosc: " + "\nTopic: " + msg.topic + "\nWiadomosc: "+ str(msg.payload))
	message = str(msg.payload)
	rs = message.split(" ")

#---------------------------------------------------------------------
#Sprawdzenie topic'u w wiadomosci - jesli jest ok to wpis odczytow 
#czujnika do bazy danych dla czujnika z ID z topic'u.
#rs[] - tabela z elementami do wpisu do bazy danych
#rs[0] - sensor_id
#rs[1] - temp_value
#rs[2] - hum_value
#rs[3] - press_value 

	if msg.topic == 'sensor/0000':
		db_mqtt.sensor_data_entry(rs[0], rs[1], rs[2], rs[3])



#def on_publish(client, obj, mid):
#    print("mid: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    print("Subskrypcja z oczekiwaniem na topic: " + topic)

def on_log(client, obj, level, string):
    print(string)


#---------------------------------------------------------------------
#-----------------------INICJALIZACJA---------------------------------
#---------------------------------------------------------------------
mqttc = mqtt.Client()

#---------------------Przypisanie wywolania eventow-------------------
mqttc.on_message = on_message
mqttc.on_connect = on_connect
#mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

#--------------------------Debug (wiadomosci)-------------------------
#mqttc.on_log = on_log

#-----------------------Podlaczenie do serwera------------------------
mqttc.username_pw_set(username, password)
mqttc.connect(server, port)

#------------------Start subskrypcji QoS level 0----------------------
mqttc.subscribe(topic, 0)

#----------------------Publikacja wiadomosci--------------------------
# mqttc.publish(topic, "my message")

#---------------------------------------------------------------------
#---------------------------------------------------------------------
#---------------------------------------------------------------------


#---------------------------------------------------------------------
#------------Petla nieskonczona, wyjscie jak wystapi blad-------------
#---------------------------------------------------------------------
rc = 0
while rc == 0:
    rc = mqttc.loop()
print("rc: " + str(rc))
#---------------------------------------------------------------------
#---------------------------------------------------------------------
#---------------------------------------------------------------------
