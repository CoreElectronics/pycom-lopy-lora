import time
import json
import pycom
import socket
import struct
from network import LoRa
from machine import Timer

class loraAPI:

    # A basic package header,
    # B: 1 byte for the deviceId,
    # B: 1 byte for the package size,
    # %ds: Formated string for string
    _LORA_GATEWAY_PKG_FORMAT = "!BB%ds"

    # A basic package header,
    # B: 1 byte for the deviceId,
    # B: 1 bytes for the package size
    _LORA_NODE_PKG_FORMAT = "BB%ds"

    # A basic ack package,
    # B: 1 byte for the deviceId,
    # B: 1 bytes for the package size,
    # B: 1 byte for the Ok (200) or error messages
    _LORA_PKG_ACK_FORMAT = "BBB"

    # Please pick the region that matches where you are using the device:
    # Asia = LoRa.AS923
    # Australia = LoRa.AU915
    # Europe = LoRa.EU868
    # United States = LoRa.US915
    _LORA_REGION = LoRa.AU915

    _LORA_ACKNOWLEDGEMENT_TIMEOUT = 3 # seconds

    def __init__(self, device_id=0, device_name='No-name', device_colour='white', device_colour_code=0xFFFFFF, is_gateway=False):
        self.device_id = device_id
        self.device_name = device_name
        self.device_colour = device_colour
        self.device_colour_code = device_colour_code
        self.is_gateway = is_gateway

        # RGBLED
        # Disable the on-board heartbeat (blue flash every 4 seconds)
        # We'll use the LED to identify each unit with different colours
        pycom.heartbeat(False)
        time.sleep(0.1) # Workaround for a bug.
                        # Above line is not actioned if another
                        # process occurs immediately afterwards
        pycom.rgbled(self.device_colour_code)
        print("{} is {}".format(self.device_name, self.device_colour))

        if self.is_gateway:
            self.lora = LoRa(mode=LoRa.LORA, rx_iq=True, region=loraAPI._LORA_REGION)
        else:
            self.lora = LoRa(mode=LoRa.LORA, tx_iq=True, region=loraAPI._LORA_REGION)
        self.sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.sock.setblocking(False)

    def send(self, message):
        package = struct.pack(loraAPI._LORA_NODE_PKG_FORMAT % len(message), self.device_id, len(message), message)
        self.sock.send(package)
        print("{}\n{} ({}) SENT".format(message, self.device_name, self.device_colour), end='')

    def to_gateway(self, submits, requests):

        communique = {} # empty dictionary

        # Only add submits if there's a dictionary of one or more submissions
        if isinstance(submits,(dict,)) and len(submits) > 0:
            communique["submits"] = submits
        # elif submits is not None:
        #     print("create_message_to_gateway() needs a <dict> of length > 0, or None, as first parameter")

        if isinstance(requests,(list,)):
            communique["requests"] = requests
        # elif requests is not None:
        #     print("create_message_to_gateway() needs a <list> of length > 0, or None, as second parameter")

        if len(communique) == 0:
            return False # Message not sent

        self.send(json.dumps(communique))
        return True

    def to_node(responses):

        communique = {} # empty dictionary

        # Only add responses if there's a dictionary of one or more responses
        if isinstance(responses,(dict,)) and len(responses) > 0:
            communique["responses"] = responses
        elif responses is not None:
            print("create_message_to_node() needs a <dict> of length > 0, or None, as a parameter")

        if len(communique) > 0:
            return communique
        else:
            return None

    def to_json(self, data):
        return json.dumps(data)

    def from_json(self, text):
        return json.loads(text)

    def debug(self):
        print("Is Gateway: %s" % self.is_gateway)
        print("Device ID : %d" % self.device_id)
        print("Region    : %s" % self.lora)
        print("Socket    : %s" % self.sock)

    def receive(self):
        package = self.sock.recv(512)
        if (len(package) > 2):
            package_length = package[1]
            node_device_id, message_length, message = struct.unpack(loraAPI._LORA_GATEWAY_PKG_FORMAT % package_length, package)

            # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
            print('Message from Node %d: %s' % (node_device_id, message))

            acknowledgement_package = struct.pack(loraAPI._LORA_PKG_ACK_FORMAT, node_device_id, 1, 200)
            # lora_sock.send(ack_package)
            self.sock.send(acknowledgement_package)

    def acknowledge(self):
        chrono = Timer.Chrono()
        chrono.start()
        waiting_ack = True
        while(waiting_ack):

            print(".", end="")
            if (chrono.read() > loraAPI._LORA_ACKNOWLEDGEMENT_TIMEOUT):
                print("NO ACK") # No acknowledgement receivedself.
                break

            package = self.sock.recv(256)
            if (len(package) > 0):
                device_id, package_len, ack = struct.unpack(loraAPI._LORA_PKG_ACK_FORMAT, package)
                if (device_id == self.device_id):
                    if (ack == 200):
                        waiting_ack = False
                        # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
                        print("ACK") # Achnowledgement recieved, message understood
                    else:
                        waiting_ack = False
                        # If the uart = machine.UART(0, 115200) and os.dupterm(uart) are set in the boot.py this print should appear in the serial port
                        print("NACK") # Achnowledgement recieved, message NOT understood
            time.sleep(0.1)
