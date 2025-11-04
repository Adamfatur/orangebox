#!/bin/bash

# ============================================================
# Orange Box - Quick Deploy untuk Development
# ============================================================
# Script simpel untuk update dan restart service
# ============================================================

echo "🔄 Updating Orange Box..."

# Stop service
echo "⏹️  Stopping service..."
sudo systemctl stop orangebox 2>/dev/null || true

# Optional: Pull from git (uncomment jika pakai git)
# echo "📥 Pulling latest changes..."
# git pull

# Restart service
echo "🚀 Starting service..."
sudo systemctl start orangebox

# Show status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo systemctl status orangebox --no-pager
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Orange Box updated and restarted"
echo "   View logs: ./service.sh logs"
echo ""
