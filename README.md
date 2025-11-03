# 🍊 OrangeBox — Sistem Sortir Sampah Cerdas

Sistem klasifikasi dan sortir sampah otomatis menggunakan AI (TensorFlow Lite). 
Dirancang khusus untuk **Raspberry Pi 5** dengan dukungan mode simulasi di macOS.

## ⚡ Quick Start — Raspberry Pi 5

```bash
# 1. Clone repository
git clone https://github.com/Adamfatur/orangebox.git
cd orangebox
git checkout v1.1

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
- **Servo**: 3-5 servo MG996R
  - **Opsi 1**: GPIO PWM (3 servo)
  - **Opsi 2**: PCA9685 (16-channel, 5 servo)
- **Power**: 5V 3A untuk RPi + power supply terpisah untuk servo (5-6V, 2A+)
- **Opsional**: GPS Module (U-blox NEO-6M), Database MySQL

### macOS (Development/Testing)
- macOS 10.15+
- Python 3.9+
- Webcam internal/external

## 🚀 Instalasi & Setup

### Raspberry Pi 5 (Production)

```bash
# 1. Update sistem
sudo apt update && sudo apt upgrade -y

# 2. Clone repository
git clone https://github.com/Adamfatur/orangebox.git
cd orangebox
git checkout v1.1

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
git checkout v1.1

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

#### Deteksi Servo

```bash
# Auto-detect servo yang terhubung
source .venv/bin/activate
python3 scripts/detect_servos.py
```

Output akan menunjukkan:
- GPIO PWM pins yang terdeteksi
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

### Servo (GPIO)
```python
SERVO_DRIVER = 'gpio'  # atau 'servokit' untuk PCA9685

# Layer 1 doors
SERVO_LAYER1_LEFT_PIN = 12
SERVO_LAYER1_RIGHT_PIN = 13

# Layer 2 selector
SERVO_LAYER2_SELECTOR_PIN = 18
SERVO_LAYER2_BIN_A = 60
SERVO_LAYER2_BIN_B = 120
```

### Servo (PCA9685)
```python
SERVO_DRIVER = 'servokit'
PCA9685_I2C_ADDRESS = 0x40

# Channel mapping
SERVO_L1_LEFT_A_CH = 2
SERVO_L1_RIGHT_A_CH = 3
SERVO_L2_SELECTOR_CH = 0
```

### UI
```python
FANCY_UI = True  # Styled UI dengan rounded cards
```

## 🧰 Tools & Testing

### Test Servo

```bash
# GPIO servo test
source .venv/bin/activate
python3 scripts/test_servo_simple.py

# PCA9685 servo test
python3 scripts/test_servo_servokit.py

# 4-servo Layer 1 test (quad mode)
python3 scripts/test_servo_layer1_quad.py
```

### Test Kamera

```bash
# Auto-detect kamera
python3 -m src.core.camera_detector
```

### Test GPS (Optional)

```bash
bash scripts/test_gps.sh
```

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
# Auto-detect servo
source .venv/bin/activate
python3 scripts/detect_servos.py

# Test GPIO servo
python3 scripts/test_servo_simple.py

# Test PCA9685 servo
python3 scripts/test_servo_servokit.py

# Check I2C enabled (untuk PCA9685)
sudo raspi-config
# → Interface Options → I2C → Enable

# Scan I2C devices
i2cdetect -y 1
# Expected: 0x40 (PCA9685 default address)
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
├── config.py              # Konfigurasi sistem
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
│       ├── gpio_servo_hardware.py       # GPIO servo (3-servo)
│       └── five_servo_hardware.py       # PCA9685 servo (5-servo)
│
├── models/
│   ├── model_quant_infer.tflite    # Quantized model
│   ├── model_float32_infer.tflite  # Float32 model
│   └── labels.txt                   # Class labels
│
├── scripts/
│   ├── detect_servos.py            # Auto-detect servo
│   ├── verify_no_conflicts.py      # Check library conflicts
│   ├── test_servo_simple.py        # Test GPIO servo
│   └── test_servo_servokit.py      # Test PCA9685 servo
│
├── deployment/
│   ├── deploy.sh                   # Setup systemd service
│   ├── service.sh                  # Service control
│   ├── health-check.sh             # Health monitoring
│   └── uninstall.sh                # Remove service
│
└── docs/
    ├── PETUNJUK_KONFIGURASI.md     # Konfigurasi detail
    └── TROUBLESHOOTING_SERVO.md    # Servo troubleshooting
```

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
- ✅ Timeout protection
- ✅ Test dengan `test_servo_simple.py` sebelum production

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
1. Check troubleshooting section di atas
2. Run diagnostic tools:
   - `python3 scripts/verify_no_conflicts.py`
   - `python3 scripts/detect_servos.py`
   - `bash deployment/health-check.sh`
3. Check logs: `./deployment/service.sh logs`
4. Open issue di GitHub

---

**Selamat menggunakan OrangeBox!** 🎉
