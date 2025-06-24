# RasPiCube

## A Raspberry Pi-powered Rubik's Cube Timer

![Rubik's Cube Timer](https://github.com/user-attachments/assets/c9dac93d-f04c-47e7-b45a-9a12dfbac601)

_NOTE: The image shows (simulated on Wokwi) demo powered by a Raspberry Pi Pico_

## Why I Made This Project

Honestly, I just wanted a cool timer for solving Rubik’s Cubes—something I could build myself, mess with, and show off to friends at school. The ones you can buy are fine, but making my own with a Raspberry Pi felt way more fun (and gave me an excuse to tinker with hardware and code). Now I’ve got a timer that does exactly what I want (although there are a few bugs to fix, and some features yet-to-be-implemented), and I learned a ton making it!! And it's portable, too! :)

## Overview

RasPiCube is a portable, Raspberry Pi Zero 2 W(H)-powered Rubik's Cube timer and scramble generator. This DIY project combines a high-resolution (320x240, pretty high) display, 7-segment timer, touch sensor input, and RGB status indicators to create a timing solution for cubers like myself.

### Features

- **Scramble Generation**: Automatically generates random, valid 3x3 Rubik's Cube scrambles
- **Dual Display System**: 
  - 2-inch IPS LCD Display (240×320) for scramble and statistics
  - 6-digit 7-segment display for precise timing readout (3d.p.)
- **Touch Sensor Input**: Capacitive touch controls for a competition-like solving experience 
- **Visual Status Indicators**: RGB LED provides clear visual feedback of the project's status
- **Statistics**: Calculates and displays session averages (ao5, ao12)
- **Battery Powered**: Portable with a 18650 lithium-ion battery

### Case (just a box for now. will modify it after getting the parts and done some measurements)

![image](https://github.com/user-attachments/assets/7346a186-b638-4fc1-b166-17f52ffb6eb9)

### Circuit diagram (in ASCII; it's bad, I know)

I couldn't find footprints/symbols for most of the parts I am using. Sooo.
[diagram here](https://github.com/QinCai-rui/RasPiCube/blob/main/DIAGRAM/diagram.txt)

### What it will end up looking like

Note: this is a picture taken in Wokwi simulator, with a very early version of this project that (barely) runs on the Raspberry Pi Pico. 
![Rubik's Cube Timer](https://github.com/user-attachments/assets/c9dac93d-f04c-47e7-b45a-9a12dfbac601)

## Hardware Components

For a complete list of components and estimated prices, please see [BOM.md](https://github.com/QinCai-rui/RasPiCube/blob/main/BOM/BOM.md).

## What’s What (What Each File/Folder Is For)

- **.gitignore** — Tells git which files/folders to ignore (so junk/config and cache files don’t get tracked).
- **BOM/** — Bill of Materials! All the parts I need and some prices. See this for shopping. (required by Highway)
- **CAD/** — 3D model files for the timer’s case. Print or edit them if you want to make/modify the enclosure.
  - `RasPiCube_Case.step` — The actual 3D model of the case.
- **DIAGRAM/** — Circuit diagrams and wiring info.
  - `diagram.txt` — Text version of the wiring/circuit diagram. (bc I couldn't find footprints/symbols for most of the parts I am using)
- **JOURNAL.md** — My build log, notes, and what worked/didn’t along the way.
- **LICENSE** — Legal stuff (open source license details).
- **README.md** — You’re reading it rn! All the info about the project.
- **pi02w-rubiks.py** — The main code that runs the timer and scramble generator on the RPi Zero 2 W.
- **proofOfConcept/** — Early test code and experiments before the main build. These can run on any OS with Python 3 installed. No special hardware needed.
  - `basic_scramble_3x3.py` — Simple script to generate 3x3 scrambles (terminal version).
  - `rubiks_terminal.py` — Terminal-based prototype timer/scrambler.

## Circuit Diagram

See [diagram.txt](DIAGRAM/diagram.txt).
