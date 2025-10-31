# 🚨 Quick Fix - Missing Dependencies

Berdasarkan error log Anda:

```
❌ No module named 'tensorflow'
❌ No module named 'pymysql'  
❌ No module named 'adafruit_servokit'
⚠️  GPSD service not running
```

## ⚡ Solusi Tercepat

Di Raspberry Pi, jalankan:

```bash
cd ~/Unduhan/orangebox-1.1

# Option 1: Automated Fix (RECOMMENDED)
bash scripts/fix_dependencies.sh

# Option 2: Manual Quick Fix
pip3 install tflite-runtime pymysql adafruit-circuitpython-servokit
sudo systemctl start gpsd

# Option 3: Complete Reinstall
sudo bash deployment/deploy.sh
```

## 🔍 Verify Installation

Setelah install, cek dengan:

```bash
python3 scripts/system_diagnostic.py
```

Expected output:
```
✅ TensorFlow Lite          INSTALLED
✅ PyMySQL                  INSTALLED
✅ Adafruit ServoKit        INSTALLED
✅ gpsd                     RUNNING
```

## 🚀 Test System

Kalau semua OK, test system:

```bash
python3 main.py
```

Should NOT show:
- ❌ "No module named..." errors
- ❌ "library not available" warnings

Should show:
- ✅ "All components initialized successfully!"
- ✅ System ready

## �� Troubleshooting

Lihat file lengkap: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Files created:**
- `scripts/fix_dependencies.sh` - Automated dependency installer
- `scripts/system_diagnostic.py` - System health checker
- `TROUBLESHOOTING.md` - Comprehensive troubleshooting guide
