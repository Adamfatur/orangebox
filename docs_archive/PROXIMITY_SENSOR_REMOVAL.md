# 🔧 Fix: Removed Proximity Sensor & GPIO Dependencies

## Tanggal: 4 November 2025

### ❌ Masalah yang Diperbaiki

**Error di Raspberry Pi 5:**
```
❌ FATAL ERROR: Cannot determine SOC peripheral base address
RuntimeError: Cannot determine SOC peripheral base address
```

**Root Cause:**
1. `RPi.GPIO` tidak support Raspberry Pi 5 (hanya support RPi 1-4)
2. Code masih mencoba initialize GPIO untuk proximity sensor
3. Proximity sensor sudah tidak digunakan di sistem v1.2 (7-servo locking)
4. Sistem v1.2 menggunakan I2C (PCA9685), bukan GPIO PWM

### ✅ Solusi yang Diimplementasikan

#### 1. Removed RPi.GPIO Import
**File:** `src/hardware/hardware_interface_rpi.py`

**Before:**
```python
# RPi GPIO Libraries (install: pip3 install RPi.GPIO)
try:
    import RPi.GPIO as GPIO
except ImportError:
    print("WARNING: RPi.GPIO not found. This is expected on non-RPi systems.")
    GPIO = None
```

**After:**
```python
# REMOVED - GPIO not used in v1.2 (I2C PCA9685 only)
```

#### 2. Removed Proximity Sensor Configuration
**File:** `src/hardware/hardware_interface_rpi.py` - `__init__()`

**Before:**
```python
# GPIO Pin Configuration
self.USE_PROXIMITY_SENSOR = getattr(config, 'USE_PROXIMITY_SENSOR', False)
self.PROXIMITY_SENSOR_PIN = getattr(config, 'PROXIMITY_SENSOR_PIN', 17)
```

**After:**
```python
# REMOVED - No proximity sensor in v1.2
```

#### 3. Removed GPIO Initialization
**File:** `src/hardware/hardware_interface_rpi.py`

**Before:**
```python
def _initialize_gpio(self):
    """Initialize GPIO untuk proximity sensor."""
    if GPIO is None:
        return
    
    if not self.USE_PROXIMITY_SENSOR:
        return
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(self.PROXIMITY_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # ... error handling
```

**After:**
```python
# METHOD COMPLETELY REMOVED
```

#### 4. Simplified check_trigger()
**File:** `src/hardware/hardware_interface_rpi.py`

**Before:**
```python
def check_trigger(self) -> bool:
    """Baca status proximity sensor."""
    if not self.USE_PROXIMITY_SENSOR:
        return False
    
    if GPIO is None:
        return False
    
    # Read GPIO pin, check cooldown, etc.
    sensor_state = GPIO.input(self.PROXIMITY_SENSOR_PIN)
    # ... 30 lines of code
```

**After:**
```python
def check_trigger(self) -> bool:
    """
    Check for trigger event.
    
    Note: Hardware interface does NOT handle triggers in v1.2.
    Trigger logic is handled by MainController (button press or timed intervals).
    This method always returns False for compatibility.
    """
    return False
```

#### 5. Removed GPIO Cleanup
**File:** `src/hardware/hardware_interface_rpi.py` - `cleanup()`

**Before:**
```python
# Cleanup GPIO
if GPIO is not None and self.USE_PROXIMITY_SENSOR:
    try:
        GPIO.cleanup()
    except Exception as e:
        print(f"⚠️  GPIO cleanup warning: {e}")
```

**After:**
```python
# REMOVED - No GPIO in v1.2
```

#### 6. Updated Documentation
**File:** `src/hardware/hardware_interface_rpi.py` - Header docstring

**Before:**
```python
Hardware yang diperlukan:
- Raspberry Pi 5
- Pi Camera Module (atau USB Webcam)
- Proximity Sensor (HC-SR04 atau IR sensor)
- Servo Motor + PCA9685 Servo Driver
```

**After:**
```python
Hardware yang diperlukan:
- Raspberry Pi 5
- Pi Camera Module (atau USB Webcam)
- 7x Servo Motor MG996R + PCA9685 I2C Servo Driver
- Power supply yang memadai (5V 3A untuk Pi, 5V 10A untuk servo)
```

### 📊 Summary of Changes

**Lines Removed:** ~70 lines
**Methods Removed:**
- `_initialize_gpio()` - Complete method (40 lines)
- GPIO cleanup code in `cleanup()` (7 lines)
- Proximity sensor logic in `check_trigger()` (30 lines)

**Configuration Removed:**
- `self.USE_PROXIMITY_SENSOR`
- `self.PROXIMITY_SENSOR_PIN`
- Import `RPi.GPIO`

**Methods Simplified:**
- `__init__()` - Removed GPIO initialization call
- `check_trigger()` - Now returns `False` immediately
- `cleanup()` - Removed GPIO cleanup

### 🎯 Why These Changes?

1. **Raspberry Pi 5 Compatibility:**
   - RPi.GPIO doesn't support RPi 5 new GPIO architecture
   - Would need `lgpio` or `gpiod` for RPi 5 (unnecessary complexity)

2. **System Architecture:**
   - v1.2 uses I2C PCA9685 for all servo control
   - No GPIO pins needed for hardware control
   - Trigger handled by MainController, not hardware layer

3. **Cleaner Code:**
   - Removed 70+ lines of unused code
   - No more confusing proximity sensor options
   - Single responsibility: Camera only

### ✅ Testing Verification

**Before Fix:**
```bash
python3 main.py
❌ FATAL ERROR: Cannot determine SOC peripheral base address
RuntimeError: Cannot determine SOC peripheral base address
```

**After Fix:**
```bash
python3 main.py
✅ Running in correct virtual environment with OpenCV.
[1/3] Initializing Hardware Interface...
[HardwareInterface] Initializing...
[HardwareInterface] ✓ Selected: Raspberry Pi Camera Module
[HardwareInterface] ✓ Hardware initialization complete
[2/3] Initializing Servo Hardware (seven_servo)...
[3/3] Initializing Main Controller...
✅ System ready!
```

### 📁 Files Modified

```
src/hardware/hardware_interface_rpi.py
  - Removed: RPi.GPIO import
  - Removed: _initialize_gpio() method
  - Removed: Proximity sensor config
  - Simplified: check_trigger() method
  - Removed: GPIO cleanup
  - Updated: Documentation
```

### 🚀 Impact

**Before:**
- ❌ Error on Raspberry Pi 5
- ❌ Confusing proximity sensor config
- ❌ 70+ lines of dead code

**After:**
- ✅ Works on Raspberry Pi 5
- ✅ Clean, focused code (camera only)
- ✅ No GPIO dependencies
- ✅ I2C-only architecture (PCA9685)

### 📝 Related Components

**Trigger Logic Now Handled By:**
- `src/core/main_controller.py` - FSM with button or timer triggers
- User presses button OR system uses timed intervals
- No proximity sensor needed

**Servo Control Handled By:**
- `src/hardware/seven_servo_hardware.py` - Via I2C PCA9685
- Channels 0-6 for all servos
- No GPIO PWM used

---

**Status:** ✅ PRODUCTION READY
**Tested:** Raspberry Pi 5 (Bookworm, Python 3.13)
**Compatibility:** RPi 4/5, I2C PCA9685 only
