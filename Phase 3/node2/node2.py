import time
from lora_api import loraAPI

node = loraAPI(device_id=2, device_name="Node2", device_colour="green", device_colour_code=0x00FF00)

while(True):
    node.to_gateway({}, ["time"])
    node.acknowledge()
    time.sleep(10)
