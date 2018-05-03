import json
import time
import machine                # Interfaces with hardware components
import ubinascii              # Needed to run any MicroPython code
from network import WLAN      # For operation of WiFi network
from machine import Timer
from lora_api import loraAPI
from umqtt import MQTTClient  # For use of MQTT protocol to talk to Adafruit IO

# SETTINGS

# Wireless network
WIFI_SSID = "IoT"
WIFI_PASS = "79Password#" # No this is not our regular password. :)

# Adafruit IO (AIO) configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "CoreChris"
AIO_KEY = "7b2d0601a9694589a52fb2d614122cff"
AIO_CLIENT_ID = ubinascii.hexlify(machine.unique_id())  # Can be anything
AIO_CONTROL_FEED = "CoreChris/feeds/control"
AIO_TEMP_FEED = "CoreChris/feeds/temp"
AIO_HUMI_FEED = "CoreChris/feeds/humi"

LORA_SENSOR_DEVICE_ID = 1

# End SETTINGS

# FUNCTIONS

# Function to respond to messages from Adafruit IO
def sub_cb(topic, msg):          # sub_cb means "callback subroutine"

    print("io.adafruit.com says: {} {}".format(topic, msg))          # Outputs the message that was received. Debugging use.
    if int(msg) == 1:
        gateway.send_as_json({"requests": ["temperature", "humidity"]}, LORA_SENSOR_DEVICE_ID)

def send_temp_to_aio():
    global temperature  # This makes the function use the variable called 'humidity'
                        # that is declared outside of this function.

    send_to_aio(AIO_TEMP_FEED, temperature)

def send_humi_to_aio():
    global humidity     # This makes the function use the variable called 'humidity'
                        # that is declared outside of this function.

    send_to_aio(AIO_HUMI_FEED, humidity)

def send_to_aio(feed, value):

    value_string = str(value)
    print("Publishing: {0} to {1} ... ".format(str(value_string), feed), end='')
    try:
        adafruit_io.publish(topic=feed, msg=str(value_string))
        print("DONE")
    except Exception as e:
        print("FAILED")

# CONNECT TO WIFI
# We need to have a connection to WiFi for Internet access
# Code source: https://docs.pycom.io/chapter/tutorials/all/wlan.html

print("Connecting to WiFi ... ", end='')
wlan = WLAN(mode=WLAN.STA)
wlan.connect(WIFI_SSID, auth=(WLAN.WPA2, WIFI_PASS), timeout=5000)

while not wlan.isconnected():    # Code waits here until WiFi connects
    machine.idle()

print("done.")

# CONNECT TO ADAFRUIT IO
# Use the MQTT protocol to connect to Adafruit IO
adafruit_io = MQTTClient(AIO_CLIENT_ID, AIO_SERVER, AIO_PORT, AIO_USER, AIO_KEY)

# Subscribed messages will be delivered to this callback
adafruit_io.set_callback(sub_cb)
adafruit_io.connect()
adafruit_io.subscribe(AIO_CONTROL_FEED)
print("Connected to %s, subscribed to %s topic" % (AIO_SERVER, AIO_CONTROL_FEED))

# When we are given values for these, store them here
temperature = None
humidity = None

# Make this a gateway on the LoRa network.
gateway = loraAPI(device_name='Gateway', device_colour="blue", device_colour_code=0x0000FF, is_gateway=True)

# Do this forever!
while (True):

    # Check for an MQTT message from Adafruit IO
    adafruit_io.check_msg()

    # Receive the next LoRa package
    # It will either be an update from node1, or a request for data from node2
    # After this line, device_id is the number of the node to reply to.
    # If receive_json() worked, we'll have a Python dictionary object with
    # either a dictionary {} or a list [] inside it
    device_id, data = gateway.receive_json()

    if device_id and data:  # Ensure a valid package before trying to dissect it.
                            # Same as: if device_is is not None and data is not None:

        # Note that we don't decide what to do based on which
        # device_id sent the package. The contents of the package
        # itself is what determines what we do with it. We can
        # reassign device_ids however we like, it will still work.

        # A "submits" package provides data we want
        # Dictionaries have {key: value} pairs in them.
        # We're asking if there's a key called "submits"
        if "submits" in data:

            # Now we'll take the value side of the "submits" pair...
            submits = data['submits']

            # ...and look inside that for another dictionary with keys
            # for "temperature" and "humidity". If found, grab their values.
            if "temperature" in submits:
                temperature = submits['temperature']
                print("Temp >> {}".format(temperature))
                send_temp_to_aio()
            if "humidity" in submits:
                humidity = submits['humidity']
                print("humi >> {}".format(humidity))
                send_humi_to_aio()

        # A "requests" package asks us for data we have
        # In reply we send a "responses" package
        if "requests" in data:
            if "temperature" in data["requests"] and "humidity" in data["requests"]:
                gateway.send_as_json({"responses": {"temperature": temperature, "humidity": humidity}}, device_id)
