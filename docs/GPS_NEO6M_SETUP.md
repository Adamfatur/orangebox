# 🛰️ GPS Neo-6M Setup Guide - OrangeBox

## Overview

Panduan setup GPS module U-blox NEO-6M-0-001 untuk tracking lokasi OrangeBox.

**⚠️ IMPORTANT: GPS is OPTIONAL!**
- GPS **disabled by default** (`ENABLE_GPS = False`)
- Sistem berjalan normal tanpa GPS
- Enable hanya jika Anda punya hardware GPS dan ingin tracking lokasi

---

## Hardware: U-blox NEO-6M-0-001

### Spesifikasi

| Feature | Specification |
|---------|--------------|
| **Model** | NEO-6M-0-001 |
| **Chipset** | U-blox NEO-6M |
| **Channels** | 50 |
| **Sensitivity** | -161 dBm |
| **Update Rate** | 1-10 Hz (default: 1 Hz) |
| **UART Baudrate** | 9600 bps (default) |
| **Protocol** | NMEA 0183 |
| **Voltage** | 3.3V - 5V |
| **Cold Start** | 26s (first fix) |
| **Warm Start** | 1s (subsequent fix) |
| **Accuracy** | 2.5m CEP |

### Pin Connections

```
┌─────────────────────────────────────────────┐
│  NEO-6M-0-001   →   Raspberry Pi 5         │
├─────────────────────────────────────────────┤
│  VCC (3-5V)     →   3.3V (Pin 1)           │
│                  or 5V (Pin 2)              │
│  GND            →   GND (Pin 6, 9, 14, ...) │
│  TX (Transmit)  →   GPIO15 RX (Pin 10)     │
│  RX (Receive)   →   GPIO14 TX (Pin 8)      │
│  PPS (optional) →   GPIO18 (Pin 12)        │
└─────────────────────────────────────────────┘
```

**Diagram:**
```
    NEO-6M Module          Raspberry Pi 5
    ┌───────────┐         ┌──────────────┐
    │           │         │              │
    │  VCC ●────┼─────────┼──● Pin 1 (3.3V)
    │  GND ●────┼─────────┼──● Pin 6 (GND)
    │   TX ●────┼─────────┼──● Pin 10 (GPIO15/RX)
    │   RX ●────┼─────────┼──● Pin 8 (GPIO14/TX)
    │  PPS ●    │         │
    │           │         │
    └───────────┘         └──────────────┘
         LED
          ●
```

---

## Installation

### 1. Hardware Setup

1. **Connect GPS module** to Raspberry Pi 5 (see pinout above)
2. **Position antenna** outdoors or near window for satellite signal
3. **Power on** - LED should start blinking when searching for satellites

### 2. Enable UART

```bash
# Open Raspberry Pi configuration
sudo raspi-config

# Navigate to:
# 3 Interface Options → P6 Serial Port

# Answer the prompts:
# "Would you like a login shell accessible over serial?" → NO
# "Would you like the serial port hardware to be enabled?" → YES

# Reboot
sudo reboot
```

### 3. Install GPS Daemon (Optional but Recommended)

```bash
# Install gpsd
sudo apt-get update
sudo apt-get install -y gpsd gpsd-clients

# Configure gpsd
sudo nano /etc/default/gpsd

# Edit the file:
DEVICES="/dev/serial0"
GPSD_OPTIONS="-n"
USBAUTO="false"

# Restart gpsd
sudo systemctl restart gpsd
sudo systemctl enable gpsd
```

### 4. Test GPS Connection

```bash
# Test 1: Raw NMEA data
cat /dev/serial0

# Expected output (NMEA sentences):
# $GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
# $GPGSV,2,1,08,01,40,083,46,02,17,308,41,12,07,344,39,14,22,228,45*75
# ...

# Test 2: Using gpspipe (if gpsd installed)
gpspipe -r

# Test 3: Check GPS status
cgps -s

# Press q to quit
```

---

## Configuration

Edit `config.py`:

```python
# ============================================
# GPS SETTINGS
# ============================================

# Enable GPS (default: False)
# Set to True ONLY if GPS hardware is connected
ENABLE_GPS = True  # ← Change to True

# GPS update interval (seconds)
GPS_UPDATE_INTERVAL = 300  # 5 minutes

# GPS Hardware Settings
GPS_SERIAL_PORT = '/dev/serial0'  # UART port
GPS_BAUDRATE = 9600               # Default for NEO-6M
GPS_READ_TIMEOUT = 5              # Seconds
GPS_MIN_SATELLITES = 4            # Min satellites for valid fix
GPS_USE_GPSD = True               # Use gpsd daemon (recommended)

# Timeouts
GPS_COLD_START_TIMEOUT = 30       # First fix (26s typical)
GPS_WARM_START_TIMEOUT = 5        # Subsequent fix (1s typical)

# History logging
GPS_SAVE_HISTORY = True
GPS_HISTORY_FILE = 'data/location_history.jsonl'
```

---

## Usage

### Auto-Start with Main System

GPS automatically starts when `ENABLE_GPS = True`:

```bash
# Run main system
python3 main.py

# GPS will:
# 1. Initialize on startup
# 2. Wait for satellite fix (up to 30s)
# 3. Update location every 5 minutes
# 4. Log to database with waste classification data
# 5. Save history to location_history.jsonl
```

### Test GPS Only

```python
# Test script
from src.core.location_service import LocationService

# Initialize
gps = LocationService(
    platform='rpi',
    mock_location=None  # Use real GPS
)

# Start background updates
gps.start_background_update(update_interval=10)

# Get location
import time
time.sleep(35)  # Wait for first fix

location = gps.get_location()
print(f"Latitude: {location['latitude']}")
print(f"Longitude: {location['longitude']}")
print(f"Satellites: {location['satellites']}")
print(f"Accuracy: {location['accuracy']} meters")

# Stop
gps.stop_background_update()
```

---

## Troubleshooting

### Issue 1: No GPS Data

**Symptoms:**
- `cat /dev/serial0` shows nothing
- Error: "Failed to open GPS serial port"

**Solutions:**

1. **Check UART is enabled:**
   ```bash
   ls -l /dev/serial0
   # Should show: /dev/serial0 -> ttyAMA0
   ```

2. **Check permissions:**
   ```bash
   sudo usermod -a -G dialout $USER
   # Logout and login
   ```

3. **Verify wiring:**
   - TX (GPS) → RX (Pi GPIO15)
   - RX (GPS) → TX (Pi GPIO14)
   - **NOT** TX→TX or RX→RX!

4. **Check if Bluetooth is interfering:**
   ```bash
   # Disable Bluetooth UART (if not needed)
   sudo nano /boot/config.txt
   # Add: dtoverlay=disable-bt
   sudo systemctl disable hciuart
   sudo reboot
   ```

### Issue 2: No Satellite Fix

**Symptoms:**
- Data appears but no valid coordinates
- Satellites = 0

**Solutions:**

1. **Move GPS outdoors or near window**
   - GPS needs clear view of sky
   - Indoor operation very difficult

2. **Wait longer for cold start**
   - First fix can take 26-60 seconds
   - Subsequent fixes are faster (1-5s)

3. **Check LED status:**
   - **Blinking fast**: Searching for satellites
   - **Blinking slow (1Hz)**: GPS fix acquired
   - **Off**: No power or module error

4. **Verify antenna connection:**
   - Active antenna must be connected
   - Check antenna cable not damaged

### Issue 3: Inaccurate Location

**Symptoms:**
- Location jumps around
- Accuracy >10 meters

**Solutions:**

1. **Wait for more satellites:**
   ```python
   # Increase minimum satellites
   GPS_MIN_SATELLITES = 6  # Default: 4
   ```

2. **Check for multipath interference:**
   - Move away from buildings/trees
   - Avoid metal surfaces nearby

3. **Enable SBAS (if available):**
   - Some NEO-6M modules support SBAS/WAAS
   - Improves accuracy to <2.5m

### Issue 4: gpsd Not Working

**Symptoms:**
- `cgps -s` shows "NO FIX"
- gpsd errors in logs

**Solutions:**

1. **Check gpsd configuration:**
   ```bash
   cat /etc/default/gpsd
   # Should have: DEVICES="/dev/serial0"
   ```

2. **Restart gpsd:**
   ```bash
   sudo killall gpsd
   sudo gpsd /dev/serial0 -F /var/run/gpsd.sock
   ```

3. **Check gpsd status:**
   ```bash
   sudo systemctl status gpsd
   journalctl -u gpsd -f
   ```

4. **Test with gpsmon:**
   ```bash
   gpsmon /dev/serial0
   ```

---

## Integration with Bin Monitoring

GPS data is automatically included in bin capacity logs when enabled:

```python
# Database: bin_capacity_logs table
{
  'device_id': 'orangebox-001',
  'timestamp': '2025-11-06 10:30:00',
  'bin_a_level': 45.2,
  'bin_b_level': 78.9,
  'location_latitude': -6.2088,    # ← From GPS
  'location_longitude': 106.8456,  # ← From GPS
  'bin_a_status': 'OK',
  'bin_b_status': 'WARNING'
}
```

**Query devices by location:**
```sql
SELECT 
  device_id,
  bin_a_level,
  bin_b_level,
  location_latitude,
  location_longitude
FROM bin_capacity_logs
WHERE location_latitude BETWEEN -6.3 AND -6.1
  AND location_longitude BETWEEN 106.7 AND 106.9
ORDER BY timestamp DESC
LIMIT 10;
```

---

## Performance Tips

### Reduce Power Consumption

```python
# Increase update interval (less frequent GPS reads)
GPS_UPDATE_INTERVAL = 600  # 10 minutes instead of 5
```

### Faster Fix Time

```python
# Use GPSD with network time assist (if available)
GPS_USE_GPSD = True

# Reduce timeout for warm starts
GPS_WARM_START_TIMEOUT = 2  # Down from 5s
```

### Improve Accuracy

```python
# Wait for more satellites
GPS_MIN_SATELLITES = 6  # Up from 4

# Add HDOP threshold (if implementing custom parser)
GPS_MAX_HDOP = 2.0  # Horizontal Dilution of Precision
```

---

## Advanced: Custom NMEA Parsing

If not using gpsd, parse NMEA sentences manually:

```python
import serial
import pynmea2

ser = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)

while True:
    line = ser.readline().decode('ascii', errors='replace')
    
    if line.startswith('$GPGGA'):  # GPS Fix Data
        msg = pynmea2.parse(line)
        
        lat = msg.latitude
        lon = msg.longitude
        sats = msg.num_sats
        quality = msg.gps_qual
        
        print(f"Lat: {lat}, Lon: {lon}, Sats: {sats}")
```

---

## Monitoring & Alerts

### Check GPS Status via Database

```sql
-- Get devices with GPS data
SELECT 
  device_id,
  COUNT(*) AS gps_records,
  MIN(timestamp) AS first_seen,
  MAX(timestamp) AS last_seen
FROM bin_capacity_logs
WHERE location_latitude IS NOT NULL
GROUP BY device_id;
```

### Alert on Missing GPS Data

```python
# In bin_monitor.py
if self.location_service:
    location = self.location_service.get_location()
    if not location or not location.get('latitude'):
        print("[BinMonitor] ⚠️  GPS fix lost - using last known location")
```

---

## Maintenance

### Weekly

- **Check satellite count:** Should be ≥4 consistently
- **Verify accuracy:** Should be <10m in open area
- **Clean antenna:** Remove dust/debris

### Monthly

- **Test GPS fix time:** Cold start should be <30s
- **Check data logs:** Verify continuous GPS data
- **Update firmware:** (if manufacturer provides updates)

---

## References

- **U-blox NEO-6 Datasheet:** https://www.u-blox.com/en/product/neo-6-series
- **NMEA Protocol:** https://www.gpsinformation.org/dale/nmea.htm
- **gpsd Documentation:** https://gpsd.gitlab.io/gpsd/
- **Raspberry Pi UART:** https://www.raspberrypi.com/documentation/computers/configuration.html#configure-uarts

---

## License

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
