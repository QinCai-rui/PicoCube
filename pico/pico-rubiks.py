import machine
import time
import random

# screen library
import st7789py as st7789

# fonts
import vga1_16x32 as font_big
import vga1_8x16 as font_small

# json processor
import ujson

TFT_WIDTH = 240
TFT_HEIGHT = 320
spi = machine.SPI(1, baudrate=40000000, polarity=1, phase=0) # haven;t yet experimented with higher data rates
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
        pass

def clear_times():
    try:
        with open(RESULTS_FILE, "w") as f:
            ujson.dump([], f)
    except Exception as e:
        pass

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

def display_timer(time_val, running=True, clear_all=False):
    if clear_all:
        tft.fill(st7789.BLACK)
    
    timer_str = "{:6.1f}".format(time_val) if running else "{:6.3f}".format(time_val)
    x_timer = max(0, (TFT_WIDTH - font_big.WIDTH * len(timer_str)) // 2)
    y_timer = (TFT_HEIGHT - font_big.HEIGHT) // 2
    
    timer_width = font_big.WIDTH * len(timer_str)
    
    # Only clear the rectangle where the time will be displayed
    tft.fill_rect(x_timer, y_timer, timer_width, font_big.HEIGHT, st7789.BLACK)
    
    tft.text(font_big, timer_str, x_timer, y_timer, st7789.GREEN if running else st7789.CYAN)

def avg_of(times, count):
    """
    Calculate average of count solves, trimming best and worst for count >= 5
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
        return
    s = "Latest: {:.3f}".format(latest_time)
    tft.text(font_small, s, 10, 40, st7789.GREEN)
    y = 60
    tft.text(font_small, "Last 5:", 10, y, st7789.YELLOW)
    for i, entry in enumerate(times[-5:][::-1]):
        t = entry["time"]
        tft.text(font_small, "{:2d}: {:.3f}".format(len(times)-i, t), 70, y, st7789.WHITE)
        y += font_small.HEIGHT + 2
    y += 10
    
    # Fixed average calculations
    ao5 = avg_of(times, 5)
    ao12 = avg_of(times, 12)
    
    ao5_str = "ao5:  --.--" if ao5 is None else "ao5: {:.3f}".format(ao5)
    ao12_str = "ao12: --.--" if ao12 is None else "ao12: {:.3f}".format(ao12)
    tft.text(font_small, ao5_str, 10, y, st7789.CYAN)
    y += font_small.HEIGHT + 2
    tft.text(font_small, ao12_str, 10, y, st7789.CYAN)
    prompt = "GP19: Clear | GP15: Exit"
    x_prompt = max(0, (TFT_WIDTH - font_small.WIDTH * len(prompt)) // 2)
    tft.text(font_small, prompt, x_prompt, TFT_HEIGHT - font_small.HEIGHT - 4, st7789.MAGENTA)

def display_are_you_sure():
    tft.fill(st7789.BLACK)
    msg = "Are you sure?"
    x_msg = max(0, (TFT_WIDTH - font_small.WIDTH * len(msg)) // 2)
    tft.text(font_small, msg, x_msg, 40, st7789.YELLOW)
    msg2 = "GP19: Clear | GP15: Cancel"
    x_msg2 = max(0, (TFT_WIDTH - font_small.WIDTH * len(msg2)) // 2)
    tft.text(font_small, msg2, x_msg2, 90, st7789.MAGENTA)

def wait_for_next_with_results():
    while True:
        if next_pin.value():
            while next_pin.value():
                time.sleep_ms(10)
            return "clear"
        if timer_pin.value():
            while timer_pin.value():
                time.sleep_ms(10)
            return "exit"
        time.sleep_ms(10)

def wait_for_confirm_clear():
    # Wait for GP19 (confirm clear) or GP15 (cancel)
    while True:
        if next_pin.value():
            while next_pin.value():
                time.sleep_ms(10)
            return "clear"
        if timer_pin.value():
            while timer_pin.value():
                time.sleep_ms(10)
            return "cancel"
        time.sleep_ms(10)

BACKLIGHT_TIMEOUT_MS = 20000
BACKLIGHT_SOLVE_EXTRA_MS = 10000
last_touch_time = time.ticks_ms()
backlight_on = True

def set_backlight(state):
    global backlight_on
    tft.backlight.value(1 if state else 0)
    backlight_on = state

def any_touch():
    return timer_pin.value() or next_pin.value()

def wait_for_release(pin):
    while pin.value():
        time.sleep_ms(10)

def wait_for_press(pin):
    while not pin.value():
        time.sleep_ms(10)

def wait_for_next():
    global last_touch_time, backlight_on
    while True:
        if next_pin.value() or timer_pin.value():
            time.sleep_ms(50)
            if next_pin.value() or timer_pin.value():
                if next_pin.value():
                    while next_pin.value():
                        time.sleep_ms(10)
                else:
                    while timer_pin.value():
                        time.sleep_ms(10)
                last_touch_time = time.ticks_ms()
                if not backlight_on:
                    set_backlight(True)
                    time.sleep_ms(200)
                    continue
                return
        if backlight_on and time.ticks_diff(time.ticks_ms(), last_touch_time) > BACKLIGHT_TIMEOUT_MS:
            set_backlight(False)
        time.sleep_ms(10)

def timer_control():
    # need to add more comments here later
    global last_touch_time
    subtitle = "Hold GP15 to prep"
    x_sub = max(0, (TFT_WIDTH - font_big.WIDTH * len(subtitle)) // 2)
    tft.fill_rect(0, 45, TFT_WIDTH, font_big.HEIGHT, st7789.BLACK)
    tft.text(font_big, subtitle, x_sub, 45, st7789.YELLOW)
    while not timer_pin.value():
        if not backlight_on and any_touch():
            set_backlight(True)
            last_touch_time = time.ticks_ms()
        time.sleep_ms(10)
    last_touch_time = time.ticks_ms()
    subtitle = "Release to start!"
    x_sub = max(0, (TFT_WIDTH - font_big.WIDTH * len(subtitle)) // 2)
    tft.fill_rect(0, 45, TFT_WIDTH, font_big.HEIGHT, st7789.BLACK)
    tft.text(font_big, subtitle, x_sub, 45, st7789.YELLOW)
    while timer_pin.value():
        if not backlight_on and any_touch():
            set_backlight(True)
            last_touch_time = time.ticks_ms()
        time.sleep_ms(10)
    timer_start = time.ticks_ms()
    last_touch_time = time.ticks_ms()
    running = True
    first_update = True
    while True:
        elapsed = (time.ticks_ms() - timer_start) / 1000
        display_timer(elapsed, running=True, clear_all=first_update)
        first_update = False
        time.sleep_ms(100)
        if timer_pin.value():
            break
        if any_touch():
            last_touch_time = time.ticks_ms()
    final_elapsed = (time.ticks_ms() - timer_start) / 1000
    display_timer(final_elapsed, running=False, clear_all=True)
    while timer_pin.value():
        time.sleep_ms(10)
    subtitle = "Done! Tap GP19"
    x_sub = max(0, (TFT_WIDTH - font_big.WIDTH * len(subtitle)) // 2)
    tft.text(font_big, subtitle, x_sub, 45, st7789.YELLOW)
    global BACKLIGHT_TIMEOUT_MS
    if final_elapsed >= 20:
        last_touch_time = time.ticks_ms()
        extra_wait = 0
        while extra_wait < BACKLIGHT_SOLVE_EXTRA_MS:
            time.sleep_ms(100)
            extra_wait += 100
            if any_touch():
                last_touch_time = time.ticks_ms()
                break
    return final_elapsed

# --- Main loop ---
solve_times = load_times()
while True:
    scramble = generate_scramble(20)
    display_scramble(scramble)
    timer_val = timer_control()
    solve_times.append({"time": timer_val, "scramble": scramble})
    save_times(solve_times)
    # Wait for tap of GP19 to show results/averages
    while not next_pin.value():
        time.sleep_ms(10)
    while next_pin.value():
        time.sleep_ms(10)
    display_results_and_avgs(timer_val, solve_times)
    # Wait for tap of GP19 (clear) or GP15 (exit)
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
            while not timer_pin.value():
                time.sleep_ms(10)
            while timer_pin.value():
                time.sleep_ms(10)
            continue
        else:
            # Cancel, redisplay stats
            display_results_and_avgs(timer_val, solve_times)
            # Wait again for user input
            action = wait_for_next_with_results()
            if action == "exit":
                continue
            # If user hits clear again, repeat confirmation
            elif action == "clear":
                display_are_you_sure()
                confirm_action = wait_for_confirm_clear()
                if confirm_action == "clear":
                    solve_times = []
                    clear_times()
                    display_results_and_avgs(0, solve_times, clear_msg=True)
                    while not timer_pin.value():
                        time.sleep_ms(10)
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
                                while not timer_pin.value():
                                    time.sleep_ms(10)
                                while timer_pin.value():
                                    time.sleep_ms(10)
                                break