from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
from time import sleep

# --- OLED Setup ---
I2C_PORT = 1
I2C_ADDRESS = 0x3C

serial = i2c(port=I2C_PORT, address=I2C_ADDRESS)
device = ssd1306(serial, width=128, height=64)

def show_shutdown_notice():
    device.clear()
    image = Image.new('1', (device.width, device.height))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
    msg = "System is down.\nUnplug power."
    # Multi-line centering
    lines = msg.split('\n')
    # Handle font deprecation (Pillow >=10)
    def get_text_size(txt):
        try:
            bbox = draw.textbbox((0,0), txt, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            return draw.textsize(txt, font=font)
    line_heights = [get_text_size(line)[1] for line in lines]
    total_height = sum(line_heights)
    y = (device.height - total_height) // 2
    for i, line in enumerate(lines):
        w, h = get_text_size(line)
        x = (device.width - w) // 2
        draw.text((x, y), line, font=font, fill=255)
        y += line_heights[i]
    device.display(image)

if __name__ == "__main__":
    show_shutdown_notice()
    sleep(2)  # Keep the message displayed for a while