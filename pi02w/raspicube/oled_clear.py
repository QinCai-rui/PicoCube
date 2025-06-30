from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=64)
device.clear()