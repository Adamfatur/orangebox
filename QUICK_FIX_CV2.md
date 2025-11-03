# Quick Fix: ModuleNotFoundError: No module named 'cv2'

## 🔴 Problem
```
ModuleNotFoundError: No module named 'cv2'
```

## ✅ Solution (Raspberry Pi)

### Option 1: Automatic Fix (RECOMMENDED)
```bash
./fix_venv.sh
```

### Option 2: Manual Fix
```bash
# 1. Install system packages
sudo apt-get update --allow-releaseinfo-change
sudo apt-get install -y python3-opencv python3-picamera2 python3-tflite-runtime

# 2. Recreate venv with system packages
rm -rf .venv
python3 -m venv .venv --system-site-packages

# 3. Upgrade pip
.venv/bin/pip install --upgrade pip

# 4. Install requirements (excluding opencv)
grep -Ev '^(opencv-python|tflite-runtime|picamera2)' requirements.txt > .req.tmp
.venv/bin/pip install -r .req.tmp
rm .req.tmp

# 5. Verify
.venv/bin/python3 -c "import cv2; print('OpenCV OK')"
```

### Option 3: Quick Test
```bash
# Verify OpenCV is installed system-wide
python3 -c "import cv2; print(cv2.__version__)"

# If that works but venv doesn't, recreate venv:
rm -rf .venv
python3 -m venv .venv --system-site-packages
```

## 🧪 Verify Installation
```bash
# Test OpenCV
.venv/bin/python3 -c "import cv2; print('✓ OpenCV:', cv2.__version__)"

# Test PiCamera2 (optional)
.venv/bin/python3 -c "import picamera2; print('✓ PiCamera2')"

# Test TFLite
.venv/bin/python3 -c "import tflite_runtime; print('✓ TFLite')"

# Run application
./start.sh
```

## 📝 Why This Happens

The installer creates a virtual environment, but on Raspberry Pi, some packages (like OpenCV) 
should be installed via `apt` (system packages) rather than `pip` because:
- Faster (pre-compiled binaries)
- Hardware-optimized (NEON, GPU acceleration)
- Better integration with camera drivers

The fix ensures the venv is created with `--system-site-packages` flag, allowing it to 
access system-installed Python packages.

## 🔧 Prevention

The updated `install.sh` now:
1. Creates venv with `--system-site-packages` from the start
2. Uses venv Python for camera detection
3. Installs OpenCV via apt before creating venv
4. Properly handles system package dependencies

## 💡 For Future Installations

Use the updated installer:
```bash
./install.sh
```

It will now correctly setup the environment from the beginning.
