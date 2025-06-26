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
"""

import time
import random
import json
import os
from datetime import datetime
import sys

# GPIO and SPI libraries for Pi
import RPi.GPIO as GPIO
import spidev
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Try to import ST7789 library
try:
    import st7789
    HAS_ST7789 = True
except ImportError:
    print("Warning: st7789 library not found. Install with: pip3 install st7789")
    HAS_ST7789 = False

VERSION = "v1.5.1-1-Pi"

# GPIO Pin definitions (BCM numbering)
TIMER_PIN = 15  # GPIO 15 (Physical pin 10) - Timer control (GP15 equivalent)
NEXT_PIN = 19   # GPIO 19 (Physical pin 35) - Next scramble / show avgs (GP19 equivalent)

# Display dimensions (same as Pico)
TFT_WIDTH = 240  
TFT_HEIGHT = 320
REAL_WIDTH = 320  # Physical dimensions in landscape mode
REAL_HEIGHT = 240

# ST7789 Colors (matching Pico st7789 library)
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

RESULTS_FILE = "cube_times.json"

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
        self.big_font = self._load_font(24)    # Matches vga1_16x32 appearance
        self.small_font = self._load_font(12)  # Matches vga1_8x16 appearance
        
        # Calculate font metrics (matching Pico's font.WIDTH and font.HEIGHT)
        self.big_width = 16
        self.big_height = 32
        self.small_width = 8
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
        # Initialize components
        self.setup_gpio()
        self.setup_display()
        self.font_manager = FontManager()
        
        # State management
        self.solve_times = self.load_times()
        self.last_touch_time = self.ticks_ms()
        self.backlight_on = True
        
        print("🚀 RasPiCube Timer initialized!")
    
    def setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TIMER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(NEXT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        print("✅ GPIO initialized")
    
    def setup_display(self):
        """Initialize the ST7789 display"""
        if HAS_ST7789:
            try:
                self.disp = st7789.ST7789(
                    port=0,        # SPI port
                    cs=0,          # CE0
                    dc=24,         # GPIO 24
                    rst=25,        # GPIO 25  
                    backlight=23,  # GPIO 23
                    spi_speed_hz=40000000,
                    width=TFT_WIDTH,
                    height=TFT_HEIGHT,
                    rotation=90    # Landscape mode (rotation=1 equivalent)
                )
                print("✅ ST7789 display initialized")
                
                # Initialize with black screen
                self.fill(Colors.BLACK)
                
            except Exception as e:
                print(f"❌ Failed to initialize display: {e}")
                self.disp = None
        else:
            print("⚠️  Running in headless mode (no display)")
            self.disp = None
    
    def ticks_ms(self):
        """Get current time in milliseconds (like Pico's time.ticks_ms())"""
        return int(time.time() * 1000)
    
    def ticks_diff(self, new_ticks, old_ticks):
        """Calculate time difference (like Pico's time.ticks_diff())"""
        return new_ticks - old_ticks
    
    def sleep_ms(self, ms):
        """Sleep for milliseconds (like Pico's time.sleep_ms())"""
        time.sleep(ms / 1000.0)
    
    # Display functions (matching Pico st7789 API)
    def fill(self, color):
        """Fill entire screen with color"""
        if self.disp:
            try:
                image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), color)
                self.disp.display(image)
            except Exception as e:
                print(f"Display error in fill: {e}")
    
    def fill_rect(self, x, y, width, height, color):
        """Fill rectangle with color"""
        if self.disp:
            try:
                # Get current image or create new one
                image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
                draw = ImageDraw.Draw(image)
                draw.rectangle([x, y, x + width - 1, y + height - 1], fill=color)
                self.disp.display(image)
            except Exception as e:
                print(f"Display error in fill_rect: {e}")
    
    def text(self, font_type, text, x, y, color):
        """Display text (matching Pico's tft.text() API)"""
        if self.disp:
            try:
                image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
                draw = ImageDraw.Draw(image)
                
                # Select font based on type
                if font_type == "big":
                    font = self.font_manager.big_font
                else:
                    font = self.font_manager.small_font
                
                draw.text((x, y), text, font=font, fill=color)
                self.disp.display(image)
            except Exception as e:
                print(f"Display error in text: {e}")
        
        # Always print to console as well
        print(f"📺 {text}")
    
    def text_on_image(self, image, font_type, text, x, y, color):
        """Draw text on existing image"""
        draw = ImageDraw.Draw(image)
        
        # Select font based on type
        if font_type == "big":
            font = self.font_manager.big_font
        else:
            font = self.font_manager.small_font
        
        draw.text((x, y), text, font=font, fill=color)
    
    def display_image(self, image):
        """Display PIL image"""
        if self.disp:
            try:
                self.disp.display(image)
            except Exception as e:
                print(f"Display error: {e}")
    
    # Backlight management (matching Pico functionality)
    def set_backlight(self, state):
        """Set the backlight state"""
        self.backlight_on = state
        if self.disp and hasattr(self.disp, '_backlight'):
            try:
                if hasattr(self.disp._backlight, 'value'):
                    self.disp._backlight.value = 1 if state else 0
                else:
                    # Try different backlight control methods
                    pass
            except:
                pass
    
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
    
    # Core timer functions (matching Pico implementation exactly)
    def load_times(self):
        """Load solve times from file"""
        try:
            with open(RESULTS_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    
    def save_times(self, times):
        """Save solve times to file"""
        try:
            with open(RESULTS_FILE, "w") as f:
                json.dump(times, f, indent=2)
        except Exception as e:
            print(f"Error saving times: {e}")
    
    def clear_times(self):
        """Clear all solve times"""
        try:
            with open(RESULTS_FILE, "w") as f:
                json.dump([], f)
        except Exception as e:
            print(e)
    
    def generate_scramble(self, n_moves=20):
        """Generate a random Rubik's cube scramble (exact Pico implementation)"""
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
    
    def wrap_scramble(self, scramble, max_line_len=15):
        """Wrap scramble text into lines (exact Pico implementation)"""
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
        """Calculate average of count solves with trimming (exact Pico implementation)"""
        if len(times) < count:
            return None
        
        # Get the most recent 'count' times
        recent_times = [entry["time"] for entry in times[-count:]]
        
        # For ao5 and ao12, trim the best and worst times according to WCA standards
        sorted_times = sorted(recent_times)
        trimmed = sorted_times[1:-1]  # Remove best and worst
        return sum(trimmed) / len(trimmed)
    
    # Display functions (exact Pico implementations)
    def draw_version(self):
        """Draw version in bottom-right corner (exact Pico implementation)"""
        if not self.disp:
            return
            
        version_str = VERSION
        
        # Calculate version string width
        version_width = self.font_manager.small_width * len(version_str)
        
        # Calculate position - preserve the right and bottom offsets that worked
        x = 255 - (version_width - len("v1.1.0") * self.font_manager.small_width)
        y = 210
        
        # Create image for just the version area
        image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
        
        # Clear background area with a bit of padding
        draw = ImageDraw.Draw(image)
        draw.rectangle([x-2, y-2, x+version_width+2, y+self.font_manager.small_height+2], fill=Colors.BLACK)
        
        # Draw version text
        self.text_on_image(image, "small", version_str, x, y, Colors.RED)
        self.display_image(image)
    
    def display_scramble(self, scramble):
        """Display scramble screen (exact Pico implementation)"""
        image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
        
        # Title
        title = "RasPiCube - PicoCube"
        x_title = max(0, (TFT_WIDTH - self.font_manager.big_width * len(title)) // 2)
        self.text_on_image(image, "big", title, x_title, 10, Colors.CYAN)
        
        # Subtitle
        subtitle = "Hold GP15 to prep"
        x_sub = max(0, (TFT_WIDTH - self.font_manager.big_width * len(subtitle)) // 2)
        self.text_on_image(image, "big", subtitle, x_sub, 45, Colors.YELLOW)
        
        # Scramble text
        lines = self.wrap_scramble(scramble)
        block_height = len(lines) * 35
        y = max(70, (TFT_HEIGHT - block_height) // 2)
        for line in lines:
            x_line = max(0, (TFT_WIDTH - self.font_manager.big_width * len(line)) // 2)
            self.text_on_image(image, "big", line, x_line, y, Colors.WHITE)
            y += 35
        
        # Version
        version_str = VERSION
        version_width = self.font_manager.small_width * len(version_str)
        x = 255 - (version_width - len("v1.1.0") * self.font_manager.small_width)
        y = 210
        draw = ImageDraw.Draw(image)
        draw.rectangle([x-2, y-2, x+version_width+2, y+self.font_manager.small_height+2], fill=Colors.BLACK)
        self.text_on_image(image, "small", version_str, x, y, Colors.RED)
        
        self.display_image(image)
        print(f"🎲 Scramble: {scramble}")
    
    def display_timer(self, time_val, running=True, clear_all=False):
        """Display timer (exact Pico implementation)"""
        if clear_all:
            image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
        else:
            image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
        
        timer_str = "{:6.1f}".format(time_val) if running else "{:6.2f}".format(time_val)
        x_timer = max(0, (TFT_WIDTH - self.font_manager.big_width * len(timer_str)) // 2)
        y_timer = (TFT_HEIGHT - self.font_manager.big_height) // 2
        
        # Clear the rectangle where the time will be displayed
        draw = ImageDraw.Draw(image)
        timer_width = self.font_manager.big_width * len(timer_str)
        draw.rectangle([x_timer, y_timer, x_timer + timer_width, y_timer + self.font_manager.big_height], fill=Colors.BLACK)
        
        color = Colors.GREEN if running else Colors.CYAN
        self.text_on_image(image, "big", timer_str, x_timer, y_timer, color)
        self.display_image(image)
        
        print(f"⏱️  {timer_str}")
    
    def display_results_and_avgs(self, latest_time, times, clear_msg=False):
        """Display solve results and averages (exact Pico implementation)"""
        image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
        
        # Title
        title = "Solve Results"
        x_title = max(0, (TFT_WIDTH - self.font_manager.small_width * len(title)) // 2)
        self.text_on_image(image, "small", title, x_title, 10, Colors.CYAN)
        
        if clear_msg:
            msg = "History Cleared!"
            x_msg = max(0, (TFT_WIDTH - self.font_manager.small_width * len(msg)) // 2)
            self.text_on_image(image, "small", msg, x_msg, 30, Colors.RED)
            prompt = "Tap GP15 to exit"
            x_prompt = max(0, (TFT_WIDTH - self.font_manager.small_width * len(prompt)) // 2)
            self.text_on_image(image, "small", prompt, x_prompt, TFT_HEIGHT - self.font_manager.small_height - 4, Colors.MAGENTA)
            
            # Version
            version_str = VERSION
            version_width = self.font_manager.small_width * len(version_str)
            x = 255 - (version_width - len("v1.1.0") * self.font_manager.small_width)
            y = 210
            draw = ImageDraw.Draw(image)
            draw.rectangle([x-2, y-2, x+version_width+2, y+self.font_manager.small_height+2], fill=Colors.BLACK)
            self.text_on_image(image, "small", version_str, x, y, Colors.RED)
            
            self.display_image(image)
            print("🗑️  History Cleared!")
            return
        
        # Latest time
        s = "Latest: {:.2f}".format(latest_time)
        self.text_on_image(image, "small", s, 10, 40, Colors.GREEN)
        
        # Last 5 times
        y = 60
        self.text_on_image(image, "small", "Last 5:", 10, y, Colors.YELLOW)
        for i, entry in enumerate(times[-5:][::-1]):
            t = entry["time"]
            self.text_on_image(image, "small", "{:2d}: {:.2f}".format(len(times)-i, t), 70, y, Colors.WHITE)
            y += self.font_manager.small_height + 2
        
        y += 10
        
        # Averages
        ao5 = self.avg_of(times, 5)
        ao12 = self.avg_of(times, 12)
        
        ao5_str = "ao5:  --.--" if ao5 is None else "ao5: {:.2f}".format(ao5)
        ao12_str = "ao12: --.--" if ao12 is None else "ao12: {:.2f}".format(ao12)
        
        self.text_on_image(image, "small", ao5_str, 10, y, Colors.CYAN)
        y += self.font_manager.small_height + 2
        self.text_on_image(image, "small", ao12_str, 10, y, Colors.CYAN)
        
        # Prompt
        prompt = "GP19: Clear | GP15: Exit"
        x_prompt = max(0, (TFT_WIDTH - self.font_manager.small_width * len(prompt)) // 2)
        self.text_on_image(image, "small", prompt, x_prompt, TFT_HEIGHT - self.font_manager.small_height - 4, Colors.MAGENTA)
        
        # Version
        version_str = VERSION
        version_width = self.font_manager.small_width * len(version_str)
        x = 255 - (version_width - len("v1.1.0") * self.font_manager.small_width)
        y = 210
        draw = ImageDraw.Draw(image)
        draw.rectangle([x-2, y-2, x+version_width+2, y+self.font_manager.small_height+2], fill=Colors.BLACK)
        self.text_on_image(image, "small", version_str, x, y, Colors.RED)
        
        self.display_image(image)
        
        print(f"📊 Latest: {latest_time:.2f}s")
        if ao5:
            print(f"📊 ao5: {ao5:.2f}s")
        if ao12:
            print(f"📊 ao12: {ao12:.2f}s")
    
    def display_are_you_sure(self):
        """Display confirmation dialog (exact Pico implementation)"""
        image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
        
        msg = "Are you sure?"
        x_msg = max(0, (TFT_WIDTH - self.font_manager.small_width * len(msg)) // 2)
        self.text_on_image(image, "small", msg, x_msg, 40, Colors.YELLOW)
        
        msg2 = "GP19: Clear | GP15: Cancel"
        x_msg2 = max(0, (TFT_WIDTH - self.font_manager.small_width * len(msg2)) // 2)
        self.text_on_image(image, "small", msg2, x_msg2, 90, Colors.MAGENTA)
        
        # Version
        version_str = VERSION
        version_width = self.font_manager.small_width * len(version_str)
        x = 255 - (version_width - len("v1.1.0") * self.font_manager.small_width)
        y = 210
        draw = ImageDraw.Draw(image)
        draw.rectangle([x-2, y-2, x+version_width+2, y+self.font_manager.small_height+2], fill=Colors.BLACK)
        self.text_on_image(image, "small", version_str, x, y, Colors.RED)
        
        self.display_image(image)
        print("❓ Are you sure you want to clear history?")
    
    # Button handling functions (exact Pico implementations with touch-to-wake)
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
        """Timer control logic (exact Pico implementation)"""
        HOLD_TIME_MS = 400  # Minimum hold time to qualify as "ready"
        
        # Wait for button release first
        while GPIO.input(TIMER_PIN):
            self.update_touch_time()
            self.sleep_ms(10)
        
        while True:
            # Create image for the prep screen
            image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
            
            # Draw title (preserve other content)
            title = "RasPiCube - PicoCube"
            x_title = max(0, (TFT_WIDTH - self.font_manager.big_width * len(title)) // 2)
            self.text_on_image(image, "big", title, x_title, 10, Colors.CYAN)
            
            # Draw "Hold GP15 to prep" every retry
            subtitle = "Hold GP15 to prep"
            x_sub = max(0, (TFT_WIDTH - self.font_manager.big_width * len(subtitle)) // 2)
            # Clear the subtitle area
            draw = ImageDraw.Draw(image)
            draw.rectangle([0, 45, REAL_WIDTH, 45 + self.font_manager.big_height], fill=Colors.BLACK)
            self.text_on_image(image, "big", subtitle, x_sub, 45, Colors.YELLOW)
            self.display_image(image)
            
            # Wait for button press
            while not GPIO.input(TIMER_PIN):
                self.check_backlight_timeout()
                self.sleep_ms(10)
            
            hold_start = self.ticks_ms()
            held_long_enough = False
            prev_state = ""  # Track current instruction
            
            while GPIO.input(TIMER_PIN):
                held_time = self.ticks_diff(self.ticks_ms(), hold_start)
                
                # Create new image for status updates
                image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
                
                # Preserve title
                self.text_on_image(image, "big", title, x_title, 10, Colors.CYAN)
                
                # Show "Keep holding it" if under 400ms, otherwise "Release to start!"
                if not held_long_enough and held_time < HOLD_TIME_MS:
                    if prev_state != "keep":
                        subtitle = "Keep holding it"
                        x_sub = max(0, (TFT_WIDTH - self.font_manager.big_width * len(subtitle)) // 2)
                        draw = ImageDraw.Draw(image)
                        draw.rectangle([0, 45, REAL_WIDTH, 45 + self.font_manager.big_height], fill=Colors.BLACK)
                        self.text_on_image(image, "big", subtitle, x_sub, 45, Colors.YELLOW)
                        self.display_image(image)
                        prev_state = "keep"
                elif not held_long_enough and held_time >= HOLD_TIME_MS:
                    held_long_enough = True
                    subtitle = "Release to start!"
                    x_sub = max(0, (TFT_WIDTH - self.font_manager.big_width * len(subtitle)) // 2)
                    draw = ImageDraw.Draw(image)
                    draw.rectangle([0, 45, REAL_WIDTH, 45 + self.font_manager.big_height], fill=Colors.BLACK)
                    self.text_on_image(image, "big", subtitle, x_sub, 45, Colors.RED)
                    self.display_image(image)
                    prev_state = "release"
                
                self.update_touch_time()
                self.sleep_ms(30)
            
            if held_long_enough:
                break
            else:
                # Button released too soon, loop and redraw "Hold GP15 to prep"
                self.update_touch_time()
                # Loop repeats, "Hold GP15 to prep" will be redrawn
        
        # Wait for button release to start timer
        while GPIO.input(TIMER_PIN):
            self.update_touch_time()
            self.sleep_ms(10)
        
        timer_start = self.ticks_ms()
        self.update_touch_time()
        running = True
        first_update = True
        
        update_interval = 100  # ms, how often to update LCD
        poll_interval = 10     # ms, how often to poll button
        last_update = self.ticks_ms()
        
        while True:
            elapsed = (self.ticks_ms() - timer_start) / 1000
            now = self.ticks_ms()
            if self.ticks_diff(now, last_update) >= update_interval:
                self.display_timer(elapsed, running=True, clear_all=first_update)
                first_update = False
                last_update = now
            self.sleep_ms(poll_interval)
            if GPIO.input(TIMER_PIN):
                break
            if self.any_touch():
                self.update_touch_time()
        
        final_elapsed = (self.ticks_ms() - timer_start) / 1000
        self.display_timer(final_elapsed, running=False, clear_all=True)
        
        while GPIO.input(TIMER_PIN):
            self.update_touch_time()
            self.sleep_ms(10)
        
        # Create completion screen
        image = Image.new('RGB', (TFT_WIDTH, TFT_HEIGHT), Colors.BLACK)
        
        # Show final time
        timer_str = "{:6.2f}".format(final_elapsed)
        x_timer = max(0, (TFT_WIDTH - self.font_manager.big_width * len(timer_str)) // 2)
        y_timer = (TFT_HEIGHT - self.font_manager.big_height) // 2
        self.text_on_image(image, "big", timer_str, x_timer, y_timer, Colors.CYAN)
        
        # Show completion message
        subtitle = "Done! Tap GP19"
        x_sub = max(0, (TFT_WIDTH - self.font_manager.big_width * len(subtitle)) // 2)
        draw = ImageDraw.Draw(image)
        draw.rectangle([0, 45, REAL_WIDTH, 45 + self.font_manager.big_height], fill=Colors.BLACK)
        self.text_on_image(image, "big", subtitle, x_sub, 45, Colors.YELLOW)
        
        # Version
        version_str = VERSION
        version_width = self.font_manager.small_width * len(version_str)
        x = 255 - (version_width - len("v1.1.0") * self.font_manager.small_width)
        y = 210
        draw.rectangle([x-2, y-2, x+version_width+2, y+self.font_manager.small_height+2], fill=Colors.BLACK)
        self.text_on_image(image, "small", version_str, x, y, Colors.RED)
        
        self.display_image(image)
        
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
        """Main loop (exact Pico implementation)"""
        try:
            while True:
                scramble = self.generate_scramble(20)
                self.display_scramble(scramble)
                self.wait_for_next_scramble()  # 30s timeout on scramble screen, touch-to-wake logic
                timer_val = self.timer_control()
                self.solve_times.append({"time": timer_val, "scramble": scramble})
                self.save_times(self.solve_times)
                
                # Wait for tap of GP19 to show results/averages (touch-to-wake)
                self.wait_for_touch_or_action(lambda: GPIO.input(NEXT_PIN))
                while GPIO.input(NEXT_PIN):
                    self.sleep_ms(10)
                
                self.display_results_and_avgs(timer_val, self.solve_times)
                
                # Wait for tap of GP19 (clear) or GP15 (exit), touch-to-wake
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
                        # Wait for tap of GP15 to exit cleared screen
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
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            GPIO.cleanup()
            print("🧹 GPIO cleaned up")

if __name__ == "__main__":
    print("🚀 Starting RasPiCube Timer for Pi Zero 2W...")
    print("🔌 Hardware should be connected as follows:")
    print("   Timer Button:  GPIO 15 (Physical pin 10) -> Button -> GND")
    print("   Next Button:   GPIO 19 (Physical pin 35) -> Button -> GND")
    print("   ST7789 Display:")
    print("     VCC -> 3.3V, GND -> GND")
    print("     SCL -> GPIO 11 (SCLK), SDA -> GPIO 10 (MOSI)")
    print("     RES -> GPIO 25, DC -> GPIO 24, BLK -> GPIO 23, CS -> GPIO 8 (CE0)")
    print("")
    
    timer = PiCubeTimer()
    timer.main()