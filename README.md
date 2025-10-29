# 🍊 OrangeBox — Panduan Singkat

Sistem klasifikasi dan sortir sampah otomatis menggunakan AI. Dapat dijalankan di macOS (mode simulasi) dan Raspberry Pi (mode produksi).

## 🚀 Instalasi

- Pastikan `python3` dan `pip3` tersedia.
- Jalankan installer otomatis:

```bash
./install.sh
```

Installer akan:
- Mendeteksi platform (macOS/Raspberry Pi)
- Menginstal dependencies yang diperlukan
- Mendeteksi kamera dan meminta pilihan indeks bila perlu
- Mengupdate `config.py` sesuai platform dan kamera
- Menjalankan uji kamera singkat

## ▶️ Menjalankan Aplikasi

- Mode uji (tanpa servo nyata, aman di macOS):
```bash
python3 main.py --test
```
- Mode penuh:
```bash
python3 main.py
```

## ⚙️ Konfigurasi Utama

Edit `config.py` jika diperlukan:
- `PLATFORM`: `'mac'` atau `'rpi'` (diset otomatis oleh installer)
- `CAMERA_INDEX`: angka indeks kamera (diset otomatis oleh installer)
- Opsi lain (GPS/servo/database) disetel otomatis berdasarkan platform

Untuk panduan lengkap pengaturan servo & kamera (bahasa Indonesia), lihat:

- `docs/PETUNJUK_KONFIGURASI.md`

## 🧭 Raspberry Pi (Produksi)

Untuk auto-start sebagai service, lihat folder `deployment/` (opsional):
- `deployment/deploy.sh` — contoh setup service
- `deployment/orangebox.service.template` — template systemd

Perintah umum:
```bash
sudo systemctl enable orangebox.service
sudo systemctl start orangebox.service
sudo systemctl status orangebox.service
```

## 📦 Struktur Proyek (ringkas)

- `main.py` — aplikasi utama
- `install.sh` — installer otomatis
- `config.py` — konfigurasi sistem
- `src/` — kode inti (core dan hardware abstraction)
- `models/` — model TFLite dan `labels.txt`
- `tools/` — utilitas (training, testing)
- `deployment/` — skrip layanan (opsional untuk RPi)

## ❓ Troubleshooting Singkat

- Kamera tidak terdeteksi: pastikan izin kamera (macOS) atau aktifkan kamera (RPi)
- TFLite gagal di macOS: installer otomatis fallback ke `tensorflow`
- Gunakan `config.py.backup` bila ingin mengembalikan pengaturan lama

Selamat menggunakan OrangeBox! 🎉
