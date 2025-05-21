#!/usr/bin/env python3
"""
Rubik's Cube Timer

A bunch of random comments added by GitHub Copilot after I requested feedback

Hardware:
- Raspberry Pi Zero 2 W
- 2-inch IPS LCD Display (ST7789, 240x320)
- 6-Digit 7-Segment Display
- TTP223 Touch Sensor
- Common Cathode RGB LED
"""

import time
import random
import signal
import sys
from gpiozero import Button, RGBLED
import ST7789
from PIL import Image, ImageDraw, ImageFont
from tm1637 import TM1637
import os

# --- Setup signal handler for clean exit
def signal_handler(sig, frame):
    print("\nExiting program...")
    lcd.reset()
    seg.clear()
    led.color = (0, 0, 0)  # Turn off LED
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# --- Hardware initialization
# THIS PART IS MADE ENTIRELY BY GITHUB COPILOT!!
# 2-inch LCD ST7789 240x320 Display (from Waveshare)
# Documentation: https://www.waveshare.com/wiki/2inch_LCD_Module
lcd = ST7789.ST7789(
    port=0,
    cs=8,
    dc=25,
    backlight=24,
    rotation=90,
    spi_speed_hz=80000000
)
lcd.begin()
WIDTH = 320  # Width in rotation 90
HEIGHT = 240  # Height in rotation 90

# Load fonts
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
except IOError:
    font = ImageFont.load_default()
    font_large = ImageFont.load_default()

# Common Cathode RGB LED on GPIOs 17 (R), 22 (G), 4 (B)
# 1 = on, 0 = off
led = RGBLED(red=17, green=22, blue=4)

# 6-Digit 7-segment Display, CLK=GPIO5, DIO=GPIO6
seg = TM1637(clk=5, dio=6)
seg.brightness(1)  # Set initial brightness (0-7)

# TTP223 Touch Sensor, GPIO23
touch = Button(23)

# --- Cube scramble generation ---
faces = ['U', 'D', 'L', 'R', 'F', 'B']
modifiers = ['', "'", '2']

def generate_scramble(moves=18):
    """Generate a random cube scramble sequence"""
    scramble = []
    prev_face = None
    opposite_faces = {'U': 'D', 'D': 'U', 'L': 'R', 'R': 'L', 'F': 'B', 'B': 'F'}
    
    for _ in range(moves):
        while True:
            face = random.choice(faces)
            # Avoid consecutive moves on same face and also avoid opposite faces
            if face != prev_face and (prev_face is None or face != opposite_faces.get(prev_face)):
                break
        modifier = random.choice(modifiers)
        scramble.append(face + modifier)
        prev_face = face
    return " ".join(scramble)

def set_led(r, g, b):
    """Set RGB LED color with specified RGB values (0-255)
    
    For common cathode LED, standard logic applies
    """
    # Convert 0-255 values to 0-1 range
    led.color = (r/255, g/255, b/255)

# --- Display functions ---
def display_lcd(scramble, time_display, status, solves):
    """Display information on LCD screen"""
    # Calculate averages
    ao5, ao12 = calculate_averages(solves)
    
    # Create a new image with mode 'RGB' in the specified size
    image = Image.new('RGB', (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw title with background
    draw.rectangle([(0, 0), (WIDTH, 30)], fill=(0, 64, 128))
    draw.text((10, 5), "Rubik's Cube Timer", fill=(255, 255, 255), font=font_large)
    
    # Draw scramble section with background
    draw.rectangle([(0, 35), (WIDTH, 100)], fill=(20, 20, 40))
    draw.text((10, 40), "Scramble:", fill=(255, 255, 255), font=font)
    
    # Dynamic word wrapping for scramble
    words = scramble.split()
    line1 = line2 = line3 = ""
    max_chars = 26  # Apprx max chars per line
    
    for word in words:
        if len(line1) + len(word) < max_chars:
            line1 += word + " "
        elif len(line2) + len(word) < max_chars:
            line2 += word + " "
        else:
            line3 += word + " "
    
    draw.text((10, 60), line1.strip(), fill=(255, 255, 0), font=font)
    if line2:
        draw.text((10, 75), line2.strip(), fill=(255, 255, 0), font=font)
    if line3:
        draw.text((10, 90), line3.strip(), fill=(255, 255, 0), font=font)
    
    # Draw time with background
    time_color = (0, 255, 0) if status == "Ready" else (0, 128, 255) if status == "Timing" else (255, 0, 0)
    draw.rectangle([(0, 105), (WIDTH, 145)], fill=(30, 30, 30))
    draw.text((10, 110), "Time:", fill=(255, 255, 255), font=font)
    draw.text((80, 110), time_display, fill=time_color, font=font_large)
    
    # Draw status
    draw.text((10, 155), f"Status: {status}", fill=(255, 255, 255), font=font)
    
    # Display averages with colored backgrounds
    draw.rectangle([(0, 180), (WIDTH/2-5, 210)], fill=(40, 0, 40))
    draw.rectangle([(WIDTH/2+5, 180), (WIDTH, 210)], fill=(0, 40, 40))
    
    ao5_display = f"{ao5:.2f}" if ao5 is not None else "--.-"
    ao12_display = f"{ao12:.2f}" if ao12 is not None else "--.-"
    
    draw.text((10, 185), f"ao5: {ao5_display}", fill=(255, 128, 255), font=font)
    draw.text((WIDTH/2+15, 185), f"ao12: {ao12_display}", fill=(128, 255, 255), font=font)
    
    # Draw solves count
    draw.rectangle([(0, 215), (WIDTH, 240)], fill=(50, 50, 0))
    draw.text((10, 220), f"Solves: {len(solves)}", fill=(255, 255, 128), font=font)
    
    # Display the image on the LCD
    lcd.display(image)

def display_7seg(seconds, is_running=True):
    """Display time on 6-digit 7-segment display
    
    THIS PART IS MADE ENTIRELY BY GITHUB COPILOT!!
    
    Parameters:
        seconds (float): Time in seconds to display
        is_running (bool): If True, show 1 decimal place. If False, show 3 decimal places
    """
    try:
        if is_running:
            # When timer is running, show 1 decimal place (XX.X)
            if seconds < 100:
                # Format as XX.X for times under 100 seconds
                s = "{:05.1f}".format(seconds)
                segments = []
                for c in s:
                    if c.isdigit():
                        segments.append(int(c))
                    elif c == '.':
                        # Mark previous digit for decimal point
                        segments[-1] |= 128  # Set the decimal point bit
                segments += [10] * (6 - len(segments))  # Pad with spaces if needed
                seg.write(segments[:6])
            else:
                # For times >= 100 seconds, show whole seconds only
                s = "{:6d}".format(int(seconds))
                seg.write([int(c) if c.isdigit() else 10 for c in s[:6]])
        else:
            # When timer stops, show 3 decimal places (XX.XXX or XXX.XXX)
            if seconds < 1000:
                # Format with 3 decimal places for precision timing
                s = "{:07.3f}".format(seconds)
                
                # If more than 6 digits are needed, we need to truncate
                if len(s.replace('.', '')) > 6:
                    # For longer times, sacrifice a decimal place
                    s = "{:06.2f}".format(seconds)
                
                segments = []
                for c in s:
                    if c.isdigit():
                        segments.append(int(c))
                    elif c == '.':
                        # Mark previous digit for decimal point
                        segments[-1] |= 128  # Set the decimal point bit
                
                # Ensure we don't exceed 6 digits
                seg.write(segments[:6])
            else:
                # For very large times, show whole seconds only
                s = "{:6d}".format(int(seconds))
                seg.write([int(c) if c.isdigit() else 10 for c in s[:6]])
    except Exception as e:
        print(f"7-segment display error: {e}")

def calculate_averages(times):
    """Calculate average of 5 and average of 12 solve times"""
    ao5 = sum(times[-5:]) / 5 if len(times) >= 5 else None
    ao12 = sum(times[-12:]) / 12 if len(times) >= 12 else None
    return ao5, ao12

# --- File operations ---
SOLVE_FILE = "solve_times.txt"

def load_solve_times():
    """Load solve times from file"""
    times = []
    if not os.path.exists(SOLVE_FILE):
        return times
    
    try:
        with open(SOLVE_FILE, "r") as f:
            lines = f.readlines()
        
        for line in lines:
            try:
                times.append(float(line.strip()))
            except ValueError:
                # Skip invalid lines
                continue
    except Exception as e:
        print(f"Error loading solve times: {e}")
    
    return times

def append_solve_time(solve_time):
    """Append solve time to file"""
    try:
        with open(SOLVE_FILE, "a") as f:
            f.write(f"{solve_time:.3f}\n")  # Save with 3 decimal places
    except Exception as e:
        print(f"Error saving solve time: {e}")

# --- Touch sensor functions with debounce ---
def wait_for_press(debounce_time=0.05):
    """Wait for button press with debouncing"""
    while True:
        if touch.is_pressed:
            # Wait for debounce period
            time.sleep(debounce_time)
            # Check if still pressed after debounce
            if touch.is_pressed:
                return True
        time.sleep(0.01)

def wait_for_release(debounce_time=0.05):
    """Wait for button release with debouncing"""
    while True:
        if not touch.is_pressed:
            # Wait for debounce period
            time.sleep(debounce_time)
            # Check if still released after debounce
            if not touch.is_pressed:
                return True
        time.sleep(0.01)

# --- Main program ---
def main():
    solve_times = load_solve_times()
    status = "Ready"
    scramble = generate_scramble(18)
    set_led(0, 80, 0)  # Green for ready
    
    print("Rubik's Cube Timer Started")
    print("Press Ctrl+C to exit")

    try:
        while True:
            # Show ready state
            time_display = "0.00"  # Consistent format with 2 decimal places
            display_lcd(scramble, time_display, status, solve_times)
            display_7seg(0.00, is_running=False)  # Start with 3 decimal places
            set_led(0, 80, 0)  # Green
            print("Touch and HOLD to start...")
            
            # Wait for user to touch and hold with debouncing
            wait_for_press()
            
            # Flash LED while holding
            status = "Hold"
            display_lcd(scramble, time_display, status, solve_times)
            hold_start = time.time()
            
            # Wait for release or timeout (2 seconds to prepare)
            holding = True
            led_state = True
            
            while holding and touch.is_pressed:
                # Flash LED
                if led_state:
                    set_led(255, 255, 255)  # White on
                else:
                    set_led(0, 0, 0)        # Off
                led_state = not led_state
                
                # Check if held long enough (0.5 sec minimum)
                if time.time() - hold_start >= 0.5:
                    holding = False
                
                time.sleep(0.15)
            
            # Wait for full release with debouncing
            wait_for_release()
            
            # On release, start timer
            status = "Timing"
            set_led(0, 0, 255)  # Blue for timing
            start_time = time.time()
            last_update = start_time
            
            # Show real-time timer with improved update frequency
            while True:
                elapsed = time.time() - start_time
                
                # Update display less frequently to reduce flicker
                if time.time() - last_update >= 0.1:  # Update every 100ms
                    time_display = "{:.2f}".format(elapsed)  # Consistent 2 decimal places for LCD
                    display_lcd(scramble, time_display, status, solve_times)
                    display_7seg(elapsed, is_running=True)  # 1 decimal place while running
                    last_update = time.time()
                
                # Check for button press with minimal delay
                if touch.is_pressed:
                    # Debounce the press
                    time.sleep(0.05)
                    if touch.is_pressed:
                        break
                        
                time.sleep(0.01)  # Shorter sleep for more responsive button checking
            
            # On next touch, stop timer
            end_time = time.time()
            solve_time = round(end_time - start_time, 3)  # Round to 3 decimal places
            solve_times.append(solve_time)
            append_solve_time(solve_time)
            set_led(255, 0, 0)  # Red for finished
            
            # Calculate and display final stats
            time_display = "{:.2f}".format(solve_time)  # Keep 2 decimal places for LCD
            
            # Display result for ~4 seconds
            status = "Solved"
            for _ in range(40):
                display_lcd(scramble, time_display, status, solve_times)
                display_7seg(solve_time, is_running=False)  # 3 decimal places when stopped
                time.sleep(0.1)
            
            # Prepare for next solve
            scramble = generate_scramble(18)
            status = "Ready"
            set_led(0, 80, 0)
            
    except KeyboardInterrupt:
        print("\nExiting program...")
        lcd.reset()
        seg.clear()
        led.color = (0, 0, 0)
        sys.exit(0)

if __name__ == "__main__":
    main()
