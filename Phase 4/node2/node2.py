import time
import struct
import json
from lora_api import loraAPI
from machine import Pin
from pyb_gpio_lcd import GpioLcd

# Set myself up for connection to the LoRa network
node = loraAPI(device_id=2, device_name="Node2", device_colour="green", device_colour_code=0x00FF00)

# Need to look at the pinout diagram for the Pycom microcontroller
# to make sure all these pins are available.
lcd = GpioLcd(rs_pin=Pin('P2'), enable_pin=Pin('P3'), d4_pin=Pin('P4'), d5_pin=Pin('P8'), d6_pin=Pin('P9'), d7_pin=Pin('P10'), num_lines=2, num_columns=16)

# Keep a copy of the last values we received
temperature = None
humidity = None

# Arrange the text on the LCD screen
# Being careful not to overlap things.
def update():
    lcd.clear()
    lcd.move_to(0, 0)
    if temperature is None:   # Just in case we haven't got a valid value yet
        lcd.putstr("Temp: ?")
    else:
        # Display as integer. Otherwise too many decimal places.
        lcd.putstr("Temp: {} C".format(int(temperature)))

    lcd.move_to(0, 1)
    if humidity is None:   # Just in case we haven't got a valid value yet
        lcd.putstr("Humi: ?")
    else:
        # Display as integer. Otherwise too many decimal places.
        lcd.putstr("Humi: {} %RH".format(int(humidity)))

# Start of program

# Put something on the screen so we know it's working
# Even if there's no valid data yet
update()

# Repeat this forever
while(True):

    # Send a message to the gateway asking for temperature and humidity
    node.send_as_json({"requests": ["temperature", "humidity"]})

    # If the gateway is doing its job, it will reply
    device_id, data = node.receive_json()

    # If either are "None" then code below doesn't run
    if device_id and data:

        # Only act on what we receive if it's sent as a 'response' to our 'request'
        # See node1.py for more info on how the below lines work
        if "responses" in data:
            response_data = data["responses"]
            if "temperature" in response_data:
                temperature = response_data['temperature']
            if "humidity" in response_data:
                humidity = response_data['humidity']

        # Update the LCD screen
        update()

    # Don't request again too soon. LoRa should be used infrequently.
    time.sleep(10)
