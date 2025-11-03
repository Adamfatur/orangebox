#!/bin/bash
# 🚀 OrangeBox Quick Start (non-interaktif, satu perintah)

set -e

# Pindah ke direktori proyek
cd "$(dirname "$0")"

echo "🧡 OrangeBox Waste Sorter System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Pilih interpreter: gunakan venv jika tersedia
PYTHON_BIN="python3"
if [ -x ".venv/bin/python3" ]; then
  PYTHON_BIN=".venv/bin/python3"
fi

# CRITICAL: Auto-fix OpenCV pada Raspberry Pi
# Jika cv2 tidak bisa di-import, fix opencv conflict
if ! $PYTHON_BIN -c "import cv2" 2>/dev/null; then
  echo "⚠️  OpenCV not available in venv"
  
  # Detect Raspberry Pi
  if [ -f /proc/cpuinfo ] && grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "🔧 Raspberry Pi detected - fixing OpenCV (using system cv2)..."
    
    # Remove pip opencv if exists
    if [ -d ".venv" ]; then
      .venv/bin/pip uninstall opencv-python opencv-contrib-python opencv-python-headless -y 2>/dev/null || true
    fi
    
    # Install system opencv
    echo "📦 Installing python3-opencv from apt..."
    sudo apt-get update -qq 2>/dev/null || true
    sudo apt-get install -y python3-opencv 2>/dev/null || true
    
    # Verify
    if ! $PYTHON_BIN -c "import cv2; print('✓ OpenCV OK')" 2>/dev/null; then
      echo "❌ OpenCV still not working. Running full install..."
      bash ./install.sh
      PYTHON_BIN=".venv/bin/python3"
    else
      echo "✓ OpenCV fixed!"
    fi
  else
    # Non-RPi: run normal install
    echo "📦 Running installer..."
    bash ./install.sh
    PYTHON_BIN=".venv/bin/python3"
  fi
fi

# Deteksi platform sederhana
IS_RPI=false
if [ -f /proc/cpuinfo ] && grep -q "Raspberry Pi" /proc/cpuinfo; then
  IS_RPI=true
fi
# Tentukan model TFLite jika ada
MODEL_ARG=""
if [ -f "models/model_quant_infer.tflite" ]; then
  MODEL_ARG="--model models/model_quant_infer.tflite"
elif [ -f "models/model_float32_infer.tflite" ]; then
  MODEL_ARG="--model models/model_float32_infer.tflite"
fi

echo "🚀 Starting..."
if [ "$IS_RPI" = true ]; then
  # Mode produksi di Raspberry Pi
  # Biarkan hardware interface auto-detect: PiCamera2 → USB webcam
  exec $PYTHON_BIN main.py $MODEL_ARG "$@"
else
  # Mode simulasi di macOS/Non-RPi
  exec $PYTHON_BIN main.py --test --confidence 0.7 "$@"
fi
