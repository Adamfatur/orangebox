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

# Pastikan dependency siap: jika cv2 tidak bisa di-import, jalankan installer otomatis
if ! $PYTHON_BIN -c "import cv2" 2>/dev/null; then
  echo "📦 Dependencies belum lengkap. Menjalankan installer..."
  bash ./install.sh
  PYTHON_BIN=".venv/bin/python3"
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
  exec $PYTHON_BIN main.py $MODEL_ARG --camera 0 "$@"
else
  # Mode simulasi di macOS/Non-RPi
  exec $PYTHON_BIN main.py --test --confidence 0.7 "$@"
fi
