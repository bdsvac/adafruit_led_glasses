from array import array
from math import log
from time import monotonic
from rainbowio import colorwheel
from ulab import numpy as np
from ulab.scipy.signal import spectrogram

class AudioEyes:

    def __init__(self, g, m):
        self.glasses = g
        # FFT/SPECTRUM CONFIG ----
        self.fft_size = 256  # Sample size for Fourier transform, MUST be power of two
        self.spectrum_size = self.fft_size // 2  # Output spectrum is 1/2 of FFT result
        # Bottom of spectrum tends to be noisy, while top often exceeds musical
        # range and is just harmonics, so clip both ends off:
        self.low_bin = 10  # Lowest bin of spectrum that contributes to graph
        self.high_bin = 75  # Highest bin "

        self.mic = m
        self.rec_buf = array("H", [0] * self.fft_size)  # 16-bit audio samples

        # FFT/SPECTRUM SETUP -----

        # To keep the display lively, tables are precomputed where each column of
        # the matrix (of which there are few) is the sum value and weighting of
        # several bins from the FFT spectrum output (of which there are many).
        # The tables also help visually linearize the output so octaves are evenly
        # spaced, as on a piano keyboard, whereas the source spectrum data is
        # spaced by frequency in Hz.
        self.column_table = []

        self.spectrum_bits = log(self.spectrum_size, 2)  # e.g. 7 for 128-bin spectrum
        # Scale low_bin and high_bin to 0.0 to 1.0 equivalent range in spectrum
        self.low_frac = log(self.low_bin, 2) / self.spectrum_bits
        self.frac_range = log(self.high_bin, 2) / self.spectrum_bits - self.low_frac

        for column in range(self.glasses.width):
            # Determine the lower and upper frequency range for this column, as
            # fractions within the scaled 0.0 to 1.0 spectrum range. 0.95 below
            # creates slight frequency overlap between columns, looks nicer.
            lower = self.low_frac + self.frac_range * (column / self.glasses.width * 0.95)
            upper = self.low_frac + self.frac_range * ((column + 1) / self.glasses.width)
            mid = (lower + upper) * 0.5  # Center of lower-to-upper range
            half_width = (upper - lower) * 0.5  # 1/2 of lower-to-upper range
            # Map fractions back to spectrum bin indices that contribute to column
            first_bin = int(2 ** (self.spectrum_bits * lower) + 1e-4)
            last_bin = int(2 ** (self.spectrum_bits * upper) + 1e-4)
            bin_weights = []  # Each spectrum bin's weighting will be added here
            for bin_index in range(first_bin, last_bin + 1):
                # Find distance from column's overall center to individual bin's
                # center, expressed as 0.0 (bin at center) to 1.0 (bin at limit of
                # lower-to-upper range).
                bin_center = log(bin_index + 0.5, 2) / self.spectrum_bits
                dist = abs(bin_center - mid) / half_width
                if dist < 1.0:  # Filter out a few math stragglers at either end
                    # Bin weights have a cubic falloff curve within range:
                    dist = 1.0 - dist  # Invert dist so 1.0 is at center
                    bin_weights.append(((3.0 - (dist * 2.0)) * dist) * dist)
            # Scale bin weights so total is 1.0 for each column, but then mute
            # lower columns slightly and boost higher columns. It graphs better.
            total = sum(bin_weights)
            bin_weights = [
                (weight / total) * (0.8 + idx / self.glasses.width * 1.4)
                for idx, weight in enumerate(bin_weights)
            ]
            # List w/five elements is stored for each column:
            # 0: Index of the first spectrum bin that impacts this column.
            # 1: A list of bin weights, starting from index above, length varies.
            # 2: Color for drawing this column on the LED matrix. The 225 is on
            #    purpose, providing hues from red to purple, leaving out magenta.
            # 3: Current height of the 'falling dot', updated each frame
            # 4: Current velocity of the 'falling dot', updated each frame
            self.column_table.append(
                [
                    first_bin - self.low_bin,
                    bin_weights,
                    colorwheel(225 * column / self.glasses.width),
                    self.glasses.height,
                    0.0,
                ]
            )

        self.dynamic_level = 10  # For responding to changing volume levels
        self.frames, self.start_time = 0, monotonic()  # For frames-per-second calc

        print("audio eyes init done")

    def run(self):
        self.mic.record(self.rec_buf, self.fft_size)  # Record batch of 16-bit samples
        samples = np.array(self.rec_buf)  # Convert to ndarray
        # Compute spectrogram and trim results. Only the left half is
        # normally needed (right half is mirrored), but we trim further as
        # only the low_bin to high_bin elements are interesting to graph.
        spectrum = spectrogram(samples)[self.low_bin : self.high_bin + 1]
        # Linearize spectrum output. spectrogram() is always nonnegative,
        # but add a tiny value to change any zeros to nonzero numbers
        # (avoids rare 'inf' error)
        spectrum = np.log(spectrum + 1e-7)
        # Determine minimum & maximum across all spectrum bins, with limits
        lower = max(np.min(spectrum), 4)
        upper = min(max(np.max(spectrum), lower + 6), 20)

        # Adjust dynamic level to current spectrum output, keeps the graph
        # 'lively' as ambient volume changes. Sparkle but don't saturate.
        if upper > self.dynamic_level:
            # Got louder. Move level up quickly but allow initial "bump."
            self.dynamic_level = upper * 0.7 + self.dynamic_level * 0.3
        else:
            # Got quieter. Ease level down, else too many bumps.
            self.dynamic_level = self.dynamic_level * 0.5 + lower * 0.5
        # Apply vertical scale to spectrum data. Results may exceed
        # matrix height...that's OK, adds impact!
        data = (spectrum - lower) * (7 / (self.dynamic_level - lower))
        for column, element in enumerate(self.column_table):
            # Start BELOW matrix and accumulate bin weights UP, saves math
            first_bin = element[0]
            column_top = self.glasses.height + 1
            for bin_offset, weight in enumerate(element[1]):
                column_top -= data[first_bin + bin_offset] * weight

            if column_top < element[3]:  #       Above current falling dot?
                element[3] = column_top - 0.5  # Move dot up
                element[4] = 0  #                and clear out velocity
            else:
                element[3] += element[4]  #      Move dot down
                element[4] += 0.2  #             and accelerate

            column_top = int(column_top)  #      Quantize to pixel space
            for row in range(column_top):  #     Erase area above column
                self.glasses.pixel(column, row, 0)
            for row in range(column_top, 5):  #  Draw column
                self.glasses.pixel(column, row, element[2])
            self.glasses.pixel(column, int(element[3]), 0xE08080)  # Draw peak dot

        self.glasses.show()  # Buffered mode MUST use show() to refresh matrix

        self.frames += 1
        # print(frames / (monotonic() - start_time), "FPS")
