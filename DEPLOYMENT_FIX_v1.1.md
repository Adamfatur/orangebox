# 🚨 CRITICAL FIX APPLIED - Deployment Guide

## 🔴 Masalah yang Sudah Diperbaiki

### 1. **TensorFlow Lite Import Error** ✅ FIXED
```
AttributeError: module 'tensorflow' has no attribute 'lite'
```

**Root Cause:** Import tflite salah urutan - coba import tensorflow.lite sebelum cek tflite_runtime tersedia.

**Fix:** Ubah urutan import di `waste_classifier.py` untuk try tflite_runtime dulu.

---

### 2. **Servo Berputar Tanpa Henti** ✅ FIXED
```
Servo bergerak saat startup dan tidak berhenti
```

**Root Cause:** `_initialize_servo()` langsung set servo ke posisi neutral saat init, tanpa menunggu perintah sorting.

**Fix:** 
- Hapus `self.servo_motor.angle = NEUTRAL` dari init
- Servo HANYA bergerak setelah klasifikasi selesai
- Tambah emergency stop di error handler

---

### 3. **UI Kamera Tidak Muncul** ✅ FIXED
```
cv2.imshow error di headless/SSH mode
```

**Root Cause:** Raspberry Pi diakses via SSH tanpa DISPLAY, cv2.imshow gagal.

**Fix:**
- Deteksi headless mode (cek env DISPLAY)
- Fallback ke logging saja jika tidak ada display
- Wrap cv2.imshow dengan error handling

---

## 🚀 Cara Deploy Fix di Raspberry Pi

### Step 1: Pull Update dari Branch v1.1

```bash
cd ~/Unduhan/orangebox-1.1

# Pull latest fixes
git fetch origin
git checkout v1.1
git pull origin v1.1
```

### Step 2: Verify TFLite Runtime

```bash
# Test import
.venv/bin/python3 -c "
try:
    import tflite_runtime.interpreter as tflite
    print('✓ tflite_runtime available')
except ImportError:
    print('✗ tflite_runtime NOT available')
    print('Installing...')
"

# Install jika belum ada
sudo apt-get install -y python3-tflite-runtime

# Atau via venv
.venv/bin/pip install tflite-runtime
```

### Step 3: Test Servo (Opsional - Untuk Debugging)

**JANGAN COLOK SERVO SAAT TEST INI - HANYA TEST DRIVER**

```bash
# Test PCA9685 driver (tanpa servo fisik)
.venv/bin/python3 -c "
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
print('✓ PCA9685 driver OK')
pca.deinit()
print('✓ Driver stopped')
"
```

### Step 4: Emergency Stop Script (Jika Servo Masih Berputar)

Jika servo masih bergerak setelah update, jalankan emergency stop:

```bash
# Stop semua servo IMMEDIATELY
.venv/bin/python3 scripts/emergency_stop_pca9685.py
```

**Atau manual:**
```bash
.venv/bin/python3 -c "
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685

i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)

# Disable all channels
for ch in range(16):
    pca.channels[ch].duty_cycle = 0
    print(f'Channel {ch} STOPPED')

pca.deinit()
print('All servos stopped')
"
```

### Step 5: Test Aplikasi

**Dengan Display (Monitor/VNC):**
```bash
# UI akan tampil
./start.sh
```

**Headless/SSH (Tanpa Display):**
```bash
# Aplikasi jalan tapi tanpa UI window
# Status akan di-print ke console
./start.sh
```

**Test Mode (Tanpa Model):**
```bash
# Untuk test servo tanpa AI
.venv/bin/python3 main.py --test
```

---

## 🛠️ Troubleshooting

### Q: Servo masih berputar setelah update?

**A:** Jalankan emergency stop:
```bash
.venv/bin/python3 scripts/emergency_stop_pca9685.py

# Atau cabut power servo sementara
# Update kode
# Colok kembali servo
```

### Q: Error "module 'tensorflow' has no attribute 'lite'"?

**A:** Install tflite-runtime:
```bash
sudo apt-get install -y python3-tflite-runtime

# Atau rebuild venv
./fix_venv.sh
```

### Q: UI tidak muncul?

**A:** Normal jika via SSH. Untuk tampilkan UI:
- Option 1: Gunakan VNC Viewer
- Option 2: Colok monitor langsung
- Option 3: Export DISPLAY jika forward X11:
  ```bash
  export DISPLAY=:0
  ./start.sh
  ```

### Q: Camera tidak terdeteksi?

**A:** Run diagnostic:
```bash
./scripts/diagnose_camera.sh
```

---

## 📝 Perubahan File

Files yang diubah di commit ini:

1. **`src/core/waste_classifier.py`** - Fix TFLite import
2. **`src/hardware/hardware_interface_rpi.py`** - Fix servo init & display
3. **`main.py`** - Add emergency cleanup
4. **`scripts/emergency_stop_pca9685.py`** - New emergency stop script

---

## ✅ Verification Checklist

Setelah deploy, verify:

- [ ] Application starts tanpa error TFLite
- [ ] Servo TIDAK bergerak saat startup
- [ ] Servo HANYA bergerak setelah klasifikasi
- [ ] Camera terdeteksi dan frame captured
- [ ] UI tampil (jika ada display) atau logging (jika headless)
- [ ] Ctrl+C stops semua servo dengan aman

---

## 🚀 Next Steps

1. **Test sorting:** Letakkan objek di depan camera
2. **Monitor servo:** Pastikan servo bergerak SETELAH prediksi selesai
3. **Check timing:** Servo harus berhenti setelah ~0.5 detik
4. **Emergency stop:** Ctrl+C harus stop semua servo immediately

---

**Commit:** 06a7963  
**Branch:** v1.1  
**Date:** 2025-11-03
