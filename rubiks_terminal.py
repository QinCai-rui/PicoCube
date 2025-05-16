import random
import time
import os
from basic_scramble_3x3 import generate_scramble  # Custom scramble generator (basic_scramble_3x3.py in the same dir)
from colorama import Fore, Style, init  # For coloured text in CLI

# Initialise colorama
init(autoreset=True)

# Calculate averages (Ao5 and Ao12)
def calculate_averages(times):
    ao5 = sum(times[-5:]) / 5 if len(times) >= 5 else None	# last 5 solves
    ao12 = sum(times[-12:]) / 12 if len(times) >= 12 else None	# last 12 solves
    return ao5, ao12

def display_solve_history(solve_times):
    print(Fore.YELLOW + "Solve History:")
    for idx, solve_time in enumerate(solve_times, start=1):  # display all solves
        print(f"{Fore.CYAN}{idx}: {Fore.GREEN}{solve_time:.3f}s")

def main():
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

        # Start the timer
        start_time = time.time()

        # Wait for the user to stop
        input()
        end_time = time.time()

        # Calculate the solve time
        solve_time = round(end_time - start_time, 3)
        solve_times.append(solve_time)
        print(Fore.GREEN + Style.BRIGHT + f"Solve Time: {solve_time} seconds\n")

        # Display solve history
        display_solve_history(solve_times)

        # Calculate and display averages
        ao5, ao12 = calculate_averages(solve_times)
        if ao5 is not None:
            print(Fore.LIGHTMAGENTA_EX + f"\nAverage of 5 (Ao5): {Fore.LIGHTGREEN_EX}{ao5:.3f}s")
        if ao12 is not None:
            print(Fore.LIGHTMAGENTA_EX + f"Average of 12 (Ao12): {Fore.LIGHTGREEN_EX}{ao12:.3f}s")

        # Line separator for better UX ig
        print(Fore.MAGENTA + "\n" + "=" * 40 + "\n")
        
        print(Fore.GREEN + Style.BRIGHT + f"Press ENTER to continue cubing!")

        input()

if __name__ == "__main__":
    main()
