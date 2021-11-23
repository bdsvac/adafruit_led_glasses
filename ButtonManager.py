import board
from digitalio import DigitalInOut, Direction, Pull

class ButtonManager:
    def __init__(self):
        self.enabled = True
        self.Button = self.InitButton(board.SWITCH)

    def InitButton(self, pin):
        btn = DigitalInOut(pin)
        btn.direction = Direction.INPUT
        btn.pull = Pull.UP
        return btn

    def Clicked(self, btn, waitForRelease = False):
        if not btn.value:
            if waitForRelease:
                while not btn.value:
                    pass
            return True
        return False;

    def ButtonClicked(self, waitForRelease = False):
        return self.Clicked(self.Button, waitForRelease)
