# 🔧 Auto-Fix OpenCV Error

## Masalah yang Diperbaiki

Error: `ModuleNotFoundError: No module named 'cv2'`

## ✅ Solusi Otomatis

Sistem sekarang **OTOMATIS mendeteksi dan memperbaiki** masalah OpenCV tanpa perlu script tambahan!

### Cara Kerja Auto-Fix

1. **Saat menjalankan `./start.sh`:**
   - Mendeteksi jika OpenCV tidak bisa diakses di venv
   - Memeriksa apakah ini Raspberry Pi
   - Otomatis recreate venv dengan `--system-site-packages`
   - Install `python3-opencv` dari apt jika belum ada
   - Reinstall semua dependencies
   - Verify dan lanjutkan

2. **Saat menjalankan `python3 main.py`:**
   - Sama seperti di atas
   - Auto-fix sebelum import module apapun
   - Re-launch otomatis setelah fix

### Yang Terjadi di Balik Layar

```bash
# Virtual environment LAMA (error):
python3 -m venv .venv  # ❌ Tidak bisa akses system packages

# Virtual environment BARU (fixed):
python3 -m venv --system-site-packages .venv  # ✅ Bisa akses python3-opencv dari apt
```

### Kenapa Harus `--system-site-packages`?

Pada Raspberry Pi:
- `python3-opencv` (dari apt) punya dukungan penuh V4L2 untuk camera
- `opencv-python` (dari pip) TIDAK punya V4L2 support → camera tidak detect
- Solusi: Akses `python3-opencv` sistem dari dalam venv

## 📋 Tidak Perlu Script Tambahan

~~`FIX_OPENCV.sh`~~ - Tidak perlu lagi!  
~~`deployment/fix_opencv_venv.sh`~~ - Tidak perlu lagi!

Cukup jalankan:
```bash
./start.sh
```

atau

```bash
python3 main.py
```

Auto-fix akan berjalan otomatis jika ada masalah! 🎉

## 🧪 Verifikasi Manual (Opsional)

Jika ingin verifikasi OpenCV manual:

```bash
# Aktivasi venv
source .venv/bin/activate

# Test import
python3 -c "import cv2; print(f'OpenCV {cv2.__version__} from {cv2.__file__}')"
```

Expected output:
```
OpenCV 4.10.0 from /usr/lib/python3/dist-packages/cv2/__init__.py
```

## 🆘 Troubleshooting

Jika auto-fix gagal, jalankan manual:

```bash
# 1. Hapus venv lama
rm -rf .venv

# 2. Install system opencv
sudo apt-get update
sudo apt-get install -y python3-opencv

# 3. Jalankan installer
./install.sh

# 4. Test
./start.sh
```

## 📝 Technical Details

**Root Cause:**
- Virtual environment dibuat tanpa `--system-site-packages`
- Python di venv tidak bisa akses library sistem
- `python3-opencv` terinstall di sistem tapi tidak di venv

**Fix:**
- Recreate venv dengan flag `--system-site-packages`
- Reinstall pip packages
- System packages (opencv, tflite) tetap dari apt
- Pip packages (numpy, adafruit, dll) dari pip

**Files Modified:**
- `start.sh` - Auto-fix di line 18-61
- `main.py` - Auto-fix di function `check_and_fix_venv()` line 19-107

---

**Last Updated:** November 4, 2025  
**OrangeBox Version:** 1.2
