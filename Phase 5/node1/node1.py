import time
from lora_api import loraAPI
from pysense import Pysense
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01

UPDATE_INTERVAL = 10000 # milliseconds

# Set myself up for connection to the LoRa network
node = loraAPI(device_id=1, device_name="Node1", device_colour="red", device_colour_code=0xFF0000)

# Set up the Pysense so we can read sensors
py = Pysense()
si = SI7006A20(py)
lt = LTR329ALS01(py)

def send_measurements():

    # Read temperature and humidity from Pysense
    temperature = si.temperature()
    humidity = si.humid_ambient(temperature)

    # Send the data to the gateway.
    # This data structure is a dictonary: {"submits": thing_to_be_submitted}
    # And thing_to_be_submitted is another dictionary.
    # We use dictionaries and lists because they convert nicely into JSON (a plain text format)
    node.send_as_json({"submits": {"temperature": temperature, "humidity": humidity}})

# This function can be called repeatedly at a high rate. It does nothing
# if no new LoRa message has been received since it last ran.
def check_lora_messages():

    # Get the last LoRa package containing data in JSON format
    device_id, data = node.receive_json()

    # If there was a message and both device_id and data (from JSON text) was understood...
    if device_id and data:
        # Look inside the data dictionary for a key of "requests" which has inside it
        # a list containing both the words "temperature" and "humidity"
        if "requests" in data and "temperature" in data["requests"] and "humidity" in data["requests"]:
            # If all that succeeds, it's a request to update the gateway with the sensor data
            send_measurements()

# last_update_time needs to be set before the while(True) loop
# so UPDATE_INTERVAL can be correctly observed
last_update_time = time.ticks_ms()

# Do this forever
while(True):

    # If anything came in on the LoRa network, handle that message now
    check_lora_messages()

    # Send updates to the gateway on a fixed interval without using time.sleep()
    if (time.ticks_ms() - last_update_time) > UPDATE_INTERVAL:
        send_measurements()
        last_update_time = time.ticks_ms()
