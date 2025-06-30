import time
import subprocess
import RPi.GPIO as GPIO
import logging
import sys
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

# --- Configuration ---
SHUTDOWN_PIN = 27  # BCM 27 (physical pin 13)
I2C_PORT = 1
I2C_ADDRESS = 0x3C

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# --- OLED Setup ---
serial = i2c(port=I2C_PORT, address=I2C_ADDRESS)
device = ssd1306(serial, width=128, height=64)

def show_shutdown_notice():
    logging.info("Displaying shutdown notice.")
    device.clear()
    image = Image.new('1', (device.width, device.height))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
    msg = "Shutting down..."
    w, h = draw.textsize(msg, font=font)
    x = (device.width - w) // 2
    y = (device.height - h) // 2
    draw.text((x, y), msg, font=font, fill=255)
    device.display(image)

def main():
    logging.info("Starting OLED shutdown service on GPIO27 (pin 13).")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(SHUTDOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    try:
        while True:
            if GPIO.input(SHUTDOWN_PIN):
                logging.info("Button pressed on GPIO27! Initiating shutdown...")
                show_shutdown_notice()
                time.sleep(1)  # Give time for display update
                logging.info("Calling system shutdown.")
                subprocess.Popen(["sudo", "systemctl", "poweroff"])
                break
            time.sleep(0.05)
    except Exception as e:
        logging.error(f"Exception occurred: {e}")
    finally:
        logging.info("Cleaning up GPIO.")
        GPIO.cleanup()

if __name__ == "__main__":
    main()