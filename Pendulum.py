import math
import random
import board

class Pendulum:
    """A small class for our pendulum simulation."""

    def __init__(self, ring, color):
        """Initial pendulum position, plus axle friction, are randomized
        so the two rings don't spin in perfect lockstep."""
        self.ring = ring  # Save reference to corresponding LED ring
        self.color = color  # (R,G,B) tuple for color
        self.angle = random.random()  # Position around ring, in radians
        self.momentum = 0
        self.friction = random.uniform(0.85, 0.9)  # Inverse friction, really

    def interp(self, pixel, scale):
        """Given a pixel index (0-23) and a scaling factor (0.0-1.0),
        interpolate between LED "off" color (at 0.0) and this item's fully-
        lit color (at 1.0) and set pixel to the result."""
        self.ring[pixel] = (
            (int(self.color[0] * scale) << 16)
            | (int(self.color[1] * scale) << 8)
            | int(self.color[2] * scale)
        )

    def iterate(self, xyz):
        """Given an accelerometer reading, run one cycle of the pendulum
        physics simulation and render the corresponding LED ring."""
        # Minus here is because LED pixel indices run clockwise vs. trigwise.
        # 0.05 is just an empirically-derived scaling fudge factor that looks
        # good; smaller values for more sluggish rings, higher = more twitch.
        self.momentum = (
            self.momentum * self.friction
            - (math.cos(self.angle) * xyz[2] + math.sin(self.angle) * xyz[0]) * 0.05
        )
        self.angle += self.momentum

        # Scale pendulum angle into pixel space
        midpoint = self.angle * 12 / math.pi % 24
        # Go around the whole ring, setting each pixel based on proximity
        # (this is also to erase the prior position)...
        for i in range(24):
            dist = abs(midpoint - i)  # Pixel to pendulum distance...
            if dist > 12:  #            If it crosses the "seam" at top,
                dist = 24 - dist  #      take the shorter path.
            if dist > 5:  #             Not close to pendulum,
                self.ring[i] = 0  #      erase pixel.
            elif dist < 2:  #           Close to pendulum,
                self.interp(i, 1.0)  #   solid color
            else:  #                    Anything in-between,
                self.interp(i, (5 - dist) / 3)  # interpolate
