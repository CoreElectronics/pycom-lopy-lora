import time
from lora_api import loraAPI
from pysense import Pysense
from SI7006A20 import SI7006A20
from LTR329ALS01 import LTR329ALS01

# Set myself up for connection to the LoRa network
node = loraAPI(device_id=1, device_name="Node1", device_colour="red", device_colour_code=0xFF0000)

# Set up the Pysense so we can read sensors
py = Pysense()
si = SI7006A20(py)
lt = LTR329ALS01(py)

# Do this forever
while(True):

    # Read temperature and humidity from Pysense
    temperature = si.temperature()
    humidity = si.humid_ambient(temperature)

    # Send the data to the gateway.
    # This data structure is a dictonary: {"submits": thing_to_be_submitted}
    # And thing_to_be_submitted is another dictionary.
    # We use dictionaries and lists because they convert nicely into JSON (a plain text format)
    node.send_as_json({"submits": {"temperature": temperature, "humidity": humidity}})

    # Update the gateway every 10 seconds. That's not too much for LoRa to handle.
    time.sleep(10)
