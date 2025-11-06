#!/bin/bash

# ============================================================
# Orange Box v1.3 - Service Uninstaller
# ============================================================
# Script untuk menghapus systemd service dan auto-start
# ============================================================

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║         🧡 ORANGE BOX - SERVICE UNINSTALLER 🧡               ║"
echo "║          Menghapus Auto-Start dari Sistem                   ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Cek jika dijalankan dengan sudo
if [ "$EUID" -eq 0 ]; then 
    echo "❌ JANGAN jalankan script ini dengan sudo!"
    echo "   Gunakan: ./deployment/uninstall_service.sh"
    exit 1
fi

SERVICE_FILE="/etc/systemd/system/orangebox.service"

# Cek apakah service ada
if [ ! -f "$SERVICE_FILE" ]; then
    echo "ℹ️  Service tidak ditemukan. Tidak ada yang perlu dihapus."
    exit 0
fi

echo "⚠️  WARNING: Ini akan menghapus Orange Box service dari sistem."
echo "   (File project TIDAK akan dihapus, hanya auto-start)"
echo ""
echo "   Lanjutkan? (y/n)"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Uninstall dibatalkan."
    exit 0
fi

echo ""

echo "⏹️  Stopping Orange Box service..."
sudo systemctl stop orangebox 2>/dev/null || true
echo "  ✓ Service stopped"
echo ""

echo "🚫 Disabling auto-start..."
sudo systemctl disable orangebox 2>/dev/null || true
echo "  ✓ Auto-start disabled"
echo ""

echo "🗑️  Removing service file..."
sudo rm -f "$SERVICE_FILE"
echo "  ✓ Service file removed"
echo ""

echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload
sudo systemctl reset-failed 2>/dev/null || true
echo "  ✓ Systemd daemon reloaded"
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              ✅ UNINSTALLATION COMPLETE! ✅                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Orange Box service telah dihapus dari sistem."
echo "   Aplikasi tidak akan jalan otomatis lagi saat boot."
echo ""
echo "💡 Untuk menjalankan manual:"
echo "   $ cd $(dirname "$(dirname "$(readlink -f "$0")")")"
echo "   $ python3 main.py"
echo ""
echo "🔄 Untuk install ulang auto-start:"
echo "   $ ./deployment/install_service.sh"
echo ""
