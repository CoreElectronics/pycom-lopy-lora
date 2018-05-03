# Chris@Core: These import statements are required to ensure use
# of keywords like 'socket' make sense later.
import os
import socket
import time
import struct
from network import LoRa

# A basic package header, B: 1 byte for the deviceId, B: 1 bytes for the pkg size

# Chris@Core: _LORA_PKG_FORMAT is how information will be sent using LoRa.
# Each 'letter' in the format is actually a number or letter, a BYTE.
# If we send "hello world!" (which requires 12 letters), to device 1:
# 1. We replace %d with the length of characters we use, so get "BB12s"
# 2. Then we replace the first B with a number of which LoRa device to send to, so: 1.
# 3. We replace the second B with the length of the message: 12
# 4. We replace the 12s with the message itself
# So we get:
# 1  (the device that should receive it)
# 12 (The number of characters following. Remember each can be a number or a character)
# h
# e
# l
# l
# o
#   (space)
# w
# o
# r
# l
# d
# !
# Messages sent from a node are received by gateway.
# Messages from the gateway go to ALL NODES, so the node needs to decide
# if the message is for them. Hence the first number!
_LORA_PKG_FORMAT = "BB%ds"

# Chris@Core: "ACK_FORMAT" means "acknowledgement format". This message is
# sent from the receipient back to the sender using "BBB" format. It contains:
# B     (the number of the device who should receive it)
# 1     (the number of bytes coming after the 1)
# 200   (success, or some other code for error)
_LORA_PKG_ACK_FORMAT = "BBB"

# Chris@Core: As discussed above, each node on the network needs its
# own number. When we create a second node it will be 0x02.
# The "0x" prefix means hexadecimal.
DEVICE_ID = 0x01


# Open a Lora Socket, use tx_iq to avoid listening to our own messages
# Please pick the region that matches where you are using the device:
# Asia = LoRa.AS923
# Australia = LoRa.AU915
# Europe = LoRa.EU868
# United States = LoRa.US915
# Chris@Core: this line sets up the LoRa radio and afterwards is not
# used again. But it's important!
lora = LoRa(mode=LoRa.LORA, tx_iq=True, region=LoRa.AU915)

# Chris@Core: A socket is a connection to a network. We're using a
# generic 'socket', calling it 'lora_socket', and tying it to the LoRa radio
lora_sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)

# Chris@Core: when we ask if there's been a message, we don't want to wait
# until a message comes in. We want our program to continue even if there's
# no message
lora_sock.setblocking(False)

# Chris@Core: Repeat this forever!
while(True):
    # Package send containing a simple string
    # Chris@Core: This is kind of our "hello world!" message
    msg = "Device 1 Here"

    # Chris@Core: This is all the fancy reformatting of the _LORA_PKG_FORMAT
    # so that it now contains a DEVICE_ID, message length and the message itself.
    # It's now a "package" that LoRa can handle.
    pkg = struct.pack(_LORA_PKG_FORMAT % len(msg), DEVICE_ID, len(msg), msg)

    # Chris@Core: Now we can use the network socket we set up to send the package.
    lora_sock.send(pkg)

    # Wait for the response from the gateway. NOTE: For this demo the device does an infinite loop for while waiting the response. Introduce a max_time_waiting for you application
    # Chris@Core: Having sent the package, we expect we'll get an acknowledgement
    # but have no idea when. Since we said lora_sock.setblocking(False),
    # every time we do recv_ack = lora_sock.recv(256) we'll get something or
    # nothing.

    # Chris@Core: This variable keep the while() loop repeating until we're sure
    # we don't need to repeat again.
    waiting_ack = True
    # Chris@Core: Do this until we receive the acknowledgement!
    while(waiting_ack):
        # Chris@Core: Get data from the LoRa network, which might be nothing
        recv_ack = lora_sock.recv(256)

        # Chris@Core: If we got nothing, it's length is 0. If 0, ignore it.
        if (len(recv_ack) > 0):

            # Chris@Core: Now we unpack the data to get device_id, pkg_len and ack (a number)
            device_id, pkg_len, ack = struct.unpack(_LORA_PKG_ACK_FORMAT, recv_ack)

            # Chris@Core: Check if the package is addressed to this node
            if (device_id == DEVICE_ID):
                # Chris@Core: Check if the code is 200. (HTML "success" code)
                if (ack == 200):
                    # Chris@Core: Now we don't need to keep waiting
                    waiting_ack = False
                    # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
                    # Chris@Core: Display the acknowledgement was received
                    print("ACK")
                else:
                    # Chris@Core: The message failed, but it DEFINITELY failed.
                    # There won't be another acknowledgement, so stop waiting
                    waiting_ack = False
                    # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
                    # Chris@Core: Display the failed acknowledgement
                    print("Message Failed")

    # Chris@Core: Slow main loop down. Send messages every 5 seconds.
    time.sleep(5)
