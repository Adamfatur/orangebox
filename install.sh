#!/bin/bash
# OrangeBox Installer - Automatic Setup Script

set -e  # Exit on any error

echo "🍊 OrangeBox Installer"
echo "======================"
echo ""

# Auto-detect platform
PLATFORM=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="mac"
    echo "🖥️  Platform detected: macOS"
elif [[ "$OSTYPE" == "linux"* ]]; then
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        PLATFORM="rpi"
        echo "🥧 Platform detected: Raspberry Pi"
    else
        PLATFORM="linux"
        echo "🐧 Platform detected: Linux"
    fi
else
    echo "❌ Unsupported platform: $OSTYPE"
    exit 1
fi

echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Please install Python 3 first:"
    if [[ "$PLATFORM" == "mac" ]]; then
        echo "  brew install python3"
        echo "  or download from: https://www.python.org/downloads/"
    elif [[ "$PLATFORM" == "rpi" ]]; then
        echo "  sudo apt update && sudo apt install python3 python3-pip"
    fi
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Install dependencies based on platform
echo "📦 Installing dependencies for $PLATFORM..."

if [[ "$PLATFORM" == "rpi" ]]; then
    # Raspberry Pi - install system packages first
    echo "Installing system packages..."
    sudo apt update --allow-releaseinfo-change -qq
    # Note: libatlas-base-dev is not available on Raspberry Pi OS Bookworm/ARM64
    # Use OpenBLAS + LAPACK instead for NumPy/linear algebra support
    sudo apt install -y python3-pip python3-opencv libopenblas-dev liblapack-dev
    
    # Create and use virtual environment to avoid PEP 668 (externally-managed)
    echo "Setting up Python virtual environment (.venv)..."
    # Ensure python3-venv is installed
    sudo apt-get install -y python3-venv
    # Create venv in project root
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    # Upgrade pip inside venv
    .venv/bin/pip install --upgrade pip
    
    echo "Installing system packages for Raspberry Pi..."
    sudo apt-get update --allow-releaseinfo-change
    # OpenCV via apt (faster, has native bindings)
    sudo apt-get install -y python3-opencv
    # Libcamera + Picamera2 support (Bookworm)
    sudo apt-get install -y python3-picamera2 libcamera-apps
    # Camera tooling
    sudo apt-get install -y v4l-utils
    # GPS support (gpsd) clients
    sudo apt-get install -y gpsd gpsd-clients
    # I2C and SMBus tools for PCA9685/Adafruit Blinka
    sudo apt-get install -y i2c-tools python3-smbus

    echo "Installing Python packages for Raspberry Pi (in venv)..."
    # Core Python libs in venv
    .venv/bin/pip install numpy RPi.GPIO gpiozero pymysql pynmea2
    # TFLite runtime (prefer runtime; fallback to TensorFlow if wheel unavailable)
    if ! .venv/bin/pip install tflite-runtime 2>/dev/null; then
        echo "⚠️  TFLite runtime not available for this arch, installing TensorFlow (may be heavy)..."
        .venv/bin/pip install tensorflow
    fi
    # Adafruit PCA9685 + motor (optional; for I2C servo driver boards)
    .venv/bin/pip install adafruit-blinka adafruit-circuitpython-pca9685 adafruit-circuitpython-motor

    # Enable camera and GPIO/I2C/SPI
    echo "Enabling camera and GPIO/I2C/SPI..."
    # Note: On Raspberry Pi OS Bookworm, camera works via libcamera; do_camera is kept for legacy compatibility
    sudo raspi-config nonint do_camera 0 || true
    sudo raspi-config nonint do_spi 0 || true
    sudo raspi-config nonint do_i2c 0 || true

    echo ""
    echo "✅ Python virtual environment ready"
    echo "To activate: source .venv/bin/activate"
    echo "To run app: .venv/bin/python3 main.py (or ./start.sh)"
    echo "To run servo test: .venv/bin/python3 scripts/test_servo_simple.py"
    
elif [[ "$PLATFORM" == "mac" ]]; then
    # macOS - lighter installation
    echo "Installing Python packages..."
    pip3 install --upgrade pip
    pip3 install numpy opencv-python
    
    # Try TFLite first, fallback to TensorFlow
    if ! pip3 install tflite-runtime 2>/dev/null; then
        echo "⚠️  TFLite runtime not available, installing TensorFlow..."
        pip3 install tensorflow
    fi
fi

echo ""

# Interactive camera setup
echo "🎥 Camera Configuration"
echo "======================"
echo ""

# Auto-detect available cameras
echo "Detecting available cameras..."
CAMERAS=()
for i in {0..5}; do
    if python3 -c "import cv2; cap = cv2.VideoCapture($i); ret, _ = cap.read(); cap.release(); exit(0 if ret else 1)" 2>/dev/null; then
        CAMERAS+=($i)
    fi
done

if [ ${#CAMERAS[@]} -eq 0 ]; then
    echo "❌ No cameras detected!"
    echo "Please connect a camera and try again."
    exit 1
fi

echo "✅ Found cameras at index: ${CAMERAS[*]}"
echo ""

# Ask user to select camera
if [ ${#CAMERAS[@]} -eq 1 ]; then
    CAMERA_INDEX=${CAMERAS[0]}
    echo "Using camera index: $CAMERA_INDEX"
else
    echo "Multiple cameras detected. Please select:"
    for cam in "${CAMERAS[@]}"; do
        echo "  $cam - Camera $cam"
    done
    echo ""
    
    while true; do
        read -p "Enter camera index [${CAMERAS[0]}]: " CAMERA_INDEX
        CAMERA_INDEX=${CAMERA_INDEX:-${CAMERAS[0]}}
        
        if [[ " ${CAMERAS[*]} " =~ " $CAMERA_INDEX " ]]; then
            break
        else
            echo "❌ Invalid camera index. Please choose from: ${CAMERAS[*]}"
        fi
    done
fi

echo ""

# Update configuration
echo "⚙️  Updating configuration..."

# Create backup
cp config.py config.py.backup

# Update platform and camera settings
python3 -c "
import re

# Read config
with open('config.py', 'r') as f:
    content = f.read()

# Update platform
content = re.sub(r\"PLATFORM = '[^']*'\", f\"PLATFORM = '$PLATFORM'\", content)

# Update camera index
content = re.sub(r'CAMERA_INDEX = \d+', f'CAMERA_INDEX = $CAMERA_INDEX', content)

# Set platform-specific defaults
if '$PLATFORM' == 'rpi':
    # Raspberry Pi defaults
    content = re.sub(r'ENABLE_GPS = (True|False)', 'ENABLE_GPS = True', content)
    content = re.sub(r'AUTO_DETECT_SERVOS = (True|False)', 'AUTO_DETECT_SERVOS = True', content)
    content = re.sub(r'ENABLE_DATABASE = (True|False)', 'ENABLE_DATABASE = True', content)
else:
    # macOS/Linux defaults (development mode)
    content = re.sub(r'ENABLE_GPS = (True|False)', 'ENABLE_GPS = False', content)
    content = re.sub(r'AUTO_DETECT_SERVOS = (True|False)', 'AUTO_DETECT_SERVOS = False', content)
    content = re.sub(r'ENABLE_DATABASE = (True|False)', 'ENABLE_DATABASE = False', content)

# Write updated config
with open('config.py', 'w') as f:
    f.write(content)

print('✅ Configuration updated')
"

echo ""

# Test camera
echo "🧪 Testing camera..."
if python3 -c "
import cv2
import sys

cap = cv2.VideoCapture($CAMERA_INDEX)
if not cap.isOpened():
    print('❌ Failed to open camera $CAMERA_INDEX')
    sys.exit(1)

ret, frame = cap.read()
if not ret:
    print('❌ Failed to read from camera $CAMERA_INDEX')
    sys.exit(1)

height, width = frame.shape[:2]
print(f'✅ Camera working: {width}x{height}')
cap.release()
"; then
    echo "✅ Camera test passed"
else
    echo "❌ Camera test failed"
    echo "Please check your camera connection and try again."
    exit 1
fi

echo ""

# Installation complete
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "Configuration Summary:"
echo "  Platform: $PLATFORM"
echo "  Camera Index: $CAMERA_INDEX"
if [[ "$PLATFORM" == "rpi" ]]; then
    echo "  GPS: Enabled"
    echo "  Servos: Auto-detect enabled"
    echo "  Database: Enabled"
else
    echo "  GPS: Disabled (development mode)"
    echo "  Servos: Disabled (development mode)"
    echo "  Database: Disabled (development mode)"
fi
echo ""
echo "🚀 Ready to run!"
echo "  Test mode: python3 main.py --test"
echo "  Full mode: python3 main.py"
echo "  Or use: ./start.sh"
echo ""
echo "📝 Configuration backup saved as: config.py.backup"
echo ""
