#!/bin/bash
# RasPiCube Pi Zero 2W Installation Script

set -e

echo "Installing RasPiCube for Raspberry Pi Zero 2W..."

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing Python dependencies..."
sudo apt install -y \
    python3-pip \
    python3-gpiozero \
    python3-rpi.gpio \
    python3-spidev \
    python3-pil \
    python3-numpy \
    python3-setuptools \
    git

# Install Python packages
echo "Installing Python libraries..."
pip3 install --user \
    luma.oled \
    luma.lcd \
    st7789 \
    adafruit-circuitpython-st7789 \
    RPi.GPIO \
    spidev \
    Pillow

# Enable SPI
echo "Enabling SPI interface..."
if ! grep -q "dtparam=spi=on" /boot/config.txt; then
    echo 'dtparam=spi=on' | sudo tee -a /boot/config.txt
fi
