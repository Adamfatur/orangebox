#!/bin/bash
# Quick Fix untuk Camera Permission Issues
# Jalankan dengan: bash scripts/fix_camera_permission.sh

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║           FIX CAMERA PERMISSION - RASPBERRY PI               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

CURRENT_USER=$(whoami)
echo "Current user: $CURRENT_USER"
echo ""

# 1. Cek apakah video device ada
echo "1️⃣  Checking video devices..."
if ls /dev/video* 2>/dev/null; then
    echo "✓ Video devices found:"
    ls -l /dev/video*
else
    echo "✗ NO VIDEO DEVICES FOUND!"
    echo ""
    echo "Possible solutions:"
    echo "  1. Unplug and replug USB webcam"
    echo "  2. Try different USB port (USB 2.0 instead of USB 3.0)"
    echo "  3. Check if camera is recognized: lsusb | grep -i logitech"
    echo "  4. Load USB video driver: sudo modprobe uvcvideo"
    echo "  5. Reboot: sudo reboot"
    exit 1
fi
echo ""

# 2. Add user to video group
echo "2️⃣  Adding user to 'video' group..."
if groups | grep -q video; then
    echo "✓ User already in 'video' group"
else
    echo "Adding $CURRENT_USER to video group..."
    sudo usermod -a -G video $CURRENT_USER
    echo "✓ User added to video group"
    echo ""
    echo "⚠️  IMPORTANT: You must LOGOUT and LOGIN again (or reboot) for this to take effect!"
    echo "    Run: sudo reboot"
fi
echo ""

# 3. Set permissions on video devices
echo "3️⃣  Setting permissions on video devices..."
for dev in /dev/video*; do
    if [ -e "$dev" ]; then
        echo "Setting permission on $dev..."
        sudo chmod 666 $dev
        echo "✓ $dev now accessible by all users"
    fi
done
echo ""

# 4. Test camera access
echo "4️⃣  Testing camera access with OpenCV..."
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
    print("✗ No working camera found via OpenCV")
    print("\nTroubleshooting:")
    print("  1. Reboot: sudo reboot")
    print("  2. Check camera with: cheese (GUI app)")
    print("  3. Check driver: sudo modprobe uvcvideo")
    print("  4. Check kernel log: dmesg | grep -i video")
EOF
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                           DONE                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "If camera still not working:"
echo "  1. REBOOT: sudo reboot"
echo "  2. Run diagnostic: bash scripts/diagnose_camera.sh"
echo "  3. Test with GUI app: cheese"
echo ""
