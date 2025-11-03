#!/bin/bash
# Auto-setup U-blox NEO-6M GPS Module untuk Raspberry Pi
# Run: sudo bash scripts/setup_gps.sh

set -e

echo "==================================="
echo "OrangeBox - GPS NEO-6M Auto Setup"
echo "==================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Error: Script harus dijalankan dengan sudo"
    echo "   Run: sudo bash scripts/setup_gps.sh"
    exit 1
fi

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "❌ Error: Script ini hanya untuk Raspberry Pi"
    exit 1
fi

echo "✓ Running on Raspberry Pi"
echo ""

# Step 1: Enable UART
echo "📍 Step 1/5: Enable UART..."
if ! grep -q "enable_uart=1" /boot/firmware/config.txt; then
    echo "enable_uart=1" >> /boot/firmware/config.txt
    echo "  ✓ Added enable_uart=1"
else
    echo "  ✓ UART already enabled"
fi

# Step 2: Disable Bluetooth (free up UART)
echo ""
echo "📍 Step 2/5: Disable Bluetooth (untuk free UART)..."
if ! grep -q "dtoverlay=disable-bt" /boot/firmware/config.txt; then
    echo "dtoverlay=disable-bt" >> /boot/firmware/config.txt
    systemctl disable hciuart 2>/dev/null || true
    echo "  ✓ Bluetooth disabled"
else
    echo "  ✓ Bluetooth already disabled"
fi

# Step 3: Remove console from serial
echo ""
echo "📍 Step 3/5: Remove console dari serial..."
if grep -q "console=serial0" /boot/firmware/cmdline.txt; then
    sed -i 's/console=serial0,[0-9]\+ //' /boot/firmware/cmdline.txt
    echo "  ✓ Console removed dari serial"
else
    echo "  ✓ Console sudah tidak pakai serial"
fi

# Step 4: Install GPSD
echo ""
echo "📍 Step 4/5: Install GPSD & dependencies..."
apt-get update -qq
apt-get install -y gpsd gpsd-clients python3-gps

echo "  ✓ GPSD installed"

# Step 5: Configure GPSD
echo ""
echo "📍 Step 5/5: Configure GPSD..."
cat > /etc/default/gpsd <<EOF
# Default settings for gpsd (NEO-6M GPS Module)
START_DAEMON="true"
GPSD_OPTIONS="-n"
DEVICES="/dev/serial0"
USBAUTO="false"
EOF

echo "  ✓ GPSD configured"

# Enable and start GPSD
systemctl enable gpsd
systemctl restart gpsd

echo ""
echo "==================================="
echo "✅ GPS Setup Complete!"
echo "==================================="
echo ""
echo "Hardware Connection:"
echo "  GPS VCC → Pi Pin 4 (5V)"
echo "  GPS GND → Pi Pin 6 (GND)"
echo "  GPS TX  → Pi Pin 10 (GPIO15/RX)"
echo "  GPS RX  → Pi Pin 8  (GPIO14/TX)"
echo ""
echo "⚠️  REBOOT DIPERLUKAN untuk apply changes"
echo ""
echo "Setelah reboot, test GPS dengan:"
echo "  cgps -s"
echo ""
echo "GPS butuh 30-60 detik untuk first fix (outdoor)."
echo ""
read -p "Reboot sekarang? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Rebooting..."
    reboot
else
    echo "Reboot nanti dengan: sudo reboot"
fi
