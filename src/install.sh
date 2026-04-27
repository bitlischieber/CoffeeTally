#!/bin/bash
# Coffee Tally - Installation Script for Linux/Raspberry Pi

echo "========================================"
echo "Coffee Tally - Installation"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    echo "On Raspberry Pi: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

echo "Python found:"
python3 --version
echo ""

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: Could not create virtual environment"
    exit 1
fi
echo "Virtual environment created successfully"
echo ""

# Activate virtual environment and install packages
echo "Installing required packages..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Could not install required packages"
    exit 1
fi
echo ""

# Install system dependencies for Kivy on Linux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ "$ID" = "raspbian" ] || [ "$ID" = "debian" ] || [ "$ID" = "ubuntu" ]; then
        echo "Installing system dependencies for Kivy..."
        sudo apt-get update
        sudo apt-get install -y \
            libsdl2-dev \
            libsdl2-image-dev \
            libsdl2-mixer-dev \
            libsdl2-ttf-dev \
            pkg-config \
            libgl1-mesa-dev \
            libgles2-mesa-dev \
            python3-setuptools \
            libgstreamer1.0-dev \
            git-core \
            gstreamer1.0-plugins-{bad,base,good,ugly} \
            gstreamer1.0-{omx,alsa} \
            python3-dev \
            libmtdev-dev \
            xclip \
            xsel
        echo ""
    fi
fi

# Create config.json from template if it doesn't exist
if [ ! -f config.json ]; then
    echo "Creating config.json from template..."
    cp config.json.template config.json
    echo ""
    echo "IMPORTANT: Please edit config.json and configure:"
    echo "  - Database provider (mysql or cosmos)"
    echo "  - Database connection settings (MySQL or Azure Cosmos DB)"
    echo "  - Card reader port (e.g., /dev/ttyUSB0)"
    echo ""
else
    echo "config.json already exists, skipping template copy"
    echo ""
fi

echo "========================================"
echo "Installation completed successfully!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit config.json with your database provider and port settings"
echo "2. Set up your database (MySQL or Azure Cosmos DB - see README.md)"
echo "3. Run the application with: ./run.sh"
echo ""

# Make run script executable
chmod +x run.sh
