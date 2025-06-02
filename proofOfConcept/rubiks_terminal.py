import random
import time
import os
import threading
from basic_scramble_3x3 import generate_scramble  # Custom scramble generator (basic_scramble_3x3.py in the same dir)
from colorama import Fore, Style, init  # For coloured text in CLI

# Initialise colorama
init(autoreset=True)

# Flag to indicate when to stop the timer
stop_timer = False

def wait_for_enter():
    """
    Wait for the user to press ENTER and set the stop_timer flag to True.
    Runs in a separate thread.
    """
    global stop_timer
    input()  # Wait for ENTER
    stop_timer = True

# Calculate averages (Ao5 and Ao12)
def calculate_averages(times):
    ao5 = sum(times[-5:]) / 5 if len(times) >= 5 else None      # last 5 solves
    ao12 = sum(times[-12:]) / 12 if len(times) >= 12 else None  # last 12 solves
    return ao5, ao12

def display_solve_history(solve_times):
    print(Fore.YELLOW + "Solve History:")
    for idx, solve_time in enumerate(solve_times, start=1):  # display all solves
        print(f"{Fore.CYAN}{idx}: {Fore.GREEN}{solve_time:.3f}s")

def main():
    global stop_timer

    print(Fore.MAGENTA + Style.BRIGHT + "Rubik's Cube Timer and Scramble Generator")
    print(Fore.MAGENTA + "=" * 40 + "\n")
    solve_times = []

    while True:
        os.system("clear")

        # Generate and display a new scramble
        scramble = generate_scramble(18)  # Generate 18 random moves
        print(Fore.BLUE + Style.BRIGHT + f"Scramble: {Fore.RESET}{scramble}")

        # Wait for the user to start
        input(Fore.YELLOW + "Press ENTER to start the timer...")
        print(Fore.YELLOW + "Timing... " + Fore.LIGHTYELLOW_EX + "Press ENTER again to stop the timer.")

        # Start the timer and the thread to listen for ENTER
        stop_timer = False
        start_time = time.time()
        threading.Thread(target=wait_for_enter, daemon=True).start()  # Start listening for ENTER

        # Continuously display elapsed time until ENTER is pressed
        while not stop_timer:
            elapsed_time = time.time() - start_time
            print(Fore.CYAN + f"Time: {elapsed_time:.1f}s", end="\r", flush=True)
            time.sleep(0.1)  # Update every 0.1 seconds

        # Calculate the solve time
        end_time = time.time()
        solve_time = round(end_time - start_time, 3)
        solve_times.append(solve_time)

        # Clear the terminal again to display updated stats
        os.system("clear")

        # Display title
        print(Fore.MAGENTA + Style.BRIGHT + "Rubik's Cube Timer and Scramble Generator")
        print(Fore.MAGENTA + "=" * 40 + "\n")

        # Display solve time
        print(Fore.GREEN + Style.BRIGHT + f"Solve Time: {solve_time} seconds\n")

        # Display solve history
        display_solve_history(solve_times)

        # Calculate and display averages
        ao5, ao12 = calculate_averages(solve_times)
        if ao5 is not None:
            print(Fore.LIGHTMAGENTA_EX + f"\nAverage of 5 (Ao5): {Fore.LIGHTGREEN_EX}{ao5:.3f}s")
        if ao12 is not None:
            print(Fore.LIGHTMAGENTA_EX + f"Average of 12 (Ao12): {Fore.LIGHTGREEN_EX}{ao12:.3f}s")

        # Line separator for better UX
        print(Fore.MAGENTA + "\n" + "=" * 40 + "\n")
        
        print(Fore.GREEN + Style.BRIGHT + f"Press ENTER to continue cubing!")

        input()  # Wait for user to proceed

if __name__ == "__main__":
    main()
