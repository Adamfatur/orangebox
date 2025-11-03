#!/bin/bash
# Fix OpenCV conflict - hapus opencv-python dari venv, pakai system opencv

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         FIX OPENCV - Hapus pip opencv, pakai system          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo "MASALAH:"
echo "  opencv-python dari pip TIDAK punya driver V4L2 lengkap"
echo "  Ini menyebabkan kamera tidak bisa diakses di Raspberry Pi"
echo ""
echo "SOLUSI:"
echo "  1. Uninstall opencv-python dari venv"
echo "  2. Pakai system opencv (python3-opencv dari apt)"
echo "  3. Venv tetap bisa akses system opencv via --system-site-packages"
echo ""

# Activate venv
if [ ! -d ".venv" ]; then
    echo "✗ No .venv found. Run install.sh first."
    exit 1
fi

echo "1️⃣  Uninstalling opencv-python from venv..."
source .venv/bin/activate
pip uninstall opencv-python opencv-contrib-python opencv-python-headless -y 2>/dev/null || echo "  (already uninstalled)"
deactivate
echo "✓ opencv-python removed from venv"
echo ""

echo "2️⃣  Installing system opencv via apt..."
sudo apt-get update -qq
sudo apt-get install -y python3-opencv
echo "✓ System opencv installed"
echo ""

echo "3️⃣  Verifying opencv accessibility in venv..."
source .venv/bin/activate
if python3 -c "import cv2; print(f'OpenCV: {cv2.__version__} from {cv2.__file__}')" 2>/dev/null; then
    echo "✓ System OpenCV accessible in venv!"
else
    echo "✗ OpenCV still not accessible"
    echo "  Venv may not have --system-site-packages"
    echo "  Fix: Remove and recreate venv with:"
    echo "    rm -rf .venv"
    echo "    python3 -m venv --system-site-packages .venv"
    echo "    bash install.sh"
    deactivate
    exit 1
fi
deactivate
echo ""

echo "4️⃣  Testing camera access..."
source .venv/bin/activate
python3 << 'EOF'
import cv2
import os
os.environ['QT_QPA_PLATFORM'] = 'xcb'

print("Testing camera...")
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"✓ Camera {i} WORKS: {frame.shape[1]}x{frame.shape[0]}")
            cap.release()
            break
        cap.release()
    if i == 4:
        print("✗ No camera working")
        print("\nNext steps:")
        print("  1. Check camera: lsusb | grep -i logitech")
        print("  2. Check /dev/video*: ls -l /dev/video*")
        print("  3. Fix permission: bash scripts/fix_camera_permission.sh")
        print("  4. Reboot: sudo reboot")
EOF
deactivate
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                           DONE                                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Now run: python3 main.py"
echo ""
