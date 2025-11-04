#!/bin/bash

# ============================================================
# Orange Box - Health Check Script
# ============================================================
# Script untuk monitoring kesehatan system
# ============================================================

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          🧡 ORANGE BOX - HEALTH CHECK 🧡                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check service status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Service Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if systemctl is-active --quiet orangebox; then
    echo -e "${GREEN}✅ Service is running${NC}"
    uptime=$(systemctl show orangebox --property=ActiveEnterTimestamp --value)
    echo "   Started: $uptime"
else
    echo -e "${RED}❌ Service is NOT running${NC}"
    echo "   Run: sudo systemctl start orangebox"
fi

if systemctl is-enabled --quiet orangebox; then
    echo -e "${GREEN}✅ Auto-start is enabled${NC}"
else
    echo -e "${YELLOW}⚠️  Auto-start is disabled${NC}"
    echo "   Run: sudo systemctl enable orangebox"
fi

echo ""

# Check for recent errors
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Recent Logs (Last 10 lines)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo journalctl -u orangebox -n 10 --no-pager

echo ""

# Check resources
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💻 System Resources"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# CPU Temperature (Raspberry Pi)
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    temp=$(cat /sys/class/thermal/thermal_zone0/temp)
    temp=$(echo "scale=1; $temp / 1000" | bc)
    
    if (( $(echo "$temp > 80" | bc -l) )); then
        echo -e "${RED}🌡️  CPU Temp: ${temp}°C (HIGH!)${NC}"
    elif (( $(echo "$temp > 70" | bc -l) )); then
        echo -e "${YELLOW}🌡️  CPU Temp: ${temp}°C (Warm)${NC}"
    else
        echo -e "${GREEN}🌡️  CPU Temp: ${temp}°C${NC}"
    fi
fi

# Memory usage
mem_total=$(free -m | awk 'NR==2{print $2}')
mem_used=$(free -m | awk 'NR==2{print $3}')
mem_percent=$(echo "scale=1; $mem_used * 100 / $mem_total" | bc)
echo "💾 Memory: ${mem_used}MB / ${mem_total}MB (${mem_percent}%)"

# Disk usage
disk_usage=$(df -h / | awk 'NR==2{print $5}' | sed 's/%//')
disk_avail=$(df -h / | awk 'NR==2{print $4}')
if [ "$disk_usage" -gt 90 ]; then
    echo -e "${RED}💿 Disk: ${disk_usage}% used (Available: ${disk_avail}) - LOW!${NC}"
elif [ "$disk_usage" -gt 80 ]; then
    echo -e "${YELLOW}💿 Disk: ${disk_usage}% used (Available: ${disk_avail})${NC}"
else
    echo -e "${GREEN}💿 Disk: ${disk_usage}% used (Available: ${disk_avail})${NC}"
fi

# Check camera
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📷 Camera Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v vcgencmd &> /dev/null; then
    camera_status=$(vcgencmd get_camera 2>&1)
    if echo "$camera_status" | grep -q "detected=1"; then
        echo -e "${GREEN}✅ Camera detected${NC}"
    else
        echo -e "${YELLOW}⚠️  Camera not detected${NC}"
        echo "   Check cable connection or enable camera in raspi-config"
    fi
else
    echo "ℹ️  Camera check not available (not on Raspberry Pi)"
fi

# Check model file
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 Model & Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_FILE="$PROJECT_DIR/models/model_quant_infer.tflite"

if [ -f "$MODEL_FILE" ]; then
    model_size=$(du -h "$MODEL_FILE" | cut -f1)
    echo -e "${GREEN}✅ Model file found${NC} (Size: $model_size)"
else
    echo -e "${RED}❌ Model file not found!${NC}"
    echo "   Expected: $MODEL_FILE"
fi

# Restart count
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Service Restarts"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

restart_count=$(systemctl show orangebox -p NRestarts --value 2>/dev/null || echo "0")
echo "Total restarts since last boot: $restart_count"

if [ "$restart_count" -gt 5 ]; then
    echo -e "${YELLOW}⚠️  Service has restarted $restart_count times${NC}"
    echo "   Check logs for recurring errors: sudo journalctl -u orangebox -n 100"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Quick Actions:"
echo "   View logs:    ./service.sh logs"
echo "   Restart:      ./service.sh restart"
echo "   Full status:  ./service.sh status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
