# loraAPI
# Chris Murphy
# Core Electronics
# Adapted from Pycom Libraries: https://github.com/pycom/pycom-libraries
import time
import json
import pycom
import socket
import struct
from network import LoRa
from machine import Timer

# About loraAPI
# This class provides functionality for a nano-gateway and provides communications
# in and out of the gateway. Each non-gateway node needs to identify iteself by
# a device_id
class loraAPI:

    # These attributes (above def __init__) belong to the class and not any objects
    # created from this class. They are all referenced using the prefix of loraAPI.
    # By convention attributes starting with an underscore are private and should
    # not be accessed from outside the class or object.

    # The gateway sends packages of data in this format
    # B: 1 byte for the device_id to send data to,
    # B: 1 byte for the package size,
    # %d: length of the string
    # s: text as a string of bytes
    RECEIVE_FORMAT = "!BB%ds"

    # All nodes send data in this format
    # B: 1 byte for the device_id data is sent from,
    # B: 1 bytes for the package size
    # %d is the length of text
    # s: text as bytes
    SEND_FORMAT = "BB%ds"

    # A three-byte package used to acknowledge a package was received,
    # B: 1 byte for the device_id,
    # B: 1 byte for the package size (size=1),
    # B: 1 byte for the Ok (200) or error messages
    ACKNOWLEDGE_FORMAT = "BBB"

    # Please pick the region that matches where you are using the device:
    # Asia = LoRa.AS923
    # Australia = LoRa.AU915
    # Europe = LoRa.EU868
    # United States = LoRa.US915
    LORA_REGION = LoRa.AU915

    LORA_ACKNOWLEDGEMENT_TIMEOUT = 3 # seconds
    LORA_RESPONSE_TIMEOUT = 3 # seconds

    LORA_RECEIVE_BUFFER_SIZE = 512

    # Creates a new object of the loraAPI type
    def __init__(self, device_id=0, device_name='No-name', device_colour='white', device_colour_code=0xFFFFFF, is_gateway=False):

        # These attributes are attached to every object created from this class
        self.device_id = device_id
        self.device_name = device_name
        self.device_colour = device_colour
        self.device_colour_code = device_colour_code
        self.is_gateway = is_gateway

        # The remainder of this function's code runs whenever a new loraAPI object is created.

        # RGBLED
        # Disable the on-board heartbeat (blue flash every 4 seconds)
        # We'll use the LED to identify each unit with different colours
        pycom.heartbeat(False)
        time.sleep(0.1) # Workaround for a bug.
                        # Above line is not actioned if another
                        # process occurs immediately afterwards
        pycom.rgbled(self.device_colour_code)
        print("{} is {}".format(self.device_name, self.device_colour))

        # Set up the LoRa radio.
        if self.is_gateway:
            self.lora = LoRa(mode=LoRa.LORA, rx_iq=True, region=loraAPI.LORA_REGION)
        else:
            self.lora = LoRa(mode=LoRa.LORA, tx_iq=True, region=loraAPI.LORA_REGION)

        # Create a LoRa network socket to use in communications.
        self.sock = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
        self.sock.setblocking(False)

    # Convert a dictionary data structure to JSON and send it out over LoRa
    # Parameter: dictionary
    #   Must be a Python dictionary data type.
    # Parameter: device_id
    #   If the sender is the gateway, device_id is the destination node device_id.
    #   Otherwise, nodes send their own device_id so the gateway can reply to them.
    def send_as_json(self, dictionary, device_id=0):

        # Make sure 'dictionary' really is one.
        if isinstance(dictionary,(dict,)) and len(dictionary) > 0:
            # Format the data structure into text in JSON format
            # To Do: Exception handling here
            self.send(json.dumps(dictionary), device_id)
        else:
            print("send_as_json() failed. Was not given a dictionary data structure")

    # Send a message out on the LoRa network
    # Parameter: message
    #   Must be a string of bytes.
    # Parameter: device_id
    #   If the sender is the gateway, device_id is the destination node device_id.
    #   Otherwise, nodes send their own device_id so the gateway can reply to them.
    def send(self, message, device_id=0):

        # Gateway must have a device_id to send to
        # device_id is not required when sending to gateway
        # as it has a different package format
        if self.is_gateway and device_id == 0:
            print("loraAPI.send() requires device_id when gateway sends")
            return

        format = "BB%ds"

        if not self.is_gateway:
            device_id = self.device_id
        # if self.is_gateway:
        #     # format = loraAPI.GATEWAY_SEND_FORMAT
        #     # length_index = 2
        #     format = loraAPI.NODE_SEND_FORMAT
        #     length_index = 1
        # else:
        #     format = loraAPI.NODE_SEND_FORMAT
        #     length_index = 1
        #     device_id = self.device_id  # Set device_id to self when sending from a node
            # print("Self Device_ID: {}".format(self.device_id))

        # Format the data into a LoRa network package
        # Example:
        #   Suppose the message is "Hello!"
        #   The length of that message is 6 characters.
        #   The gateway's sending format is: "!BB%ds"
        #   self.send_package_format() % len(message) changes the format string to "!BB6s"
        #   Now the format says:
        #       "B" = 1 byte for destination device_id
        #       "B" = 1 byte for the length of the package
        #      "6s" = 6 bytes of string data (text)

        package = struct.pack(loraAPI.SEND_FORMAT % len(message), device_id, len(message), message)
        # print("SEND begin")
        # print("Length Index: {}".format(length_index))
        #
        # print("package[length_index] = {}".format(package[length_index]))
        #
        # print("SEND PACKAGE: {} {} {} {} {}".format(format, package[0], package[1], package[2], package))
        # print("SEND end")

        # Send the message on the network
        self.sock.send(package)

        # Print out what was sent
        print("{} ({}) sent {} to {}".format(self.device_name, self.device_colour, message, 'node{}'.format(device_id) if self.is_gateway else 'gateway'))

        # if (self.package_was_acknowledged()):
        #     print("ACK")
        # else:
        #     print("NACK")

    # Waits for a limited time for a LoRa package.
    # Returns whatever message is received with the device_id of who sent it.
    # If waiting time runs out, returns (None, None)
    def receive(self):

        # Use a timer to put a limit on waiting
        chrono = Timer.Chrono()
        chrono.start()

        # Repeat 'forever'
        while(True):

            # Check if time's up. If so, break out of while(True) loop
            if (chrono.read() > loraAPI.LORA_RESPONSE_TIMEOUT):
                # print("TIMEOUT")
                return None, None

            # Try to get a LoRa package
            package = self.sock.recv(loraAPI.LORA_RECEIVE_BUFFER_SIZE)

            # If the length of [package] not 0, a valid package was received.
            if (len(package) > 0):

                # Unpack the package into its three component parts
                device_id, length, message = struct.unpack(loraAPI.RECEIVE_FORMAT % package[1], package)

                # Packages received at the gateway are tagged with the sender's device_id
                if self.is_gateway:
                    print("Received {} from device ID {}".format(message, device_id))
                    return device_id, message

                # Packages recieved at a node could be for any nodeself.
                # Need to check the package's device_id matches the node's own device_id
                if device_id == self.device_id:
                    print("Received {}".format(message))
                    return device_id, message
                # else:
                #     print("Ignored message for device ID {}".format(device_id))

            # Slow down the loop
            time.sleep(0.1)

    # This function takes data from receive(), interprets the message as JSON text
    # and converts it back into a dictionary type object. Displays an error if it
    # can't understand the JSON it was given.
    def receive_json(self):

        # Receive function gives device_id and message but these may have the
        # special value None, meaning we couldn't understand the package
        device_id, message = self.receive()

        # If either value is None, we can't try to interpret JSON data.
        # So stop here.
        if device_id is None or message is None:
            return None, None

        # Even if we think the message is JSON, there could be something
        # wrong with it. So we're ready if it blows up - we'll just return
        # the device_id with no data.
        try:
            data = json.loads(message)
        except (Exception):
            return device_id, None

        # Everything worked! We have a device_id and we managed to
        # convert the JSON formatted text back into a dictionary.
        return device_id, data

    def send_acknowledgement(self, device_id):

        acknowledgement_package = struct.pack(loraAPI.ACKNOWLEDGE_FORMAT, device_id, 1, 200)
        self.sock.send(acknowledgement_package)

    def package_was_acknowledged(self):

        device_id, ack_code = self.receive()
        if len(ack_code) == 1 and ack_code == 200:
            return True
        return False
