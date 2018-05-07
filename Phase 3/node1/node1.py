# Chris@Core: in getting rid of all the redundant code we had to make
# a new file to keep it all together. Now the only thing our devices
# need to import is the new loraAPI, that's in /lib/lora_api.py
import time
from lora_api import loraAPI

# Chris@Core: Here's a couple of dummy data values we want to send
# to the gateway
temp = 33
humi = 66

# Chris@Core: This is how we use the loraAPI we added. We create
# an 'object' using the loraAPI 'class'. When we create this thing
# we give it all the details it will need to know about itself.
node = loraAPI(device_id=1, device_name="Node1", device_colour="red", device_colour_code=0xFF0000)

# Chris@Core: We still want the node to send messages repeatedly
while(True):
    # Chris@Core: The to_gateway() function expects two things:
    # - a "dictionary" of key:value pairs. These are things we're sending
    # to the gateway.
    # - a "list" of things we want back from the Gateway.
    node.to_gateway({"temperature": temp, "humidity": humi}, ["time", "location"])
    # Chris@Core: As usual, after every package we expect an acknowledgement()
    node.acknowledge()
    # Chris@Core: Then we wait before sending another package
    time.sleep(5)
