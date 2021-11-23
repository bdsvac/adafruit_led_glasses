import time
import board
import busio
import digitalio
import supervisor
import adafruit_lis3dh
import adafruit_is31fl3741
from audiobusio import PDMIn
from adafruit_is31fl3741.adafruit_ledglasses import LED_Glasses
from ButtonManager import ButtonManager
from BlinkyEyes import BlinkyEyes
from PendulumEyes import PendulumEyes
from AudioEyes import AudioEyes
from BleEyes import BleEyes

#i2c = board.I2C()
i2c = busio.I2C(board.SCL, board.SDA, frequency=1000000)
lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c)
mic = PDMIn(board.MICROPHONE_CLOCK, board.MICROPHONE_DATA, bit_depth=16)
glasses = LED_Glasses(i2c, allocate=adafruit_is31fl3741.MUST_BUFFER)
glasses.show()  # Clear any residue on startup
glasses.global_current = 20  # Just middlin' bright, please

bm = ButtonManager()
ae = AudioEyes(glasses, mic)
be = BlinkyEyes(glasses)
pe = PendulumEyes(glasses, lis3dh)
ble = BleEyes(glasses)

index = 0
animationList = [ble, ae, be, pe]

while True:
    try:
        if (bm.ButtonClicked(True)):
            index = index + 1
            index = index % len(animationList)
            glasses.fill(0x000000)
            glasses.left_ring.fill(0x000000)
            glasses.right_ring.fill(0x000000)
            glasses.show()
        animationList[index].run()
    except OSError:
        print("Restarting")
        supervisor.reload()









