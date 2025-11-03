#!/bin/bash
# Camera Diagnostic Tool for Raspberry Pi
# Helps diagnose why camera is not detected

echo "🔍 Camera Detection Diagnostic Tool"
echo "===================================="
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  This script is designed for Raspberry Pi"
    echo "   Running anyway for diagnostic purposes..."
    echo ""
fi

# 1. Check USB devices
echo "1️⃣  Checking USB devices..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v lsusb >/dev/null 2>&1; then
    echo "All USB devices:"
    lsusb
    echo ""
    echo "Camera-related devices:"
    lsusb | grep -iE "camera|webcam|video|logitech|microsoft" || echo "  ✗ No camera devices found via lsusb"
else
    echo "  ✗ lsusb not available (install: sudo apt install usbutils)"
fi
echo ""

# 2. Check video devices
echo "2️⃣  Checking /dev/video* devices..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ls /dev/video* >/dev/null 2>&1; then
    echo "Found video devices:"
    ls -la /dev/video* | grep -E "video[0-9]+"
    echo ""
    
    # Check permissions
    echo "Checking permissions:"
    for dev in /dev/video*; do
        if [ -e "$dev" ]; then
            perm=$(ls -l "$dev" | awk '{print $1, $3, $4}')
            echo "  $dev: $perm"
        fi
    done
else
    echo "  ✗ No /dev/video* devices found"
    echo "  → Camera may not be detected by kernel"
fi
echo ""

# 3. Check v4l2 capabilities
echo "3️⃣  Checking v4l2 capabilities..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v v4l2-ctl >/dev/null 2>&1; then
    echo "Listing video devices:"
    v4l2-ctl --list-devices
    echo ""
    
    # Check each video device
    for dev in /dev/video*; do
        if [ -c "$dev" ]; then
            echo "Device: $dev"
            v4l2-ctl --device="$dev" --all 2>&1 | grep -E "Driver|Card|Bus|Video Capture" | head -5
            echo ""
        fi
    done
else
    echo "  ✗ v4l2-ctl not available (install: sudo apt install v4l-utils)"
fi
echo ""

# 4. Check user permissions
echo "4️⃣  Checking user permissions..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Current user: $(whoami)"
echo "User groups:"
groups
echo ""

if groups | grep -q video; then
    echo "  ✓ User is in 'video' group"
else
    echo "  ✗ User NOT in 'video' group"
    echo "  → Add user to video group:"
    echo "     sudo usermod -a -G video $(whoami)"
    echo "     Then logout and login again"
fi
echo ""

# 5. Check kernel modules
echo "5️⃣  Checking kernel modules..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Video-related modules:"
lsmod | grep -E "uvcvideo|videodev|v4l2" || echo "  ✗ No video modules loaded"
echo ""

echo "Loading uvcvideo module (if not loaded)..."
if ! lsmod | grep -q uvcvideo; then
    sudo modprobe uvcvideo 2>/dev/null && echo "  ✓ uvcvideo loaded" || echo "  ✗ Failed to load uvcvideo"
else
    echo "  ✓ uvcvideo already loaded"
fi
echo ""

# 6. Check Python OpenCV
echo "6️⃣  Checking Python OpenCV..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# System Python
echo "System Python 3:"
if python3 -c "import cv2; print(f'  ✓ OpenCV {cv2.__version__}')" 2>/dev/null; then
    echo "  Testing camera access with system Python..."
    python3 -c "
import cv2
for i in range(6):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, _ = cap.read()
        if ret:
            print(f'    ✓ Camera found at index {i}')
        cap.release()
" 2>/dev/null || echo "    ✗ No cameras accessible"
else
    echo "  ✗ OpenCV not available in system Python"
fi
echo ""

# Venv Python
if [ -f ".venv/bin/python3" ]; then
    echo "Virtual Environment Python:"
    if .venv/bin/python3 -c "import cv2; print(f'  ✓ OpenCV {cv2.__version__}')" 2>/dev/null; then
        echo "  Testing camera access with venv Python..."
        .venv/bin/python3 -c "
import cv2
for i in range(6):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, _ = cap.read()
        if ret:
            print(f'    ✓ Camera found at index {i}')
        cap.release()
" 2>/dev/null || echo "    ✗ No cameras accessible"
    else
        echo "  ✗ OpenCV not available in venv"
        echo "  → Run: ./fix_venv.sh"
    fi
else
    echo "  ℹ️  No virtual environment found (.venv)"
fi
echo ""

# 7. Recommendations
echo "7️⃣  Recommendations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

HAS_ISSUES=false

# Check for common issues
if ! ls /dev/video* >/dev/null 2>&1; then
    echo "🔴 No video devices found!"
    echo "   → Reconnect camera"
    echo "   → Try different USB port"
    echo "   → Check camera LED (should light up when connected)"
    HAS_ISSUES=true
fi

if ! groups | grep -q video; then
    echo "🔴 User not in video group!"
    echo "   → Run: sudo usermod -a -G video $(whoami)"
    echo "   → Then logout and login"
    HAS_ISSUES=true
fi

if ! lsmod | grep -q uvcvideo; then
    echo "🟡 UVC driver not loaded"
    echo "   → Run: sudo modprobe uvcvideo"
    HAS_ISSUES=true
fi

if ! python3 -c "import cv2" 2>/dev/null; then
    echo "🔴 OpenCV not available!"
    echo "   → Run: sudo apt-get install python3-opencv"
    HAS_ISSUES=true
fi

if [ -f ".venv/bin/python3" ] && ! .venv/bin/python3 -c "import cv2" 2>/dev/null; then
    echo "🟡 OpenCV not available in venv"
    echo "   → Run: ./fix_venv.sh"
    HAS_ISSUES=true
fi

if [ "$HAS_ISSUES" = false ]; then
    echo "✅ No obvious issues detected"
    echo ""
    echo "If camera still not working:"
    echo "1. Try rebooting: sudo reboot"
    echo "2. Try different camera"
    echo "3. Check dmesg for errors: dmesg | grep -i video"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Diagnostic complete!"
