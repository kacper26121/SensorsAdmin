import database_mqtt as db_mqtt
import paho.mqtt.client as mqtt
import threading


def on_connect(client, userdata, flags, rc):
    print("Server: " + mqtt.connack_string(rc))

def on_message(client, obj, msg):
    print("Otrzymana wiadomosc: " + "\nTopic: " + msg.topic + "\nWiadomosc: "+ str(msg.payload))
    message = str(msg.payload, 'utf-8')
    reviews = message.split(" ")

    if msg.topic == 'sensor/0000':
        db_mqtt.sensor_data_entry(reviews[0], reviews[1], reviews[2], reviews[3])

def on_subscribe(client, obj, mid, granted_qos):
    print("Subskrypcja z oczekiwaniem na topic: " + topic)



class MqttServer(mqtt.Client, threading.Thread):
    def __init__(self, server, port, username, password, messageClb, connectClb, subscribeClb):
        mqtt.Client.__init__(self)
        threading.Thread.__init__(self)
        self.topic = "sensor/+"
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.on_message = messageClb
        self.on_connect = connectClb
        self.on_subscribe = subscribeClb
        self.rc = 0


    def Start(self):
        self.subscribe(self.topic, 0)
        while 1:
            self.loop_forever()

    def ChangeDataToConnect(self, server, port, username, password):
        self.server = server
        self.port = port
        self.username = username
        self.password = password

    def Reconnect(self):
        self.disconnect()
        self.Connect()

    def Connect(self):
        self.username_pw_set(self.username, self.password)
        self.connect(self.server, self.port)

#---------------------------------------------------------------------
#------------Petla nieskonczona, wyjscie jak wystapi blad-------------
#---------------------------------------------------------------------

if __name__ == "__main__":
    mqtt_sensor = MqttServer("m24.cloudmqtt.com", 15966, "wnztitmo", "0qytqhgzfa9A", on_message, on_connect, on_subscribe)

    mqtt_sensor.Connect()
    mqtt_sensor.Start()

    # rc = 0
    # while rc == 0:
    #     rc = mqtt_sensor.loop()
