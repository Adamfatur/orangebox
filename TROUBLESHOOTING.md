# 🔧 Orange Box - Troubleshooting Guide

## ❌ Common Errors and Solutions

### 1. `No module named 'tensorflow'` atau `No module named 'tflite_runtime'`

**Problem:** TensorFlow Lite interpreter tidak terinstall

**Solution:**
```bash
# Option 1: Install dari piwheels (Raspberry Pi)
pip3 install --index-url https://www.piwheels.org/simple tflite-runtime

# Option 2: Install dari PyPI
pip3 install tflite-runtime

# Option 3: Use full TensorFlow (lebih besar)
pip3 install tensorflow
```

**Test:**
```bash
python3 -c "import tflite_runtime; print('OK')"
```

---

### 2. `No module named 'pymysql'`

**Problem:** Database driver tidak terinstall

**Solution:**
```bash
pip3 install pymysql
```

**Test:**
```bash
python3 -c "import pymysql; print('OK')"
```

---

### 3. `No module named 'adafruit_servokit'`

**Problem:** Adafruit servo library tidak terinstall

**Solution:**
```bash
# Install semua Adafruit dependencies
pip3 install adafruit-blinka
pip3 install adafruit-circuitpython-pca9685
pip3 install adafruit-circuitpython-motor
pip3 install adafruit-circuitpython-servokit
```

**Test:**
```bash
python3 -c "import adafruit_servokit; print('OK')"
```

---

### 4. `GPSD service not running`

**Problem:** GPS daemon belum jalan

**Solution:**
```bash
# Start GPSD service
sudo systemctl start gpsd

# Enable auto-start on boot
sudo systemctl enable gpsd

# Check status
sudo systemctl status gpsd
```

---

### 5. `Adafruit PCA9685 library not available!`

**Problem:** PCA9685 servo driver board tidak terdeteksi

**Possible Causes:**
1. I2C belum enabled
2. PCA9685 tidak terhubung
3. Library tidak terinstall

**Solution:**

**A. Enable I2C:**
```bash
sudo raspi-config
# → Interface Options → I2C → Enable
sudo reboot
```

**B. Check I2C devices:**
```bash
# Install i2c-tools
sudo apt-get install i2c-tools

# Scan I2C bus
i2cdetect -y 1

# Should show device at 0x40 (PCA9685 default address)
```

**C. Install libraries:**
```bash
pip3 install adafruit-circuitpython-pca9685
```

---

### 6. Camera not detected

**Problem:** Camera tidak terdeteksi atau error

**Solution:**

**For Pi Camera Module:**
```bash
# Enable camera
sudo raspi-config
# → Interface Options → Camera → Enable
sudo reboot

# Test camera
libcamera-hello

# Check if detected
vcgencmd get_camera
```

**For USB Camera:**
```bash
# List video devices
ls -l /dev/video*

# Test with v4l2
v4l2-ctl --list-devices
```

---

## 🚀 Quick Fix - Install All Dependencies

### Method 1: Automated Fix Script
```bash
cd ~/Unduhan/orangebox-1.1
bash scripts/fix_dependencies.sh
```

### Method 2: Manual Install
```bash
# Update system
sudo apt-get update

# Install system dependencies
sudo apt-get install -y python3-pip i2c-tools gpsd gpsd-clients

# Install Python packages
pip3 install -r requirements.txt
```

### Method 3: Re-run Deployment Script
```bash
cd ~/Unduhan/orangebox-1.1
sudo bash deployment/deploy.sh
```

---

## 🔍 System Diagnostic

Run diagnostic tool to check all dependencies:

```bash
python3 scripts/system_diagnostic.py
```

This will check:
- ✅ Python modules (TFLite, PyMySQL, Adafruit, etc.)
- ✅ System commands (i2cdetect, gpspipe, etc.)
- ✅ Hardware detection (PCA9685, Camera, GPS)
- ✅ Services (GPSD)
- ✅ Permissions (GPIO access)

---

## 📊 Expected Output (Normal Operation)

```
╔══════════════════════════════════════════════════════════════╗
║               🧡 ORANGE BOX SYSTEM 🧡                        ║
║        Intelligent Waste Classification & Sorting           ║
╚══════════════════════════════════════════════════════════════╝

🔧 Initializing components...

[1/3] Initializing Hardware Interface (Auto-detect camera)...
      ✓ Pi Camera Module detected
      ✓ GPIO initialized
      ✓ Hardware Interface initialized

[2/3] Initializing Waste Classifier...
      ✓ TFLite model loaded: models/model_quant_infer.tflite
      ✓ Waste Classifier initialized

[3/3] Initializing Main Controller...
      ✓ 5-Servo hardware initialized (PCA9685)
      ✓ GPS service initialized
      ✓ Database service initialized
      ✓ Main Controller initialized

✓ All components initialized successfully!

📊 System Configuration:
   Mode: PRODUCTION
   Camera: Pi Camera Module
   Confidence Threshold: 50%
   Device ID: orangebox-abc123

🚀 Starting Orange Box System...
```

---

## 🐛 Debug Mode

Run with verbose logging:

```bash
# Enable debug mode in config.py
DEBUG = True

# Run with output
python3 main.py 2>&1 | tee orangebox.log
```

---

## 📝 Log Files

Check logs for errors:

```bash
# System service logs
sudo journalctl -u orangebox -f

# GPSD logs
sudo journalctl -u gpsd -n 50

# Kernel messages (for I2C/GPIO issues)
dmesg | grep -i "i2c\|gpio"
```

---

## ⚙️ Configuration Check

Verify config.py settings:

```bash
python3 -c "
import config
print(f'Platform: {config.PLATFORM}')
print(f'Camera: {config.CAMERA_INDEX}')
print(f'Servos: {config.NUM_SERVOS}')
print(f'GPS: {config.GPS_USE_GPSD}')
print(f'Database: {config.DB_HOST}')
"
```

---

## 🆘 Still Having Issues?

1. **Check hardware connections:**
   - PCA9685: VCC, GND, SDA (GPIO 2), SCL (GPIO 3)
   - GPS: VCC, GND, TX→GPIO15, RX→GPIO14
   - Servos: Connect to PCA9685 channels 0-4

2. **Verify I2C enabled:**
   ```bash
   sudo raspi-config
   # Interface Options → I2C → Enable
   ```

3. **Check permissions:**
   ```bash
   # Add user to required groups
   sudo usermod -a -G gpio,i2c,dialout $USER
   
   # Logout and login again
   ```

4. **Reinstall from scratch:**
   ```bash
   cd ~/Unduhan/orangebox-1.1
   pip3 uninstall -y -r requirements.txt
   pip3 install -r requirements.txt
   ```

---

## 📞 Support

If problems persist, provide this information:
- Output of `python3 scripts/system_diagnostic.py`
- Output of `python3 main.py`
- Output of `i2cdetect -y 1`
- Content of error logs

---

**Last updated:** October 31, 2025
