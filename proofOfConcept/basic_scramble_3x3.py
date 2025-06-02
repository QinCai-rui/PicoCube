import random

# the (basic) possible moves and modifiers
faces = ['U', 'D', 'L', 'R', 'F', 'B']
modifiers = ['', "'", '2']

def generate_scramble(moves = 18):
    scramble = []
    prev_face = None

    for _ in range(moves):
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
