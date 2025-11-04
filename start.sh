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
    echo "🔧 Raspberry Pi detected - fixing OpenCV access..."
    
    # FIX: Recreate venv with --system-site-packages to access system opencv
    if [ -d ".venv" ]; then
      # Check if venv has system-site-packages enabled
      if [ ! -f ".venv/pyvenv.cfg" ] || ! grep -q "include-system-site-packages = true" ".venv/pyvenv.cfg"; then
        echo "🔨 Recreating venv with system packages access..."
        
        # Backup and recreate
        rm -rf .venv.backup 2>/dev/null || true
        mv .venv .venv.backup 2>/dev/null || true
        
        # Create new venv with system-site-packages
        python3 -m venv --system-site-packages .venv
        .venv/bin/pip install --upgrade pip --quiet
        
        # Reinstall packages
        echo "📦 Reinstalling Python packages..."
        .venv/bin/pip install --quiet numpy RPi.GPIO gpiozero pymysql pynmea2 pyserial python-dotenv
        .venv/bin/pip install --quiet adafruit-blinka adafruit-circuitpython-pca9685 adafruit-circuitpython-servokit
        
        PYTHON_BIN=".venv/bin/python3"
      fi
    fi
    
    # Install system opencv if not present
    if ! dpkg -l | grep -q python3-opencv; then
      echo "📦 Installing python3-opencv from apt..."
      sudo apt-get update -qq 2>/dev/null || true
      sudo apt-get install -y python3-opencv
    fi
    
    # Verify fix
    if ! $PYTHON_BIN -c "import cv2; print('✅ OpenCV accessible')" 2>/dev/null; then
      echo "❌ OpenCV still not accessible. Running full installer..."
      bash ./install.sh
      PYTHON_BIN=".venv/bin/python3"
    else
      echo "✅ OpenCV fix successful!"
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
