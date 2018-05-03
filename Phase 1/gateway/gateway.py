import pycom
import socket
import time
import struct
from network import LoRa

# A basic package header, B: 1 byte for the deviceId, B: 1 bytes for the pkg size
_LORA_PKG_FORMAT = "BB%ds"
_LORA_PKG_ACK_FORMAT = "BBB"
_LORA_ACKNOWLEDGEMENT_TIMEOUT = 3 # seconds
DEVICE_ID = 0x00
DEVICE_NAME = "gateway"
DEVICE_COLOUR = "blue"
DEVICE_COLOUR_CODE = 0x0000FF

# RGBLED
# Disable the on-board heartbeat (blue flash every 4 seconds)
# We'll use the LED to identify each unit with different colours
pycom.heartbeat(False)
time.sleep(0.1) # Workaround for a bug.
                # Above line is not actioned if another
                # process occurs immediately afterwards
pycom.rgbled(DEVICE_COLOUR_CODE)
print("{} is {}".format(DEVICE_NAME, DEVICE_COLOUR))

# Open a LoRa Socket, use rx_iq to avoid listening to our own messages
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
lora = LoRa(mode=LoRa.LORA, rx_iq=True, region=LoRa.AU915)
lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
lora_sock.setblocking(False)

while (True):
   recv_pkg = lora_sock.recv(512)
   if (len(recv_pkg) > 2):
      recv_pkg_len = recv_pkg[1]

      device_id, pkg_len, msg = struct.unpack(_LORA_PKG_FORMAT % recv_pkg_len, recv_pkg)

      # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
      print('Device: %d - Pkg:  %s' % (device_id, msg))

      ack_pkg = struct.pack(_LORA_PKG_ACK_FORMAT, device_id, 1, 200)
      lora_sock.send(ack_pkg)
