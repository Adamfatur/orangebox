# 🍊 OrangeBox — Panduan Singkat

Sistem klasifikasi dan sortir sampah otomatis menggunakan AI. Dapat dijalankan di macOS (mode simulasi) dan Raspberry Pi 5 (mode produksi) dengan lingkungan virtual terisolasi.

## 🚀 Instalasi Cepat

- Pastikan `python3` dan `pip3` tersedia.
- Jalankan installer otomatis yang menyiapkan virtual environment (`.venv`) dan dependency:

```bash
./install.sh
```

Installer akan:
- Mendeteksi platform (macOS/Raspberry Pi)
- Membuat dan menggunakan virtualenv `.venv` dengan `--system-site-packages`
- Menginstal semua dependency ke `.venv` (hindari konflik PEP 668)
- Mengaktifkan kamera/I2C (RPi), dan paket pendukung (OpenCV, NumPy, dsb.)
- Mengupdate `config.py` sesuai platform

### 🔧 Jika Ada Error "No module named 'cv2'" di Raspberry Pi

Jika setelah instalasi muncul error `ModuleNotFoundError: No module named 'cv2'`, jalankan:

```bash
./fix_venv.sh
```

Script ini akan:
- Reinstall python3-opencv dari apt
- Recreate virtual environment dengan `--system-site-packages`
- Verifikasi OpenCV, PiCamera2, dan TFLite tersedia

## ▶️ Menjalankan Aplikasi

- macOS (simulasi, aman tanpa hardware):
```bash
.venv/bin/python3 main.py --test --confidence 0.7
```
- Raspberry Pi 5 (produksi):
```bash
.venv/bin/python3 main.py --camera 0
# atau
./start.sh
```

Catatan macOS: paket `tflite-runtime` tidak tersedia. Mode `--test` tetap berjalan dengan Mock Classifier; kamera dan UI berfungsi.

## 🧭 Raspberry Pi 5 — Service (Auto-Start)

- Setup service systemd dengan interpreter dari `.venv`:
```bash
bash deployment/deploy.sh
```
- Kontrol service dengan helper:
```bash
./deployment/service.sh start
./deployment/service.sh status
./deployment/service.sh logs
./deployment/service.sh stop
```
- Periksa cepat kesehatan layanan:
```bash
bash deployment/health-check.sh
```
- Uninstall service bila perlu:
```bash
bash deployment/uninstall.sh
```

Service menggunakan `ExecStart` dari `.venv/bin/python3` untuk stabilitas dan konsistensi dependency.

## 🎛️ Konfigurasi Utama

- Edit `config.py` bila diperlukan:
  - `PLATFORM`: `'mac'` atau `'rpi'` (diset otomatis installer)
  - `CAMERA_INDEX`: angka indeks kamera (auto, bisa override via argumen `--camera`)
  - `FANCY_UI`: `True` untuk UI bergaya konsisten (default aktif di RPi). Set `False` bila prioritas performa.
  - Opsi lain (GPS/servo/database) disetel otomatis; dapat disesuaikan manual.
- Device ID (opsional): diset saat `deploy.sh` (Step 2.8) atau langsung di `config.py` (`DEVICE_ID`, `DEVICE_NAME`).

## 🖼️ UI Kamera

- UI kamera di Raspberry Pi diselaraskan dengan macOS menggunakan elemen bergaya (rounded cards, shadowed text, badge) ketika `FANCY_UI=True`.
- Jika FPS kurang, matikan `FANCY_UI` di `config.py` untuk overlay minimalis.

## 🧰 Alat & Diagnostik

- Deteksi kamera otomatis:
```bash
python3 -m src.core.camera_detector
```
- Verifikasi lingkungan dan import modul:
```bash
bash tools/verify.sh
```
- Tes servo/GPS (RPi):
```bash
bash scripts/test_servo_simple.sh
bash scripts/test_servo_servokit.sh
bash scripts/test_gps.sh
```

## 📦 Struktur Proyek (ringkas)

- `main.py` — aplikasi utama
- `install.sh` — installer otomatis (virtualenv + dependency)
- `config.py` — konfigurasi sistem
- `src/` — kode inti (core dan hardware abstraction)
- `models/` — model TFLite dan `labels.txt`
- `tools/` — utilitas (training, testing, verifikasi)
- `deployment/` — skrip layanan (service, health-check, uninstall, update)

## ❓ Troubleshooting Singkat

- Kamera tidak terdeteksi: cek izin kamera (macOS) atau aktifkan kamera di RPi (`raspi-config`).
- `tflite-runtime` tidak tersedia di macOS: gunakan mode `--test`; aplikasi tetap berjalan.
- Konflik paket sistem (PEP 668): pastikan menjalankan dari `.venv` (`.venv/bin/python3`).
- Layar kosong saat service: pastikan `DISPLAY=:0` tersedia (X/desktop aktif) dan user service sesuai.

Selamat menggunakan OrangeBox! 🎉
