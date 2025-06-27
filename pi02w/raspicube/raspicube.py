#!/usr/bin/env python3
"""
Optimized RasPiCube with frame buffer and selective updates
"""

import time
import random
import json
import os
from datetime import datetime
import sys

# GPIO libraries for Pi
import RPi.GPIO as GPIO

# Display libraries - optimized approach
from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from PIL import Image, ImageDraw, ImageFont

VERSION = "v1.6.2-rpi"

# GPIO Pin definitions (BCM numbering)
TIMER_PIN = 26
NEXT_PIN = 19

# Display dimensions
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

# Rubik's cube settings
faces = ['U', 'D', 'L', 'R', 'F', 'B']
modifiers = ['', "'", '2']
opposite = {'U':'D', 'D':'U', 'L':'R', 'R':'L', 'F':'B', 'B':'F'}

RESULTS_FILE = "cube_times.json"

# Backlight management
BACKLIGHT_TIMEOUT_MS = 20000
BACKLIGHT_SOLVE_EXTRA_MS = 10000
SCRAMBLE_BACKLIGHT_TIMEOUT_MS = 30000

class OptimizedPiCubeTimer:
    def __init__(self):
        # Initialize components
        self.setup_gpio()
        self.setup_display()
        self.setup_fonts()
        
        # Frame buffer for optimization
        self.frame_buffer = Image.new('RGB', (DISPLAY_WIDTH, DISPLAY_HEIGHT), Colors.BLACK)
        self.buffer_draw = ImageDraw.Draw(self.frame_buffer)
        self.last_timer_value = None
        
        # State management
        self.solve_times = self.load_times()
        self.last_touch_time = self.ticks_ms()
        self.backlight_on = True
        
        print("🚀 Optimized RasPiCube Timer initialized!")
    
    def setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TIMER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(NEXT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        print("✅ GPIO initialized")
    
    def setup_display(self):
        """Initialize the ST7789 display"""
        try:
            # Initialize SPI interface with higher speed
            self.serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25, spi_speed_hz=64000000)
            self.device = st7789(self.serial, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, rotate=0)
            print("✅ ST7789 display initialized with optimized SPI speed")
        except Exception as e:
            print(f"❌ Failed to initialize display: {e}")
            self.device = None
    
    def setup_fonts(self):
        """Initialize fonts"""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        
        self.big_font = None
        self.small_font = None
        
        for path in font_paths:
            try:
                self.big_font = ImageFont.truetype(path, 28)
                self.small_font = ImageFont.truetype(path, 14)
                break
            except:
                continue
        
        if not self.big_font:
            self.big_font = ImageFont.load_default()
            self.small_font = ImageFont.load_default()
    
    def ticks_ms(self):
        return int(time.time() * 1000)
    
    def ticks_diff(self, new_ticks, old_ticks):
        return new_ticks - old_ticks
    
    def sleep_ms(self, ms):
        time.sleep(ms / 1000.0)
    
    def update_display(self, force=False):
        """Update the physical display from frame buffer"""
        if self.device and (force or self.frame_buffer):
            try:
                self.device.display(self.frame_buffer)
            except Exception as e:
                print(f"Display error: {e}")
    
    def clear_buffer(self, color=Colors.BLACK):
        """Clear the frame buffer"""
        self.buffer_draw.rectangle([(0, 0), (DISPLAY_WIDTH, DISPLAY_HEIGHT)], fill=color)
    
    def draw_text_buffer(self, text, x, y, font, color):
        """Draw text to frame buffer"""
        self.buffer_draw.text((x, y), text, font=font, fill=color)
    
    def get_text_size(self, text, font):
        """Get text size"""
        bbox = self.buffer_draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    def center_text_x(self, text, font):
        """Get x coordinate to center text"""
        width, _ = self.get_text_size(text, font)
        return max(0, (DISPLAY_WIDTH - width) // 2)
    
    # Optimized timer display with minimal redraws
    def display_timer_optimized(self, time_val, running=True):
        """Optimized timer display - only update the timer area"""
        timer_str = "{:6.1f}".format(time_val) if running else "{:6.2f}".format(time_val)
        
        # Only redraw if the timer value changed significantly
        if self.last_timer_value is None or abs(time_val - self.last_timer_value) >= 0.1:
            # Clear only the timer area
            timer_width, timer_height = self.get_text_size(timer_str, self.big_font)
            x_timer = self.center_text_x(timer_str, self.big_font)
            y_timer = (DISPLAY_HEIGHT - timer_height) // 2
            
            # Clear the timer area with some padding
            padding = 10
            self.buffer_draw.rectangle([
                x_timer - padding, y_timer - padding,
                x_timer + timer_width + padding, y_timer + timer_height + padding
            ], fill=Colors.BLACK)
            
            # Draw new timer value
            color = Colors.GREEN if running else Colors.CYAN
            self.draw_text_buffer(timer_str, x_timer, y_timer, self.big_font, color)
            
            # Update display
            self.update_display()
            self.last_timer_value = time_val
    
    def display_full_screen(self, draw_func):
        """Display a full screen with the given draw function"""
        self.clear_buffer()
        draw_func()
        self.update_display(force=True)
        self.last_timer_value = None  # Reset timer cache
    
    def display_scramble(self, scramble):
        """Display scramble screen"""
        def draw_scramble():
            # Title
            title = "RasPiCubeZero"
            x_title = self.center_text_x(title, self.big_font)
            self.draw_text_buffer(title, x_title, 10, self.big_font, Colors.CYAN)
            
            # Subtitle
            subtitle = "Hold GP15 to prep"
            x_sub = self.center_text_x(subtitle, self.big_font)
            self.draw_text_buffer(subtitle, x_sub, 50, self.big_font, Colors.YELLOW)
            
            # Scramble text
            lines = self.wrap_scramble(scramble)
            y = 90
            for line in lines:
                x_line = self.center_text_x(line, self.big_font)
                self.draw_text_buffer(line, x_line, y, self.big_font, Colors.WHITE)
                y += 35
            
            # Version
            version_width, _ = self.get_text_size(VERSION, self.small_font)
            x_version = DISPLAY_WIDTH - version_width - 10
            y_version = DISPLAY_HEIGHT - 25
            self.draw_text_buffer(VERSION, x_version, y_version, self.small_font, Colors.RED)
        
        self.display_full_screen(draw_scramble)
        print(f"🎲 Scramble: {scramble}")
    
    def display_timer_prep(self, message, color):
        """Display timer preparation screen"""
        def draw_prep():
            # Title
            title = "RasPiCubeZero"
            x_title = self.center_text_x(title, self.big_font)
            self.draw_text_buffer(title, x_title, 10, self.big_font, Colors.CYAN)
            
            # Message
            x_msg = self.center_text_x(message, self.big_font)
            self.draw_text_buffer(message, x_msg, 80, self.big_font, color)
        
        self.display_full_screen(draw_prep)
    
    def start_timer_display(self):
        """Initialize timer display screen"""
        self.clear_buffer()
        self.update_display(force=True)
        self.last_timer_value = None
    
    # Core timer functions (same as before)
    def load_times(self):
        try:
            with open(RESULTS_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    
    def save_times(self, times):
        try:
            with open(RESULTS_FILE, "w") as f:
                json.dump(times, f, indent=2)
        except Exception as e:
            print(f"Error saving times: {e}")
    
    def clear_times(self):
        try:
            with open(RESULTS_FILE, "w") as f:
                json.dump([], f)
        except Exception as e:
            print(e)
    
    def generate_scramble(self, n_moves=20):
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
        if len(times) < count:
            return None
        recent_times = [entry["time"] for entry in times[-count:]]
        sorted_times = sorted(recent_times)
        trimmed = sorted_times[1:-1]
        return sum(trimmed) / len(trimmed)
    
    # Backlight and touch management
    def set_backlight(self, state):
        self.backlight_on = state
    
    def update_touch_time(self):
        self.last_touch_time = self.ticks_ms()
        if not self.backlight_on:
            self.set_backlight(True)
    
    def check_backlight_timeout(self, timeout_ms=None):
        effective_timeout = timeout_ms if timeout_ms is not None else BACKLIGHT_TIMEOUT_MS
        if self.backlight_on and self.ticks_diff(self.ticks_ms(), self.last_touch_time) > effective_timeout:
            self.set_backlight(False)
            return True
        return False
    
    def any_touch(self):
        return GPIO.input(TIMER_PIN) or GPIO.input(NEXT_PIN)
    
    # Button handling (simplified for performance)
    def wait_for_button(self, pin_check_fn, timeout_ms=None):
        while True:
            self.check_backlight_timeout(timeout_ms)
            if pin_check_fn():
                self.update_touch_time()
                if not self.backlight_on:
                    while pin_check_fn():
                        self.sleep_ms(10)
                    continue
                while pin_check_fn():
                    self.sleep_ms(10)
                return
            self.sleep_ms(10)
    
    def timer_control(self):
        """Optimized timer control"""
        HOLD_TIME_MS = 400
        
        # Wait for button release
        while GPIO.input(TIMER_PIN):
            self.update_touch_time()
            self.sleep_ms(10)
        
        while True:
            self.display_timer_prep("Hold GP15 to prep", Colors.YELLOW)
            
            # Wait for button press
            while not GPIO.input(TIMER_PIN):
                self.check_backlight_timeout()
                self.sleep_ms(10)
            
            hold_start = self.ticks_ms()
            held_long_enough = False
            
            while GPIO.input(TIMER_PIN):
                held_time = self.ticks_diff(self.ticks_ms(), hold_start)
                
                if not held_long_enough and held_time < HOLD_TIME_MS:
                    self.display_timer_prep("Keep holding it", Colors.YELLOW)
                elif not held_long_enough and held_time >= HOLD_TIME_MS:
                    held_long_enough = True
                    self.display_timer_prep("Release to start!", Colors.RED)
                
                self.update_touch_time()
                self.sleep_ms(50)  # Slightly longer delay for prep screen
            
            if held_long_enough:
                break
            else:
                self.update_touch_time()
        
        # Wait for button release
        while GPIO.input(TIMER_PIN):
            self.update_touch_time()
            self.sleep_ms(10)
        
        # Start timer with optimized display
        timer_start = self.ticks_ms()
        self.update_touch_time()
        self.start_timer_display()
        
        # Optimized timer loop
        update_interval = 50   # 50ms updates for smooth display
        poll_interval = 5      # 5ms button polling
        last_update = self.ticks_ms()
        
        while True:
            elapsed = (self.ticks_ms() - timer_start) / 1000
            now = self.ticks_ms()
            
            # Update display at regular intervals
            if self.ticks_diff(now, last_update) >= update_interval:
                self.display_timer_optimized(elapsed, running=True)
                last_update = now
            
            # Check for button press
            if GPIO.input(TIMER_PIN):
                break
            
            if self.any_touch():
                self.update_touch_time()
            
            self.sleep_ms(poll_interval)
        
        final_elapsed = (self.ticks_ms() - timer_start) / 1000
        self.display_timer_optimized(final_elapsed, running=False)
        
        while GPIO.input(TIMER_PIN):
            self.update_touch_time()
            self.sleep_ms(10)
        
        return final_elapsed
    
    def main(self):
        """Main loop"""
        try:
            while True:
                scramble = self.generate_scramble(20)
                self.display_scramble(scramble)
                
                # Wait for button press
                self.wait_for_button(
                    lambda: GPIO.input(NEXT_PIN) or GPIO.input(TIMER_PIN),
                    timeout_ms=SCRAMBLE_BACKLIGHT_TIMEOUT_MS
                )
                
                timer_val = self.timer_control()
                self.solve_times.append({"time": timer_val, "scramble": scramble})
                self.save_times(self.solve_times)
                
                print(f"⏱️ Solved in {timer_val:.2f}s")
                
                # Simple completion message
                self.display_timer_prep("Done! Tap any button", Colors.GREEN)
                
                # Wait for any button to continue
                self.wait_for_button(lambda: GPIO.input(NEXT_PIN) or GPIO.input(TIMER_PIN))
                
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
    print("🚀 Starting Optimized RasPiCube Timer...")
    print("🔧 Optimizations:")
    print("   - Frame buffer for selective updates")
    print("   - Higher SPI speed (64MHz)")
    print("   - Minimal timer redraws")
    print("   - Reduced update intervals")
    print("")
    
    timer = OptimizedPiCubeTimer()
    timer.main()