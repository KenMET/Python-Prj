#!/usr/bin/env python3
# coding=utf-8
import time
import os, sys
import threading
import Adafruit_SSD1306 as SSD

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import subprocess

# V1.0.6
# one char width=6px, hight=8px
class Yahboom_OLED:
    def __init__(self, i2c_bus="auto", clear=False):
        self.__clear = clear
        self.__clear_count = 0
        self.__top = -2
        self.__x = 0

        self.__BUS_LIST = [1, 0, 7, 8]
        self.__bus_index = 0
        if i2c_bus != "auto":
            self.__i2c_bus = int(i2c_bus)
            self.__bus_index = 0xFF
        else:
            self.__i2c_bus = self.__BUS_LIST[self.__bus_index]

        self.__WIDTH = 128
        self.__HEIGHT = 32
        self.__image = Image.new('1', (self.__WIDTH, self.__HEIGHT))
        self.__draw = ImageDraw.Draw(self.__image)
        self.__font = ImageFont.load_default()

        self.mutex = threading.Lock()

    # Initialize OLED, return True on success, False on failure
    def begin(self):
        try:
            self.__oled = SSD.SSD1306_128_32(
                rst=None, i2c_bus=self.__i2c_bus, gpio=1)
            self.__oled.begin()
            self.__oled.clear()
            self.__oled.display()
            return True
        except:
            if self.__bus_index == 0xFF:
                return
            max_bus = len(self.__BUS_LIST)
            self.__bus_index = (self.__bus_index + 1) % max_bus
            self.__i2c_bus = self.__BUS_LIST[self.__bus_index]
            return False

    # 清除显示。refresh=True立即刷新，refresh=False不刷新。
    # Clear the display.  Refresh =True Refresh immediately, refresh=False refresh not
    def clear(self, refresh=False):
        self.__draw.rectangle(
            (0, 0, self.__WIDTH, self.__HEIGHT), outline=0, fill=0)
        if refresh:
            try:
                self.refresh()
                return True
            except:
                return False

    # 增加字符。start_x start_y表示开始的点。text是要增加的字符。
    # refresh=True立即刷新，refresh=False不刷新。
    # Add characters.  Start_x Start_y indicates the starting point.  Text is the character to be added
    # Refresh =True Refresh immediately, refresh=False refresh not
    def add_text(self, start_x, start_y, text, refresh=False):
        if start_x > self.__WIDTH or start_y > self.__HEIGHT:
            return
        x = int(start_x + self.__x)
        y = int(start_y + self.__top)
        self.__draw.text((x, y), str(text), font=self.__font, fill=255)
        if refresh:
            self.refresh()

    # 写入一行字符text。refresh=True立即刷新，refresh=False不刷新。
    # line=[0, 3]
    # Write a line of character text.  Refresh =True Refresh immediately, refresh=False refresh not.
    def add_line(self, text, line=0, refresh=False):
        if line < 0 or line > 3:
            return
        y = int(8 * line)
        self.add_text(0, y, text, refresh)

    # Refresh the OLED to display the content
    def refresh(self):
        self.__oled.image(self.__image)
        self.mutex.acquire()
        self.__oled.display()
        self.mutex.release()
