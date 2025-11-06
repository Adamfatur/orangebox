# Orange Box v1.3 - Auto-Start Deployment Guide

## 🎯 Tujuan

Membuat Orange Box berjalan **otomatis** saat Raspberry Pi boot/reboot menggunakan **systemd service**.

---

## 📋 Prerequisites

1. **Raspberry Pi 5** dengan Raspberry Pi OS Bookworm 64-bit
2. Orange Box sudah terinstall (sudah jalankan `./install.sh`)
3. Virtual environment sudah dibuat (folder `.venv` ada)
4. User sudah dalam grup `gpio`, `i2c`, `spi`, `video`

---

## 🚀 Quick Start (Recommended)

### 1. Install Auto-Start Service

```bash
cd /path/to/orangebox
chmod +x deployment/install_service.sh
./deployment/install_service.sh
```

Script ini akan:
- ✅ Verifikasi semua file yang diperlukan
- ✅ Menambahkan user ke grup GPIO/I2C/SPI/Video
- ✅ Membuat systemd service file
- ✅ Enable auto-start
- ✅ Start service
- ✅ Verifikasi service running

### 2. Reboot Test

```bash
sudo reboot
```

Setelah reboot, cek apakah service jalan otomatis:

```bash
sudo systemctl status orangebox
```

**Expected output:**
```
● orangebox.service - Orange Box v1.3 - AI Waste Sorting System
   Loaded: loaded (/etc/systemd/system/orangebox.service; enabled)
   Active: active (running) since ...
```

---

## 🛠️ Manual Commands

### Control Service

```bash
# Start service
sudo systemctl start orangebox

# Stop service
sudo systemctl stop orangebox

# Restart service
sudo systemctl restart orangebox

# Check status
sudo systemctl status orangebox

# View logs (live)
sudo journalctl -u orangebox -f

# View logs (last 100 lines)
sudo journalctl -u orangebox -n 100
```

### Enable/Disable Auto-Start

```bash
# Enable auto-start on boot
sudo systemctl enable orangebox

# Disable auto-start
sudo systemctl disable orangebox
```

### Using Helper Script

```bash
./deployment/service.sh start      # Start service
./deployment/service.sh stop       # Stop service
./deployment/service.sh restart    # Restart service
./deployment/service.sh status     # Show status
./deployment/service.sh logs       # Show live logs
./deployment/service.sh enable     # Enable auto-start
./deployment/service.sh disable    # Disable auto-start
```

---

## 🗑️ Uninstall Auto-Start

Untuk menghapus auto-start (tanpa menghapus file project):

```bash
./deployment/uninstall_service.sh
```

Atau manual:

```bash
sudo systemctl stop orangebox
sudo systemctl disable orangebox
sudo rm /etc/systemd/system/orangebox.service
sudo systemctl daemon-reload
```

---

## 🔧 Troubleshooting

### Service Gagal Start

**1. Cek logs untuk error:**
```bash
sudo journalctl -u orangebox -n 50
```

**2. Cek permissions:**
```bash
groups $(whoami)
```

Pastikan ada: `gpio i2c spi video`

Jika tidak ada, tambahkan:
```bash
sudo usermod -a -G gpio,i2c,spi,video $(whoami)
# Logout/login atau reboot untuk apply
```

**3. Cek file main.py executable:**
```bash
ls -la /path/to/orangebox/main.py
```

**4. Cek virtual environment:**
```bash
/path/to/orangebox/.venv/bin/python3 --version
```

### Service Start Tapi Camera Error

**Problem:** Service running tapi camera tidak bisa dibuka

**Solution:**
```bash
# Cek camera available
vcgencmd get_camera

# Enable camera
sudo raspi-config
# Interface Options → Camera → Enable

# Reboot
sudo reboot
```

### I2C/GPIO Permission Denied

**Problem:** Error "Permission denied" untuk `/dev/i2c-1` atau GPIO

**Solution:**
```bash
# Cek apakah user dalam grup yang benar
groups $(whoami)

# Tambahkan ke grup
sudo usermod -a -G gpio,i2c,spi $(whoami)

# Logout dan login ulang, atau:
sudo reboot
```

### Service Restart Terus Menerus

**Problem:** Service restart berkali-kali (crash loop)

**Solution:**
```bash
# Cek logs untuk error
sudo journalctl -u orangebox -n 100 --no-pager

# Cek resource usage
sudo systemctl status orangebox

# Stop service sementara
sudo systemctl stop orangebox

# Debug manual
cd /path/to/orangebox
.venv/bin/python3 main.py
```

### Delay Start Terlalu Lama

**Problem:** Service butuh waktu lama untuk start setelah boot

**Solution:** Edit `/etc/systemd/system/orangebox.service`

```ini
# Kurangi delay jika hardware sudah stabil
ExecStartPre=/bin/sleep 3   # Default: 5 detik
```

Reload service:
```bash
sudo systemctl daemon-reload
sudo systemctl restart orangebox
```

---

## 📊 Monitoring

### Real-time Logs

```bash
# Follow logs
sudo journalctl -u orangebox -f

# Dengan timestamp
sudo journalctl -u orangebox -f -o short-precise
```

### Log Files Location

Logs disimpan di **systemd journal**. Untuk export:

```bash
# Export logs ke file
sudo journalctl -u orangebox > orangebox_logs.txt

# Logs untuk hari ini saja
sudo journalctl -u orangebox --since today > orangebox_today.txt
```

### Check Service Health

```bash
# Status ringkas
systemctl is-active orangebox   # Output: active/inactive

# Status auto-start
systemctl is-enabled orangebox  # Output: enabled/disabled

# Detail lengkap
sudo systemctl status orangebox
```

---

## 🔐 Security Notes

Service berjalan sebagai user **current user** (biasanya `pi`), bukan root.

Permissions yang diperlukan:
- **GPIO**: Akses hardware GPIO pins
- **I2C**: Komunikasi dengan PCA9685 (servo driver)
- **SPI**: Komunikasi hardware (jika diperlukan)
- **Video**: Akses camera

**Tidak perlu sudo** untuk jalankan service setelah setup!

---

## 📝 Service Configuration Details

**File Location:** `/etc/systemd/system/orangebox.service`

**Key Settings:**
```ini
[Service]
Type=simple                    # Service tipe sederhana
User=pi                        # Jalankan sebagai user pi
WorkingDirectory=/home/pi/orangebox
ExecStartPre=/bin/sleep 5      # Delay 5 detik sebelum start
Restart=always                 # Auto-restart jika crash
RestartSec=10                  # Tunggu 10 detik sebelum restart
StartLimitBurst=10             # Max 10 restart attempts
```

---

## ✅ Verification Checklist

Setelah install, pastikan:

- [ ] Service status: **active (running)**
- [ ] Auto-start: **enabled**
- [ ] Logs tidak ada error critical
- [ ] Camera berfungsi
- [ ] Servo berfungsi (jika test)
- [ ] Database connection OK (jika enabled)
- [ ] Blynk connection OK (jika enabled)
- [ ] GPS connection OK (jika enabled)

Test reboot:
- [ ] Reboot Raspberry Pi
- [ ] Service start otomatis dalam 15 detik
- [ ] Sistem berfungsi normal

---

## 🆘 Support

Jika ada masalah:

1. **Cek logs:** `sudo journalctl -u orangebox -n 100`
2. **Cek status:** `sudo systemctl status orangebox`
3. **Test manual:** `cd /path/to/orangebox && .venv/bin/python3 main.py`
4. **Buka issue:** https://github.com/Adamfatur/orangebox/issues

---

## 📚 Additional Resources

- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Raspberry Pi GPIO Permissions](https://www.raspberrypi.com/documentation/computers/os.html#permissions)
- [Orange Box Main README](../README.md)

---

**Last Updated:** November 6, 2025  
**Version:** v1.3
