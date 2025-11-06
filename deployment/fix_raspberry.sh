#!/bin/bash
#
# RASPBERRY PI 5 - DEPLOYMENT FIX SCRIPT
# Script ini memastikan instalasi yang benar dan menghilangkan segfault
#
# Jalankan dengan: bash deployment/fix_raspberry.sh
#

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     🍊 ORANGE BOX - RASPBERRY PI 5 FIX DEPLOYMENT 🍊        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Deteksi Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo -e "${YELLOW}⚠️  WARNING: Script ini dirancang untuk Raspberry Pi${NC}"
    echo "Melanjutkan dengan asumsi environment kompatibel..."
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Update dari Git Repository"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Stash local changes jika ada
if git diff-index --quiet HEAD --; then
    echo "✓ No local changes to stash"
else
    echo "⚠️  Stashing local changes..."
    git stash
fi

# Pull latest dari v1.1
echo "Pulling latest changes from origin/v1.1..."
git fetch origin v1.1
git checkout v1.1
git reset --hard origin/v1.1
echo -e "${GREEN}✓ Code updated to latest v1.1${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Hapus Virtual Environment Lama"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d ".venv" ]; then
    echo "Menghapus .venv lama untuk instalasi bersih..."
    rm -rf .venv
    echo -e "${GREEN}✓ Old venv removed${NC}"
else
    echo "✓ No existing venv found"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Uninstall Konflik Library dari System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Hapus package yang bisa konflik
echo "Menghapus python3-opencv dari system (akan diinstall via pip)..."
sudo apt remove -y python3-opencv 2>/dev/null || echo "  (python3-opencv tidak terinstall)"

echo "Menghapus adafruit-motor yang redundant..."
.venv/bin/pip uninstall -y adafruit-motor 2>/dev/null || echo "  (belum ada di venv)"

# CRITICAL: Pastikan tflite-runtime dari APT
echo "Memastikan tflite-runtime dari APT terinstall..."
sudo apt update
sudo apt install -y python3-tflite-runtime
echo -e "${GREEN}✓ System packages cleaned${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 4: Clean Install dengan install.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

bash install.sh
echo -e "${GREEN}✓ Installation complete${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 5: Verifikasi - Cek Konflik Library"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if python3 scripts/verify_no_conflicts.py; then
    echo -e "${GREEN}✓ No conflicts detected!${NC}"
else
    echo -e "${RED}✗ Conflicts detected - see output above${NC}"
    exit 1
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 6: Test Run"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Testing dengan python3 main.py --test..."
echo ""
timeout 10s python3 main.py --test || {
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 139 ]; then
        echo -e "${RED}✗ SEGMENTATION FAULT DETECTED!${NC}"
        echo ""
        echo "Diagnostics:"
        echo "1. Cek tflite-runtime source:"
        python3 -c "import tflite_runtime; print('  tflite_runtime:', tflite_runtime.__file__)"
        echo ""
        echo "2. Cek apakah tensorflow terinstall (HARUS TIDAK):"
        python3 -c "import tensorflow" 2>&1 && echo -e "${RED}  ✗ TensorFlow TERDETEKSI - INI MASALAHNYA!${NC}" || echo -e "${GREEN}  ✓ TensorFlow tidak ada (correct)${NC}"
        echo ""
        echo "3. Cek opencv source:"
        python3 -c "import cv2; print('  opencv:', cv2.__file__)"
        echo ""
        exit 1
    elif [ $EXIT_CODE -eq 124 ]; then
        echo -e "${GREEN}✓ Test timeout (normal - kamera inisialisasi)${NC}"
    else
        echo -e "${YELLOW}⚠️  Exit code: $EXIT_CODE${NC}"
    fi
}
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    ✅ FIX COMPLETE ✅                         ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "Sekarang jalankan dengan:"
echo -e "  ${GREEN}python3 main.py${NC}"
echo ""
echo "Atau gunakan systemd service:"
echo -e "  ${GREEN}bash deployment/service.sh install${NC}"
echo -e "  ${GREEN}sudo systemctl start orangebox${NC}"
echo ""
