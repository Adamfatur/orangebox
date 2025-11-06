#!/bin/bash
# OrangeBox Installer - Automatic Setup Script

set -e  # Exit on any error

echo "🍊 OrangeBox Installer"
echo "======================"
echo ""

# Auto-detect platform
PLATFORM=""
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="mac"
    echo "🖥️  Platform detected: macOS"
elif [[ "$OSTYPE" == "linux"* ]]; then
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        PLATFORM="rpi"
        echo "🥧 Platform detected: Raspberry Pi"
    else
        PLATFORM="linux"
        echo "🐧 Platform detected: Linux"
    fi
else
    echo "❌ Unsupported platform: $OSTYPE"
    exit 1
fi

echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "Please install Python 3 first:"
    if [[ "$PLATFORM" == "mac" ]]; then
        echo "  brew install python3"
        echo "  or download from: https://www.python.org/downloads/"
    elif [[ "$PLATFORM" == "rpi" ]]; then
        echo "  sudo apt update && sudo apt install python3 python3-pip"
    fi
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Install dependencies based on platform
echo "📦 Installing dependencies for $PLATFORM..."

if [[ "$PLATFORM" == "rpi" ]]; then
    # Raspberry Pi - install system packages first
    echo "Installing system packages..."
    sudo apt update --allow-releaseinfo-change -qq
    
    # Install essential packages
    sudo apt install -y python3-pip python3-venv
    
    # Create and use virtual environment to avoid PEP 668 (externally-managed)
    echo "Setting up Python virtual environment (.venv)..."
    # Ensure python3-venv is installed
    sudo apt-get install -y python3-venv
    # Create venv in project root WITH system-site-packages so apt Python modules are visible
    if [ ! -d ".venv" ]; then
        python3 -m venv --system-site-packages .venv
    fi
    # Upgrade pip inside venv
    .venv/bin/pip install --upgrade pip
    
    echo "Installing system packages for Raspberry Pi..."
    # TensorFlow Lite Runtime via apt (CRITICAL - no pip alternative on RPi)
    sudo apt-get install -y python3-tflite-runtime || true
    # Libcamera + Picamera2 support (Bookworm)
    sudo apt-get install -y python3-picamera2 libcamera-apps || true
    # Camera tooling
    sudo apt-get install -y v4l-utils || true
    # GPS support (gpsd) clients
    sudo apt-get install -y gpsd gpsd-clients || true
    # I2C and SMBus tools for PCA9685/Adafruit Blinka
    sudo apt-get install -y i2c-tools python3-smbus || true

    echo "Installing Python packages for Raspberry Pi (in venv)..."
    # Core Python libs in venv
    .venv/bin/pip install --upgrade pip
    
    # CRITICAL: DO NOT install opencv-python on Raspberry Pi!
    # System opencv (python3-opencv from apt) has full V4L2 support for camera access
    # Pip opencv-python is precompiled WITHOUT V4L2 support and will BREAK camera detection
    # Install only numpy via pip
    .venv/bin/pip install numpy
    
    # Verify system opencv is accessible via venv (--system-site-packages)
    echo "Verifying system OpenCV accessibility..."
    if .venv/bin/python3 -c "import cv2; print(f'OpenCV: {cv2.__version__} from {cv2.__file__}')" 2>/dev/null; then
        echo "✅ System OpenCV accessible in venv"
    else
        echo "⚠️  System OpenCV not accessible - installing via apt..."
        sudo apt-get install -y python3-opencv
    fi
    
    # GPIO and hardware libraries
    .venv/bin/pip install RPi.GPIO gpiozero

    echo "Installing Adafruit Blinka and ServoKit for PCA9685..."
    .venv/bin/pip install adafruit-blinka adafruit-circuitpython-servokit

    # Database and GPS
    .venv/bin/pip install pymysql pynmea2 pyserial python-dotenv
    
    # IoT Cloud: Blynk for bin capacity monitoring
    echo "Installing Blynk IoT library for bin monitoring..."
    .venv/bin/pip install blynk-library-python
    
    # Adafruit libraries for PCA9685 servo control
    # Note: adafruit-circuitpython-servokit already includes motor functionality
    .venv/bin/pip install adafruit-blinka adafruit-circuitpython-pca9685 adafruit-circuitpython-servokit
    
    echo "Verifying TFLite runtime availability..."
    if ! .venv/bin/python3 - << 'PY'
try:
    import tflite_runtime.interpreter as tflite
    print('TFLITE_OK')
except Exception as e:
    import sys
    sys.exit(2)
PY
    then
        echo "⚠️  tflite-runtime not detected. TensorFlow (full) will NOT be installed to avoid segfaults."
        echo "    Please ensure python3-tflite-runtime is available for your OS/arch, or run in --test mode."
    else
        echo "✅ tflite-runtime available"
    fi

    # Enable camera and GPIO/I2C/SPI (guarded with timeout to avoid hanging)
    echo "Enabling camera and GPIO/I2C/SPI..."
    # On Raspberry Pi OS Bookworm, camera works via libcamera; do_camera remains for legacy
    ENABLE_CMDS=(
        "raspi-config nonint do_camera 0"
        "raspi-config nonint do_spi 0"
        "raspi-config nonint do_i2c 0"
    )
    for CMD in "${ENABLE_CMDS[@]}"; do
        if command -v timeout >/dev/null 2>&1; then
            # Limit to 8s per command to avoid script getting stuck
            if ! sudo timeout 8s bash -lc "$CMD"; then
                echo "   ↪ Skipped ($CMD) due to timeout or non-critical error"
            fi
        else
            # Fallback without timeout (still non-fatal)
            sudo bash -lc "$CMD" || true
        fi
    done
    echo "Done enabling interfaces (reboot may be required)."

    echo ""
    echo "✅ Python virtual environment ready"
    echo "To activate: source .venv/bin/activate"
    echo "To run app: .venv/bin/python3 main.py (atau ./start.sh)"
    echo "To run servo test: .venv/bin/python3 scripts/test_seven_servo.py"
    
elif [[ "$PLATFORM" == "mac" ]]; then
    # macOS - lighter installation
    echo "Installing Python packages..."
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
    
    # Try TFLite first, fallback to TensorFlow (requirements may fail on macOS)
    if ! pip3 install tflite-runtime 2>/dev/null; then
        echo "⚠️  TFLite runtime not available, installing TensorFlow..."
        pip3 install tensorflow
    fi
fi

echo ""

# Interactive camera setup
echo "🎥 Camera Configuration"
echo "======================"
echo ""

# Auto-detect available cameras
echo "Detecting available cameras..."
CAMERAS=()
PICAM_AVAILABLE=0

# Use appropriate Python based on platform
if [[ "$PLATFORM" == "rpi" ]]; then
    PYTHON_CMD=".venv/bin/python3"
    
    # Verify OpenCV is available in venv
    if ! $PYTHON_CMD -c "import cv2" 2>/dev/null; then
        echo "⚠️  OpenCV not yet available in venv, using system Python for detection"
        PYTHON_CMD="python3"
    fi
    
    # Prefer Raspberry Pi Camera Module via Picamera2 when available
    if $PYTHON_CMD - << 'PYCODE'
try:
    from picamera2 import Picamera2
    try:
        cams = Picamera2.global_camera_info()
    except Exception:
        cams = []
    if cams:
        print("PICAM2_FOUND")
    else:
        # Fallback: try instantiation
        try:
            cam = Picamera2(); cam.close(); print("PICAM2_FOUND")
        except Exception:
            pass
except Exception:
    pass
PYCODE
    then
        PICAM_AVAILABLE=1
        echo "✅ Raspberry Pi Camera Module detected (Picamera2)."
        echo "   Using Picamera2 backend; skipping V4L2 index selection."
    fi
else
    PYTHON_CMD="python3"
fi

if [ $PICAM_AVAILABLE -eq 0 ]; then
    # Try OpenCV-based detection first (USB webcams)
    for i in {0..5}; do
        if $PYTHON_CMD -c "import cv2; cap = cv2.VideoCapture($i); ret, _ = cap.read(); cap.release(); exit(0 if ret else 1)" 2>/dev/null; then
            CAMERAS+=($i)
        fi
    done
fi

# Fallback: If no cameras found with OpenCV, try v4l2 on Raspberry Pi
if [ ${#CAMERAS[@]} -eq 0 ] && [[ "$PLATFORM" == "rpi" ]] && [ $PICAM_AVAILABLE -eq 0 ]; then
    echo "⚠️  OpenCV detection failed, trying v4l2 fallback..."
    
    # Check for video devices
    if ls /dev/video* >/dev/null 2>&1; then
        echo "✓ Video devices found:"
        ls -la /dev/video* 2>/dev/null | grep -E "video[0-9]+" || true
        
        # Use v4l2-ctl to find actual capture devices
        for device in /dev/video*; do
            if v4l2-ctl --device="$device" --all 2>/dev/null | grep -q "Video Capture"; then
                # Extract index from /dev/videoN
                idx="${device##*/video}"
                if [[ "$idx" =~ ^[0-9]+$ ]]; then
                    CAMERAS+=($idx)
                    echo "  → Found camera at index $idx ($device)"
                fi
            fi
        done
    fi
fi

# If still no cameras, provide helpful troubleshooting
if [ ${#CAMERAS[@]} -eq 0 ] && [ $PICAM_AVAILABLE -eq 0 ]; then
    echo "❌ No cameras detected!"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check if camera is connected:"
    echo "   lsusb | grep -i camera"
    echo "   ls -la /dev/video*"
    echo ""
    echo "2. Try listing v4l2 devices:"
    echo "   v4l2-ctl --list-devices"
    echo ""
    echo "3. Check camera permissions:"
    echo "   groups \$USER | grep video"
    echo "   If not in 'video' group, add with:"
    echo "   sudo usermod -a -G video \$USER"
    echo "   Then logout and login again"
    echo ""
    echo "4. For USB cameras, try:"
    echo "   sudo modprobe uvcvideo"
    echo ""
    echo "5. Manual camera index selection:"
    echo "   You can skip auto-detection and set CAMERA_INDEX manually in config.py"
    echo ""
    
    # Don't exit, allow manual configuration
    echo "⚠️  Continuing with default camera index 0"
    echo "    You can change this later in config.py"
    CAMERA_INDEX=0
elif [ $PICAM_AVAILABLE -eq 0 ]; then
    echo "✅ Found cameras at index: ${CAMERAS[*]}"
    echo ""
    
    # Ask user to select camera
    if [ ${#CAMERAS[@]} -eq 1 ]; then
        CAMERA_INDEX=${CAMERAS[0]}
        echo "Using camera index: $CAMERA_INDEX"
    else
        echo "Multiple cameras detected. Please select:"
        for cam in "${CAMERAS[@]}"; do
            echo "  $cam - Camera $cam"
        done
        echo ""
        
        while true; do
            read -p "Enter camera index [${CAMERAS[0]}]: " CAMERA_INDEX
            CAMERA_INDEX=${CAMERA_INDEX:-${CAMERAS[0]}}
            
            if [[ " ${CAMERAS[*]} " =~ " $CAMERA_INDEX " ]]; then
                break
            else
                echo "❌ Invalid camera index. Please choose from: ${CAMERAS[*]}"
            fi
        done
    fi
else
    # Picamera2 present; we won't ask for an index
    CAMERA_INDEX=0
fi

echo ""

# Update configuration
echo "⚙️  Updating configuration..."

# Create backup
cp config.py config.py.backup

# Update platform and camera settings
python3 -c "
import re

# Read config
with open('config.py', 'r') as f:
    content = f.read()

# Update platform
content = re.sub(r\"PLATFORM = '[^']*'\", f\"PLATFORM = '$PLATFORM'\", content)

# Update camera index
content = re.sub(r'CAMERA_INDEX = \d+', f'CAMERA_INDEX = $CAMERA_INDEX', content)

# Set platform-specific defaults
if '$PLATFORM' == 'rpi':
    # Raspberry Pi defaults
    content = re.sub(r'ENABLE_GPS = (True|False)', 'ENABLE_GPS = True', content)
    content = re.sub(r'AUTO_DETECT_SERVOS = (True|False)', 'AUTO_DETECT_SERVOS = True', content)
    content = re.sub(r'ENABLE_DATABASE = (True|False)', 'ENABLE_DATABASE = True', content)
else:
    # macOS/Linux defaults (development mode)
    content = re.sub(r'ENABLE_GPS = (True|False)', 'ENABLE_GPS = False', content)
    content = re.sub(r'AUTO_DETECT_SERVOS = (True|False)', 'AUTO_DETECT_SERVOS = False', content)
    content = re.sub(r'ENABLE_DATABASE = (True|False)', 'ENABLE_DATABASE = False', content)

# Write updated config
with open('config.py', 'w') as f:
    f.write(content)

print('✅ Configuration updated')
"

echo ""

echo "🧪 Testing camera..."
if [ $PICAM_AVAILABLE -eq 1 ]; then
    if $PYTHON_CMD - << 'PYCODE'
try:
    from picamera2 import Picamera2
    cam = Picamera2()
    cam.configure(cam.create_still_configuration(main={"size": (640,480), "format": "RGB888"}))
    cam.start()
    import time; time.sleep(0.5)
    arr = cam.capture_array()
    cam.close()
    print(f"✅ PiCamera2 working: {arr.shape[1]}x{arr.shape[0]}")
except Exception as e:
    print(f"❌ PiCamera2 test failed: {e}")
    raise
PYCODE
    then
        echo "✅ Camera test passed (PiCamera2)"
    else
        echo "❌ Camera test failed (PiCamera2)"
        exit 1
    fi
else
    if $PYTHON_CMD -c "
import cv2
import sys

cap = cv2.VideoCapture($CAMERA_INDEX)
if not cap.isOpened():
    print('❌ Failed to open camera $CAMERA_INDEX')
    sys.exit(1)

ret, frame = cap.read()
if not ret:
    print('❌ Failed to read from camera $CAMERA_INDEX')
    sys.exit(1)

height, width = frame.shape[:2]
print(f'✅ Camera working: {width}x{height}')
cap.release()
"; then
        echo "✅ Camera test passed"
    else
        echo "❌ Camera test failed"
        echo "Please check your camera connection and try again."
        exit 1
    fi
fi

echo ""

# Installation complete
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "Configuration Summary:"
echo "  Platform: $PLATFORM"
if [ $PICAM_AVAILABLE -eq 1 ]; then
    echo "  Camera: Raspberry Pi Camera (Picamera2 auto)"
else
    echo "  Camera Index: $CAMERA_INDEX"
fi
if [[ "$PLATFORM" == "rpi" ]]; then
    echo "  GPS: Enabled"
    echo "  Servos: Auto-detect enabled"
    echo "  Database: Enabled"
    echo ""
    
    # ============================================================
    # AUTO-START SERVICE SETUP (Raspberry Pi only)
    # ============================================================
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 AUTO-START SERVICE SETUP"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Apakah Anda ingin Orange Box berjalan OTOMATIS saat Raspberry Pi boot?"
    echo "  ✅ YES: Orange Box akan start otomatis setiap kali RPi menyala/reboot"
    echo "  ❌ NO:  Anda harus jalankan manual dengan: ./start.sh atau python3 main.py"
    echo ""
    
    while true; do
        read -p "Install auto-start service? (Y/n): " auto_start
        auto_start=${auto_start:-Y}  # Default: Yes
        
        case $auto_start in
            [Yy]* )
                echo ""
                echo "📦 Installing auto-start service..."
                
                # Check if deployment script exists
                if [ -f "deployment/install_service.sh" ]; then
                    # Make it executable
                    chmod +x deployment/install_service.sh
                    
                    # Run installer
                    if ./deployment/install_service.sh; then
                        echo ""
                        echo "✅ AUTO-START SERVICE INSTALLED!"
                        echo ""
                        echo "📋 Orange Box akan:"
                        echo "   • Start otomatis saat Raspberry Pi boot"
                        echo "   • Restart otomatis jika crash"
                        echo "   • Berjalan di background sebagai service"
                        echo ""
                        echo "🔧 Perintah berguna:"
                        echo "   • Lihat status:  sudo systemctl status orangebox"
                        echo "   • Lihat logs:    sudo journalctl -u orangebox -f"
                        echo "   • Stop service:  sudo systemctl stop orangebox"
                        echo "   • Start service: sudo systemctl start orangebox"
                        echo ""
                        echo "💡 TIP: Untuk test auto-start, reboot sekarang:"
                        echo "   $ sudo reboot"
                    else
                        echo ""
                        echo "⚠️  Auto-start installation failed!"
                        echo "   You can install manually later with:"
                        echo "   $ ./deployment/install_service.sh"
                    fi
                else
                    echo "⚠️  Auto-start installer not found!"
                    echo "   File deployment/install_service.sh missing"
                fi
                break
                ;;
            [Nn]* )
                echo ""
                echo "⏭️  Skipping auto-start setup."
                echo ""
                echo "💡 You can install auto-start later dengan:"
                echo "   $ ./deployment/install_service.sh"
                break
                ;;
            * )
                echo "Please answer Y (yes) or N (no)."
                ;;
        esac
    done
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
else
    echo "  GPS: Disabled (development mode)"
    echo "  Servos: Disabled (development mode)"
    echo "  Database: Disabled (development mode)"
fi
echo ""
echo "🚀 Ready to run!"
echo "  Test mode: .venv/bin/python3 main.py --test"
echo "  Full mode: .venv/bin/python3 main.py"
echo "  Atau gunakan: ./start.sh"
echo ""
echo "📝 Configuration backup saved as: config.py.backup"
echo ""
