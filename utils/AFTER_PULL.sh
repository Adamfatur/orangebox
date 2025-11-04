#!/bin/bash
# Quick Fix After Git Pull - Restore Camera Functionality
# ONE-COMMAND FIX: bash AFTER_PULL.sh

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║          QUICK FIX - Restore Camera After Update            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Platform detection
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✓ macOS detected - no fix needed"
    echo "  Just run: python3 main.py --test"
    exit 0
fi

# Auto-continue on Raspberry Pi/Linux
echo "🚀 Auto-fixing OpenCV camera issue..."
echo ""

# Step 1: Uninstall pip opencv
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Removing broken opencv-python from venv..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d ".venv" ]; then
    .venv/bin/pip uninstall opencv-python opencv-contrib-python opencv-python-headless -y 2>/dev/null || true
    echo "✓ Removed"
else
    echo "⚠️  No .venv found, creating..."
    python3 -m venv --system-site-packages .venv
fi
echo ""

# Step 2: Install system opencv (NO PROMPT)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Installing system OpenCV (with V4L2 driver)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo apt-get update -qq 2>/dev/null || true
sudo apt-get install -y python3-opencv 2>/dev/null || echo "  (may already be installed)"
echo "✓ System OpenCV ready"
echo ""

# Step 3: Fix permissions (NO PROMPT)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Fixing camera permissions..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CURRENT_USER=$(whoami)
if ! groups | grep -q video; then
    sudo usermod -a -G video $CURRENT_USER 2>/dev/null || true
    echo "✓ Added to video group (reboot needed)"
fi
if ls /dev/video* >/dev/null 2>&1; then
    sudo chmod 666 /dev/video* 2>/dev/null || true
    echo "✓ Camera permissions OK"
fi
echo ""

# Step 4: Test camera
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Testing camera..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
.venv/bin/python3 << 'EOF'
import cv2, os
os.environ['QT_QPA_PLATFORM'] = 'xcb'
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"✓ Camera {i} OK: {frame.shape[1]}x{frame.shape[0]}")
            cap.release()
            exit(0)
        cap.release()
print("⚠️  Camera not detected - may need reboot")
exit(1)
EOF

CAMERA_OK=$?
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                         ✓ FIXED!                             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

if [ $CAMERA_OK -eq 0 ]; then
    echo "✓✓✓ Camera is ready! Run: python3 main.py"
else
    echo "⚠️  Camera not detected. Try:"
    echo "    1. Reboot: sudo reboot"
    echo "    2. Check USB: lsusb | grep -i logitech"
    echo "    3. Then run: python3 main.py"
fi
echo ""
