from subprocess import check_output
import requests
from requests.exceptions import HTTPError
import re

node_MCU_IP = "http://192.168.4.1"

def wifi_connect(ssid, password):
    try:
        print("Connecting to %s" % ssid)
        response = check_output(["nmcli", "d", "wifi", "connect", ssid, "password", password])
        ssid_connected = check_output(["iwgetid"]).decode("utf-8")
        print(ssid_connected.split('"'))
        if(ssid_connected.split('"')[1] == ssid):
            print("Connected to %s" % ssid)
            return 0
        else:
            print("Error problem with connect")
            return -1
    except Exception as e:
        return -1


def wifi_request(cmd):
    print("Send cmd %s" % cmd)
    try:
        response = requests.get(node_MCU_IP+cmd)
    except Exception as exp:
        return -1
    else:
        print("Response %s" % response.text)
