#!/usr/bin/env python3

import enum
import time
import random

from samplebase import SampleBase
from PIL import Image


class Direction(enum.Enum):
    UP_LEFT = 'ul'
    UP_RIGHT = 'ur'
    DOWN_LEFT = 'dl'
    DOWN_RIGHT = 'dr'


class ImageScroller(SampleBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser.add_argument("-i", "--image", help="The image to display", default="../../../examples-api-use/runtext.ppm")

    def run(self):
        if not 'image' in self.__dict__:
            self.image = Image.open(self.args.image).convert('RGB')

        self.image.resize((self.matrix.width, self.matrix.height), Image.ANTIALIAS)
        img_width, img_height = self.image.size

        multiplier = self.args.led_cols
        x_panels = self.matrix.width / multiplier
        x_pos = random.randint(0, self.matrix.width - img_width)
        y_pos = random.randint(0, self.matrix.height - img_height)
        direction = random.choice(list(Direction))

        max_x = self.matrix.width - img_width
        max_y = self.matrix.height - img_height

        double_buffer = self.matrix.CreateFrameCanvas()

        while True:
            # Check for corner hit
            if x_pos == 0 and y_pos == 0:
                direction = Direction.DOWN_RIGHT
                print('top left corner bounce')
            elif x_pos == 0 and y_pos == max_y:
                direction = Direction.UP_RIGHT
                print('bottom left corner bounce')
            elif x_pos == max_x and y_pos == 0:
                direction = Direction.DOWN_LEFT
                print('top right corner bounce')
            elif x_pos == max_x and y_pos == max_x:
                direction = Direction.UP_LEFT
                print('botom right corner bounce')

            # Check for left edge
            elif x_pos == 0 and direction == Direction.UP_LEFT:
                direction = Direction.UP_RIGHT
            elif x_pos == 0 and direction == Direction.DOWN_LEFT:
                direction = Direction.DOWN_RIGHT

            # Check for right edge
            elif x_pos == max_x and direction == Direction.UP_RIGHT:
                direction = Direction.UP_LEFT
            elif x_pos == max_x and direction == Direction.DOWN_RIGHT:
                direction = Direction.DOWN_LEFT

            # Check for top edge bounce
            elif y_pos == 0 and direction == Direction.UP_LEFT:
                direction = Direction.DOWN_LEFT
            elif y_pos == 0 and direction == Direction.UP_RIGHT:
                direction = Direction.DOWN_RIGHT

            # Check for bottom edge bounce
            elif y_pos == max_y and direction == Direction.DOWN_LEFT:
                direction = Direction.UP_LEFT
            elif y_pos == max_y and direction == Direction.DOWN_RIGHT:
                direction = Direction.UP_RIGHT

            # Move it
            if direction == Direction.UP_LEFT:
                x_pos -= 1
                y_pos -= 1
            elif direction == Direction.UP_RIGHT:
                x_pos += 1
                y_pos -= 1
            elif direction == Direction.DOWN_LEFT:
                x_pos -= 1
                y_pos += 1
            elif direction == Direction.DOWN_RIGHT:
                x_pos += 1
                y_pos += 1

            double_buffer.SetImage(self.image, x_pos, y_pos)
            double_buffer = self.matrix.SwapOnVSync(double_buffer)

            time.sleep(0.02)
            self.matrix.Clear()

# Main function
# e.g. call with
#  sudo ./image-scroller.py --chain=4
# if you have a chain of four
if __name__ == "__main__":
    image_scroller = ImageScroller()
    if (not image_scroller.process()):
        image_scroller.print_help()
