# 🍊 OrangeBox v1.2 — Sistem Sortir Sampah Cerdas dengan 7-Servo Locking System

Sistem klasifikasi dan sortir sampah otomatis menggunakan AI (TensorFlow Lite). 
Dirancang khusus untuk **Raspberry Pi 5** dengan dukungan mode simulasi di macOS.

**🆕 Version 1.2 Features:**
- ✨ **7-Servo Advanced Locking System** - Gravitational drop + automatic locking
- ✨ **Parallel Servo Control** - All servos move simultaneously (realtime)
- ✨ **Energy Efficient** - Lock servos only active during lock/unlock (~0.2s)
- ✨ **Faster Cycle Time** - ~2-3 seconds per sorting cycle

## ⚡ Quick Start — Raspberry Pi 5

```bash
# 1. Clone repository
git clone https://github.com/Adamfatur/orangebox.git
cd orangebox
git checkout v1.2

# 2. Install otomatis (setup venv + dependencies)
./install.sh

# 3. Jalankan aplikasi
python3 main.py
```

**Itu saja!** Script otomatis menangani:
- ✅ Virtual environment dengan `--system-site-packages`
- ✅ Install `python3-tflite-runtime` dari apt (stabil, no segfault)
- ✅ Install semua Python packages (OpenCV, NumPy, dll)
- ✅ Deteksi kamera otomatis
- ✅ Konfigurasi GPIO/I2C/SPI

## 📋 Persyaratan Hardware

### Raspberry Pi 5 (Recommended)
- **Raspberry Pi 5** (4GB/8GB RAM)
- **Raspberry Pi OS Bookworm** (64-bit)
- **Kamera**: USB webcam (Logitech C270/C920) atau Raspberry Pi Camera Module
- **Servo**: **7 servo MG996R** (sistem terbaru)
  - **4 Corner Servos**: Mengangkat/menurunkan wadah di setiap sudut
  - **2 Lock Servos**: Mengunci wadah di posisi atas
  - **1 Selector Servo**: Memilah ke Bin A (Organic) atau Bin B (Anorganic)
  - **Driver**: PCA9685 16-channel I2C servo driver board
- **Power**: 
  - 5V 3A untuk Raspberry Pi
  - 5V 10A untuk 7 servo (terpisah!)
  - Capacitor 1000μF untuk power stabilization
- **Opsional**: GPS Module (U-blox NEO-6M), Database MySQL

### macOS (Development/Testing)
- macOS 10.15+
- Python 3.9+
- Webcam internal/external

## 🏗️ Arsitektur 7-Servo System

### **Layer 1 - Container Management (6 Servo)**

#### **Corner Servos (4 servo)** - Mengangkat/Menurunkan Wadah
| Servo | Posisi | Channel | UP | DOWN |
|-------|--------|---------|-----|------|
| Corner A | Kiri Atas | CH 0 | 0° | 90° |
| Corner B | Kiri Bawah | CH 1 | 0° | 90° |
| Corner C | Kanan Atas | CH 2 | 0° | 90° |
| Corner D | Kanan Bawah | CH 3 | 0° | 90° |

#### **Lock Servos (2 servo)** - Mengunci Wadah
| Servo | Posisi | Channel | LOCKED | UNLOCKED |
|-------|--------|---------|---------|----------|
| Lock Left | Tengah Kiri | CH 4 | 90° | 0° |
| Lock Right | Tengah Kanan | CH 5 | 90° | 0° |

**Konsep Locking:**
- **LOCKED (90°)**: Servo arm horizontal di bawah wadah → menahan
- **UNLOCKED (0°)**: Servo arm vertikal → wadah jatuh gravitasi

### **Layer 2 - Waste Selector (1 Servo)**
| Servo | Channel | NEUTRAL | BIN A | BIN B |
|-------|---------|---------|-------|-------|
| Selector | CH 6 | 90° | 60° | 120° |

## 🔄 Alur Kerja Sorting (5 Fase)

### **FASE 1: SELECTOR POSITIONING** 🎯
- Servo selector bergerak 30° ke arah target
- BIN A (Organic): 60° | BIN B (Anorganic): 120°
- Delay 0.3s untuk stabilisasi

### **FASE 2: UNLOCK & DROP** 🔓
- **2 Lock servos UNLOCK simultaneously** (90° → 0°)
- Wadah jatuh **OTOMATIS** karena gravitasi
- 4 Corner servos tetap di posisi UP (0°)
- ✅ Hemat energi - tidak perlu servo aktif turun

### **FASE 3: WAITING** ⏳
- Tunggu sampah jatuh (~0.5s)
- Tunggu sampah meluncur di selector (~0.5s)

### **FASE 4: LIFT & LOCK** ⬆️🔒
- **4 Corner servos LIFT simultaneously** (90° → 0°)
  - Gerakan PARALLEL/REALTIME menggunakan threading
- **2 Lock servos LOCK simultaneously** (0° → 90°)
  - Wadah terkunci kembali di posisi atas

### **FASE 5: RESET** 🔄
- Selector kembali ke NEUTRAL (90°)
- Sistem siap sorting berikutnya

**⚡ Total Waktu: ~2-3 detik** (vs 5-6 detik di sistem lama)

## 🚀 Instalasi & Setup

### Raspberry Pi 5 (Production)

```bash
# 1. Update sistem
sudo apt update && sudo apt upgrade -y

# 2. Clone repository
git clone https://github.com/Adamfatur/orangebox.git
cd orangebox
git checkout v1.2

# 3. Jalankan installer
./install.sh
```

Installer akan:
1. Deteksi platform otomatis (Raspberry Pi)
2. Buat virtual environment (`.venv`) dengan `--system-site-packages`
3. Install system packages via apt:
   - `python3-tflite-runtime` (CRITICAL - stable TFLite di RPi)
   - `python3-picamera2` (Raspberry Pi Camera support)
   - `libcamera-apps`, `v4l-utils` (camera tools)
   - `i2c-tools`, `python3-smbus` (I2C untuk PCA9685)
4. Install Python packages via pip (dalam venv):
   - `numpy`, `opencv-python` (computer vision)
   - `RPi.GPIO`, `gpiozero` (GPIO control)
   - `adafruit-servokit` (PCA9685 servo driver)
   - `pymysql`, `pynmea2` (database & GPS)
5. Enable camera, I2C, SPI interfaces
6. Deteksi dan konfigurasi kamera otomatis

### macOS (Development/Testing)

```bash
# 1. Clone repository
git clone https://github.com/Adamfatur/orangebox.git
cd orangebox
git checkout v1.2

# 2. Jalankan installer (akan skip RPi-specific packages)
./install.sh

# 3. Jalankan dalam mode test
python3 main.py --test
```

## ▶️ Menjalankan Aplikasi

### Raspberry Pi 5

```bash
# Cara 1: Direct run (RECOMMENDED - auto-fix venv)
python3 main.py

# Cara 2: Via start script
./start.sh

# Cara 3: Manual venv activation
source .venv/bin/activate
python3 main.py
```

**CATATAN PENTING**: 
- ✅ `python3 main.py` otomatis mendeteksi dan menggunakan venv yang benar
- ✅ Jika venv belum ada, otomatis jalankan `install.sh`
- ✅ Tidak perlu manual `source .venv/bin/activate` lagi!

### macOS (Mode Simulasi)

```bash
# Mode test dengan mock classifier
python3 main.py --test

# Atau dengan venv
source .venv/bin/activate
python3 main.py --test
```

## 🔧 Command Line Options

```bash
python3 main.py [OPTIONS]

Options:
  --test              Mode simulasi (mock classifier, no model file)
  --camera INDEX      Camera index (default: auto-detect)
  --confidence FLOAT  Confidence threshold 0.0-1.0 (default: 0.5)
  --model PATH        Path to .tflite model (default: auto-select)
  --labels PATH       Path to labels.txt (default: models/labels.txt)
```

### 🔍 Deteksi Hardware

#### Test 7-Servo System

```bash
# Comprehensive 7-servo test dengan interactive menu
source .venv/bin/activate
python3 scripts/test_seven_servo.py
```

Test yang tersedia:
- **Test 1-7**: Individual servo test (Corner A/B/C/D, Lock L/R, Selector)
- **Test 8**: Full sequence BIN A (Organic)
- **Test 9**: Full sequence BIN B (Anorganic)
- **Test 0**: Display current configuration

#### Deteksi Servo

```bash
# Auto-detect servo yang terhubung
source .venv/bin/activate
python3 scripts/detect_servos.py
```

Output akan menunjukkan:
- PCA9685 di I2C bus (address & channels)
- Rekomendasi konfigurasi untuk `config.py`

#### Verifikasi Library (No Conflicts)

```bash
# Check tidak ada konflik library
source .venv/bin/activate
python3 scripts/verify_no_conflicts.py
```

Akan verify:
- ✅ NumPy & OpenCV version konsisten
- ✅ TFLite runtime dari apt (bukan pip)
- ✅ Tidak ada TensorFlow (prevent segfault)
- ✅ Tidak ada duplikasi library

## 🎛️ Konfigurasi

Edit `config.py` untuk menyesuaikan:

### Platform
```python
PLATFORM = 'rpi'  # atau 'mac'
```

### Kamera
```python
CAMERA_INDEX = 0  # auto-detect jika None
```

### Servo Driver
```python
SERVO_DRIVER = 'seven_servo'  # 7-servo system (default)

# PCA9685 I2C Configuration
SERVO_I2C_ADDRESS = 0x40
SERVO_FREQUENCY = 50  # Hz (standard servo PWM)
```

### 7-Servo Channel Mapping
```python
# Layer 1 - Corner Servos (mengangkat/menurunkan wadah)
SERVO_L1_CORNER_A_CHANNEL = 0  # Kiri Atas
SERVO_L1_CORNER_B_CHANNEL = 1  # Kiri Bawah
SERVO_L1_CORNER_C_CHANNEL = 2  # Kanan Atas
SERVO_L1_CORNER_D_CHANNEL = 3  # Kanan Bawah

# Layer 1 - Lock Servos (mengunci wadah di posisi atas)
SERVO_L1_LOCK_LEFT_CHANNEL = 4   # Lock Kiri
SERVO_L1_LOCK_RIGHT_CHANNEL = 5  # Lock Kanan

# Layer 2 - Selector Servo
SERVO_L2_SELECTOR_CHANNEL = 6

# Selector Angles
SERVO_LAYER2_BIN_A = 60   # Organic
SERVO_LAYER2_BIN_B = 120  # Anorganic
SERVO_LAYER2_NEUTRAL = 90 # Default position
```

### Servo Position Angles
```python
# Corner Servos
SERVO_L1_CORNER_UP = 0     # Wadah terangkat
SERVO_L1_CORNER_DOWN = 90  # Wadah turun (setelah unlock)

# Lock Servos
SERVO_L1_LOCK_LOCKED = 90     # Arm horizontal, mengunci
SERVO_L1_LOCK_UNLOCKED = 0    # Arm vertical, unlock
```

### Timing Configuration
```python
# Parallel Movement (no stagger)
SERVO_STAGGER_DELAY_MS = 0  # All servos move simultaneously

# Phase delays
SERVO_SELECTOR_DELAY_MS = 300   # After selector moves
SERVO_UNLOCK_DELAY_MS = 0       # Instant unlock
SERVO_DROP_WAIT_MS = 500        # Wait for waste drop
SERVO_SLIDE_WAIT_MS = 500       # Wait for waste slide
SERVO_LIFT_DELAY_MS = 0         # Instant lift
SERVO_LOCK_DELAY_MS = 200       # Lock servo active time
SERVO_RESET_DELAY_MS = 300      # Before next cycle
```

### UI
```python
FANCY_UI = True  # Styled UI dengan rounded cards
```

## 🧰 Tools & Testing

### Test 7-Servo System

```bash
# Comprehensive 7-servo test (RECOMMENDED)
source .venv/bin/activate
python3 scripts/test_seven_servo.py
```

Interactive menu dengan test:
1. Test individual servo (Corner A/B/C/D, Lock L/R, Selector)
2. Full sorting sequence untuk BIN A (Organic)
3. Full sorting sequence untuk BIN B (Anorganic)
4. Display konfigurasi servo

### Test Kamera

```bash
# Auto-detect kamera
python3 -m src.core.camera_detector
```

### Test GPS (Optional)

```bash
bash scripts/test_gps.sh
```

## 🔌 Wiring Diagram - PCA9685

### Power Connection
```
PCA9685 Board:
  VCC → 5V (Raspberry Pi)
  GND → GND (Raspberry Pi)
  V+  → 5V 10A Power Supply (EXTERNAL!)
  GND → GND (Power Supply)

IMPORTANT: 
- Servo power (V+) MUST use separate 5V 10A PSU
- Add 1000μF capacitor between V+ and GND
- Connect RPi GND and PSU GND together (common ground)
```

### I2C Connection
```
PCA9685 → Raspberry Pi 5
  SDA → GPIO 2 (Pin 3)
  SCL → GPIO 3 (Pin 5)
  VCC → 5V (Pin 2)
  GND → GND (Pin 6)
```

### Servo Connection (7-Servo System)
```
PCA9685 Channel → Servo
  CH 0 → Corner A (Kiri Atas)
  CH 1 → Corner B (Kiri Bawah)
  CH 2 → Corner C (Kanan Atas)
  CH 3 → Corner D (Kanan Bawah)
  CH 4 → Lock Left (Kunci Kiri)
  CH 5 → Lock Right (Kunci Kanan)
  CH 6 → Selector (Pemilah)
```

Each servo: **Brown (GND), Red (V+), Orange/Yellow (Signal)**

## 🌐 Systemd Service (Auto-Start)

Setup aplikasi agar otomatis berjalan saat boot:

```bash
# Deploy as systemd service
bash deployment/deploy.sh
```

Service akan:
- ✅ Otomatis start saat boot
- ✅ Auto-restart jika crash
- ✅ Log ke systemd journal

### Kontrol Service

```bash
# Start/stop/restart
./deployment/service.sh start
./deployment/service.sh stop
./deployment/service.sh restart

# Check status
./deployment/service.sh status

# View logs
./deployment/service.sh logs

# Health check
bash deployment/health-check.sh
```

### Uninstall Service

```bash
bash deployment/uninstall.sh
```

## 🐛 Troubleshooting

### Segmentation Fault di Raspberry Pi

**PENYEBAB**: Menggunakan TensorFlow full library atau tidak di venv yang benar.

**SOLUSI**: Script `main.py` sudah auto-fix! Cukup jalankan:
```bash
python3 main.py
```

Script akan:
1. Deteksi jika tidak di venv → auto re-launch dengan venv
2. Jika venv tidak ada → auto jalankan `install.sh`
3. Gunakan `tflite-runtime` dari apt (bukan TensorFlow)

**MANUAL CHECK**:
```bash
# Verify no conflicts
source .venv/bin/activate
python3 scripts/verify_no_conflicts.py

# Expected output:
# ✅ NO CONFLICTS DETECTED - All libraries are properly configured!
```

### Kamera Tidak Terdeteksi

```bash
# Check kamera tersedia
python3 -m src.core.camera_detector

# Raspberry Pi: Enable camera
sudo raspi-config
# → Interface Options → Legacy Camera → Enable

# Check USB webcam
v4l2-ctl --list-devices
```

### Servo Tidak Bergerak

```bash
# Test 7-servo system
source .venv/bin/activate
python3 scripts/test_seven_servo.py

# Auto-detect servo (check PCA9685)
python3 scripts/detect_servos.py

# Check I2C enabled (untuk PCA9685)
sudo raspi-config
# → Interface Options → I2C → Enable

# Scan I2C devices
i2cdetect -y 1
# Expected: 0x40 (PCA9685 default address)
```

**PENTING untuk 7-Servo:**
- ✅ Power servo harus dari PSU terpisah 5V 10A (bukan dari RPi!)
- ✅ Pasang capacitor 1000μF di V+ dan GND
- ✅ Common ground antara RPi dan PSU servo
- ✅ Periksa wiring: Brown=GND, Red=V+, Orange/Yellow=Signal

### Servo Bergerak Tidak Sinkron

**PENYEBAB**: Servo tidak menggunakan parallel movement

**CEK CONFIG**:
```python
# config.py
SERVO_STAGGER_DELAY_MS = 0  # MUST be 0 for parallel movement
```

**TEST**:
```bash
# Run test 8 atau 9 untuk lihat fase lengkap
python3 scripts/test_seven_servo.py
# Pilih test 8 (BIN A) atau 9 (BIN B)
# Perhatikan: Lock servos unlock bersamaan, corner servos lift bersamaan
```

### Dependency Issues

```bash
# Re-run installer
rm -rf .venv
./install.sh

# Verify no conflicts
source .venv/bin/activate
python3 scripts/verify_no_conflicts.py
```

## 📦 Struktur Proyek

```
orangebox/
├── main.py                 # Entry point (auto-fix venv)
├── config.py              # Konfigurasi 7-servo system
├── install.sh             # Auto installer
├── start.sh               # Quick start script
├── requirements.txt       # Python dependencies
│
├── src/
│   ├── core/
│   │   ├── camera_detector.py      # Auto-detect kamera
│   │   ├── waste_classifier.py     # TFLite classifier
│   │   ├── main_controller.py      # FSM controller
│   │   ├── database_service.py     # MySQL integration
│   │   └── location_service.py     # GPS support
│   │
│   └── hardware/
│       ├── hardware_interface_rpi.py    # RPi hardware
│       ├── hardware_interface_mock.py   # macOS mock
│       └── seven_servo_hardware.py      # 7-servo system (NEW!)
│
├── models/
│   ├── model_quant_infer.tflite    # Quantized model
│   ├── model_float32_infer.tflite  # Float32 model
│   └── labels.txt                   # Class labels
│
├── scripts/
│   ├── test_seven_servo.py         # 7-servo comprehensive test
│   ├── validate_config.py          # Validate 7-servo configuration
│   ├── detect_servos.py            # Auto-detect PCA9685
│   ├── verify_no_conflicts.py      # Check library conflicts
│   ├── emergency_stop_pca9685.py   # Emergency servo stop
│   ├── test_classifier.py          # Test AI model
│   └── system_diagnostic.py        # System diagnostics
│
├── deployment/
│   ├── deploy.sh                   # Setup systemd service
│   ├── service.sh                  # Service control
│   ├── health-check.sh             # Health monitoring
│   └── uninstall.sh                # Remove service
│
└── tools/
    ├── test_model_accuracy.py      # Model accuracy testing
    └── train_model.py              # Custom model training
```

## 🎯 Fitur 7-Servo System

### ✅ Parallel Servo Movement
- **Threading-based synchronization** untuk gerakan realtime
- 4 corner servos bergerak bersamaan saat lift
- 2 lock servos unlock/lock bersamaan
- Zero stagger delay (SERVO_STAGGER_DELAY_MS = 0)

### ✅ Energy Efficiency
- Lock servos hanya aktif saat lock/unlock (~0.2s)
- PWM duty cycle = 0 di luar waktu aktif (no power draw)
- Gravitational drop (tidak perlu power untuk turun)

### ✅ Safety Features
- Emergency stop (Ctrl+C)
- Timeout protection per fase
- Movement validation
- Error handling & logging

### ✅ Faster Cycle Time
- **~2-3 detik** per sorting cycle (vs 5-6 detik sistem lama)
- Parallel movement vs sequential
- Gravitational drop vs powered descent

## 🔐 Keamanan & Best Practices

### Virtual Environment
- ✅ **ALWAYS** gunakan virtual environment
- ✅ Script `main.py` auto-enforce venv
- ✅ `--system-site-packages` untuk akses apt packages

### Library Management
- ✅ `tflite-runtime` dari **apt** (bukan pip)
- ✅ OpenCV & NumPy dari **pip** (konsisten)
- ✅ Tidak ada duplikasi library
- ✅ Verifikasi dengan `verify_no_conflicts.py`

### Servo Safety
- ✅ PWM duty cycle = 0 setelah movement (prevent jitter)
- ✅ Emergency stop pada Ctrl+C
- ✅ Timeout protection per fase
- ✅ Test dengan `test_seven_servo.py` sebelum production
- ✅ Separate power supply (5V 10A) untuk servo

## 🎓 Training Model

Gunakan Google Teachable Machine untuk training:

1. Kunjungi: https://teachablemachine.withgoogle.com/
2. Pilih "Image Project" → "Standard image model"
3. Buat 2 class: `ORGANIC` dan `ANORGANIC`
4. Upload gambar (minimal 100+ per class)
5. Train model
6. Export → "TensorFlow Lite"
7. Download `model.tflite` dan `labels.txt`
8. Copy ke folder `models/`

Atau gunakan custom training:
```bash
python3 tools/train_model.py
```

## 📊 Monitoring & Logs

### Systemd Logs
```bash
# Real-time logs
./deployment/service.sh logs

# Last 100 lines
journalctl -u orangebox -n 100

# Today's logs
journalctl -u orangebox --since today
```

### Health Check
```bash
# Quick health check
bash deployment/health-check.sh

# Expected output:
# ✅ Service is running
# ✅ Camera accessible
# ✅ Model file found
# ✅ No recent crashes
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.

## 🆘 Support

Jika menemui masalah:
1. **Quick Start**: Lihat `QUICK_START.md` untuk setup cepat
2. **Validate Config**: `python3 scripts/validate_config.py`
3. **Run Diagnostics**:
   - `python3 scripts/verify_no_conflicts.py` - Check library conflicts
   - `python3 scripts/detect_servos.py` - Detect PCA9685
   - `python3 scripts/test_seven_servo.py` - Test servo system
   - `bash deployment/health-check.sh` - System health
4. **Check Logs**: `./deployment/service.sh logs`
5. **Emergency Stop**: `python3 scripts/emergency_stop_pca9685.py`
6. **GitHub Issues**: https://github.com/Adamfatur/orangebox/issues

---

**Selamat menggunakan OrangeBox!** 🎉
