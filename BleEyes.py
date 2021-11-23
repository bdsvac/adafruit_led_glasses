import time
import board
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_bluefruit_connect.packet import Packet
from adafruit_bluefruit_connect.color_packet import ColorPacket
from adafruit_bluefruit_connect.button_packet import ButtonPacket

class BleEyes:
    def __init__(self, g):
        self.glasses = g
        self.ble = BLERadio()
        self.uart = UARTService()
        self.advertisement = ProvideServicesAdvertisement(self.uart)
        self.ble.name = "LED Glasses"
        self.DEBOUNCE = 0.25
        self.color = 0x000000
        print("ble eyes init done")

    def rgb_to_hex(self, rgb):
        hex_str = '0x%02x%02x%02x' % rgb
        return int(hex_str, 16)

    def run(self):
        if not self.ble.connected:
            self.ble.start_advertising(self.advertisement)
        while not self.ble.connected:
            self.glasses.fill(self.color)
            self.glasses.left_ring.fill(self.color)
            self.glasses.right_ring.fill(self.color)
            self.glasses.show()
        try:
            incoming_bytes = self.uart.in_waiting
            if incoming_bytes:
                bytes_in = self.uart.read(incoming_bytes)
                packet = Packet.from_bytes(bytes_in)
                if isinstance(packet, ColorPacket):
                    self.color = self.rgb_to_hex(packet.color)
                    self.glasses.fill(self.color)
                    self.glasses.left_ring.fill(self.color)
                    self.glasses.right_ring.fill(self.color)
                    self.glasses.show()
                if isinstance(packet, ButtonPacket):
                    tempMode = packet.button
                    #if (tempMode in allowedModes):
                    #    mode = tempMode
                    #uart.write(str.encode(mode))
                    #print(tempMode)
                time.sleep(self.DEBOUNCE)
        except:
            pass
