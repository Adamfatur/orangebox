#!/usr/bin/env python3
"""
Orange Box - System Diagnostic Tool
Checks all dependencies and hardware connections
"""

import sys
import subprocess

def print_header(title):
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70 + "\n")

def check_python_module(name, import_name=None):
    """Check if Python module is available"""
    if import_name is None:
        import_name = name
    
    try:
        __import__(import_name)
        print(f"  ✅ {name:30} INSTALLED")
        return True
    except ImportError as e:
        print(f"  ❌ {name:30} MISSING")
        print(f"     Error: {e}")
        return False

def check_system_command(cmd, name):
    """Check if system command exists"""
    try:
        result = subprocess.run(['which', cmd], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ {name:30} {result.stdout.strip()}")
            return True
        else:
            print(f"  ❌ {name:30} NOT FOUND")
            return False
    except:
        print(f"  ❌ {name:30} CHECK FAILED")
        return False

def check_service(service_name):
    """Check if systemd service is running"""
    try:
        result = subprocess.run(['systemctl', 'is-active', service_name], 
                              capture_output=True, text=True)
        status = result.stdout.strip()
        if status == 'active':
            print(f"  ✅ {service_name:30} RUNNING")
            return True
        else:
            print(f"  ⚠️  {service_name:30} {status.upper()}")
            return False
    except:
        print(f"  ❌ {service_name:30} CHECK FAILED")
        return False

def check_i2c():
    """Check I2C devices"""
    try:
        result = subprocess.run(['i2cdetect', '-y', '1'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout
            # Check for PCA9685 (usually at 0x40)
            if '40' in output:
                print(f"  ✅ I2C Device (PCA9685)       DETECTED at 0x40")
                return True
            else:
                print(f"  ⚠️  I2C Device (PCA9685)       NOT FOUND at 0x40")
                print(f"     Run: i2cdetect -y 1")
                return False
        else:
            print(f"  ⚠️  I2C                          Cannot scan (i2c-tools missing)")
            return False
    except FileNotFoundError:
        print(f"  ⚠️  I2C                          i2c-tools not installed")
        return False

def main():
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║          🔍 ORANGE BOX - SYSTEM DIAGNOSTIC 🔍                ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    all_ok = True
    
    # Check Python version
    print_header("Python Environment")
    print(f"  Python Version: {sys.version.split()[0]}")
    print(f"  Executable: {sys.executable}")
    
    # Check core Python modules
    print_header("Core Python Modules")
    modules = {
        'NumPy': 'numpy',
        'OpenCV': 'cv2',
        'TensorFlow Lite': 'tflite_runtime.interpreter',
        'PyMySQL': 'pymysql',
        'PySerial': 'serial',
        'PyNMEA2': 'pynmea2',
    }
    
    for name, import_name in modules.items():
        if not check_python_module(name, import_name):
            all_ok = False
    
    # Check Adafruit modules
    print_header("Adafruit Hardware Modules")
    adafruit_modules = {
        'Adafruit Blinka': 'board',
        'Adafruit PCA9685': 'adafruit_pca9685',
        'Adafruit ServoKit': 'adafruit_servokit',
        'Adafruit Motor': 'adafruit_motor',
    }
    
    for name, import_name in adafruit_modules.items():
        if not check_python_module(name, import_name):
            all_ok = False
    
    # Check Raspberry Pi modules
    print_header("Raspberry Pi Modules")
    rpi_modules = {
        'RPi.GPIO': 'RPi.GPIO',
        'picamera2': 'picamera2',
    }
    
    for name, import_name in rpi_modules.items():
        check_python_module(name, import_name)  # Don't fail on these
    
    # Check system commands
    print_header("System Commands")
    commands = {
        'i2cdetect': 'I2C Tools',
        'gpspipe': 'GPSD Client',
        'vcgencmd': 'Raspberry Pi Utils',
    }
    
    for cmd, name in commands.items():
        check_system_command(cmd, name)
    
    # Check I2C devices
    print_header("Hardware Detection")
    check_i2c()
    
    # Check services
    print_header("System Services")
    services = ['gpsd']
    
    for service in services:
        check_service(service)
    
    # Check GPIO permissions
    print_header("Permissions")
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()
        print(f"  ✅ GPIO Access                 OK")
    except:
        print(f"  ⚠️  GPIO Access                 Limited (need sudo or gpio group)")
    
    # Final summary
    print_header("SUMMARY")
    
    if all_ok:
        print("  ✅ All critical dependencies installed!")
        print("  ✅ System ready to run")
        print("\n  Run: python3 main.py")
    else:
        print("  ❌ Some dependencies are missing")
        print("\n  Fix with:")
        print("     bash scripts/fix_dependencies.sh")
        print("\n  Or install manually:")
        print("     pip3 install -r requirements.txt")
    
    print("\n" + "="*70 + "\n")
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())
