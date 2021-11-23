class Eye:
    """Holds per-eye positional data; each covers a different area of the
    overall LED matrix."""

    def __init__(self, glasses, left, xoff):
        self.glasses = glasses
        self.left = left  #     Leftmost column on LED matrix
        self.x_offset = xoff  # Horizontal offset (3X space) to fixate

    def smooth(self, data, rect, colormap):
        """Scale bitmap (in 'data') to LED array, with smooth 1:3
        downsampling. 'rect' is a 4-tuple rect of which pixels get
        filtered (anything outside is cleared to 0), saves a few cycles."""
        # Quantize bounds rect from 3X space to LED matrix space.
        rect = (
            rect[0] // 3,  #       Left
            rect[1] // 3,  #       Top
            (rect[2] + 2) // 3,  # Right
            (rect[3] + 2) // 3,  # Bottom
        )
        for y in range(rect[1]):  # Erase rows above top
            for x in range(6):
                self.glasses.pixel(self.left + x, y, 0)
        for y in range(rect[1], rect[3]):  #  Each row, top to bottom...
            pixel_sum = bytearray(6)  #  Initialize row of pixel sums to 0
            for y1 in range(3):  # 3 rows of bitmap...
                row = data[y * 3 + y1]  # Bitmap data for current row
                for x in range(rect[0], rect[2]):  # Column, left to right
                    x3 = x * 3
                    # Accumulate 3 pixels of bitmap into pixel_sum
                    pixel_sum[x] += row[x3] + row[x3 + 1] + row[x3 + 2]
            # 'pixel_sum' will now contain values from 0-9, indicating the
            # number of set pixels in the corresponding section of the 3X
            # bitmap. 'colormap' expands the sum to 24-bit RGB space.
            for x in range(rect[0]):  # Erase any columns to left
                self.glasses.pixel(self.left + x, y, 0)
            for x in range(rect[0], rect[2]):  # Column, left to right
                self.glasses.pixel(self.left + x, y, colormap[pixel_sum[x]])
            for x in range(rect[2], 6):  # Erase columns to right
                self.glasses.pixel(self.left + x, y, 0)
        for y in range(rect[3], 5):  # Erase rows below bottom
            for x in range(6):
                self.glasses.pixel(self.left + x, y, 0)
