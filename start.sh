#!/bin/bash
# 🚀 OrangeBox Quick Start

echo "� OrangeBox Waste Sorter System"
echo "=================================="
echo ""

# Kill any existing instance
pkill -f "python3 main.py" 2>/dev/null
[ $? -eq 0 ] && echo "⏹️  Stopped existing instance" && sleep 1

echo "🚀 Starting system..."

# Prefer Python from virtual environment if available
PYTHON_BIN="python3"
if [ -x ".venv/bin/python3" ]; then
  PYTHON_BIN=".venv/bin/python3"
fi

$PYTHON_BIN main.py --model models/model_quant_infer.tflite

# Change to script directory
cd "$(dirname "$0")"

# Check if dependencies are installed
if ! $PYTHON_BIN -c "import cv2" 2>/dev/null; then
    echo "📦 Dependencies not installed!"
    echo ""
    read -p "Install now? (y/n): " install_choice
    
    if [ "$install_choice" = "y" ] || [ "$install_choice" = "Y" ]; then
        ./install.sh
    else
        echo ""
        echo "Please install manually:"
        echo "  pip3 install -r requirements.txt"
        echo ""
        exit 1
    fi
    echo ""
fi

# Check for model files
if [ ! -f "models/model.tflite" ]; then
    echo "⚠️  Model file tidak ditemukan!"
    echo ""
    echo "Pilih mode:"
    echo "1) Test mode (tanpa model AI)"
    echo "2) Exit dan setup model dulu"
    read -p "Pilihan (1/2): " choice
    
    case $choice in
        1)
            echo ""
            echo "🎮 Running in TEST MODE..."
            $PYTHON_BIN run.py --test
            ;;
        2)
            echo ""
            echo "Setup model:"
            echo "1. Buka: https://teachablemachine.withgoogle.com/"
            echo "2. Train model dengan 2 class: ORGANIC dan ANORGANIC"
            echo "3. Export sebagai TensorFlow Lite"
            echo "4. Letakkan model.tflite dan labels.txt di folder models/"
            echo ""
            echo "Atau jalankan: ./start.sh untuk test mode"
            exit 0
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
else
    echo "✅ Model ditemukan!"
    echo ""
    echo "🚀 Starting Waste Sorter System..."
    echo ""
    $PYTHON_BIN run.py "$@"
fi
