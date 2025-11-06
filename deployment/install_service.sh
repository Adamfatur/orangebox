#!/bin/bash

# ============================================================
# Orange Box v1.3 - Auto-Start Service Installer
# ============================================================
# Script ini akan setup systemd service agar Orange Box
# berjalan otomatis saat Raspberry Pi boot/reboot
# ============================================================

set -e  # Exit on error

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║       🧡 ORANGE BOX v1.3 - SERVICE INSTALLER 🧡              ║"
echo "║         Setup Auto-Start pada Raspberry Pi 5                ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================
# Deteksi project directory
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Project directory: $PROJECT_DIR"
echo ""

# ============================================================
# Verifikasi di Raspberry Pi
# ============================================================
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  WARNING: Script ini dirancang untuk Raspberry Pi"
    echo "   Apakah Anda yakin ingin melanjutkan? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Installation dibatalkan."
        exit 1
    fi
fi

# ============================================================
# Cek user yang menjalankan
# ============================================================
if [ "$EUID" -eq 0 ]; then 
    echo "❌ JANGAN jalankan script ini dengan sudo!"
    echo "   Gunakan: ./deployment/install_service.sh"
    exit 1
fi

CURRENT_USER=$(whoami)
echo "👤 Running as user: $CURRENT_USER"
echo ""

# ============================================================
# Verifikasi file penting ada
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 STEP 1: Verifying Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Cek main.py
if [ ! -f "$PROJECT_DIR/main.py" ]; then
    echo "❌ Error: main.py not found in $PROJECT_DIR"
    exit 1
fi
echo "  ✓ main.py found"

# Cek virtual environment
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "   Please run: ./install.sh first"
    exit 1
fi
echo "  ✓ Virtual environment found"

# Cek Python dalam venv
if [ ! -f "$PROJECT_DIR/.venv/bin/python3" ]; then
    echo "❌ Error: Python3 not found in virtual environment"
    exit 1
fi
echo "  ✓ Python3 found in venv"

# Cek config.py
if [ ! -f "$PROJECT_DIR/config.py" ]; then
    echo "❌ Error: config.py not found"
    exit 1
fi
echo "  ✓ config.py found"

echo ""

# ============================================================
# Cek dan tambahkan user ke grup yang diperlukan
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👥 STEP 2: Setting Up User Permissions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Tambahkan user ke grup GPIO, I2C, SPI, Video, Dialout (serial/GPS)
for group in gpio i2c spi video dialout; do
    if ! groups "$CURRENT_USER" | grep -q "\b$group\b"; then
        sudo usermod -a -G "$group" "$CURRENT_USER"
        echo "  ✓ Added $CURRENT_USER to $group group"
    else
        echo "  ✓ Already in $group group"
    fi
done

echo ""
echo "  ℹ️  Note: Jika baru ditambahkan ke grup, logout/login atau reboot"
echo "     untuk mengaktifkan permissions."
echo ""

# ============================================================
# Buat systemd service file
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  STEP 3: Creating Systemd Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SERVICE_FILE="/etc/systemd/system/orangebox.service"
TEMPLATE_FILE="$SCRIPT_DIR/orangebox.service.template"

# Cek apakah template ada
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ Error: Template file not found: $TEMPLATE_FILE"
    exit 1
fi

# Buat service file dari template dengan substitusi variabel
sed -e "s|PROJECT_DIR|$PROJECT_DIR|g" \
    -e "s|User=pi|User=$CURRENT_USER|g" \
    -e "s|Group=pi|Group=$CURRENT_USER|g" \
    -e "s|/home/pi|/home/$CURRENT_USER|g" \
    "$TEMPLATE_FILE" | sudo tee "$SERVICE_FILE" > /dev/null

echo "  ✓ Service file created: $SERVICE_FILE"
echo ""

# ============================================================
# Reload systemd dan enable service
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 STEP 4: Enabling Auto-Start"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Reload systemd daemon
sudo systemctl daemon-reload
echo "  ✓ Systemd daemon reloaded"

# Stop service jika sedang running
sudo systemctl stop orangebox 2>/dev/null || true
echo "  ✓ Stopped existing service (if any)"

# Enable service untuk auto-start
sudo systemctl enable orangebox
echo "  ✓ Service enabled for auto-start on boot"

# Start service
sudo systemctl start orangebox
echo "  ✓ Service started"

echo ""

# ============================================================
# Verifikasi service running
# ============================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ STEP 5: Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

sleep 3  # Tunggu service start

if sudo systemctl is-active --quiet orangebox; then
    echo "  ✅ Service is ACTIVE and RUNNING"
    echo ""
    sudo systemctl status orangebox --no-pager --lines=10
else
    echo "  ❌ Service FAILED to start!"
    echo ""
    echo "  Checking logs:"
    sudo journalctl -u orangebox --no-pager --lines=20
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                  ✅ INSTALLATION COMPLETE! ✅                 ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🎉 Orange Box sekarang berjalan otomatis!"
echo ""
echo "📋 INFORMASI PENTING:"
echo "  • Service name: orangebox.service"
echo "  • Auto-start: ENABLED (akan jalan saat boot/reboot)"
echo "  • User: $CURRENT_USER"
echo "  • Working directory: $PROJECT_DIR"
echo ""
echo "🔧 PERINTAH BERGUNA:"
echo "  • Lihat status:       sudo systemctl status orangebox"
echo "  • Lihat logs:         sudo journalctl -u orangebox -f"
echo "  • Stop service:       sudo systemctl stop orangebox"
echo "  • Start service:      sudo systemctl start orangebox"
echo "  • Restart service:    sudo systemctl restart orangebox"
echo "  • Disable auto-start: sudo systemctl disable orangebox"
echo ""
echo "  Atau gunakan: ./deployment/service.sh {start|stop|restart|status|logs}"
echo ""
echo "📝 REBOOT TEST:"
echo "  Untuk test auto-start, reboot Raspberry Pi:"
echo "  $ sudo reboot"
echo ""
echo "  Setelah reboot, cek apakah service jalan otomatis:"
echo "  $ sudo systemctl status orangebox"
echo ""
echo "✨ Happy sorting! ✨"
echo ""
