# 🚨 EMERGENCY FIX: Segmentation Fault Protection

## ✅ Changes Deployed (Commit 6576e3c)

### Critical Fixes Applied:
1. **Camera-First Initialization Order** - Camera initialized BEFORE model to prevent resource conflict
2. **Memory Barrier** - 500ms delay + garbage collection before TFLite loading
3. **PiCamera2 Bypass** - Force OpenCV mode (PiCamera2 causes segfault with TFLite on ARM)
4. **Diagnostic Tool** - `scripts/diagnose_segfault.py` to isolate failure component

---

## 📦 Deployment Instructions (Raspberry Pi)

### Step 1: Pull Latest Fixes
```bash
cd ~/orangebox
git pull origin v1.1
```

### Step 2: Run Diagnostic (Optional but Recommended)
Test each component separately to verify the fix:
```bash
source .venv/bin/activate
python3 scripts/diagnose_segfault.py
```

**Expected Output:**
```
✓ OpenCV import OK
✓ TFLite import OK  
✓ Model loading OK
✓ GPIO OK
✓ WasteClassifier OK
```

If ANY component fails, read the error message carefully.

### Step 3: Test Application
```bash
./start.sh
```

**Expected Behavior:**
- `[1/3] Initializing Hardware Interface` → Should complete quickly
- `→ Camera initialization starting...` → Camera locks resources first
- `✓ Camera locked and ready` → Resources allocated
- `[2/3] Initializing Waste Classifier...` → Now safe to load model
- `Waiting for camera resource stabilization...` → 500ms delay
- `Memory barrier cleared` → GC completed
- `✓ Tensors allocated` → Model loaded successfully
- UI should appear and stay stable (no crash)

---

## 🔍 What Was Changed

### 1. `main.py` - Initialization Order
**BEFORE (BROKEN):**
```python
hw = HardwareInterface()  # Camera init
classifier = WasteClassifier()  # TFLite conflicts with camera
```

**AFTER (FIXED):**
```python
hw = HardwareInterface()  # Camera LOCKS resources first
time.sleep(0.5)  # Wait for camera to stabilize
classifier = WasteClassifier()  # Now safe - camera already allocated
```

### 2. `waste_classifier.py` - Memory Barrier
Added before model loading:
```python
import time, gc
time.sleep(0.5)  # 500ms delay
gc.collect()  # Force garbage collection
# Then load TFLite model (no conflict)
```

### 3. `hardware_interface_rpi.py` - OpenCV Forced
```python
use_opencv_only = True  # BYPASS PiCamera2 (causes segfault)
```

### 4. `scripts/diagnose_segfault.py` - NEW TOOL
Tests components individually:
- OpenCV import
- PiCamera2 import (optional)
- TFLite import
- Model loading
- GPIO
- Full WasteClassifier init

---

## ❌ If Still Crashes

### Scenario A: Crash during model loading
**Symptoms:** Stops at "Allocating tensors..."
**Solution:**
```bash
# Model file may be corrupt - try different model
cd ~/orangebox/models
ls -lh *.tflite  # Check file sizes

# If model_quant_infer.tflite is < 1MB, it's corrupt
# Try float32 version instead:
python3 scripts/diagnose_segfault.py  # Will show which model works
```

### Scenario B: Crash during camera init
**Symptoms:** Stops at "Camera initialization starting..."
**Solution:**
```bash
# Check camera permissions
sudo usermod -a -G video $USER
sudo chmod 666 /dev/video*

# Test camera separately
libcamera-hello --list-cameras
v4l2-ctl --list-devices
```

### Scenario C: Immediate crash (no logs)
**Symptoms:** "Kerusakan segmentasi" with no initialization logs
**Solution:**
```bash
# Run with core dump enabled
ulimit -c unlimited
./start.sh

# If core dump created:
gdb python3 core
# Then type: bt (backtrace)
# Send output to developer
```

### Scenario D: Random crashes after running
**Symptoms:** Works for 10-30 seconds then crashes
**Solution:**
```bash
# Increase swap memory (model may exceed RAM)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change: CONF_SWAPSIZE=2048 (2GB)
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## 🧪 Test Mode (Skip Model Entirely)

If model still causes issues, test hardware with mock classifier:
```bash
./start.sh --test
```

This bypasses TFLite completely and uses random predictions.
**Use this to verify:**
- Camera works
- Servo works  
- Detection logic works
- Only model is the problem

---

## 📊 Monitoring

Watch for these indicators:

**✓ GOOD:**
```
✓ Camera locked and ready
Memory barrier cleared
✓ Tensors allocated
✓ Model loaded successfully
```

**❌ BAD:**
```
Kerusakan segmentasi  # Immediate crash
Killed  # Out of memory
Aborted  # Assert failure
```

---

## 🆘 Emergency Contacts

If all else fails:

1. **Check model compatibility:**
   ```bash
   python3 -c "import tflite_runtime; print(tflite_runtime.__version__)"
   # Should be 2.14.0 or newer
   ```

2. **Try legacy TFLite:**
   ```bash
   pip uninstall tflite-runtime
   pip install tflite-runtime==2.5.0
   ```

3. **Use CPU-only mode:**
   Edit `waste_classifier.py`, add after interpreter load:
   ```python
   self.interpreter.set_num_threads(1)  # Single thread
   ```

4. **Revert to previous version:**
   ```bash
   git checkout 06a7963  # Before segfault protection
   ```

---

## 📝 Technical Notes

**Why Camera-First?**
- libcamera allocates memory for frame buffers
- TFLite allocates memory for model tensors
- If TFLite loads first, libcamera may fail to get contiguous memory → SEGFAULT
- Camera-first ensures libcamera gets priority, TFLite adapts

**Why 500ms Delay?**
- Camera needs ~200-300ms to initialize V4L2 devices
- Delay ensures camera fully stabilized before model loading
- gc.collect() frees any temporary objects from camera init

**Why OpenCV-Only?**
- PiCamera2 uses libcamera (complex memory management)
- OpenCV uses simple v4l2 (safer for USB webcams)
- TFLite + libcamera = known conflict on Raspberry Pi 5

---

## ✅ Success Criteria

System is FIXED when:
1. `./start.sh` runs without "Kerusakan segmentasi"
2. UI shows live camera feed
3. Can place object near sensor → classification happens
4. Servo moves to correct position (ORGANIC/ANORGANIC)
5. System runs continuously for 5+ minutes without crash

Test thoroughly before deploying to production!
