import random

# the (basic) possible moves and modifiers
faces = ['U', 'D', 'L', 'R', 'F', 'B']
modifiers = ['', "'", '2']

def generate_scramble():
    scramble = []
    prev_face = None

    for _ in range(18):  # Generate a 18-move scramble (apparently 18 is good)
        while True:
            face = random.choice(faces)
            if face != prev_face:  # Avoid consecutive moves on the same face
                break
        modifier = random.choice(modifiers)
        scramble.append(face + modifier)
        prev_face = face

    return " ".join(scramble)

if __name__ == "__main__":
    print("Generated Scramble:", generate_scramble())
