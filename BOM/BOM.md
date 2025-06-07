# PiCubeZero - Bill of Materials

---

## Core Components

| Component | Description | Quantity | Link | Est. Price (inc. shipping) | Purpose |
|--------------------------|---------------------------------------|----------|---------------------------------------------------------------------------------------------------------------------------|-----------------|-------------------------------------|
| Raspberry Pi Zero 2 WH | 1GHz quad-core ARM CPU with WiFi, BT, and header pins| 1 | [AliExpress](https://www.aliexpress.com/item/1005007982832720.html) | $24.93 | Main controller/computer for the timer |
| 802.11ax USB adapter | WiFi 6, mt7921au, dual-band | 1 | [AliExpress](https://www.aliexpress.com/item/1005005935638503.html) | $1.72 | 5GHz WiFi 6 networking; our home network does not have working 2.4GHz..... |
| 2-inch IPS LCD Display | 240x320 ST7789, Waveshare compatible | 1 | [Amazon](https://www.amazon.com/LCD-2inch-Module-Compatible-Display/dp/B0DRS9YQCK) | $14.40 | Scramble/time/statistics display |
| 6-Digit 7-Segment Display| TM1637-compatible LED display module | 1 | [AliExpress](https://www.aliexpress.com/item/1005001582129952.html) | $2.64 | Real-time/final time display |
| TTP223 Touch Sensor | Capacitive touch sensor | 2 | [AliExpress](https://www.aliexpress.com/item/1005006153014582.html) | $1.70 | Start/stop timer input |
| SanDisk Extreme microSD | 64GB, Class A2, 190MB/s | 1 | [Amazon](https://www.amazon.com/SanDisk-Extreme-microSDXC-Memory-Adapter/dp/B09X7C7LL1) | $11.27 | OS and storage |
| RGB LED (Common Cathode) | 5mm tri-color diffused | 1 | [AliExpress](https://www.aliexpress.com/item/1005004963591071.html) | $3.18 (100x)| Status indicator (colour coding) |

---

## Additional Components & Accessories

| Component | Description | Quantity | Link | Est. Price | Purpose |
|--------------------------|---------------------------------------|----------|---------------------------------------------------------------------------------------------------------------------------|-----------------|-------------------------------------------|
| Resistors | 220Ω for RGB LED (x3) | 3 | [AliExpress](https://www.aliexpress.com/item/1005008494728485.html) | $5.58 (600x) | Current limiting for RGB LED |
| Wires | Solid core, white, 24AWG | 10 metres | [AliExpress](https://www.aliexpress.com/item/1005006106330815.html) | $2.10 | Connecting components |
| Large Breadboard | 630 holes | 1 | [AliExpress](https://www.aliexpress.com/item/1005007085965483.html) | $1.54 | Housing the electronics |
| Protoboard | 400 holes | 5 | [AliExpress](https://www.aliexpress.com/item/1005007204514719.html) | $9.31 | To solder the electronics on |
| USB Cable | Data, USB 2.0, 1m | 1 | [AliExpress](https://www.aliexpress.com/item/1005007504624576.html) | $0.99 | For data transfer and Pi first-boot configuration |
| Foam Tape | Double Sided Adhesive Foam Tape - 1.5cm, 5m | 1 | [AliExpress](https://www.aliexpress.com/item/1005006891100106.html?) | $0.99 | Temporary mounting and fixing electronics |
| Li-ion Battery | 18650 3.7V 3500mAh | 1 | [AliExpress](https://www.aliexpress.com/item/1005008078553867.html) | $4.98 | Powering the electronics |
| Battery Charger & Booster | Charging Circuit Board Step Up Boost Power Supply Module; 2xUSB-A output | 1 | [AliExpress](https://www.aliexpress.com/item/1005007457573822.html) | $0.59 | Charging and converting battery to 5V |
| 18650 Holder | Holder with cable | 1 | [AliExpress](https://www.aliexpress.com/item/1005006089547043.html) | $0.99 | Holder for 18650 battery
---

## Wiring Reference

| Component | Raspberry Pi Zero 2 W Connection |
|--------------------------|---------------------------------------|
| 2-inch LCD Display | VCC→3.3V, GND→GND, DIN/MOSI→GPIO10, CLK→GPIO11, CS→GPIO8, DC→GPIO25, RST→GPIO27, BL→GPIO24 |
| 6-Digit 7-Segment | CLK→GPIO5, DIO→GPIO6, VCC→5V, GND→GND |
| RGB LED (Common Cathode) | Common→GND, R→220Ω→GPIO17, G→220Ω→GPIO22, B→220Ω→GPIO4 |
| TTP223 Touch Sensor | Signal→GPIO23, VCC→3.3V, GND→GND |

---

## Notes

- Use only 1 RGB LED from the pack of 100.
- Use only 3 resistors from the pack of 600.
- The microSD card (64GB) is more than sufficient for OS and solve log storage.
- All links and prices were last verified as of 2025-06-02.

---
