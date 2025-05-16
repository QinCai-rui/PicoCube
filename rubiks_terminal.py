import random
import time

# Custom code (basic_scramble_3x3.py in the same dir)
from basic_scramble_3x3 import generate_scramble

# Function to calculate averages
def calculate_averages(times):
    if len(times) >= 5:
        ao5 = sum(times[-5:]) / 5
    else:
        ao5 = None

    if len(times) >= 12:
        ao12 = sum(times[-12:]) / 12
    else:
        ao12 = None

    return ao5, ao12

def main():
    print("Rubik's Cube Timer and Scramble Generator")
    print("========================================\n")
    solve_times = []

    while True:
        # Generate and display a new scramble
        scramble = generate_scramble(18)
        print(f"Scramble: {scramble}")

        # Wait for the user
        input("Press ENTER to start the timer...")
        print("Timing... Press ENTER again to stop the timer.")

        # Start 
        start_time = time.time()

        # Wait for the user to stop
        input()
        end_time = time.time()

        # Calculate solve time
        solve_time = round(end_time - start_time, 2)
        solve_times.append(solve_time)
        print(f"Solve Time: {solve_time} seconds\n")

        print("Solve History:")
        for _, _time in enumerate(solve_times[-12:]):  # Show the last 12 solves
            print(f"{_+1}: {_time:.2f}s")

        # display averages
        ao5, ao12 = calculate_averages(solve_times)
        if ao5 is not None:
            print(f"\nAverage of 5 (Ao5): {ao5:.2f}s")
        if ao12 is not None:
            print(f"Average of 12 (Ao12): {ao12:.2f}s")

        print("\n========================================\n")

if __name__ == "__main__":
    main()
