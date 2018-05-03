import json
import time
from lora_api import loraAPI
from machine import Timer

# Create a chronometer to measure elapsed time
# This is used later to ensure we don't wait
# forever for something to happen
chrono = Timer.Chrono()
chrono.start()

# When we are given values for these, store them here
temperature = None
humidity = None

# Make this a gateway on the LoRa network.
gateway = loraAPI(device_name='Gateway', device_colour="blue", device_colour_code=0x0000FF, is_gateway=True)

# Do this forever!
while (True):

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
            if "humidity" in submits:
                humidity = submits['humidity']
                print("humi >> {}".format(humidity))

        # A "requests" package asks us for data we have
        # In reply we send a "responses" package
        if "requests" in data:
            if "temperature" in data["requests"] and "humidity" in data["requests"]:
                gateway.send_as_json({"responses": {"temperature": temperature, "humidity": humidity}}, device_id)
