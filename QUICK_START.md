# 🚀 QUICK START - OrangeBox v1.2 (7-Servo System)

## ⚡ Installation - ONE COMMAND!

```bash
bash install.sh
```

**Itu saja!** Script akan otomatis:
- ✅ Deteksi platform (macOS/Raspberry Pi 5)
- ✅ Install semua dependencies (TensorFlow Lite, OpenCV, PCA9685, dll)
- ✅ Setup virtual environment
- ✅ Enable I2C/Camera di Raspberry Pi
- ✅ Konfigurasi servo driver otomatis

---

## ▶️ Running - ONE COMMAND!

```bash
python3 main.py
```

Untuk mode test (tanpa model AI):
```bash
python3 main.py --test
```

---

## 🔧 Test Servo - ONE COMMAND!

```bash
source .venv/bin/activate
python3 scripts/test_seven_servo.py
```

Interactive menu:
- **1-7**: Test individual servo (Corner A/B/C/D, Lock L/R, Selector)
- **8**: Full BIN A sequence (ORGANIC)
- **9**: Full BIN B sequence (ANORGANIC)
- **0**: Show configuration

---

## 📋 Checklist Raspberry Pi 5

### 1. Hardware Setup
- [ ] PCA9685 terhubung ke I2C (GPIO 2/3)
- [ ] 7 servo terhubung ke PCA9685 CH0-6
- [ ] Power supply 5V 10A terpisah untuk servo
- [ ] Capacitor 1000μF di V+ dan GND
- [ ] Common ground RPi dan PSU servo
- [ ] Camera terhubung (USB atau Pi Camera)

### 2. Software Setup
```bash
# Check I2C enabled dan PCA9685 terdeteksi
i2cdetect -y 1
# Expected: 0x40 muncul

# Test camera
python3 -m src.core.camera_detector

# Run system
python3 main.py
```

---

## ⚙️ Configuration (Optional)

Edit `config.py` jika perlu adjust:

### Servo Channels
```python
SERVO_L1_CORNER_A_CHANNEL = 0    # Corner A
SERVO_L1_CORNER_B_CHANNEL = 1    # Corner B
SERVO_L1_CORNER_C_CHANNEL = 2    # Corner C
SERVO_L1_CORNER_D_CHANNEL = 3    # Corner D
SERVO_L1_LOCK_LEFT_CHANNEL = 4   # Lock Left
SERVO_L1_LOCK_RIGHT_CHANNEL = 5  # Lock Right
SERVO_L2_SELECTOR_CHANNEL = 6    # Selector
```

### Servo Angles (0-180° ONLY!)
```python
# Corner servos
SERVO_L1_CORNER_UP = 0          # Wadah terangkat
SERVO_L1_CORNER_DOWN = 90       # Wadah turun

# Lock servos
SERVO_L1_LOCK_LOCKED = 90       # Locked (horizontal)
SERVO_L1_LOCK_UNLOCKED = 0      # Unlocked (vertical)

# Selector servo
SERVO_L2_SELECTOR_NEUTRAL = 90  # Neutral
SERVO_L2_SELECTOR_BIN_A = 60    # Bin A (Organic)
SERVO_L2_SELECTOR_BIN_B = 120   # Bin B (Anorganic)
```

### Timing (Seconds)
```python
SERVO_DROP_DELAY = 0.3      # Setelah selector posisi
SERVO_FALL_TIME = 0.5       # Waktu wadah jatuh
SERVO_SLIDE_TIME = 0.5      # Waktu sampah meluncur
SERVO_LIFT_TIME = 0.3       # Waktu angkat wadah
SERVO_LOCK_DELAY = 0.1      # Setelah unlock/lock
SERVO_RESET_DELAY = 0.3     # Sebelum next cycle
```

---

## 🛡️ Safety Features

### ✅ Angle Validation
- **Semua angle LIMITED 0-180°** (prevent 360° rotation)
- Automatic validation sebelum servo move
- Error log jika angle invalid

### ✅ Power Management
- Lock servos **ONLY active saat lock/unlock** (~0.2s)
- PWM duty cycle = 0 setelah movement (no jitter)
- Parallel movement untuk efisiensi daya

### ✅ Error Handling
- Try-catch di setiap servo movement
- Graceful fallback ke simulation mode
- Emergency stop (Ctrl+C)

---

## 🐛 Troubleshooting

### Servo tidak bergerak
```bash
# 1. Check I2C
i2cdetect -y 1
# Expected: 0x40

# 2. Check config
python3 scripts/test_seven_servo.py
# Pilih 0 untuk show config

# 3. Test individual servo
# Pilih 1-7 untuk test masing-masing servo
```

### Servo berputar liar (360°)
- ✅ **PROTECTED!** Code has angle validation (0-180° only)
- Check calibration di config.py:
```python
SERVOKIT_MIN_PULSE_MICROS = 500
SERVOKIT_MAX_PULSE_MICROS = 2500
SERVOKIT_ACTUATION_RANGE = 180
```

### PCA9685 tidak terdeteksi
```bash
# Enable I2C
sudo raspi-config
# Interface Options → I2C → Enable → Reboot

# Check wiring:
# SDA → GPIO 2 (Pin 3)
# SCL → GPIO 3 (Pin 5)
# VCC → 5V
# GND → GND
```

---

## 📊 Expected Behavior

### Sorting Sequence (5 Phases)
1. **SELECTOR POSITIONING** (0.3s)
   - Selector moves to BIN A (60°) or BIN B (120°)

2. **UNLOCK & DROP** (0.1s)
   - Both locks unlock simultaneously (90° → 0°)
   - Container drops by gravity

3. **WAITING** (1.0s)
   - Wait for waste to fall and slide

4. **LIFT & LOCK** (0.4s)
   - All 4 corners lift simultaneously (90° → 0°)
   - Both locks lock simultaneously (0° → 90°)

5. **RESET** (0.3s)
   - Selector returns to NEUTRAL (90°)

**Total Time: ~2-3 seconds per cycle**

---

## 📝 Next Steps

1. ✅ Install: `bash install.sh`
2. ✅ Validate: `python3 scripts/validate_config.py`
3. ✅ Test: `python3 scripts/test_seven_servo.py`
4. ✅ Run: `python3 main.py`
5. 🔧 Customize: Edit `config.py` if needed

---

**Need Help?**
- 📖 Full Documentation: `README.md`
- � Quick Start Guide: This file!
- ✅ Config Validator: `python3 scripts/validate_config.py`
- 🧪 Test Suite: `python3 scripts/test_seven_servo.py`
- 🚨 Emergency Stop: `python3 scripts/emergency_stop_pca9685.py`
- 💬 GitHub Issues: https://github.com/Adamfatur/orangebox/issues
