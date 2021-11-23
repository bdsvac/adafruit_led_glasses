import math
import time
import random
from Eye import Eye

class BlinkyEyes:

    def rasterize(self, data, point1, point2, rect):
        """Rasterize an arbitrary ellipse into the 'data' bitmap (3X pixel
        space), given foci point1 and point2 and with area determined by global
        'radius' (when foci are same point; a circle). Foci and radius are all
        floating point values, which adds to the buttery impression. 'rect' is
        a 4-tuple rect of which pixels are likely affected. Data is assumed 0
        before arriving here; no clearing is performed."""

        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        d2 = dx * dx + dy * dy  # Dist between foci, squared
        if d2 <= 0:
            # Foci are in same spot - it's a circle
            perimeter = 2 * self.radius
            d = 0
        else:
            # Foci are separated - it's an ellipse.
            d = d2 ** 0.5  # Distance between foci
            c = d * 0.5  # Center-to-foci distance
            # This is an utterly brute-force way of ellipse-filling based on
            # the "two nails and a string" metaphor...we have the foci points
            # and just need the string length (triangle perimeter) to yield
            # an ellipse with area equal to a circle of 'radius'.
            # c^2 = a^2 - b^2  <- ellipse formula
            #   a = r^2 / b    <- substitute
            # c^2 = (r^2 / b)^2 - b^2
            # b = sqrt(((c^2) + sqrt((c^4) + 4 * r^4)) / 2)  <- solve for b
            b2 = ((c ** 2) + (((c ** 4) + 4 * (self.radius ** 4)) ** 0.5)) * 0.5
            # By my math, perimeter SHOULD be...
            # perimeter = d + 2 * ((b2 + (c ** 2)) ** 0.5)
            # ...but for whatever reason, working approach here is really...
            perimeter = d + 2 * (b2 ** 0.5)

        # Like I'm sure there's a way to rasterize this by spans rather than
        # all these square roots on every pixel, but for now...
        for y in range(rect[1], rect[3]):  # For each row...
            y5 = y + 0.5  #         Pixel center
            dy1 = y5 - point1[1]  # Y distance from pixel to first point
            dy2 = y5 - point2[1]  # " to second
            dy1 *= dy1  # Y1^2
            dy2 *= dy2  # Y2^2
            for x in range(rect[0], rect[2]):  # For each column...
                x5 = x + 0.5  #         Pixel center
                dx1 = x5 - point1[0]  # X distance from pixel to first point
                dx2 = x5 - point2[0]  # " to second
                d1 = (dx1 * dx1 + dy1) ** 0.5  # 2D distance to first point
                d2 = (dx2 * dx2 + dy2) ** 0.5  # " to second
                if (d1 + d2 + d) <= perimeter:
                    data[y][x] = 1  # Point is inside ellipse


    def gammify(self, color):
        """Given an (R,G,B) color tuple, apply gamma correction and return
        a packed 24-bit RGB integer."""
        rgb = [int(((color[x] / 255) ** self.gamma) * 255 + 0.5) for x in range(3)]
        return (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]


    def interp(self, color1, color2, blend):
        """Given two (R,G,B) color tuples and a blend ratio (0.0 to 1.0),
        interpolate between the two colors and return a gamma-corrected
        in-between color as a packed 24-bit RGB integer. No bounds clamping
        is performed on blend value, be nice."""
        inv = 1.0 - blend  # Weighting of second color
        return self.gammify([color1[x] * blend + color2[x] * inv for x in range(3)])


    def __init__(self, g):
        self.glasses = g

        self.eye_color = (255, 128, 0)  #      Amber pupils
        self.ring_open_color = (75, 75, 75)  # Color of LED rings when eyes open
        self.ring_blink_color = (50, 25, 0)  # Color of LED ring "eyelid" when blinking
        self.radius = 3.4  # Size of pupil (3X because of downsampling later)
        self.gamma = 2.6  # For color adjustment. Leave as-is.

        self.colormap = []
        self.y_pos = []

        for n in range(10):
            self.colormap.append(self.gammify([n / 9 * self.eye_color[x] for x in range(3)]))

        for n in range(13):
            angle = n / 24 * math.pi * 2
            self.y_pos.append(10 - math.cos(angle) * 12)

        self.ring_open_color_packed = self.gammify(self.ring_open_color)

        self.eyelid = (
            b"\x01\x01\x00\x01\x01\x00\x01\x01\x00" b"\x01\x01\x00\x01\x01\x00\x01\x01\x00"
        )  # 2/3 of pixels set

        # Initialize eye position and move/blink animation timekeeping
        self.cur_pos = self.next_pos = (9, 7.5)  # Current, next eye position in 3X space
        self.in_motion = False  #             True = eyes moving, False = eyes paused
        self.blink_state = 0  #               0, 1, 2 = unblinking, closing, opening
        self.move_start_time = self.move_duration = self.blink_start_time = self.blink_duration = 0
        self.eyes = [Eye(self.glasses, 1, 2), Eye(self.glasses, 11, -2)]

        self.frames, self.start_time = 0, time.monotonic()  # For frames/second calculation
        print("blinky eyes init done")

    def run(self):

        now = time.monotonic()  # 'Snapshot' the time once per frame

        # Blink logic
        elapsed = now - self.blink_start_time  # Time since start of blink event

        upper = lower = 0

        if elapsed > self.blink_duration:  #     All done with event?
            self.blink_start_time = now  #       A new one starts right now
            elapsed = 0
            self.blink_state += 1  #             Cycle closing/opening/paused
            if self.blink_state == 1:  #         Starting new blink...
                self.blink_duration = random.uniform(0.06, 0.12)
            elif self.blink_state == 2:  #       Switching closing to opening...
                self.blink_duration *= 2  #      Opens at half the speed
            else:  #                        Switching to pause in blink
                self.blink_state = 0
                self.blink_duration = random.uniform(0.5, 4)
        if self.blink_state:  #                  If currently in a blink...
            ratio = elapsed / self.blink_duration  # 0.0-1.0 as it closes
            if self.blink_state == 2:
                ratio = 1.0 - ratio  #          1.0-0.0 as it opens
            upper = ratio * 15 - 4  #       Upper eyelid pos. in 3X space
            lower = 23 - ratio * 8  #       Lower eyelid pos. in 3X space

        # Eye movement logic. Two points, 'p1' and 'p2', are the foci of an
        # ellipse. p1 moves from current to next position a little faster
        # than p2, creating a "squash and stretch" effect (frame rate and
        # resolution permitting). When motion is stopped, the two points
        # are at the same position.

        elapsed = now - self.move_start_time  # Time since start of move event


        if self.in_motion:  #                   Currently moving?
            if elapsed > self.move_duration:  # If end of motion reached,
                self.in_motion = False  #            Stop motion and
                p1 = p2 = self.cur_pos = self.next_pos  # Set to new position
                self.move_duration = random.uniform(0.5, 1.5)  # Wait this long
            else:  # Still moving
                # Determine p1, p2 position in time
                delta = (self.next_pos[0] - self.cur_pos[0], self.next_pos[1] - self.cur_pos[1])
                ratio = elapsed / self.move_duration
                if ratio < 0.6:  # First 60% of move time
                    # p1 is in motion
                    # Easing function: 3*e^2-2*e^3 0.0 to 1.0
                    e = ratio / 0.6  # 0.0 to 1.0
                    e = 3 * e * e - 2 * e * e * e
                    p1 = (self.cur_pos[0] + delta[0] * e, self.cur_pos[1] + delta[1] * e)
                else:  # Last 40% of move time
                    p1 = self.next_pos  # p1 has reached end position
                if ratio > 0.3:  # Last 60% of move time
                    # p2 is in motion
                    e = (ratio - 0.3) / 0.7  #       0.0 to 1.0
                    e = 3 * e * e - 2 * e * e * e  # Easing func.
                    p2 = (self.cur_pos[0] + delta[0] * e, self.cur_pos[1] + delta[1] * e)
                else:  # First 40% of move time
                    p2 = self.cur_pos  # p2 waits at start position
        else:  # Eye is stopped
            p1 = p2 = self.cur_pos  # Both foci at current eye position
            if elapsed > self.move_duration:  # Pause time expired?
                self.in_motion = True  #        Start up new motion!
                self.move_start_time = now
                self.move_duration = random.uniform(0.15, 0.25)
                angle = random.uniform(0, math.pi * 2)
                dist = random.uniform(0, 7.5)
                self.next_pos = (
                    9 + math.cos(angle) * dist,
                    7.5 + math.sin(angle) * dist * 0.8,
                )
        # Draw the raster part of each eye...
        for eye in self.eyes:
            # Allocate/clear the 3X bitmap buffer
            bitmap = [bytearray(6 * 3) for _ in range(5 * 3)]
            # Each eye's foci are offset slightly, to fixate toward center
            p1a = (p1[0] + eye.x_offset, p1[1])
            p2a = (p2[0] + eye.x_offset, p2[1])
            # Compute bounding rectangle (in 3X space) of ellipse
            # (min X, min Y, max X, max Y). Like the ellipse rasterizer,
            # this isn't optimal, but will suffice.
            bounds = (
                max(int(min(p1a[0], p2a[0]) - self.radius), 0),
                max(int(min(p1a[1], p2a[1]) - self.radius), 0, int(upper)),
                min(int(max(p1a[0], p2a[0]) + self.radius + 1), 18),
                min(int(max(p1a[1], p2a[1]) + self.radius + 1), 15, int(lower) + 1),
            )
            self.rasterize(bitmap, p1a, p2a, bounds)  # Render ellipse into buffer
            # If the eye is currently blinking, and if the top edge of the
            # eyelid overlaps the bitmap, draw a scanline across the bitmap
            # and update the bounds rect so the whole width of the bitmap
            # is scaled.
            if self.blink_state and upper >= 0:
                bitmap[int(upper)] = self.eyelid
                bounds = (0, int(upper), 18, bounds[3])
            eye.smooth(bitmap, bounds, self.colormap)  # 1:3 downsampling for eye

        # Matrix and rings share a few pixels. To make the rings take
        # precedence, they're drawn later. So blink state is revisited now...
        if self.blink_state:  # In mid-blink?
            for i in range(13):  # Half an LED ring, top-to-bottom...
                a = min(max(self.y_pos[i] - upper + 1, 0), 3)
                b = min(max(lower - self.y_pos[i] + 1, 0), 3)
                ratio = a * b / 9  # Proximity of LED to eyelid edges
                packed = self.interp(self.ring_open_color, self.ring_blink_color, ratio)
                self.glasses.left_ring[i] = self.glasses.right_ring[i] = packed
                if 0 < i < 12:
                    i = 24 - i  # Mirror half-ring to other side
                    self.glasses.left_ring[i] = self.glasses.right_ring[i] = packed
        else:
            self.glasses.left_ring.fill(self.ring_open_color_packed)
            self.glasses.right_ring.fill(self.ring_open_color_packed)


        self.glasses.show()  # Buffered mode MUST use show() to refresh matrix
        self.frames += 1
        elapsed = time.monotonic() - self.start_time

        #print(self.frames / elapsed)

