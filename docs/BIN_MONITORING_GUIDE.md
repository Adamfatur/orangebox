# 📊 Bin Capacity Monitoring System - Setup Guide

## Overview

Sistem monitoring kapasitas tong sampah terintegrasi dengan OrangeBox untuk mencegah sorting saat bin penuh.

**Features:**
- ✅ Real-time monitoring 2 tong (BIN A & BIN B) dengan sensor HC-SR04
- ✅ Auto-prevent sorting jika bin target sudah penuh (≥85%)
- ✅ Dashboard monitoring via Blynk IoT Cloud
- ✅ **Database logging** untuk history tracking dan alerting
- ✅ **GPS integration** untuk location tracking (optional)
- ✅ Background monitoring thread (non-blocking)
- ✅ Auto-start saat boot dengan systemd service

---

## Hardware Requirements

### Sensor Ultrasonic HC-SR04 (2 unit)

| Component | Specification |
|-----------|--------------|
| Model | HC-SR04 Ultrasonic Distance Sensor |
| Operating Voltage | 5V DC |
| Max Range | 4m (400cm) |
| Min Range | 2cm |
| Measuring Angle | 15° |
| Trigger Input | TTL pulse 10μs |
| Echo Output | TTL signal |

### Pin Connections

#### BIN A (Organic) - Sensor 1
```
HC-SR04      →  Raspberry Pi 5
─────────────────────────────────
VCC          →  5V (Pin 2 or 4)
GND          →  GND (Pin 6, 9, 14, 20, 25, 30, 34, 39)
TRIG         →  GPIO 23 (Pin 16)
ECHO         →  GPIO 24 (Pin 18)
```

#### BIN B (Anorganic) - Sensor 2
```
HC-SR04      →  Raspberry Pi 5
─────────────────────────────────
VCC          →  5V (Pin 2 or 4)
GND          →  GND (Pin 6, 9, 14, 20, 25, 30, 34, 39)
TRIG         →  GPIO 27 (Pin 13)
ECHO         →  GPIO 22 (Pin 15)
```

**⚠️ IMPORTANT:** 
- DO NOT connect ECHO directly to GPIO! Use voltage divider (5V → 3.3V)
- Or use HC-SR04 module with built-in level shifter
- Raspberry Pi GPIO is 3.3V tolerant!
- GPIO 27/22 chosen to avoid I2C (GPIO 2/3) and UART (GPIO 14/15) conflicts

### Voltage Divider Circuit (if needed)

```
     ECHO (5V)
        │
       1kΩ
        │
        ├─────→ GPIO (3.3V)
        │
       2kΩ
        │
       GND
```

---

## Software Installation

### 1. Automatic Installation (Recommended)

```bash
# Clone repository
git clone https://github.com/Adamfatur/orangebox.git
cd orangebox

# Run installer (auto-detects platform and installs dependencies)
./install.sh
```

Installer will automatically:
- ✅ Install `gpiozero` and `blynk-library-python`
- ✅ Configure bin monitoring settings
- ✅ Setup systemd service for auto-start

### 2. Manual Installation

```bash
# Install dependencies
.venv/bin/pip install gpiozero blynk-library-python

# Verify installation
.venv/bin/python3 -c "from gpiozero import DistanceSensor; import BlynkLib; print('✅ OK')"
```

---

## Configuration

Edit `config.py`:

```python
# ============================================
# BIN CAPACITY MONITORING
# ============================================

# Enable/disable monitoring
ENABLE_BIN_MONITORING = True  # Set False to disable

# Sensor GPIO pins
BIN_A_SENSOR_TRIG = 23  # BIN A (Organic)
BIN_A_SENSOR_ECHO = 24
BIN_B_SENSOR_TRIG = 27  # BIN B (Anorganic) - Aman, tidak bentrok dengan I2C/UART
BIN_B_SENSOR_ECHO = 22  # GPIO 27/22 menghindari konflik dengan servo & GPS

# Calibration (measure your bin dimensions!)
BIN_EMPTY_DISTANCE_CM = 80.0      # Distance when empty (0%)
BIN_FULL_DISTANCE_CM = 5.0        # Distance when full (100%)
BIN_FULL_THRESHOLD_PERCENT = 85.0 # Threshold for "FULL" warning

# Blynk IoT configuration
BLYNK_AUTH_TOKEN = 'YOUR_TOKEN_HERE'  # Get from blynk.cloud
BLYNK_VPIN_BIN_A = 3  # Virtual pin for BIN A gauge
BLYNK_VPIN_BIN_B = 4  # Virtual pin for BIN B gauge

# Update interval
BIN_MONITOR_UPDATE_INTERVAL = 5.0  # Seconds (Blynk cloud updates)

# Database logging
BIN_DB_LOG_INTERVAL = 60.0  # Seconds (database logging interval)
BIN_WARNING_THRESHOLD_PERCENT = 70.0  # Warning threshold

# GPS Integration (optional)
ENABLE_GPS = False  # Set True if GPS hardware connected
```

---

## Calibration Steps

### Step 1: Measure Empty Bin

1. Remove all waste from bin
2. Measure distance from sensor to bottom of bin
3. Set `BIN_EMPTY_DISTANCE_CM` to this value

**Example:** Sensor mounted 80cm above bin bottom → `BIN_EMPTY_DISTANCE_CM = 80.0`

### Step 2: Measure Full Bin

1. Fill bin to maximum capacity
2. Measure distance from sensor to top of waste
3. Set `BIN_FULL_DISTANCE_CM` to this value

**Example:** Full bin is 5cm from sensor → `BIN_FULL_DISTANCE_CM = 5.0`

### Step 3: Set Threshold

Decide when bin should be considered "FULL":

```python
BIN_FULL_THRESHOLD_PERCENT = 85.0  # 85% full = warning
```

### Step 4: Test Calibration

```bash
# Run test script
.venv/bin/python3 -c "from src.core.bin_monitor import test_bin_monitor; test_bin_monitor()"
```

Place objects in/out of bins and verify readings are accurate.

---

## Blynk IoT Dashboard Setup

### 1. Create Blynk Account

1. Go to https://blynk.cloud
2. Sign up for free account
3. Create new Template: "OrangeBox Monitoring"

### 2. Add Widgets

Add 2 **Gauge** widgets to dashboard:

**BIN A (Organic):**
- Datastream: Virtual Pin V3
- Min: 0
- Max: 100
- Label: "BIN A - Organic (%)"
- Color: Green

**BIN B (Anorganic):**
- Datastream: Virtual Pin V4
- Min: 0
- Max: 100
- Label: "BIN B - Anorganic (%)"
- Color: Blue

### 3. Get Auth Token

1. Go to Template Settings → Device Info
2. Copy **Auth Token**
3. Paste to `config.py`:

```python
BLYNK_AUTH_TOKEN = 'RxBhkOBj0NkeyKRLCNWoaqb8hWy9mnFZ'
```

### 4. Deploy to Device

1. Create new Device from Template
2. Dashboard will auto-populate with widgets
3. System will auto-connect when running

---

## Running the System

### Manual Start

```bash
# Start main system (includes bin monitoring)
.venv/bin/python3 main.py
```

### Test Bin Monitor Only

```bash
# Standalone test (30 seconds)
.venv/bin/python3 src/core/bin_monitor.py
```

Expected output:
```
[BinMonitor] ╔════════════════════════════════════════════════╗
[BinMonitor] ║   Initializing Bin Capacity Monitor          ║
[BinMonitor] ╚════════════════════════════════════════════════╝
[BinMonitor] ✓ BIN A sensor initialized
[BinMonitor] ✓ BIN B sensor initialized
[BinMonitor] ✓ Blynk connected
[BinMonitor] 🔄 Monitoring thread started

[ 1s] BIN A:  12.3% 🟢 OK | BIN B:  45.6% 🟢 OK
[ 2s] BIN A:  13.1% 🟢 OK | BIN B:  46.2% 🟢 OK
...
```

### Auto-Start on Boot

```bash
# Install systemd service
sudo cp deployment/orangebox.service.template /etc/systemd/system/orangebox.service

# Edit service file (update paths if needed)
sudo nano /etc/systemd/system/orangebox.service

# Enable auto-start
sudo systemctl enable orangebox.service

# Start service now
sudo systemctl start orangebox.service

# Check status
sudo systemctl status orangebox.service

# View logs
sudo journalctl -u orangebox.service -f
```

---

## How It Works

### 1. Background Monitoring

- Thread runs every 5 seconds (configurable)
- Reads both sensors simultaneously
- Converts distance → percentage
- Updates Blynk cloud dashboard

### 2. Pre-Sorting Check

When waste is classified:

```python
# MainController automatically checks bin capacity
if bin_monitor.is_bin_full('A'):  # BIN A ≥ 85%
    print("⚠️  BIN A FULL - SORTING ABORTED")
    # Show warning on display
    # Return to IDLE without sorting
else:
    # Proceed with normal sorting
    servo_hw.sort_to_bin_a()
```

### 3. Real-time Display

System shows bin levels on camera preview:
```
⚪ Standby - No Object
BIN A: 23% 🟢 | BIN B: 87% 🔴 FULL
```

---

## Troubleshooting

### Sensor Not Detected

**Symptom:** "Sensor initialization failed"

**Solutions:**
1. Check wiring (VCC, GND, TRIG, ECHO)
2. Verify voltage divider on ECHO pin
3. Test sensor manually:

```bash
.venv/bin/python3 -c "
from gpiozero import DistanceSensor
sensor = DistanceSensor(echo=24, trigger=23)
print(f'Distance: {sensor.distance * 100:.1f} cm')
sensor.close()
"
```

### Invalid Readings (0% or jumpy)

**Symptom:** Readings fluctuate wildly or stuck at 0%

**Solutions:**
1. Check sensor mounting (must be perpendicular to surface)
2. Verify nothing blocking sensor view
3. Adjust `BIN_EMPTY_DISTANCE_CM` and `BIN_FULL_DISTANCE_CM`
4. Increase `BIN_MONITOR_UPDATE_INTERVAL` to 10 seconds

### Blynk Not Connecting

**Symptom:** "Blynk initialization failed"

**Solutions:**
1. Verify Auth Token in `config.py`
2. Check internet connection:
   ```bash
   ping blynk.cloud
   ```
3. Restart Blynk service:
   ```bash
   sudo systemctl restart orangebox.service
   ```

### GPIO Permission Error

**Symptom:** "Permission denied" when accessing GPIO

**Solutions:**
```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Logout and login again
```

---

## API Reference

### BinMonitor Class

```python
from src.core.bin_monitor import BinMonitor

# Initialize
monitor = BinMonitor(enable_blynk=True)

# Start monitoring
monitor.start_monitoring()

# Check bin level
level_a = monitor.get_bin_level('A')  # Returns: 0.0-100.0
level_b = monitor.get_bin_level('B')

# Check if full
is_full = monitor.is_bin_full('A')  # Returns: True/False

# Get complete status
status = monitor.get_status_dict()
# {
#   'bin_a_level': 23.4,
#   'bin_b_level': 87.6,
#   'bin_a_full': False,
#   'bin_b_full': True,
#   'last_update': 1699265432.123,
#   'monitoring_active': True
# }

# Stop monitoring
monitor.stop_monitoring()

# Cleanup
monitor.cleanup()
```

---

## Performance Optimization

### Reduce CPU Usage

```python
# Increase update interval (less frequent checks)
BIN_MONITOR_UPDATE_INTERVAL = 10.0  # 10 seconds

# Disable verbose logging
BIN_MONITOR_VERBOSE = False
```

### Reduce Network Usage (Blynk)

```python
# Increase update interval
BIN_MONITOR_UPDATE_INTERVAL = 15.0  # 15 seconds

# Or disable Blynk entirely (local only)
ENABLE_BIN_MONITORING = True  # Still monitors locally
# Just leave BLYNK_AUTH_TOKEN empty
```

---

## Integration with Main System

The bin monitoring system is **automatically integrated** into `MainController`:

```python
# In MainController.__init__():
self.bin_monitor = BinMonitor(enable_blynk=True)
self.bin_monitor.start_monitoring()

# In _state_classifying():
if self.bin_monitor.is_bin_full(bin_name):
    # ABORT sorting, show warning
    return State.IDLE
else:
    # Proceed with sorting
    return State.SORTING_A  # or SORTING_B
```

**Zero configuration needed** - just enable in `config.py`!

---

## Maintenance

### Regular Checks

1. **Monthly:** Clean sensors (dust can affect accuracy)
2. **Weekly:** Verify bin levels match Blynk dashboard
3. **As needed:** Recalibrate if bins are replaced

### Sensor Cleaning

```
1. Power off system
2. Gently wipe sensor face with dry microfiber cloth
3. Check for physical damage
4. Power on and verify readings
```

---

## License

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.

---

## Support

- **Issues:** https://github.com/Adamfatur/orangebox/issues
- **Documentation:** See `README.md` and `docs/`
- **Email:** support@orangebox.example.com
