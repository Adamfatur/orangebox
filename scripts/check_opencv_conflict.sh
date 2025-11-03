#!/bin/bash
# Check OpenCV conflict antara system dan venv

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         CHECK OPENCV CONFLICT (System vs Venv)               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

echo "1️⃣  OpenCV di SYSTEM (apt)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
dpkg -l | grep -i "python.*opencv" || echo "No system OpenCV via apt"
python3 -c "import sys; sys.path = [p for p in sys.path if '.venv' not in p]; import cv2; print(f'System cv2: {cv2.__version__} from {cv2.__file__}')" 2>&1 || echo "System cv2 not available"
echo ""

echo "2️⃣  OpenCV di VENV (pip)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip list | grep opencv || echo "No opencv in venv"
    python3 -c "import cv2; print(f'Venv cv2: {cv2.__version__} from {cv2.__file__}')" 2>&1 || echo "Venv cv2 not working"
    deactivate
else
    echo "No .venv found"
fi
echo ""

echo "3️⃣  KEMUNGKINAN MASALAH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Jika ada opencv-python di venv DAN python3-opencv di system:"
echo "  → BENTROK! Venv opencv tidak punya driver V4L2 lengkap"
echo ""
echo "SOLUSI:"
echo "  1. Hapus opencv dari venv:"
echo "     source .venv/bin/activate"
echo "     pip uninstall opencv-python opencv-contrib-python -y"
echo "     deactivate"
echo ""
echo "  2. Pastikan venv bisa akses system cv2:"
echo "     Venv dibuat dengan: python3 -m venv --system-site-packages .venv"
echo ""
echo "  3. Test lagi:"
echo "     python3 main.py"
echo ""
