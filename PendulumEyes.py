import math
import random
import board
from Pendulum import Pendulum

class PendulumEyes:

    def __init__(self, g, l):
        self.glasses = g
        self.lis3dh = l
        self.pendulums = [
            Pendulum(self.glasses.left_ring, (0, 20, 50)),  # Cerulean blue,
            Pendulum(self.glasses.right_ring, (0, 20, 50)),  # 50 is plenty bright!
        ]
        print("pendulum eyes init done")

    def run(self):
        accel = self.lis3dh.acceleration
        for p in self.pendulums:
            p.iterate(accel)

        self.glasses.show()
