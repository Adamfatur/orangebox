#!/bin/bash

# ============================================================
# Orange Box - Service Control Script
# ============================================================
# Script helper untuk mengontrol Orange Box service
# ============================================================

case "$1" in
    start)
        echo "🚀 Starting Orange Box service..."
        sudo systemctl start orangebox
        echo "✅ Service started"
        sudo systemctl status orangebox --no-pager
        ;;
    
    stop)
        echo "⏹️  Stopping Orange Box service..."
        sudo systemctl stop orangebox
        echo "✅ Service stopped"
        ;;
    
    restart)
        echo "🔄 Restarting Orange Box service..."
        sudo systemctl restart orangebox
        echo "✅ Service restarted"
        sudo systemctl status orangebox --no-pager
        ;;
    
    status)
        sudo systemctl status orangebox --no-pager
        ;;
    
    logs)
        echo "📋 Showing Orange Box logs (Ctrl+C to exit)..."
        sudo journalctl -u orangebox -f
        ;;
    
    enable)
        echo "⚙️  Enabling Orange Box auto-start..."
        sudo systemctl enable orangebox
        echo "✅ Auto-start enabled"
        ;;
    
    disable)
        echo "⚙️  Disabling Orange Box auto-start..."
        sudo systemctl disable orangebox
        echo "✅ Auto-start disabled"
        ;;
    
    *)
        echo ""
        echo "╔══════════════════════════════════════════════════════════════╗"
        echo "║          🧡 ORANGE BOX - SERVICE CONTROL 🧡                  ║"
        echo "╚══════════════════════════════════════════════════════════════╝"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|enable|disable}"
        echo ""
        echo "Commands:"
        echo "  start    - Start Orange Box service"
        echo "  stop     - Stop Orange Box service"
        echo "  restart  - Restart Orange Box service"
        echo "  status   - Show service status"
        echo "  logs     - Show live logs (Ctrl+C to exit)"
        echo "  enable   - Enable auto-start on boot"
        echo "  disable  - Disable auto-start"
        echo ""
        exit 1
        ;;
esac
