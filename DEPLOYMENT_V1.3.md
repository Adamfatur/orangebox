# 🚀 OrangeBox v1.3 - Deployment Checklist

## Version 1.3 - Bin Capacity Monitoring Integration

### ✅ Checklist Instalasi Raspberry Pi 5

#### 1. Hardware Setup

**Sensor Ultrasonic HC-SR04 (2 unit):**
- [ ] BIN A: TRIG→GPIO23, ECHO→GPIO24 (dengan voltage divider!)
- [ ] BIN B: TRIG→GPIO5, ECHO→GPIO6 (dengan voltage divider!)
- [ ] VCC→5V, GND→GND untuk kedua sensor
- [ ] Verifikasi voltage divider: 1kΩ + 2kΩ untuk ECHO pin

**Servo System (7 servos):**
- [ ] 4 Corner servos: CH 0,2,4,6 (MG996R positional)
- [ ] 2 Lock servos: CH 8,10 (MG996R positional)
- [ ] 1 Selector servo: CH 12 (MG996R positional)
- [ ] PCA9685 connected via I2C (address 0x40)
- [ ] Power supply: 5V 10A terpisah untuk servos

**Kamera:**
- [ ] USB webcam atau Pi Camera Module connected
- [ ] Test: `v4l2-ctl --list-devices`

---

#### 2. Software Installation

```bash
# Clone repository
git clone https://github.com/Adamfatur/orangebox.git
cd orangebox

# Run installer
./install.sh

# Installer akan otomatis:
# ✓ Install gpiozero, blynk-library-python
# ✓ Setup virtual environment
# ✓ Configure GPIO/I2C/SPI
# ✓ Detect camera
```

---

#### 3. Configuration

**Edit `config.py`:**

```python
# Platform
PLATFORM = 'rpi'  # Auto-set oleh installer

# Bin Monitoring
ENABLE_BIN_MONITORING = True

# Sensor pins (default sudah OK, ubah jika berbeda)
BIN_A_SENSOR_TRIG = 23
BIN_A_SENSOR_ECHO = 24
BIN_B_SENSOR_TRIG = 5
BIN_B_SENSOR_ECHO = 6

# Calibration - WAJIB DIUKUR!
BIN_EMPTY_DISTANCE_CM = 80.0  # Ukur jarak sensor ke dasar tong kosong
BIN_FULL_DISTANCE_CM = 5.0    # Ukur jarak sensor ke permukaan sampah penuh
BIN_FULL_THRESHOLD_PERCENT = 85.0  # Threshold "penuh"

# Blynk IoT
BLYNK_AUTH_TOKEN = 'YOUR_TOKEN_HERE'  # Dari blynk.cloud
```

---

#### 4. Blynk Dashboard Setup

1. **Create Account:**
   - Go to https://blynk.cloud
   - Sign up (free tier: 2 devices, unlimited datastreams)

2. **Create Template:**
   - Name: "OrangeBox Monitoring"
   - Hardware: Raspberry Pi
   - Connection: WiFi

3. **Add Datastreams:**
   - V3: BIN A Level (0-100, %)
   - V4: BIN B Level (0-100, %)

4. **Add Widgets:**
   - 2x Gauge: Link to V3 and V4
   - (Optional) 2x LED: Show if bin full

5. **Get Auth Token:**
   - Template Settings → Device → Auth Token
   - Copy to `config.py`

---

#### 5. Calibration

**Step 1: Measure Empty Bins**
```bash
# Test sensor readings
.venv/bin/python3 scripts/test_bin_monitor.py --sensors-only

# Place empty bins
# Read distance for both bins
# Set BIN_EMPTY_DISTANCE_CM = <reading>
```

**Step 2: Measure Full Bins**
```bash
# Fill bins to maximum capacity
# Read distance again
# Set BIN_FULL_DISTANCE_CM = <reading>
```

**Step 3: Verify**
```bash
# Run full test (30 seconds)
.venv/bin/python3 scripts/test_bin_monitor.py

# Expected: readings match actual fill level
# Adjust calibration if needed
```

---

#### 6. Testing

**Test Individual Components:**

```bash
# Test sensors only (no Blynk)
.venv/bin/python3 scripts/test_bin_monitor.py --sensors-only

# Test with Blynk integration
.venv/bin/python3 scripts/test_bin_monitor.py

# Test servos
.venv/bin/python3 scripts/test_seven_servo.py

# Test camera
.venv/bin/python3 main.py --test
```

**Expected Output (Bin Monitor):**
```
[BinMonitor] ✓ BIN A sensor initialized
[BinMonitor] ✓ BIN B sensor initialized
[BinMonitor] ✓ Blynk connected
[BinMonitor] 🔄 Monitoring thread started

[ 1s] ✅ | BIN A:  12.3% 🟢 OK   | BIN B:  45.6% 🟢 OK
[ 2s] ✅ | BIN A:  13.1% 🟢 OK   | BIN B:  46.2% 🟢 OK
```

---

#### 7. Run Main System

**Manual Start:**
```bash
# Start with bin monitoring
.venv/bin/python3 main.py

# Expected: System shows bin levels on display
# System will block sorting if bin ≥85% full
```

**Auto-Start on Boot:**
```bash
# Copy service file
sudo cp deployment/orangebox.service.template /etc/systemd/system/orangebox.service

# Edit paths if needed
sudo nano /etc/systemd/system/orangebox.service

# Enable and start
sudo systemctl enable orangebox.service
sudo systemctl start orangebox.service

# Check status
sudo systemctl status orangebox.service

# View logs
sudo journalctl -u orangebox.service -f
```

---

#### 8. Verification Checklist

**System Should:**
- [ ] Display "BIN A: X% | BIN B: X%" on camera preview
- [ ] Update Blynk dashboard every 5 seconds
- [ ] Show warning "BIN X FULL" when level ≥85%
- [ ] BLOCK sorting if target bin is full
- [ ] Resume normal operation after bin emptied

**Test Scenarios:**

1. **Normal Operation:**
   - [ ] Place waste → classified → sorted to correct bin
   - [ ] Bin levels update on display and Blynk

2. **Bin Full:**
   - [ ] Fill bin to >85%
   - [ ] Place waste → classified → see "BIN FULL" warning
   - [ ] Verify NO sorting happens
   - [ ] Empty bin → verify system resumes

3. **Network Loss:**
   - [ ] Disconnect WiFi
   - [ ] System continues working (local monitoring)
   - [ ] Blynk reconnects when WiFi restored

---

#### 9. Troubleshooting

**Sensor Not Working:**
```bash
# Check GPIO permissions
groups $USER | grep gpio

# If not in group:
sudo usermod -a -G gpio $USER
# Logout and login

# Test sensor manually
.venv/bin/python3 -c "
from gpiozero import DistanceSensor
s = DistanceSensor(echo=24, trigger=23)
print(f'Distance: {s.distance * 100:.1f} cm')
s.close()
"
```

**Blynk Not Connecting:**
```bash
# Verify internet
ping blynk.cloud

# Check token in config.py
grep BLYNK_AUTH_TOKEN config.py

# Test connection
.venv/bin/python3 -c "
import BlynkLib
blynk = BlynkLib.Blynk('YOUR_TOKEN', server='blynk.cloud', port=8080)
print('Connected!')
"
```

**Invalid Readings:**
```bash
# Check sensor mounting (must be perpendicular)
# Verify voltage divider on ECHO pin
# Adjust calibration values in config.py
```

---

#### 10. Maintenance

**Daily:**
- [ ] Check Blynk dashboard for bin levels
- [ ] Verify system logs: `sudo journalctl -u orangebox.service -n 50`

**Weekly:**
- [ ] Empty bins when >85%
- [ ] Clean sensor faces (dust affects accuracy)

**Monthly:**
- [ ] Verify calibration (readings match actual levels)
- [ ] Check sensor wiring

---

## Integration Details

### Automatic Integration Points

1. **MainController Initialization:**
   ```python
   self.bin_monitor = BinMonitor(enable_blynk=True)
   self.bin_monitor.start_monitoring()
   ```

2. **Pre-Sorting Check:**
   ```python
   if self.bin_monitor.is_bin_full(bin_name):
       # Show warning, abort sorting
       return State.IDLE
   ```

3. **Display Integration:**
   - Idle state shows bin levels
   - Full bins marked with 🔴 icon
   - Warning popup if sorting blocked

4. **Cleanup:**
   ```python
   self.bin_monitor.cleanup()  # Stops monitoring, closes sensors
   ```

### Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `ENABLE_BIN_MONITORING` | `True` | Master enable/disable |
| `BIN_FULL_THRESHOLD_PERCENT` | `85.0` | When to consider bin "full" |
| `BIN_MONITOR_UPDATE_INTERVAL` | `5.0` | Seconds between readings |
| `BIN_MONITOR_VERBOSE` | `False` | Print every reading |
| `BLYNK_AUTH_TOKEN` | `''` | Empty = local only |

---

## Files Modified/Added

### New Files:
- ✅ `src/core/bin_monitor.py` - Main monitoring class
- ✅ `scripts/test_bin_monitor.py` - Test script
- ✅ `docs/BIN_MONITORING_GUIDE.md` - Complete guide

### Modified Files:
- ✅ `config.py` - Added bin monitoring settings
- ✅ `src/core/main_controller.py` - Integrated bin checks
- ✅ `requirements.txt` - Added blynk-library-python
- ✅ `install.sh` - Auto-install Blynk
- ✅ `README.md` - Updated to v1.3

---

## Support

- **Documentation:** See `docs/BIN_MONITORING_GUIDE.md`
- **Issues:** https://github.com/Adamfatur/orangebox/issues
- **Test Script:** `scripts/test_bin_monitor.py`

---

## License

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
