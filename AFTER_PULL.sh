#!/bin/bash
# Quick Fix After Git Pull - Restore Camera Functionality
# Jalankan script ini setelah: git pull origin v1.1

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          QUICK FIX - Restore Camera After Update            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo "This script will:"
echo "  1. Remove opencv-python from venv (broken V4L2 driver)"
echo "  2. Install system opencv (python3-opencv with full V4L2)"
echo "  3. Test camera access"
echo "  4. Ready to run main.py"
echo ""
read -p "Press ENTER to continue or Ctrl+C to cancel..."
echo ""

# Step 1: Uninstall pip opencv
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Removing opencv-python from venv..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip uninstall opencv-python opencv-contrib-python opencv-python-headless -y 2>/dev/null || true
    deactivate
    echo "✓ opencv-python removed"
else
    echo "⚠️  No .venv found, skipping..."
fi
echo ""

# Step 2: Install system opencv
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Installing system OpenCV (python3-opencv)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo apt-get update -qq
sudo apt-get install -y python3-opencv
echo "✓ System OpenCV installed"
echo ""

# Step 3: Fix camera permissions
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Fixing camera permissions..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CURRENT_USER=$(whoami)

# Add to video group if not already
if groups | grep -q video; then
    echo "✓ User already in 'video' group"
else
    sudo usermod -a -G video $CURRENT_USER
    echo "✓ User added to 'video' group"
    echo "⚠️  IMPORTANT: Must logout/login for group to take effect!"
    echo "             Or just reboot: sudo reboot"
fi

# Set /dev/video* permissions
if ls /dev/video* >/dev/null 2>&1; then
    sudo chmod 666 /dev/video*
    echo "✓ Camera device permissions set"
else
    echo "⚠️  No /dev/video* devices found!"
    echo "    → Webcam may not be plugged in or recognized"
fi
echo ""

# Step 4: Test camera
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Testing camera access..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
source .venv/bin/activate
python3 << 'EOF'
import cv2
import os
os.environ['QT_QPA_PLATFORM'] = 'xcb'

success = False
for i in range(5):
    try:
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✓ Camera {i} WORKING: {frame.shape[1]}x{frame.shape[0]}")
                success = True
                cap.release()
                break
            cap.release()
    except Exception as e:
        pass

if not success:
    print("✗ No camera detected!")
    print("\nTroubleshooting:")
    print("  1. Check USB: lsusb | grep -i logitech")
    print("  2. Check /dev/video*: ls -l /dev/video*")
    print("  3. Reboot: sudo reboot")
    print("  4. Try different USB port")
else:
    print("\n✓✓✓ Camera is READY! ✓✓✓")
EOF
deactivate
echo ""

# Step 5: Final check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Final system check..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
source .venv/bin/activate
python3 << 'EOF'
import sys

print("Checking dependencies...")

# Check OpenCV
try:
    import cv2
    print(f"✓ OpenCV: {cv2.__version__} from {cv2.__file__}")
except Exception as e:
    print(f"✗ OpenCV: {e}")

# Check TFLite
try:
    import tflite_runtime.interpreter as tflite
    print(f"✓ TFLite Runtime: OK")
except Exception as e:
    print(f"✗ TFLite Runtime: {e}")

# Check ServoKit
try:
    from adafruit_servokit import ServoKit
    print(f"✓ ServoKit: OK")
except Exception as e:
    print(f"⚠️  ServoKit: {e}")

print("\nAll critical dependencies checked!")
EOF
deactivate
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                         ✓ DONE!                              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. If camera still not working → REBOOT: sudo reboot"
echo "  2. After reboot → python3 main.py"
echo ""
echo "Test servos (optional):"
echo "  python3 scripts/auto_detect_test_servo.py"
echo ""
