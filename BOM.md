# PiCubeZero - Bill of Materials

---

## Core Components

| Component                | Description                           | Quantity | Link                                                                                                                      | Est. Price      | Purpose                            |
|--------------------------|---------------------------------------|----------|---------------------------------------------------------------------------------------------------------------------------|-----------------|-------------------------------------|
| Raspberry Pi Zero 2 W    | 1GHz quad-core ARM CPU with WiFi      | 1        | [AliExpress](https://www.aliexpress.com/item/1005007982832720.html)                                                       | $14.55 USD      | Main controller for the timer       |
| 2-inch IPS LCD Display   | 240x320 ST7789, Waveshare compatible  | 1        | [Amazon](https://www.amazon.com/LCD-2inch-Module-Compatible-Display/dp/B0DRS9YQCK)                                        | $14.40 USD      | Scramble/time/statistics display    |
| 6-Digit 7-Segment Display| TM1637-compatible LED display module  | 1        | [AliExpress](https://www.aliexpress.com/item/1005001582129952.html)                                                       | $0.99 USD       | Real-time/final time display        |
| TTP223 Touch Sensor      | Capacitive touch sensor               | 2        | [AliExpress](https://www.aliexpress.com/item/1005006153014582.html)                                                       | $0.99 USD       | Start/stop timer input              |
| SanDisk Extreme microSD  | 64GB, Class A2, 190MB/s               | 1        | [Amazon](https://www.amazon.com/SanDisk-Extreme-microSDXC-Memory-Adapter/dp/B09X7C7LL1)                                   | $11.27 USD      | OS and storage                      |
| RGB LED (Common Cathode) | 5mm tri-color diffused                | 1        | [AliExpress](https://www.aliexpress.com/item/1005004963591071.html)                                                       | $3.18 USD (100x)| Status indicator (color coding)     |

---

## Additional Components & Accessories

| Component                | Description                           | Quantity | Link                                                                                                                      | Est. Price      | Purpose                                  |
|--------------------------|---------------------------------------|----------|---------------------------------------------------------------------------------------------------------------------------|-----------------|-------------------------------------------|
| Resistors                | 220Ω for RGB LED (x3)                 | 3        | [AliExpress](https://www.aliexpress.com/item/1005008494728485.html) | $5.58 USD (600x) | Current limiting for RGB LED              |
| Jumper Wires             | Female-to-Female, Male-to-Female      | 1 pack   | [AliExpress](https://www.aliexpress.com/item/1005003641187997.html)                                                                                                                         | $0.99     | Connecting components                     |
| Power Bank             | 5V/2.5A USB power supply              | 1        | [Amazon](https://www.amazon.com/Magnetic-portable-Compatible-MagneticBattery-PowerCore/dp/B0CP2RG37X)                                                                                                                         | $5.00-$10.00    | Powering the Raspberry Pi                 |
| Project Case             | 3D printed or plastic box             | 1        | —                                                                                                                         | $5.00-$15.00    | Housing the electronics                   |

---

## Wiring Reference

| Component                | Raspberry Pi Zero 2 W Connection      |
|--------------------------|---------------------------------------|
| 2-inch LCD Display       | VCC→3.3V, GND→GND, DIN/MOSI→GPIO10, CLK→GPIO11, CS→GPIO8, DC→GPIO25, RST→GPIO27, BL→GPIO24 |
| 6-Digit 7-Segment        | CLK→GPIO5, DIO→GPIO6, VCC→5V, GND→GND |
| RGB LED (Common Cathode) | Common→GND, R→220Ω→GPIO17, G→220Ω→GPIO22, B→220Ω→GPIO4 |
| TTP223 Touch Sensor      | Signal→GPIO23, VCC→3.3V, GND→GND      |

---

## Notes

- Use only 1 RGB LED from the pack of 100.
- Use only 3 resistors from the pack of 600.
- The microSD card is more than sufficient for OS and solve log storage.
- All links and prices were last verified as of 2025-05-19.

---
