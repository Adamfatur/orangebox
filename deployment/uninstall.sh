#!/bin/bash

# ============================================================
# Orange Box - Uninstall Script
# ============================================================
# Script untuk menghapus Orange Box service dari sistem
# ============================================================

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║          🧡 ORANGE BOX - UNINSTALL SCRIPT 🧡                 ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "⚠️  WARNING: This will remove Orange Box service from system"
echo "   Project files will NOT be deleted."
echo ""
echo "   Continue? (y/n)"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""
echo "🗑️  Removing Orange Box service..."
echo ""

# Stop service jika running
if systemctl is-active --quiet orangebox; then
    echo "⏹️  Stopping service..."
    sudo systemctl stop orangebox
    echo "✅ Service stopped"
fi

# Disable service
if systemctl is-enabled --quiet orangebox; then
    echo "⚙️  Disabling auto-start..."
    sudo systemctl disable orangebox
    echo "✅ Auto-start disabled"
fi

# Remove service file
if [ -f /etc/systemd/system/orangebox.service ]; then
    echo "🗑️  Removing service file..."
    sudo rm /etc/systemd/system/orangebox.service
    echo "✅ Service file removed"
fi

# Reload systemd
sudo systemctl daemon-reload
sudo systemctl reset-failed

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Orange Box service has been uninstalled"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Project files are still in: $(pwd)"
echo "   To remove completely, delete this directory manually:"
echo "   $ rm -rf $(pwd)"
echo ""
