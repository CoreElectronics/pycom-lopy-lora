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
DEVICE_ID = 0x01
DEVICE_NAME = "node1"
DEVICE_COLOUR = "red"
DEVICE_COLOUR_CODE = 0xFF0000

# Open a Lora Socket, use tx_iq to avoid listening to our own messages
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORA, tx_iq=True, region=LoRa.AU915)
sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
sock.setblocking(False)

# Chris@Core: To solve the "waiting forever for acknowledgement" problem
# I've moved the acknowledgement code into its own function.
def acknowledge():

    # Chris@Core: Create a timer. This allows us to know how much time
    # goes by while we're waiting
    chrono = Timer.Chrono()

    # Chris@Core: Set it to run.
    chrono.start()

    # Chris@Core: These two lines keep us repeatedly checking for an
    # acknowledgement. The only way out of here is if we BREAK this loop
    while(True):

        # Chris@Core: So we know what's going on while we wait, print something
        print(".", end="")

        # Chris@Core: If time's up, print that we gave up.
        if (chrono.read() > _LORA_ACKNOWLEDGEMENT_TIMEOUT):
            print(" NO ACK")
            break # Chris@Core: This stops the while(True) loop above

        # Chris@Core: This code is as before.
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
            #     print(' (Saw ACK for node{})'.format(device_id), end='')

        # Chris@Core: Every time this loop repeats it prints ....
        # So don't print thousands of them. 10 per second is heaps.
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
    print('SENT "{}" '.format(msg), end='')
    acknowledge()   # Chris@Core: Call the new function to handle acknowledgement
    time.sleep(5)
