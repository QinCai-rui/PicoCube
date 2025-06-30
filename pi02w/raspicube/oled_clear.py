from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=64)

msg = "System is down.\nUnplug power."

image = Image.new('1', (device.width, device.height))
draw = ImageDraw.Draw(image)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
except Exception:
    font = ImageFont.load_default()

# Calculate multi-line text size and center it
lines = msg.split('\n')
line_height = font.getsize("A")[1]
total_height = line_height * len(lines)
y = (device.height - total_height) // 2

for line in lines:
    w, h = draw.textsize(line, font=font)
    x = (device.width - w) // 2
    draw.text((x, y), line, font=font, fill=255)
    y += line_height

device.display(image)