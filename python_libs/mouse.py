from .config import StaticConfig
from .config import Inventory
from Xlib.display import Display
from Xlib import X
from Xlib.ext.xtest import fake_input

display = Display(':0')
display2 = Display(':0')

class Mouse:
    @staticmethod
    def click(x, y, button=1):
        Mouse.press(x, y, button)
        Mouse.release(x, y, button)

    @staticmethod
    def click_at_current_position(button=1):
        x, y = Mouse.get_position()
        Mouse.click(x, y, button)

    @staticmethod
    def press(x, y, button=1):
        Mouse.move(x, y)
        fake_input(display, X.ButtonPress, [None, 1, 3, 2][button])
        display.sync()

    @staticmethod
    def release(x, y, button=1):
        Mouse.move(x, y)
        fake_input(display, X.ButtonRelease, [None, 1, 3, 2][button])
        display.sync()

    @staticmethod
    def move(x, y):
        fake_input(display, X.MotionNotify, x=x, y=y)
        display.sync()

    @staticmethod
    def get_position():
        coord = display.screen().root.query_pointer()._data
        return coord["root_x"], coord["root_y"]

    @staticmethod
    def get_screen_size():
        width = display.screen().width_in_pixels
        height = display.screen().height_in_pixels
        return width, height
