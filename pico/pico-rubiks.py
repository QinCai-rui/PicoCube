import machine
import time
import random

# screen library
import st7789py as st7789

# fonts
import vga1_16x32 as font_big
import vga1_8x16 as font_small

# json processor for the log file
import ujson

VERSION = "v1.4.1-4"

TFT_WIDTH = 240
TFT_HEIGHT = 320
spi = machine.SPI(1, baudrate=40000000, polarity=1, phase=0) # haven't yet experimented with higher data rates
tft = st7789.ST7789(
    spi,
    TFT_WIDTH,
    TFT_HEIGHT,
    reset=machine.Pin(12, machine.Pin.OUT),
    dc=machine.Pin(8, machine.Pin.OUT),
    cs=machine.Pin(9, machine.Pin.OUT),
    backlight=machine.Pin(13, machine.Pin.OUT),
    rotation=1
)

timer_pin = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_DOWN)   # Timer control (GP15)
next_pin = machine.Pin(19, machine.Pin.IN, machine.Pin.PULL_DOWN)    # Next scramble / show avgs (GP19)

faces = ['U', 'D', 'L', 'R', 'F', 'B']
modifiers = ['', "'", '2']
opposite = {'U':'D', 'D':'U', 'L':'R', 'R':'L', 'F':'B', 'B':'F'}

RESULTS_FILE = "cube_times.json"

'''
def draw_version():
    version_str = VERSION
    tft.fill_rect(255, 210, 60, 25, st7789.BLACK)
    tft.text(font_small, version_str, 255, 210, st7789.RED)
'''

def draw_version():
    """Draw version in bottom-right corner with proper calculations
    Based on the coordinates (255, 210) that worked previously (the function above)
    
    This is created with help from GitHub Copilot, using the previous function above"""
    version_str = VERSION
    
    # Calculate version string width
    version_width = font_small.WIDTH * len(version_str)
    
    # Calculate position - preserve the right and bottom offsets that worked
    x = 255 - (version_width - len("v1.1.0") * font_small.WIDTH)  # Adjust if version is longer than v1.1.0
    y = 210  # Keep the y position that worked
    
    # Clear background area with a bit of padding
    tft.fill_rect(x-2, y-2, version_width+4, font_small.HEIGHT+4, st7789.BLACK)
    
    # Draw version text
    tft.text(font_small, version_str, x, y, st7789.RED)

def load_times():
    try:
        with open(RESULTS_FILE, "r") as f:
            return ujson.load(f)
    except:
        return []

def save_times(times):
    try:
        with open(RESULTS_FILE, "w") as f:
            ujson.dump(times, f)
    except Exception as e:
        print(e)

def clear_times():
    try:
        with open(RESULTS_FILE, "w") as f:
            ujson.dump([], f)
    except Exception as e:
        print(e)

def generate_scramble(n_moves=20):
    scramble = []
    prev = None
    for _ in range(n_moves):
        while True:
            f = random.choice(faces)
            if f != prev and (prev is None or f != opposite[prev]):
                break
        m = random.choice(modifiers)
        scramble.append(f+m)
        prev = f
    return " ".join(scramble)

def wrap_scramble(scramble, max_line_len=15):
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

def display_scramble(scramble):
    tft.fill(st7789.BLACK)
    title = "RasPiCube - PicoCube"
    x_title = max(0, (TFT_WIDTH - font_big.WIDTH * len(title)) // 2)
    tft.text(font_big, title, x_title, 10, st7789.CYAN)
    subtitle = "Hold GP15 to prep"
    x_sub = max(0, (TFT_WIDTH - font_big.WIDTH * len(subtitle)) // 2)
    tft.text(font_big, subtitle, x_sub, 45, st7789.YELLOW)
    lines = wrap_scramble(scramble)
    block_height = len(lines) * 35
    y = max(70, (TFT_HEIGHT - block_height) // 2)
    for line in lines:
        x_line = max(0, (TFT_WIDTH - font_big.WIDTH * len(line)) // 2)
        tft.text(font_big, line, x_line, y, st7789.WHITE)
        y += 35
    draw_version()

def display_timer(time_val, running=True, clear_all=False):
    if clear_all:
        tft.fill(st7789.BLACK)
    
    timer_str = "{:6.1f}".format(time_val) if running else "{:6.2f}".format(time_val)
    x_timer = max(0, (TFT_WIDTH - font_big.WIDTH * len(timer_str)) // 2)
    y_timer = (TFT_HEIGHT - font_big.HEIGHT) // 2
    
    timer_width = font_big.WIDTH * len(timer_str)
    
    # Only clear the rectangle where the time will be displayed. This should hopefully increase the frame rate and reduce flickering
    tft.fill_rect(x_timer, y_timer, timer_width, font_big.HEIGHT, st7789.BLACK)
    
    tft.text(font_big, timer_str, x_timer, y_timer, st7789.GREEN if running else st7789.CYAN)

def avg_of(times, count):
    """
    Calculate average of count solves, trimming best and worst results for count >= 5
    For a standard Rubik's cube timer, both ao5 and ao12 require trimming.
    
    This function is created with assistance from GitHub Copilot
    """
    if len(times) < count:
        return None
        
    # Get the most recent 'count' times
    recent_times = [entry["time"] for entry in times[-count:]]
    
    # For ao5 and ao12, trim the best and worst times according to WCA standards
    sorted_times = sorted(recent_times)
    trimmed = sorted_times[1:-1]  # Remove best and worst
    return sum(trimmed) / len(trimmed)

def display_results_and_avgs(latest_time, times, clear_msg=False):
    """
    Part of this function is created with assistance from GitHub Copilot
    """
    tft.fill(st7789.BLACK)
    title = "Solve Results"
    x_title = max(0, (TFT_WIDTH - font_small.WIDTH * len(title)) // 2)
    tft.text(font_small, title, x_title, 10, st7789.CYAN)
    if clear_msg:
        msg = "History Cleared!"
        x_msg = max(0, (TFT_WIDTH - font_small.WIDTH * len(msg)) // 2)
        tft.text(font_small, msg, x_msg, 30, st7789.RED)
        prompt = "Tap GP15 to exit"
        x_prompt = max(0, (TFT_WIDTH - font_small.WIDTH * len(prompt)) // 2)
        tft.text(font_small, prompt, x_prompt, TFT_HEIGHT - font_small.HEIGHT - 4, st7789.MAGENTA)
        draw_version()
        return
    s = "Latest: {:.2f}".format(latest_time)
    tft.text(font_small, s, 10, 40, st7789.GREEN)
    y = 60
    tft.text(font_small, "Last 5:", 10, y, st7789.YELLOW)
    for i, entry in enumerate(times[-5:][::-1]):
        t = entry["time"]
        tft.text(font_small, "{:2d}: {:.2f}".format(len(times)-i, t), 70, y, st7789.WHITE)
        y += font_small.HEIGHT + 2
    y += 10
    
    # Fixed average calculations
    ao5 = avg_of(times, 5)
    ao12 = avg_of(times, 12)
    
    ao5_str = "ao5:  --.--" if ao5 is None else "ao5: {:.2f}".format(ao5)
    ao12_str = "ao12: --.--" if ao12 is None else "ao12: {:.2f}".format(ao12)
    tft.text(font_small, ao5_str, 10, y, st7789.CYAN)
    y += font_small.HEIGHT + 2
    tft.text(font_small, ao12_str, 10, y, st7789.CYAN)
    prompt = "GP19: Clear | GP15: Exit"
    x_prompt = max(0, (TFT_WIDTH - font_small.WIDTH * len(prompt)) // 2)
    tft.text(font_small, prompt, x_prompt, TFT_HEIGHT - font_small.HEIGHT - 4, st7789.MAGENTA)
    draw_version()

def display_are_you_sure():
    tft.fill(st7789.BLACK)
    msg = "Are you sure?"
    x_msg = max(0, (TFT_WIDTH - font_small.WIDTH * len(msg)) // 2)
    tft.text(font_small, msg, x_msg, 40, st7789.YELLOW)
    msg2 = "GP19: Clear | GP15: Cancel"
    x_msg2 = max(0, (TFT_WIDTH - font_small.WIDTH * len(msg2)) // 2)
    tft.text(font_small, msg2, x_msg2, 90, st7789.MAGENTA)
    draw_version()

def any_touch():
    return timer_pin.value() or next_pin.value()

BACKLIGHT_TIMEOUT_MS = 20000
BACKLIGHT_SOLVE_EXTRA_MS = 10000
SCRAMBLE_BACKLIGHT_TIMEOUT_MS = 30000  # 30 seconds on scramble screen
last_touch_time = time.ticks_ms()
backlight_on = True

def set_backlight(state):
    """
    Set the backlight state properly
    
    Args:
        state (bool): True to turn backlight on, False to turn it off
    """
    global backlight_on
    tft.backlight.value(1 if state else 0)
    backlight_on = state

def update_touch_time():
    """Update the last touch time (and force backlight on if needed)"""
    global last_touch_time
    last_touch_time = time.ticks_ms()
    if not backlight_on:
        set_backlight(True)

def check_backlight_timeout(timeout_ms=None):
    """
    Check if backlight should be turned off due to timeout.
    timeout_ms: custom timeout in ms (if None, uses BACKLIGHT_TIMEOUT_MS)
    """
    global backlight_on, last_touch_time
    effective_timeout = timeout_ms if timeout_ms is not None else BACKLIGHT_TIMEOUT_MS
    if backlight_on and time.ticks_diff(time.ticks_ms(), last_touch_time) > effective_timeout:
        set_backlight(False)
        return True
    return False

def wait_for_touch_or_action(pin_check_fn, backlight_timeout=None):
    """
    Wait for a pin to be pressed.
    If the backlight is off, the first press wakes it and is ignored.
    Only when backlight is on, a press triggers the action.
    pin_check_fn: lambda returning True if action pin is pressed
    backlight_timeout: custom timeout in ms
    """
    global backlight_on
    while True:
        check_backlight_timeout(backlight_timeout)
        if pin_check_fn():
            update_touch_time()
            if not backlight_on:
                # Wake the screen, but do NOT trigger the action
                while pin_check_fn():
                    time.sleep_ms(10)
                continue
            # Backlight is on, so this is a real action
            while pin_check_fn():
                time.sleep_ms(10)
            return
        time.sleep_ms(10)

def wait_for_next_scramble():
    """
    Wait (with touch-to-wake) for either pin to be pressed (30s timeout on scramble screen).
    """
    wait_for_touch_or_action(
        lambda: next_pin.value() or timer_pin.value(),
        backlight_timeout=SCRAMBLE_BACKLIGHT_TIMEOUT_MS
    )

def wait_for_next():
    """
    Wait (with touch-to-wake) for either pin to be pressed (default timeout).
    """
    wait_for_touch_or_action(
        lambda: next_pin.value() or timer_pin.value()
    )

def wait_for_next_with_results():
    """
    Wait for next_pin or timer_pin. If screen is asleep, first press just wakes. Returns "clear" or "exit".
    """
    while True:
        check_backlight_timeout()
        if next_pin.value():
            update_touch_time()
            if not backlight_on:
                while next_pin.value():
                    time.sleep_ms(10)
                continue
            while next_pin.value():
                time.sleep_ms(10)
            return "clear"
        if timer_pin.value():
            update_touch_time()
            if not backlight_on:
                while timer_pin.value():
                    time.sleep_ms(10)
                continue
            while timer_pin.value():
                time.sleep_ms(10)
            return "exit"
        time.sleep_ms(10)

def wait_for_confirm_clear():
    """
    Wait for confirmation (next_pin for clear, timer_pin for cancel), touch-to-wake.
    Returns "clear" or "cancel".
    """
    while True:
        check_backlight_timeout()
        if next_pin.value():
            update_touch_time()
            if not backlight_on:
                while next_pin.value():
                    time.sleep_ms(10)
                continue
            while next_pin.value():
                time.sleep_ms(10)
            return "clear"
        if timer_pin.value():
            update_touch_time()
            if not backlight_on:
                while timer_pin.value():
                    time.sleep_ms(10)
                continue
            while timer_pin.value():
                time.sleep_ms(10)
            return "cancel"
        time.sleep_ms(10)

def timer_control():
    global last_touch_time
    subtitle = "Hold GP15 to prep"
    x_sub = max(0, (TFT_WIDTH - font_big.WIDTH * len(subtitle)) // 2)
    tft.fill_rect(0, 45, TFT_WIDTH, font_big.HEIGHT, st7789.BLACK)
    tft.text(font_big, subtitle, x_sub, 45, st7789.YELLOW)

    HOLD_TIME_MS = 400  # Minimum hold time to qualify as "ready"

    #print("[DEBUG] Waiting for button release before accepting hold...")
    while timer_pin.value():
        update_touch_time()
        time.sleep_ms(10)
    #print("[DEBUG] Button released. Ready for fresh hold.")

    while True:
        #print("[DEBUG] Waiting for you to press and hold GP15...")
        # Wait for button press
        while not timer_pin.value():
            check_backlight_timeout()
            time.sleep_ms(10)
        #print("[DEBUG] Button pressed. Timing hold...")

        hold_start = time.ticks_ms()
        held_long_enough = False
        release_color = st7789.YELLOW

        # Draw "Release to start!" in yellow initially
        subtitle = "Release to start!"
        x_sub = max(0, (TFT_WIDTH - font_big.WIDTH * len(subtitle)) // 2)
        tft.fill_rect(0, 45, TFT_WIDTH, font_big.HEIGHT, st7789.BLACK)
        tft.text(font_big, subtitle, x_sub, 45, release_color)

        while timer_pin.value():
            held_time = time.ticks_diff(time.ticks_ms(), hold_start)
            #print(f"[DEBUG] Holding button: {held_time} ms", end="\r")
            if not held_long_enough:
                # Draw "Release to start!" in yellow if not pressed long enough
                subtitle = "Release to start!"
                x_sub = max(0, (TFT_WIDTH - font_big.WIDTH * len(subtitle)) // 2)
                tft.fill_rect(0, 45, TFT_WIDTH, font_big.HEIGHT, st7789.BLACK)
                tft.text(font_big, subtitle, x_sub, 45, release_color)
            if not held_long_enough and held_time >= HOLD_TIME_MS:
                held_long_enough = True
                #print(f"\n[DEBUG] Button held long enough: {held_time} ms")
                # Change "Release to start!" to red
                release_color = st7789.RED
                tft.fill_rect(0, 45, TFT_WIDTH, font_big.HEIGHT, st7789.BLACK)
                tft.text(font_big, subtitle, x_sub, 45, release_color)
            update_touch_time()
            time.sleep_ms(50)

        if held_long_enough:
            #print("[DEBUG] Proceeding to 'Release to start!'")
            break
        else:
            #print("[DEBUG] Button released too soon. Restarting hold wait...")
            update_touch_time()

    # Leave "Release to start!" in red until released
    #print("[DEBUG] Waiting for button release to start timer...")
    while timer_pin.value():
        update_touch_time()
        time.sleep_ms(10)
    #print("[DEBUG] Button released. Timer started!")
    timer_start = time.ticks_ms()
    update_touch_time()
    running = True
    first_update = True

    update_interval = 100  # ms, how often to update LCD
    poll_interval = 10     # ms, how often to poll button
    last_update = time.ticks_ms()
    while True:
        elapsed = (time.ticks_ms() - timer_start) / 1000
        now = time.ticks_ms()
        if time.ticks_diff(now, last_update) >= update_interval:
            display_timer(elapsed, running=True, clear_all=first_update)
            first_update = False
            last_update = now
        time.sleep_ms(poll_interval)
        if timer_pin.value():
            #print(f"[DEBUG] Timer stopped at {elapsed:.2f} seconds")
            break
        if any_touch():
            update_touch_time()

    final_elapsed = (time.ticks_ms() - timer_start) / 1000
    display_timer(final_elapsed, running=False, clear_all=True)
    #print(f"[DEBUG] Final elapsed time: {final_elapsed:.2f} seconds")
    while timer_pin.value():
        update_touch_time()
        time.sleep_ms(10)
    subtitle = "Done! Tap GP19"
    x_sub = max(0, (TFT_WIDTH - font_big.WIDTH * len(subtitle)) // 2)
    tft.text(font_big, subtitle, x_sub, 45, st7789.YELLOW)
    draw_version()
    global BACKLIGHT_TIMEOUT_MS
    if final_elapsed >= 20:
        update_touch_time()
        extra_wait = 0
        while extra_wait < BACKLIGHT_SOLVE_EXTRA_MS:
            time.sleep_ms(100)
            extra_wait += 100
            if any_touch():
                update_touch_time()
                break
            check_backlight_timeout()
    return final_elapsed

# --- Main loop ---
# Created with assistance from GitHub Copilot and heavily commented for clarity
solve_times = load_times()
def main():
    global solve_times
    while True:
        scramble = generate_scramble(20)
        display_scramble(scramble)
        wait_for_next_scramble()  # 30s timeout on scramble screen, touch-to-wake logic
        timer_val = timer_control()
        solve_times.append({"time": timer_val, "scramble": scramble})
        save_times(solve_times)
        # Wait for tap of GP19 to show results/averages (touch-to-wake)
        wait_for_touch_or_action(lambda: next_pin.value())
        while next_pin.value():
            time.sleep_ms(10)
        display_results_and_avgs(timer_val, solve_times)
        # Wait for tap of GP19 (clear) or GP15 (exit), touch-to-wake
        action = wait_for_next_with_results()
        if action == "exit":
            continue
        elif action == "clear":
            # Are you sure dialog
            display_are_you_sure()
            confirm_action = wait_for_confirm_clear()
            if confirm_action == "clear":
                solve_times = []
                clear_times()
                display_results_and_avgs(0, solve_times, clear_msg=True)
                # Wait for tap of GP15 to exit cleared screen
                wait_for_touch_or_action(lambda: timer_pin.value())
                while timer_pin.value():
                    time.sleep_ms(10)
                continue
            else:
                # Cancel, redisplay stats
                display_results_and_avgs(timer_val, solve_times)
                action = wait_for_next_with_results()
                if action == "exit":
                    continue
                elif action == "clear":
                    display_are_you_sure()
                    confirm_action = wait_for_confirm_clear()
                    if confirm_action == "clear":
                        solve_times = []
                        clear_times()
                        display_results_and_avgs(0, solve_times, clear_msg=True)
                        wait_for_touch_or_action(lambda: timer_pin.value())
                        while timer_pin.value():
                            time.sleep_ms(10)
                        continue
                    else:
                        display_results_and_avgs(timer_val, solve_times)
                        while True:
                            a = wait_for_next_with_results()
                            if a == "exit":
                                break
                            if a == "clear":
                                display_are_you_sure()
                                c = wait_for_confirm_clear()
                                if c == "clear":
                                    solve_times = []
                                    clear_times()
                                    display_results_and_avgs(0, solve_times, clear_msg=True)
                                    wait_for_touch_or_action(lambda: timer_pin.value())
                                    while timer_pin.value():
                                        time.sleep_ms(10)
                                    break

if __name__ == "__main__":
    main()
