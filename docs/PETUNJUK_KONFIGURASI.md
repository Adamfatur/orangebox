# 📘 Petunjuk Konfigurasi Hardware (Bahasa Indonesia)

Dokumen singkat untuk bantu kamu mengatur servo, kamera, dan opsi hardware lain di proyek OrangeBox. Gaya bahasanya santai tapi to the point.

## 🔧 Di mana atur SERVO?
- File: `config.py` (bagian "SERVO CONFIGURATION (3 Servos MG996R)")
- Yang biasanya kamu ubah:
  - `SERVO_LAYER1_LEFT_PIN`, `SERVO_LAYER1_LEFT_CLOSED`, `SERVO_LAYER1_LEFT_OPEN`
  - `SERVO_LAYER1_RIGHT_PIN`, `SERVO_LAYER1_RIGHT_CLOSED`, `SERVO_LAYER1_RIGHT_OPEN`
  - `SERVO_LAYER2_SELECTOR_PIN`, `SERVO_LAYER2_BIN_A`, `SERVO_LAYER2_BIN_B`, `SERVO_LAYER2_NEUTRAL`
- Tips cepat:
  - Mulai dari `NEUTRAL = 90°`.
  - Atur `OPEN` sekitar `90°` dulu, tes, lalu geser ±5° sesuai kebutuhan mekanik.
  - Arah kebalik? Tukar nilai `BIN_A` ↔ `BIN_B` atau geser beberapa derajat.
- Mode uji aman (tanpa AI):
- Jalankan: `python3 src/hardware/gpio_servo_hardware.py`
  - Di macOS: simulasi (print saja). Di Raspberry Pi: servo fisik bergerak.

Catatan: Ada dua cara kontrol servo di repo ini:
- GPIO langsung via PWM (umum dipakai): `src/hardware/gpio_servo_hardware.py` membaca semua nilai dari `config.py`.
- Alternatif PCA9685 (I2C driver): `src/hardware/hardware_interface_rpi.py` bagian "Servo Configuration" (legacy). Kalau kamu pakai ini, atur `SERVO_CHANNEL` dan sudut di file tersebut.

## 🎥 Di mana atur KAMERA?
- Umum: `config.py` → `PLATFORM` dan `CAMERA_INDEX`.
  - `PLATFORM`: `'mac'` untuk laptop, `'rpi'` untuk Raspberry Pi.
  - `CAMERA_INDEX`: index webcam jika pakai USB cam.
- Auto-detect kamera:
  - Ada modul: `src/core/camera_detector.py`.
  - Cek cepat: `python3 -m src.core.camera_detector` (menampilkan daftar & pilihan otomatis).
- Saat run aplikasi:
  - Manual pilih kamera: `python3 main.py --camera 0`.
  - Tanpa argumen `--camera`, sistem auto-pilih (di RPi: PiCamera2 jika ada, kalau tidak USB webcam dengan OpenCV).
- Troubleshooting cepat (RPi):
  - Pastikan kamera aktif: `sudo raspi-config` → Interface → Camera → Enable → Reboot.
  - Cek device USB: `v4l2-ctl --list-devices`.

## 🧭 Pin Proximity Sensor (RPi)
- `config.py` → `PROXIMITY_SENSOR_PIN` (default `17`).
- Dipakai oleh `src/hardware/hardware_interface_rpi.py`.

## 🧪 Cara tes hardware step-by-step
1) Tes kamera saja:
   - `python3 -m src.core.camera_detector`
   - atau run app dengan pilih kamera manual: `python3 main.py --camera 0`
2) Tes servo saja (aman):
- `python3 src/hardware/gpio_servo_hardware.py`
3) Tes penuh (RPi):
   - Pastikan `PLATFORM = 'rpi'` di `config.py`.
   - `python3 main.py`

## ⚖️ Nilai waktu/gerakan servo (opsional)
- Juga di `config.py`:
  - `SERVO_OPEN_DURATION`, `SERVO_DROP_DELAY`, `SERVO_FALL_TIME`, `SERVO_SLIDE_TIME`, `SERVO_CLOSE_DELAY`, `SERVO_RESET_DELAY`
  - Kontrol halus: `SERVO_MOVEMENT_TIME`, `SERVO_POSITION_HOLD_TIME`, `SERVO_STOP_JITTER`
- Gunakan perubahan kecil (±0.05–0.2 detik) lalu tes lagi.

## 🧯 Keamanan & Daya
- Pakai power supply yang cukup untuk MG996R (arus puncak bisa tinggi).
- Hindari stall di ujung mekanik. Naikkan sudut perlahan dan amati.

## 📁 Referensi File yang Sering Disentuh
- `config.py` → Semua pengaturan inti (servo, kamera, timing)
- `src/hardware/gpio_servo_hardware.py` → Implementasi GPIO servo untuk pintu dan selector (baca dari config)
- `src/hardware/hardware_interface_rpi.py` → Alternatif dengan PCA9685 + kamera
- `src/core/camera_detector.py` → Deteksi otomatis kamera

Semoga membantu! Kalau ada perubahan mekanik, cukup balik ke `config.py` dan sesuaikan derajatnya. 👍