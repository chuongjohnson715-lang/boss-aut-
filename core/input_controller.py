import pyautogui
import time


class InputController:

    def __init__(self):
        pyautogui.PAUSE = 0.3
        pyautogui.FAILSAFE = True

    def move(self, x, y, duration=0.3):
        pyautogui.moveTo(x, y, duration=duration)

    def click(self, x=None, y=None, button="left"):
        if x is not None and y is not None:
            pyautogui.click(x, y, button=button)
        else:
            pyautogui.click(button=button)

    def double_click(self, x=None, y=None):
        if x is not None and y is not None:
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.doubleClick()

    def write(self, text, interval=0.05):
        pyautogui.write(text, interval=interval)

    def press(self, key):
        pyautogui.press(key)

    def hotkey(self, *keys):
        pyautogui.hotkey(*keys)

    def sleep(self, seconds):
        time.sleep(seconds)

    def position(self):
        return pyautogui.position()