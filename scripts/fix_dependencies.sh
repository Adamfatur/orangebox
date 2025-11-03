#!/bin/bash

# ============================================================
# Quick Fix Script - Install Missing Dependencies
# ============================================================

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║          🔧 ORANGE BOX - DEPENDENCY FIX 🔧                   ║"
echo "║              Quick Install Missing Packages                 ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Project directory: $PROJECT_DIR"
echo ""

# ============================================================
# Check and install Python packages
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Installing Python Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Upgrade pip first
echo "⬆️  Upgrading pip..."
python3 -m pip install --upgrade pip

# Install from requirements.txt
echo "📥 Installing packages from requirements.txt..."
cd "$PROJECT_DIR"
pip3 install -r requirements.txt

echo "✅ Python packages installed"
echo ""

# ============================================================
# Check TensorFlow Lite
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧠 Verifying TensorFlow Lite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python3 -c "import tflite_runtime" 2>/dev/null; then
    echo "  ✓ tflite-runtime installed"
else
    echo "  ⚠️  tflite-runtime not found, trying alternative..."
    # Try installing from piwheels (Raspberry Pi)
    pip3 install --index-url https://www.piwheels.org/simple tflite-runtime
fi
echo ""

# ============================================================
# Check Database
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💾 Verifying Database Support"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python3 -c "import pymysql" 2>/dev/null; then
    echo "  ✓ pymysql installed"
else
    echo "  ⚠️  Installing pymysql..."
    pip3 install pymysql
fi
echo ""

# ============================================================
# Check Adafruit Servo
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🦾 Verifying Servo Control (Adafruit)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python3 -c "import adafruit_servokit" 2>/dev/null; then
    echo "  ✓ adafruit-circuitpython-servokit installed"
else
    echo "  ⚠️  Installing Adafruit ServoKit..."
    pip3 install adafruit-circuitpython-servokit
fi
echo ""

# ============================================================
# Check GPS packages
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Verifying GPS Support"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check pyserial
if python3 -c "import serial" 2>/dev/null; then
    echo "  ✓ pyserial installed"
else
    echo "  ⚠️  Installing pyserial..."
    pip3 install pyserial
fi

# Check pynmea2
if python3 -c "import pynmea2" 2>/dev/null; then
    echo "  ✓ pynmea2 installed"
else
    echo "  ⚠️  Installing pynmea2..."
    pip3 install pynmea2
fi
echo ""

# ============================================================
# Start GPSD (if configured)
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛰️  Checking GPS Daemon"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet gpsd; then
    echo "  ✓ GPSD service is running"
elif systemctl is-enabled --quiet gpsd 2>/dev/null; then
    echo "  ⚠️  GPSD is enabled but not running"
    echo "  Starting GPSD..."
    sudo systemctl start gpsd
    echo "  ✓ GPSD started"
else
    echo "  ℹ️  GPSD not configured (run GPS setup if needed)"
fi
echo ""

# ============================================================
# Verification
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -c "
import sys

checks = {
    'TensorFlow Lite': 'tflite_runtime.interpreter',
    'PyMySQL': 'pymysql',
    'Adafruit ServoKit': 'adafruit_servokit',
    'PySerial': 'serial',
    'PyNMEA2': 'pynmea2',
    'NumPy': 'numpy',
    'OpenCV': 'cv2'
}

print()
all_ok = True
for name, module in checks.items():
    try:
        __import__(module)
        print(f'  ✓ {name:20} - OK')
    except ImportError:
        print(f'  ✗ {name:20} - MISSING')
        all_ok = False

print()
if all_ok:
    print('✅ All critical packages installed successfully!')
else:
    print('⚠️  Some packages are still missing. Try manual install.')
    sys.exit(1)
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPENDENCY FIX COMPLETED!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Next steps:"
echo "   1. Test system: python3 main.py"
echo "   2. Check logs for any remaining errors"
echo "   3. If servo issues persist, check I2C connection"
echo ""
