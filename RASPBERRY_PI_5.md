# 🍊 OrangeBox - Quick Start Raspberry Pi 5

## Setup Awal (1x saja)

```bash
cd ~/Unduhan/orangebox
git pull origin v1.1
./install.sh
```

**Instalasi otomatis:**
- ✅ Buat virtual environment
- ✅ Install dependencies (TFLite, OpenCV, Servo drivers)
- ✅ Fix OpenCV untuk kamera USB
- ✅ Setup permissions

---

## Jalankan Sistem

### Opsi 1: Start Script (Recommended)
```bash
./start.sh
```

### Opsi 2: Python Direct
```bash
python3 main.py
```

**Kedua cara akan:**
- ✅ Auto-fix OpenCV jika error
- ✅ Deteksi kamera otomatis
- ✅ Load model AI
- ✅ Start sorting system

---

## Troubleshooting

### Kamera tidak terdeteksi?
```bash
# Quick fix otomatis
./AFTER_PULL.sh

# Atau reboot
sudo reboot
```

### Test servo?
```bash
python3 scripts/auto_detect_test_servo.py
```

### Cek status?
```bash
python3 scripts/diagnose_camera.sh  # Cek kamera
python3 scripts/check_opencv_conflict.sh  # Cek OpenCV
```

---

## Konfigurasi Servo

Edit file: `config.py`

```python
# Channel PCA9685 yang digunakan
SERVO_LAYER1_LEFT_CHANNEL = 0      # Pintu kiri 1
SERVO_LAYER1_LEFT2_CHANNEL = 1     # Pintu kiri 2  
SERVO_LAYER1_RIGHT_CHANNEL = 2     # Pintu kanan 1
SERVO_LAYER1_RIGHT2_CHANNEL = 3    # Pintu kanan 2

# Derajat servo (sesuaikan dengan fisik)
SERVO_LAYER1_LEFT_CLOSED = 0       # Tutup
SERVO_LAYER1_LEFT_OPEN = 90        # Buka
```

**Dokumentasi lengkap:** Buka `config.py`, sudah ada petunjuk dalam Bahasa Indonesia.

---

## Update Sistem

```bash
git pull origin v1.1
./start.sh  # Auto-fix dependencies
```

Sistem akan otomatis fix OpenCV jika ada perubahan!

---

## Hardware yang Terdeteksi

- ✅ USB Webcam (Logitech) via OpenCV
- ✅ 4 Servo Layer 1 (PCA9685 CH 0,1,2,3)
- ✅ Layer 2 simulasi (bisa aktifkan nanti)
- ✅ Database MySQL RDS (statistik)

---

## Notes

- **Kamera:** Otomatis fix permission & driver V4L2
- **Servo:** Test dengan `python3 scripts/auto_detect_test_servo.py`
- **GPS:** Disabled (tidak perlu untuk setup ini)
- **Proximity Sensor:** Disabled (RPi5 compatibility)

**Jika ada masalah:** Cukup jalankan `./start.sh` lagi, sistem akan auto-fix!
