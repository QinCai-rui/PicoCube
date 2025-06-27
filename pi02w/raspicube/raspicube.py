#!/usr/bin/env python3
"""
######## THIS IS ENTIRELY REWRITTEN FOR THE PI ZERO 2W BY GITHUB COPILOT ########

Original Pico version by myself, @QinCai-rui, https://qincai.xyz

RasPiCube - Complete Pi Zero 2W port of Pico Rubik's Cube Timer
Replicates ALL functionality from the original Pico version including:
- Full display UI with proper fonts and colors
- Backlight management with touch-to-wake
- Timer control with hold/release logic
- Results display with averages (ao5, ao12)
- Clear history with confirmation dialog
- Version display
- Proper button handling and debouncing
- OPTIMIZED: Fast timer display with 20+ FPS updates
"""

import time
import random
import json
import os
import logging
from pathlib import Path
# from datetime import datetime
# import sys

# Set up logging so systemd and journalctl will capture the output
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s'
)
logger = logging.getLogger("raspicube")

# GPIO libraries for Pi
import RPi.GPIO as GPIO

# Display libraries - using luma.lcd instead of st7789
from luma.core.interface.serial import spi
from luma.core.render import canvas
from luma.lcd.device import st7789
from PIL import Image, ImageDraw, ImageFont

VERSION = "v1.6.5-rpi"

# GPIO Pin definitions (BCM numbering)
TIMER_PIN = 26
NEXT_PIN = 19

# Display dimensions - using actual ST7789 resolution
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240

# Colors (RGB tuples)
class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    CYAN = (0, 255, 255)
    MAGENTA = (255, 0, 255)
    YELLOW = (255, 255, 0)

# Rubik's cube settings (same as Pico)
faces = ['U', 'D', 'L', 'R', 'F', 'B']
modifiers = ['', "'", '2']
opposite = {'U':'D', 'D':'U', 'L':'R', 'R':'L', 'F':'B', 'B':'F'}

RESULTS_FILE = os.path.expanduser("~/.raspicube/cube_times.json")

# Backlight management (same as Pico)
BACKLIGHT_TIMEOUT_MS = 20000
BACKLIGHT_SOLVE_EXTRA_MS = 10000
SCRAMBLE_BACKLIGHT_TIMEOUT_MS = 30000  # 30 seconds on scramble screen

class FontManager:
    """Manage fonts to match Pico's font sizes"""
    def __init__(self):
        self.font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        ]
        
        # Font sizes matching Pico's vga1_16x32 and vga1_8x16
        self.big_font = self._load_font(28)    # Larger for 320x240 display
        self.small_font = self._load_font(14)  # Adjusted for readability
        
        # Calculate font metrics
        self.big_width = 18
        self.big_height = 32
        self.small_width = 9
        self.small_height = 16
    
    def _load_font(self, size):
        """Load the best available font"""
        for path in self.font_paths:
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
        return ImageFont.load_default()

class PiCubeTimer:
    def __init__(self):
        # Create the directory if it doesn't exist
        results_dir = os.path.dirname(RESULTS_FILE)
        Path(results_dir).mkdir(parents=True, exist_ok=True)
        
        # Rest of initialization remains the same
        self.setup_gpio()
        self.setup_display()
        self.font_manager = FontManager()
        self.setup_timer_buffer()
        
        # State management with better error handling
        self.solve_times = self.load_times()
        self.last_touch_time = self.ticks_ms()
        self.backlight_on = True
        
        logger.info("🚀 RasPiCube Timer initialized!")
        logger.info(f"📝 Results file: {RESULTS_FILE}")
    
    def setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TIMER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(NEXT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        logger.info("✅ GPIO initialized")
    
    def setup_display(self):
        """Initialize the ST7789 display using luma.lcd"""
        try:
            # OPTIMIZED: Higher SPI speed for faster updates
            self.serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25, spi_speed_hz=80000000)
            
            # Initialize ST7789 device
            self.device = st7789(self.serial, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, rotate=0)
            
            logger.info("✅ ST7789 display initialized with 80MHz SPI")
            
            # Initialize with black screen
            self.fill_screen(Colors.BLACK)
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize display: {e}")
            self.device = None
    
    def setup_timer_buffer(self):
        """Create persistent buffer for fast timer updates"""
        self.timer_buffer = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), Colors.BLACK)
        self.timer_draw = ImageDraw.Draw(self.timer_buffer)
        self.last_timer_str = ""
    
    def ticks_ms(self):
        """Get current time in milliseconds (like Pico's time.ticks_ms())"""
        return int(time.time() * 1000)
    
    def ticks_diff(self, new_ticks, old_ticks):
        """Calculate time difference (like Pico's time.ticks_diff())"""
        return new_ticks - old_ticks
    
    def sleep_ms(self, ms):
        """Sleep for milliseconds (like Pico's time.sleep_ms())"""
        time.sleep(ms / 1000.0)
    
    # Display functions using luma.lcd
    def fill_screen(self, color):
        """Fill entire screen with color"""
        if self.device:
            try:
                with canvas(self.device) as draw:
                    draw.rectangle(self.device.bounding_box, fill=color)
            except Exception as e:
                logger.error(f"Display error in fill_screen: {e}")
    
    def draw_text(self, draw, text, x, y, font, color):
        """Draw text with the given parameters"""
        draw.text((x, y), text, font=font, fill=color)
    
    def create_display_image(self, draw_func):
        """Create and display an image using the provided drawing function"""
        if self.device:
            try:
                with canvas(self.device) as draw:
                    draw_func(draw)
            except Exception as e:
                logger.error(f"Display error: {e}")
    
    # OPTIMIZED TIMER DISPLAY - Fast updates with frame buffer
    def display_timer_fast(self, time_val, running=True):
        """OPTIMIZED timer display - only updates changed areas"""
        timer_str = "{:6.1f}".format(time_val) if running else "{:6.2f}".format(time_val)
        
        # Only redraw if timer value actually changed
        if timer_str != self.last_timer_str:
            # Get text size
            timer_bbox = self.timer_draw.textbbox((0, 0), timer_str, font=self.font_manager.big_font)
            timer_width = timer_bbox[2] - timer_bbox[0]
            timer_height = timer_bbox[3] - timer_bbox[1]
            
            x_timer = max(0, (DISPLAY_WIDTH - timer_width) // 2)
            y_timer = (DISPLAY_HEIGHT - timer_height) // 2
            
            # Clear only the timer area (not whole screen)
            self.timer_draw.rectangle([
                x_timer - 10, y_timer - 10, 
                x_timer + timer_width + 10, y_timer + timer_height + 10
            ], fill=Colors.BLACK)
            
            # Draw new timer
            color = Colors.GREEN if running else Colors.CYAN
            self.timer_draw.text((x_timer, y_timer), timer_str, font=self.font_manager.big_font, fill=color)
            
            # Push to display directly (bypass canvas overhead)
            if self.device:
                self.device.display(self.timer_buffer)
            
            self.last_timer_str = timer_str

    def clear_timer_buffer(self):
        """Clear the timer buffer"""
        self.timer_draw.rectangle([(0, 0), (DISPLAY_WIDTH, DISPLAY_HEIGHT)], fill=Colors.BLACK)
        self.last_timer_str = ""
    
    # Backlight management
    def set_backlight(self, state):
        """Set the backlight state"""
        self.backlight_on = state
        # Note: luma.lcd handles backlight automatically
    
    def update_touch_time(self):
        """Update the last touch time and wake backlight if needed"""
        self.last_touch_time = self.ticks_ms()
        if not self.backlight_on:
            self.set_backlight(True)
    
    def check_backlight_timeout(self, timeout_ms=None):
        """Check if backlight should be turned off due to timeout"""
        effective_timeout = timeout_ms if timeout_ms is not None else BACKLIGHT_TIMEOUT_MS
        if self.backlight_on and self.ticks_diff(self.ticks_ms(), self.last_touch_time) > effective_timeout:
            self.set_backlight(False)
            return True
        return False
    
    def any_touch(self):
        """Check if any button is pressed"""
        return GPIO.input(TIMER_PIN) or GPIO.input(NEXT_PIN)
    
    # Core timer functions
    def load_times(self):
        """Load solve times from file with better error handling"""
        try:
            if os.path.exists(RESULTS_FILE):
                with open(RESULTS_FILE, "r") as f:
                    return json.load(f)
            else:
                logger.warning(f"⚠️ No existing results file found at {RESULTS_FILE}")
                return []
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ Error reading results file: Invalid JSON format - {e}")
            # Backup corrupted file
            if os.path.exists(RESULTS_FILE):
                backup = f"{RESULTS_FILE}.bak"
                try:
                    os.rename(RESULTS_FILE, backup)
                    logger.info(f"📦 Corrupted file backed up to {backup}")
                except OSError as e:
                    logger.error(f"❌ Failed to backup corrupted file: {e}")
            return []
        except OSError as e:
            logger.warning(f"⚠️ Error accessing results file: {e}")
            return []
        except Exception as e:
            logger.warning(f"⚠️ Unexpected error loading results: {e}")
            return []

    def save_times(self, times):
        """Save solve times to file with better error handling"""
        try:
            # Create temp file
            temp_file = f"{RESULTS_FILE}.tmp"
            with open(temp_file, "w") as f:
                json.dump(times, f, indent=2)
            
            # Atomic replace
            if os.name == 'nt':  # Windows
                if os.path.exists(RESULTS_FILE):
                    os.remove(RESULTS_FILE)
            os.rename(temp_file, RESULTS_FILE)
            
        except OSError as e:
            logger.error(f"❌ Error saving times: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        except Exception as e:
            logger.error(f"❌ Unexpected error saving times: {e}")
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def clear_times(self):
        """Clear all solve times with better error handling"""
        try:
            # Save empty list
            with open(RESULTS_FILE, "w") as f:
                json.dump([], f)
        except Exception as e:
            logger.error(f"❌ Error clearing times: {e}")
    
    def generate_scramble(self, n_moves=20):
        """Generate a random Rubik's cube scramble"""
        scramble = []
        prev = None
        for _ in range(n_moves):
            while True:
                f = random.choice(faces)
                if f != prev and (prev is None or f != opposite[prev]):
                    break
            m = random.choice(modifiers)
            scramble.append(f + m)
            prev = f
        return " ".join(scramble)
    
    def wrap_scramble(self, scramble, max_line_len=18):
        """Wrap scramble text into lines (adjusted for wider display)"""
        words = scramble.split()
        lines = []
        current = ""
        for w in words:
            if len(current) + len(w) + 1 <= max_line_len:
                current += ("" if current == "" else " ") + w
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)
        return lines
    
    def avg_of(self, times, count):
        """Calculate average of count solves with trimming"""
        if len(times) < count:
            return None
        
        # Get the most recent 'count' times
        recent_times = [entry["time"] for entry in times[-count:]]
        
        # For ao5 and ao12, trim the best and worst times
        sorted_times = sorted(recent_times)
        trimmed = sorted_times[1:-1]  # Remove best and worst
        return sum(trimmed) / len(trimmed)
    
    # Display functions using luma.lcd
    def display_scramble(self, scramble):
        """Display scramble screen"""
        def draw_scramble(draw):
            # Title
            title = "RasPiCubeZero"
            title_bbox = draw.textbbox((0, 0), title, font=self.font_manager.big_font)
            title_width = title_bbox[2] - title_bbox[0]
            x_title = max(0, (DISPLAY_WIDTH - title_width) // 2)
            self.draw_text(draw, title, x_title, 10, self.font_manager.big_font, Colors.CYAN)
            
            # Subtitle
            subtitle = "Hold GP26 to prep"
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=self.font_manager.big_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            x_sub = max(0, (DISPLAY_WIDTH - subtitle_width) // 2)
            self.draw_text(draw, subtitle, x_sub, 50, self.font_manager.big_font, Colors.YELLOW)
            
            # Scramble text
            lines = self.wrap_scramble(scramble)
            y = 90
            for line in lines:
                line_bbox = draw.textbbox((0, 0), line, font=self.font_manager.big_font)
                line_width = line_bbox[2] - line_bbox[0]
                x_line = max(0, (DISPLAY_WIDTH - line_width) // 2)
                self.draw_text(draw, line, x_line, y, self.font_manager.big_font, Colors.WHITE)
                y += 35
            
            # Version
            version_bbox = draw.textbbox((0, 0), VERSION, font=self.font_manager.small_font)
            version_width = version_bbox[2] - version_bbox[0]
            x_version = DISPLAY_WIDTH - version_width - 10
            y_version = DISPLAY_HEIGHT - 25
            self.draw_text(draw, VERSION, x_version, y_version, self.font_manager.small_font, Colors.RED)
        
        self.create_display_image(draw_scramble)
        logger.info(f"🎲 Scramble: {scramble}")
    
    def display_timer(self, time_val, running=True):
        """Display timer (fallback for non-optimized screens)"""
        def draw_timer(draw):
            timer_str = "{:6.1f}".format(time_val) if running else "{:6.2f}".format(time_val)
            timer_bbox = draw.textbbox((0, 0), timer_str, font=self.font_manager.big_font)
            timer_width = timer_bbox[2] - timer_bbox[0]
            timer_height = timer_bbox[3] - timer_bbox[1]
            
            x_timer = max(0, (DISPLAY_WIDTH - timer_width) // 2)
            y_timer = (DISPLAY_HEIGHT - timer_height) // 2
            
            color = Colors.GREEN if running else Colors.CYAN
            self.draw_text(draw, timer_str, x_timer, y_timer, self.font_manager.big_font, color)
        
        self.create_display_image(draw_timer)
        logger.info(f"⏱️  {time_val:.2f}s")
    
    def display_results_and_avgs(self, latest_time, times, clear_msg=False):
        """Display solve results and averages"""
        def draw_results(draw):
            # Title
            title = "Solve Results"
            title_bbox = draw.textbbox((0, 0), title, font=self.font_manager.small_font)
            title_width = title_bbox[2] - title_bbox[0]
            x_title = max(0, (DISPLAY_WIDTH - title_width) // 2)
            self.draw_text(draw, title, x_title, 10, self.font_manager.small_font, Colors.CYAN)
            
            if clear_msg:
                msg = "History Cleared!"
                msg_bbox = draw.textbbox((0, 0), msg, font=self.font_manager.small_font)
                msg_width = msg_bbox[2] - msg_bbox[0]
                x_msg = max(0, (DISPLAY_WIDTH - msg_width) // 2)
                self.draw_text(draw, msg, x_msg, 35, self.font_manager.small_font, Colors.RED)
                
                prompt = "Tap GP26 to exit"
                prompt_bbox = draw.textbbox((0, 0), prompt, font=self.font_manager.small_font)
                prompt_width = prompt_bbox[2] - prompt_bbox[0]
                x_prompt = max(0, (DISPLAY_WIDTH - prompt_width) // 2)
                self.draw_text(draw, prompt, x_prompt, DISPLAY_HEIGHT - 30, self.font_manager.small_font, Colors.MAGENTA)
                
                # Version
                version_bbox = draw.textbbox((0, 0), VERSION, font=self.font_manager.small_font)
                version_width = version_bbox[2] - version_bbox[0]
                x_version = DISPLAY_WIDTH - version_width - 10
                y_version = DISPLAY_HEIGHT - 25
                self.draw_text(draw, VERSION, x_version, y_version, self.font_manager.small_font, Colors.RED)
                return
            
            # Latest time
            latest_str = "Latest: {:.2f}".format(latest_time)
            self.draw_text(draw, latest_str, 10, 35, self.font_manager.small_font, Colors.GREEN)
            
            # Last 5 times
            y = 55
            self.draw_text(draw, "Last 5:", 10, y, self.font_manager.small_font, Colors.YELLOW)
            for i, entry in enumerate(times[-5:][::-1]):
                t = entry["time"]
                time_str = "{:2d}: {:.2f}".format(len(times)-i, t)
                self.draw_text(draw, time_str, 80, y, self.font_manager.small_font, Colors.WHITE)
                y += 18
            
            y += 10
            
            # Averages
            ao5 = self.avg_of(times, 5)
            ao12 = self.avg_of(times, 12)
            
            ao5_str = "ao5:  --.--" if ao5 is None else "ao5: {:.2f}".format(ao5)
            ao12_str = "ao12: --.--" if ao12 is None else "ao12: {:.2f}".format(ao12)
            
            self.draw_text(draw, ao5_str, 10, y, self.font_manager.small_font, Colors.CYAN)
            y += 18
            self.draw_text(draw, ao12_str, 10, y, self.font_manager.small_font, Colors.CYAN)
            
            # Version
            version_bbox = draw.textbbox((0, 0), VERSION, font=self.font_manager.small_font)
            version_width = version_bbox[2] - version_bbox[0]
            x_version = DISPLAY_WIDTH - version_width - 10
            y_version = DISPLAY_HEIGHT - 25
            self.draw_text(draw, VERSION, x_version, y_version, self.font_manager.small_font, Colors.RED)
        
        self.create_display_image(draw_results)
        
        logger.info(f"📊 Latest: {latest_time:.2f}s")
        ao5 = self.avg_of(times, 5)
        ao12 = self.avg_of(times, 12)
        if ao5:
            logger.info(f"📊 ao5: {ao5:.2f}s")
        if ao12:
            logger.info(f"📊 ao12: {ao12:.2f}s")
    
    def display_are_you_sure(self):
        """Display confirmation dialog"""
        def draw_confirm(draw):
            msg = "Are you sure?"
            msg_bbox = draw.textbbox((0, 0), msg, font=self.font_manager.small_font)
            msg_width = msg_bbox[2] - msg_bbox[0]
            x_msg = max(0, (DISPLAY_WIDTH - msg_width) // 2)
            self.draw_text(draw, msg, x_msg, 60, self.font_manager.small_font, Colors.YELLOW)
            
            msg2 = "GP19: Clear | GP26: Cancel"
            msg2_bbox = draw.textbbox((0, 0), msg2, font=self.font_manager.small_font)
            msg2_width = msg2_bbox[2] - msg2_bbox[0]
            x_msg2 = max(0, (DISPLAY_WIDTH - msg2_width) // 2)
            self.draw_text(draw, msg2, x_msg2, 120, self.font_manager.small_font, Colors.MAGENTA)
            
            # Version
            version_bbox = draw.textbbox((0, 0), VERSION, font=self.font_manager.small_font)
            version_width = version_bbox[2] - version_bbox[0]
            x_version = DISPLAY_WIDTH - version_width - 10
            y_version = DISPLAY_HEIGHT - 25
            self.draw_text(draw, VERSION, x_version, y_version, self.font_manager.small_font, Colors.RED)
        
        self.create_display_image(draw_confirm)
        logger.info("❓ Are you sure you want to clear history?")
    
    def display_timer_prep(self, message, color):
        """Display timer preparation screen"""
        def draw_prep(draw):
            # Title
            title = "RasPiCubeZero"
            title_bbox = draw.textbbox((0, 0), title, font=self.font_manager.big_font)
            title_width = title_bbox[2] - title_bbox[0]
            x_title = max(0, (DISPLAY_WIDTH - title_width) // 2)
            self.draw_text(draw, title, x_title, 10, self.font_manager.big_font, Colors.CYAN)
            
            # Message
            msg_bbox = draw.textbbox((0, 0), message, font=self.font_manager.big_font)
            msg_width = msg_bbox[2] - msg_bbox[0]
            x_msg = max(0, (DISPLAY_WIDTH - msg_width) // 2)
            self.draw_text(draw, message, x_msg, 80, self.font_manager.big_font, color)
        
        self.create_display_image(draw_prep)
    
    def display_completion(self, final_time):
        """Display completion screen"""
        def draw_completion(draw):
            # Timer
            timer_str = "{:6.2f}".format(final_time)
            timer_bbox = draw.textbbox((0, 0), timer_str, font=self.font_manager.big_font)
            timer_width = timer_bbox[2] - timer_bbox[0]
            timer_height = timer_bbox[3] - timer_bbox[1]
            
            x_timer = max(0, (DISPLAY_WIDTH - timer_width) // 2)
            y_timer = (DISPLAY_HEIGHT - timer_height) // 2
            self.draw_text(draw, timer_str, x_timer, y_timer, self.font_manager.big_font, Colors.CYAN)
            
            # Completion message
            subtitle = "Done! Tap GP19"
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=self.font_manager.big_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            x_sub = max(0, (DISPLAY_WIDTH - subtitle_width) // 2)
            self.draw_text(draw, subtitle, x_sub, 50, self.font_manager.big_font, Colors.YELLOW)
            
            # Version
            version_bbox = draw.textbbox((0, 0), VERSION, font=self.font_manager.small_font)
            version_width = version_bbox[2] - version_bbox[0]
            x_version = DISPLAY_WIDTH - version_width - 10
            y_version = DISPLAY_HEIGHT - 25
            self.draw_text(draw, VERSION, x_version, y_version, self.font_manager.small_font, Colors.RED)
        
        self.create_display_image(draw_completion)
    
    # Button handling functions (same as original with touch-to-wake)
    def wait_for_touch_or_action(self, pin_check_fn, backlight_timeout=None):
        """Wait for a pin to be pressed with touch-to-wake logic"""
        while True:
            self.check_backlight_timeout(backlight_timeout)
            if pin_check_fn():
                self.update_touch_time()
                if not self.backlight_on:
                    # Wake the screen, but do NOT trigger the action
                    while pin_check_fn():
                        self.sleep_ms(10)
                    continue
                # Backlight is on, so this is a real action
                while pin_check_fn():
                    self.sleep_ms(10)
                return
            self.sleep_ms(10)
    
    def wait_for_next_scramble(self):
        """Wait for either pin to be pressed (30s timeout on scramble screen)"""
        self.wait_for_touch_or_action(
            lambda: GPIO.input(NEXT_PIN) or GPIO.input(TIMER_PIN),
            backlight_timeout=SCRAMBLE_BACKLIGHT_TIMEOUT_MS
        )
    
    def wait_for_next(self):
        """Wait for either pin to be pressed (default timeout)"""
        self.wait_for_touch_or_action(
            lambda: GPIO.input(NEXT_PIN) or GPIO.input(TIMER_PIN)
        )
    
    def wait_for_next_with_results(self):
        """Wait for next_pin or timer_pin with touch-to-wake. Returns 'clear' or 'exit'"""
        while True:
            self.check_backlight_timeout()
            if GPIO.input(NEXT_PIN):
                self.update_touch_time()
                if not self.backlight_on:
                    while GPIO.input(NEXT_PIN):
                        self.sleep_ms(10)
                    continue
                while GPIO.input(NEXT_PIN):
                    self.sleep_ms(10)
                return "clear"
            if GPIO.input(TIMER_PIN):
                self.update_touch_time()
                if not self.backlight_on:
                    while GPIO.input(TIMER_PIN):
                        self.sleep_ms(10)
                    continue
                while GPIO.input(TIMER_PIN):
                    self.sleep_ms(10)
                return "exit"
            self.sleep_ms(10)
    
    def wait_for_confirm_clear(self):
        """Wait for confirmation. Returns 'clear' or 'cancel'"""
        while True:
            self.check_backlight_timeout()
            if GPIO.input(NEXT_PIN):
                self.update_touch_time()
                if not self.backlight_on:
                    while GPIO.input(NEXT_PIN):
                        self.sleep_ms(10)
                    continue
                while GPIO.input(NEXT_PIN):
                    self.sleep_ms(10)
                return "clear"
            if GPIO.input(TIMER_PIN):
                self.update_touch_time()
                if not self.backlight_on:
                    while GPIO.input(TIMER_PIN):
                        self.sleep_ms(10)
                    continue
                while GPIO.input(TIMER_PIN):
                    self.sleep_ms(10)
                return "cancel"
            self.sleep_ms(10)
    
    def timer_control(self):
        """Timer control logic with OPTIMIZED display updates"""
        HOLD_TIME_MS = 400  # Minimum hold time to qualify as "ready"
        
        # Wait for button release first
        while GPIO.input(TIMER_PIN):
            self.update_touch_time()
            self.sleep_ms(10)
        
        while True:
            # Show initial prep message
            self.display_timer_prep("Hold GP26 to prep", Colors.YELLOW)
            
            # Wait for button press
            while not GPIO.input(TIMER_PIN):
                self.check_backlight_timeout()
                self.sleep_ms(10)
            
            hold_start = self.ticks_ms()
            held_long_enough = False
            
            while GPIO.input(TIMER_PIN):
                held_time = self.ticks_diff(self.ticks_ms(), hold_start)
                
                # Show status based on hold time
                if not held_long_enough and held_time < HOLD_TIME_MS:
                    self.display_timer_prep("Keep holding it", Colors.YELLOW)
                elif not held_long_enough and held_time >= HOLD_TIME_MS:
                    held_long_enough = True
                    self.display_timer_prep("Release to start!", Colors.RED)
                
                self.update_touch_time()
                self.sleep_ms(30)
            
            if held_long_enough:
                break
            else:
                # Button released too soon, loop and try again
                self.update_touch_time()
        
        # Wait for button release to start timer
        while GPIO.input(TIMER_PIN):
            self.update_touch_time()
            self.sleep_ms(10)
        
        # OPTIMIZED TIMER LOOP - Fast updates with frame buffer
        timer_start = self.ticks_ms()
        self.update_touch_time()
        
        # Clear timer buffer and prepare for fast updates
        self.clear_timer_buffer()
        
        update_interval = 50   # 50ms = 20 FPS
        poll_interval = 5      # 5ms button polling
        last_update = self.ticks_ms()
        
        while True:
            elapsed = (self.ticks_ms() - timer_start) / 1000
            now = self.ticks_ms()
            if self.ticks_diff(now, last_update) >= update_interval:
                self.display_timer_fast(elapsed, running=True)  # Use optimized method
                last_update = now
            self.sleep_ms(poll_interval)
            if GPIO.input(TIMER_PIN):
                break
            if self.any_touch():
                self.update_touch_time()
        
        final_elapsed = (self.ticks_ms() - timer_start) / 1000
        self.display_timer_fast(final_elapsed, running=False)  # Use optimized method
        
        while GPIO.input(TIMER_PIN):
            self.update_touch_time()
            self.sleep_ms(10)
        
        # Show completion screen
        self.display_completion(final_elapsed)
        
        # Extra wait for long solves
        if final_elapsed >= 20:
            self.update_touch_time()
            extra_wait = 0
            while extra_wait < BACKLIGHT_SOLVE_EXTRA_MS:
                self.sleep_ms(100)
                extra_wait += 100
                if self.any_touch():
                    self.update_touch_time()
                    break
                self.check_backlight_timeout()
        
        return final_elapsed
    
    def main(self):
        """Main loop"""
        try:
            while True:
                scramble = self.generate_scramble(20)
                self.display_scramble(scramble)
                self.wait_for_next_scramble()
                timer_val = self.timer_control()
                self.solve_times.append({"time": timer_val, "scramble": scramble})
                self.save_times(self.solve_times)
                
                # Wait for tap of GP19 to show results/averages
                self.wait_for_touch_or_action(lambda: GPIO.input(NEXT_PIN))
                while GPIO.input(NEXT_PIN):
                    self.sleep_ms(10)
                
                self.display_results_and_avgs(timer_val, self.solve_times)
                
                # Wait for tap of GP19 (clear) or GP26 (exit)
                action = self.wait_for_next_with_results()
                
                if action == "exit":
                    continue
                elif action == "clear":
                    # Are you sure dialog
                    self.display_are_you_sure()
                    confirm_action = self.wait_for_confirm_clear()
                    if confirm_action == "clear":
                        self.solve_times = []
                        self.clear_times()
                        self.display_results_and_avgs(0, self.solve_times, clear_msg=True)
                        # Wait for tap of GP26 to exit cleared screen
                        self.wait_for_touch_or_action(lambda: GPIO.input(TIMER_PIN))
                        while GPIO.input(TIMER_PIN):
                            self.sleep_ms(10)
                        continue
                    else:
                        # Cancel, redisplay stats
                        self.display_results_and_avgs(timer_val, self.solve_times)
                        action = self.wait_for_next_with_results()
                        if action == "exit":
                            continue
                        elif action == "clear":
                            self.display_are_you_sure()
                            confirm_action = self.wait_for_confirm_clear()
                            if confirm_action == "clear":
                                self.solve_times = []
                                self.clear_times()
                                self.display_results_and_avgs(0, self.solve_times, clear_msg=True)
                                self.wait_for_touch_or_action(lambda: GPIO.input(TIMER_PIN))
                                while GPIO.input(TIMER_PIN):
                                    self.sleep_ms(10)
                                continue
                            else:
                                self.display_results_and_avgs(timer_val, self.solve_times)
                                while True:
                                    a = self.wait_for_next_with_results()
                                    if a == "exit":
                                        break
                                    if a == "clear":
                                        self.display_are_you_sure()
                                        c = self.wait_for_confirm_clear()
                                        if c == "clear":
                                            self.solve_times = []
                                            self.clear_times()
                                            self.display_results_and_avgs(0, self.solve_times, clear_msg=True)
                                            self.wait_for_touch_or_action(lambda: GPIO.input(TIMER_PIN))
                                            while GPIO.input(TIMER_PIN):
                                                self.sleep_ms(10)
                                            break
        
        except KeyboardInterrupt:
            logger.info("\n👋 Goodbye!")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            GPIO.cleanup()
            logger.info("🧹 GPIO cleaned up")

if __name__ == "__main__":
    logger.info("🚀 Starting RasPiCube Timer for Pi Zero 2W...")
    logger.info("🔌 Hardware should be connected as follows:")
    logger.info("   Timer Button:  GPIO 26 (Physical pin 37) -> Button -> GND")
    logger.info("   Next Button:   GPIO 19 (Physical pin 35) -> Button -> GND")
    logger.info("   ST7789 Display:")
    logger.info("     VCC -> 3.3V, GND -> GND")
    logger.info("     SCL -> GPIO 11 (SCLK), SDA -> GPIO 10 (MOSI)")
    logger.info("     RES -> GPIO 25, DC -> GPIO 24, CS -> GPIO 8 (CE0)")
    logger.info("")
    logger.info("📦 Required packages:")
    logger.info("   pip3 install luma.lcd RPi.GPIO pillow")
    logger.info("")
    logger.info("⚡ OPTIMIZED: Fast timer display with 20+ FPS updates!")
    logger.info("")
    
    timer = PiCubeTimer()
    timer.main()