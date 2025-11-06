#!/bin/bash
# Fix Virtual Environment - OpenCV Missing
# Script ini memperbaiki masalah cv2 tidak terdeteksi di venv

set -e

echo "🔧 Fixing Virtual Environment..."
echo "================================"

# Pastikan kita di direktori yang benar
cd "$(dirname "$0")"

# Cek apakah ini Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "❌ This script is for Raspberry Pi only!"
    exit 1
fi

echo "📦 Installing system packages..."
sudo apt-get update --allow-releaseinfo-change -qq
sudo apt-get install -y python3-opencv python3-picamera2 python3-tflite-runtime v4l-utils

# Load USB camera driver
echo "📹 Loading USB camera driver..."
sudo modprobe uvcvideo || echo "⚠️ Could not load uvcvideo (may already be loaded)"

# Add user to video group if not already
if ! groups | grep -q video; then
    echo "👤 Adding user to video group..."
    sudo usermod -a -G video $USER
    echo "⚠️  You need to LOGOUT and LOGIN again for group changes to take effect!"
    echo "   After relogin, run this script again."
fi

echo "🔄 Recreating virtual environment with system packages..."
# Backup old venv if exists
if [ -d ".venv" ]; then
    echo "  → Backing up old .venv to .venv.backup"
    rm -rf .venv.backup
    mv .venv .venv.backup
fi

# Create new venv with --system-site-packages flag
echo "  → Creating new .venv with system site-packages"
python3 -m venv .venv --system-site-packages

# Upgrade pip
echo "  → Upgrading pip"
.venv/bin/pip install --upgrade pip setuptools wheel

# Install requirements (excluding opencv and tflite which come from apt)
echo "  → Installing Python packages"
TMP_REQ=.requirements.rpi.txt
grep -Ev '^(opencv-python|tflite-runtime|picamera2)' requirements.txt > "$TMP_REQ" || true
.venv/bin/pip install -r "$TMP_REQ" || echo "⚠️ Some packages failed, continuing..."
rm -f "$TMP_REQ"

# Verify cv2 is available
echo ""
echo "🧪 Testing OpenCV in venv..."
if .venv/bin/python3 -c "import cv2; print(f'✓ OpenCV version: {cv2.__version__}')" 2>/dev/null; then
    echo "✅ OpenCV is working!"
else
    echo "❌ OpenCV still not available!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check if python3-opencv is installed:"
    echo "   dpkg -l | grep python3-opencv"
    echo ""
    echo "2. Check Python version compatibility:"
    echo "   python3 --version"
    echo ""
    echo "3. Try manual install:"
    echo "   .venv/bin/pip install opencv-python"
    exit 1
fi

# Test picamera2 if available
echo ""
echo "🧪 Testing PiCamera2..."
if .venv/bin/python3 -c "import picamera2; print('✓ PiCamera2 available')" 2>/dev/null; then
    echo "✅ PiCamera2 is working!"
else
    echo "⚠️  PiCamera2 not available (optional)"
fi

# Test tflite runtime
echo ""
echo "🧪 Testing TFLite Runtime..."
if .venv/bin/python3 -c "import tflite_runtime; print('✓ TFLite Runtime available')" 2>/dev/null; then
    echo "✅ TFLite Runtime is working!"
elif .venv/bin/python3 -c "import tensorflow.lite; print('✓ TensorFlow Lite available')" 2>/dev/null; then
    echo "✅ TensorFlow Lite is working!"
else
    echo "⚠️  TFLite not available - installing fallback"
    .venv/bin/pip install tensorflow-lite || echo "❌ Could not install TFLite"
fi

echo ""
echo "✅ Virtual environment fixed!"
echo ""

# Check camera detection
echo "🎥 Checking camera detection..."
if ls /dev/video* >/dev/null 2>&1; then
    echo "✓ Video devices found:"
    ls -la /dev/video* 2>/dev/null | grep -E "video[0-9]+"
    
    # Try to detect with OpenCV
    .venv/bin/python3 -c "
import cv2
found = False
for i in range(6):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, _ = cap.read()
        if ret:
            print(f'  ✓ Camera detected at index {i}')
            found = True
        cap.release()
if not found:
    print('  ⚠️ Video devices exist but not accessible via OpenCV')
    print('  → Check permissions: groups | grep video')
    print('  → Try: sudo usermod -a -G video \$USER, then logout/login')
" 2>/dev/null || echo "  ⚠️ Could not test camera with OpenCV"
else
    echo "⚠️ No /dev/video* devices found"
    echo ""
    echo "Camera troubleshooting:"
    echo "1. Reconnect camera to USB port"
    echo "2. Run diagnostic: ./scripts/diagnose_camera.sh"
    echo "3. Check if camera detected: lsusb | grep -i camera"
    echo "4. Load driver: sudo modprobe uvcvideo"
    echo "5. Reboot if needed: sudo reboot"
fi

echo ""
echo "To activate venv manually:"
echo "  source .venv/bin/activate"
echo ""
echo "To run OrangeBox:"
echo "  ./start.sh"
echo "  or: .venv/bin/python3 main.py"
echo ""
