#!/bin/bash

# ============================================================
# Orange Box - Deployment Script untuk Raspberry Pi 5
# ============================================================
# Script ini akan:
# 1. Install dependencies
# 2. Setup systemd service untuk auto-start
# 3. Enable service agar jalan otomatis saat boot
# ============================================================

set -e  # Exit on error

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║          🧡 ORANGE BOX - DEPLOYMENT SCRIPT 🧡                ║"
echo "║              Raspberry Pi 5 Auto Setup                      ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Cek apakah dijalankan di Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  WARNING: Script ini dirancang untuk Raspberry Pi"
    echo "   Apakah Anda yakin ingin melanjutkan? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Deployment dibatalkan."
        exit 1
    fi
fi

# Get absolute path of project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Project directory: $PROJECT_DIR"
echo ""

# ============================================================
# STEP 1: Update system dan install dependencies
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 STEP 1: Installing System Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-opencv \
    python3-numpy \
    python3-picamera2 \
    python3-rpi.gpio \
    libopenblas-dev \
    liblapack-dev \
    libhdf5-dev \
    libjpeg-dev \
    libpng-dev \
    v4l-utils \
    git

echo "  ✓ Core system packages"

# Camera tools
sudo apt-get install -y \
    libcamera-apps \
    libcamera-dev \
    python3-libcamera

echo "  ✓ Camera support (Pi Camera Module)"

# Database client tools
sudo apt-get install -y \
    default-libmysqlclient-dev \
    pkg-config

echo "  ✓ Database client libraries"

echo "✅ All system dependencies installed"
echo ""

# ============================================================
# STEP 2: Install Python dependencies
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 STEP 2: Installing Python Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PROJECT_DIR"
pip3 install --upgrade pip
pip3 install -r requirements.txt

echo "✅ Python dependencies installed"
echo ""

# ============================================================
# STEP 2.5: Setup GPS Module (if enabled)
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 STEP 2.5: GPS Module Setup (U-blox NEO-6M)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if user wants GPS
echo "Apakah Anda punya GPS module NEO-6M? (y/n)"
read -r gps_response

if [[ "$gps_response" =~ ^[Yy]$ ]]; then
    echo "Setting up GPS..."
    
    # Enable UART
    if ! grep -q "enable_uart=1" /boot/firmware/config.txt; then
        echo "enable_uart=1" | sudo tee -a /boot/firmware/config.txt > /dev/null
        echo "  ✓ UART enabled"
    fi
    
    # Disable Bluetooth to free UART
    if ! grep -q "dtoverlay=disable-bt" /boot/firmware/config.txt; then
        echo "dtoverlay=disable-bt" | sudo tee -a /boot/firmware/config.txt > /dev/null
        sudo systemctl disable hciuart 2>/dev/null || true
        echo "  ✓ Bluetooth disabled (untuk free UART)"
    fi
    
    # Remove console from serial
    if grep -q "console=serial0" /boot/firmware/cmdline.txt 2>/dev/null; then
        sudo sed -i 's/console=serial0,[0-9]\+ //' /boot/firmware/cmdline.txt
        echo "  ✓ Console removed dari serial"
    fi
    
    # Install GPSD
    sudo apt-get install -y gpsd gpsd-clients python3-gps pyserial pynmea2
    
    # Configure GPSD
    sudo tee /etc/default/gpsd > /dev/null << GPSD_EOF
START_DAEMON="true"
GPSD_OPTIONS="-n"
DEVICES="/dev/serial0"
USBAUTO="false"
GPSD_EOF
    
    sudo systemctl enable gpsd
    sudo systemctl restart gpsd 2>/dev/null || true
    
    echo "  ✅ GPS module configured"
    echo ""
    echo "  Hardware connection:"
    echo "    GPS VCC → Pin 4 (5V)"
    echo "    GPS GND → Pin 6 (GND)"
    echo "    GPS TX  → Pin 10 (GPIO15/RX)"
    echo "    GPS RX  → Pin 8  (GPIO14/TX)"
    echo ""
    GPS_SETUP_DONE=true
else
    echo "  ⏭️  GPS setup skipped"
    echo "     (Bisa diaktifkan nanti di config.py: ENABLE_GPS = False)"
    GPS_SETUP_DONE=false
fi
echo ""

# ============================================================
# STEP 2.8: Device ID Setup
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🆔 STEP 2.8: Device ID Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Device ID digunakan untuk multi-device deployment."
echo "Pilih mode:"
echo "  1. Auto-generate (hostname + MAC address)"
echo "  2. Manual (contoh: OB-MALL-PSX-L2-001)"
echo ""
read -p "Pilih [1-2]: " device_choice

if [ "$device_choice" = "2" ]; then
    read -p "Masukkan Device ID: " custom_device_id
    read -p "Nama lokasi (contoh: Plaza Senayan - Lantai 2): " device_name
    read -p "Lokasi (contoh: Jakarta Selatan): " device_location
    
    # Update config.py
    sed -i "s/^DEVICE_ID = None/DEVICE_ID = '$custom_device_id'/" "$PROJECT_DIR/config.py"
    sed -i "s/^DEVICE_NAME = None/DEVICE_NAME = '$device_name'/" "$PROJECT_DIR/config.py"
    sed -i "s/^DEVICE_LOCATION = None/DEVICE_LOCATION = '$device_location'/" "$PROJECT_DIR/config.py"
    
    echo "  ✓ Device ID: $custom_device_id"
    echo "  ✓ Nama: $device_name"
    echo "  ✓ Lokasi: $device_location"
else
    echo "  ✓ Device ID akan auto-generate dari hostname + MAC"
fi
echo ""

# ============================================================
# STEP 3: Verify Model Files
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 STEP 3: Verifying ML Model Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$PROJECT_DIR/models/model_quant_infer.tflite" ]; then
    model_size=$(du -h "$PROJECT_DIR/models/model_quant_infer.tflite" | cut -f1)
    echo "  ✓ Quantized model found: $model_size"
else
    echo "  ⚠️  Warning: model_quant_infer.tflite not found!"
fi

if [ -f "$PROJECT_DIR/models/model_float32_infer.tflite" ]; then
    model_size=$(du -h "$PROJECT_DIR/models/model_float32_infer.tflite" | cut -f1)
    echo "  ✓ Float32 model found: $model_size (backup)"
else
    echo "  ⚠️  Float32 model not found (optional)"
fi
echo ""

# ============================================================
# STEP 4: Create systemd service file
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  STEP 4: Creating Systemd Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SERVICE_FILE="/etc/systemd/system/orangebox.service"

sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Orange Box - Intelligent Waste Classification System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="DISPLAY=:0"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 $PROJECT_DIR/main.py --model $PROJECT_DIR/models/model_quant_infer.tflite --camera 0
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created: $SERVICE_FILE"
echo ""

# ============================================================
# STEP 5: Enable dan start service
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 STEP 5: Enabling Auto-Start Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service untuk auto-start saat boot
sudo systemctl enable orangebox.service

echo "✅ Service enabled for auto-start on boot"
echo ""

# ============================================================
# STEP 6: Test configuration
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 STEP 6: Testing Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verify service file
if systemctl list-unit-files | grep -q orangebox.service; then
    echo "✅ Service registered successfully"
else
    echo "❌ Service registration failed"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Quick Commands:"
echo ""
echo "   Start service:"
echo "   $ sudo systemctl start orangebox"
echo ""
echo "   Stop service:"
echo "   $ sudo systemctl stop orangebox"
echo ""
echo "   View logs:"
echo "   $ sudo journalctl -u orangebox -f"
echo ""
echo "   Check status:"
echo "   $ sudo systemctl status orangebox"
echo ""
echo "   Disable auto-start:"
echo "   $ sudo systemctl disable orangebox"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$GPS_SETUP_DONE" = true ]; then
    echo "⚠️  REBOOT DIPERLUKAN untuk apply GPS settings"
    echo ""
    echo "Setelah reboot:"
    echo "  1. Test GPS: bash scripts/test_gps.sh"
    echo "  2. Start OrangeBox: sudo systemctl start orangebox"
    echo ""
    read -p "Reboot sekarang? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Rebooting..."
        sudo reboot
    else
        echo "Reboot nanti dengan: sudo reboot"
    fi
else
    echo "💡 Service akan otomatis jalan setelah Raspberry Pi reboot!"
    echo "   Untuk start sekarang, jalankan: sudo systemctl start orangebox"
fi
echo ""
