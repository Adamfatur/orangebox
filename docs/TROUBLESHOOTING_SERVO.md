# Panduan Troubleshooting Servo - OrangeBox

## ⚠️ Masalah: Servo Berputar Tanpa Henti

### Penyebab Umum:
1. **PWM tidak dimatikan setelah gerakan**
2. **Timing yang tidak tepat**
3. **Power supply tidak stabil**
4. **Konfigurasi sudut yang salah**

---

## ✅ Solusi yang Sudah Diterapkan

### 1. **Mekanisme PWM Stop (PALING PENTING)**

**Di `config.py`:**
```python
SERVO_STOP_JITTER = True  # ⚠️ HARUS True!
```

**Cara Kerja:**
- Setelah servo mencapai posisi target, PWM signal dimatikan (duty cycle = 0)
- Servo MG996R akan HOLD posisi secara mekanik meskipun PWM off
- Ini mencegah servo berputar terus-menerus atau bergetar

**File yang mengimplementasi:**
- `src/hardware/gpio_servo_hardware.py` - Line ~300
- `src/hardware/five_servo_hardware.py` - Line ~120

---

### 2. **Timing Control yang Ketat**

**Di `config.py`:**
```python
SERVO_MOVEMENT_TIME = 0.15      # Waktu gerakan servo (detik)
SERVO_POSITION_HOLD_TIME = 0.05 # Waktu hold untuk lock mekanik (detik)
```

**Alur Gerakan Servo:**
```
1. Set PWM duty cycle sesuai sudut target
   ↓ tunggu SERVO_MOVEMENT_TIME (0.15s)
2. Servo mencapai posisi target
   ↓ tunggu SERVO_POSITION_HOLD_TIME (0.05s)
3. Lock mekanik gear servo
   ↓ jika SERVO_STOP_JITTER = True
4. PWM duty = 0 (STOP signal)
   ✓ Servo BERHENTI dan terkunci
```

---

### 3. **Verifikasi Posisi Otomatis**

**Di `execute_sort()`:**
- Setiap gerakan servo diverifikasi
- Jika posisi tidak sesuai → otomatis force reset
- Logging detail untuk debugging

**Contoh Output:**
```
[GPIOServo] layer1_left: 0° → 90° ✓ (PWM STOPPED)
[GPIOServo] ✓ layer1_left: 90° (verified)
```

---

### 4. **Safety Delays Antar Gerakan**

**Di `config.py`:**
```python
SERVO_DROP_DELAY = 0.3    # Delay setelah selector positioned
SERVO_CLOSE_DELAY = 0.3   # Delay setelah pintu tutup
SERVO_RESET_DELAY = 0.3   # Delay setelah selector reset
```

**Fungsi:**
- Mencegah gerakan bertabrakan
- Memastikan servo benar-benar berhenti sebelum gerakan berikutnya
- Memberi waktu untuk stabilisasi mekanik

---

## 🔧 Cara Memverifikasi

### Test 1: Jalankan Script Verifikasi
```bash
# Di Raspberry Pi
python3 scripts/verify_servo_stop.py
```

**Yang Harus Diamati:**
- ✓ Servo bergerak ke posisi lalu DIAM
- ✗ Servo terus berputar → ADA MASALAH!

---

### Test 2: Cek Config
```bash
# Lihat nilai SERVO_STOP_JITTER
grep "SERVO_STOP_JITTER" config.py
```

**Harus menunjukkan:**
```python
SERVO_STOP_JITTER = True  # ⚠️ PENTING: ...
```

---

### Test 3: Test Manual dengan Hardware
```bash
# Di Raspberry Pi
python3 src/hardware/gpio_servo_hardware.py
```

**Atau untuk 5-servo (ServoKit):**
```bash
python3 src/hardware/five_servo_hardware.py
```

---

## 🐛 Troubleshooting

### Masalah: Servo masih berputar terus

**Cek 1: Verifikasi SERVO_STOP_JITTER**
```bash
python3 -c "import config; print('SERVO_STOP_JITTER =', config.SERVO_STOP_JITTER)"
```
- Harus menampilkan `True`
- Jika `False` → ubah di `config.py`

**Cek 2: Verifikasi PWM Stop di Log**
```
[GPIOServo] layer1_left: 0° → 90° ✓ (PWM STOPPED)  # ← HARUS ADA "PWM STOPPED"
```
- Jika tidak ada "PWM STOPPED" → ada bug di kode

**Cek 3: Power Supply**
- MG996R butuh minimal 5V 3A
- Power tidak stabil → servo bisa error
- Gunakan power supply terpisah untuk servo (jangan dari Raspberry Pi)

**Cek 4: Kabel dan Koneksi**
- Periksa kabel servo tidak longgar
- Pastikan ground (GND) terhubung antara Raspberry Pi dan power supply servo

---

### Masalah: Servo bergetar/jitter setelah berhenti

**Normal untuk MG996R**, tapi bisa dikurangi:

**Solusi 1: Naikkan Hold Time**
```python
# Di config.py
SERVO_POSITION_HOLD_TIME = 0.1  # dari 0.05 → 0.1
```

**Solusi 2: Pastikan Power Stabil**
- Gunakan capacitor 470µF-1000µF dekat servo
- Power supply dengan ripple rendah

**Solusi 3: Kurangi Load Mekanik**
- Pastikan servo tidak tertahan/tersangkut
- Lumasi gear jika perlu

---

### Masalah: Servo tidak bergerak sama sekali

**Cek 1: GPIO Pin**
```python
# Cek di config.py
SERVO_LAYER1_LEFT_PIN = 12   # Sesuaikan dengan wiring
SERVO_LAYER1_RIGHT_PIN = 13
SERVO_LAYER2_SELECTOR_PIN = 18
```

**Cek 2: Enable GPIO/I2C**
```bash
# Di Raspberry Pi
sudo raspi-config
# → Interface Options → I2C/SPI → Enable
```

**Cek 3: Test Koneksi**
```bash
# Test GPIO langsung
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(12, GPIO.OUT)
pwm = GPIO.PWM(12, 50)
pwm.start(7.5)  # 90 derajat
import time; time.sleep(1)
pwm.stop()
GPIO.cleanup()
"
```

---

## 📊 Diagram Alur Sorting dengan Stop Points

```
START
  ↓
[1] Set Layer 2 Selector → Bin A/B (60°/120°)
  ↓ PWM STOP ← servo terkunci di posisi
  ↓ delay SERVO_DROP_DELAY (0.3s)
  ↓
[2] Buka Pintu Layer 1 (90°)
  ↓ PWM STOP ← servo terkunci di posisi
  ↓ delay SERVO_OPEN_DURATION (1.5s)
  ↓
[3] Sampah Jatuh
  ↓ delay SERVO_FALL_TIME + SERVO_SLIDE_TIME
  ↓
[4] Tutup Pintu Layer 1 (0°)
  ↓ PWM STOP ← servo terkunci di posisi
  ↓ delay SERVO_CLOSE_DELAY (0.3s)
  ↓
[5] Reset Layer 2 Selector → Neutral (90°)
  ↓ PWM STOP ← servo terkunci di posisi
  ↓ delay SERVO_RESET_DELAY (0.3s)
  ↓
[VERIFY] Semua servo di posisi yang benar?
  YES → END ✓
  NO  → Force Reset → END ⚠
```

---

## 🎯 Checklist Final

Sebelum deploy ke production, pastikan:

- [ ] `SERVO_STOP_JITTER = True` di `config.py`
- [ ] Script verifikasi berjalan tanpa error: `python3 scripts/verify_servo_stop.py`
- [ ] Servo terlihat BERHENTI setelah setiap gerakan (tidak berputar terus)
- [ ] Power supply stabil minimal 5V 3A
- [ ] Semua kabel terpasang kuat (tidak longgar)
- [ ] GPIO pin di `config.py` sesuai wiring fisik
- [ ] Test manual sorting: `python3 src/hardware/gpio_servo_hardware.py`
- [ ] Log menampilkan "PWM STOPPED" setelah setiap gerakan

---

## 📞 Support

Jika masalah masih berlanjut setelah mengikuti panduan ini:

1. **Capture log lengkap** dari test:
   ```bash
   python3 scripts/verify_servo_stop.py > servo_test.log 2>&1
   ```

2. **Record video** gerakan servo (untuk analisis visual)

3. **Cek hardware:**
   - Voltase power supply dengan multimeter
   - Kondisi fisik servo (apakah panas berlebihan?)
   - Koneksi kabel dengan continuity test

---

**Terakhir Diupdate:** 3 November 2025  
**Versi OrangeBox:** 1.1  
**Copyright:** AF - OrangeBox Project
