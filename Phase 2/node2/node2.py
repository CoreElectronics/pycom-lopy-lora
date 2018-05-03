import pycom
import time
import os
import socket
import time
import struct
from network import LoRa
from machine import Timer

# A basic package header, B: 1 byte for the deviceId, B: 1 bytes for the pkg size
_LORA_PKG_FORMAT = "BB%ds"
_LORA_PKG_ACK_FORMAT = "BBB"
_LORA_ACKNOWLEDGEMENT_TIMEOUT = 3 # seconds
DEVICE_ID = 0x02
DEVICE_NAME = "node2"
DEVICE_COLOUR = "green"
DEVICE_COLOUR_CODE = 0x00FF00

# Open a Lora Socket, use tx_iq to avoid listening to our own messages
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORA, tx_iq=True, region=LoRa.AU915)
sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
sock.setblocking(False)

def acknowledge():
    chrono = Timer.Chrono()
    chrono.start()
    waiting_ack = True
    while(waiting_ack):

        print(".", end="")
        if (chrono.read() > _LORA_ACKNOWLEDGEMENT_TIMEOUT):
            print(" NO ACK") # No acknowledgement receivedself.
            break

        package = sock.recv(256)
        if (len(package) > 0):
            device_id, package_len, ack = struct.unpack(_LORA_PKG_ACK_FORMAT, package)
            if (DEVICE_ID == device_id):
                if (ack == 200):
                    waiting_ack = False
                    # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
                    print(" ACK") # Achnowledgement recieved, message understood
                    # print(" ACK {}".format(package)) # Achnowledgement recieved, message understood
                else:
                    waiting_ack = False
                    # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
                    print("NACK") # Achnowledgement recieved, message NOT understood
            # else:
            #     print(' (Saw ACK for {})'.format(device_id), end='')
        time.sleep(0.1)

# RGBLED
# Disable the on-board heartbeat (blue flash every 4 seconds)
# We'll use the LED to identify each unit with different colours
pycom.heartbeat(False)
time.sleep(0.1) # Workaround for a bug.
                # Above line is not actioned if another
                # process occurs immediately afterwards
pycom.rgbled(DEVICE_COLOUR_CODE)
print("{} is {}".format(DEVICE_NAME, DEVICE_COLOUR))

while(True):
    print("{} ({}) ".format(DEVICE_NAME, DEVICE_COLOUR), end='')
    # Package send containing a simple string
    msg = "Device {} Here".format(DEVICE_ID)
    pkg = struct.pack(_LORA_PKG_FORMAT % len(msg), DEVICE_ID, len(msg), msg)
    sock.send(pkg)
    print('SENT "{}"" '.format(msg), end='')
    acknowledge()
    time.sleep(5)
