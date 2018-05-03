import time
from lora_api import loraAPI

temp = 33
humi = 66
node = loraAPI(device_id=1, device_name="Node1", device_colour="red", device_colour_code=0xFF0000)

while(True):
    node.to_gateway({"temperature": temp, "humidity": humi}, ["time", "location"])
    node.acknowledge()
    time.sleep(10)
