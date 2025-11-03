#!/bin/bash
# Test GPS NEO-6M
# Run: bash scripts/test_gps.sh

echo "==================================="
echo "Testing GPS NEO-6M"
echo "==================================="
echo ""

# Check if GPSD running
if systemctl is-active --quiet gpsd; then
    echo "✓ GPSD service running"
else
    echo "❌ GPSD service not running"
    echo "   Start dengan: sudo systemctl start gpsd"
    exit 1
fi

echo ""
echo "Waiting for GPS fix (max 60 seconds)..."
echo "Tip: Pastikan GPS outdoor dengan view ke langit"
echo ""

# Try to get fix for 60 seconds
timeout 60 gpspipe -w | grep -m 1 TPV | python3 -c "
import sys
import json

for line in sys.stdin:
    try:
        data = json.loads(line)
        if data.get('class') == 'TPV':
            lat = data.get('lat')
            lon = data.get('lon')
            mode = data.get('mode', 0)
            
            if lat and lon and mode >= 2:
                print(f'✅ GPS Fix Acquired!')
                print(f'   Latitude:  {lat:.6f}')
                print(f'   Longitude: {lon:.6f}')
                print(f'   Mode: {mode}D fix')
                print('')
                print('GPS module working correctly! 🎉')
                sys.exit(0)
    except:
        pass

print('❌ No GPS fix within 60 seconds')
print('   Check:')
print('   1. GPS antenna has clear view to sky (outdoor)')
print('   2. Hardware connections correct')
print('   3. Wait longer (cold start can take 2-3 minutes)')
sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "Try manual check:"
    echo "  cgps -s"
    echo ""
fi
