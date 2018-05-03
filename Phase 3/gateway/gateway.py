from lora_api import loraAPI

# makes a gateway type LoRa object
gateway = loraAPI(device_name='Gateway', device_colour="blue", device_colour_code=0x0000FF, is_gateway=True)
while (True):
    gateway.receive()
