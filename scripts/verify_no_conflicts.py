#!/usr/bin/env python3
"""
Verify No Library Conflicts - Raspberry Pi
Script untuk memastikan tidak ada konflik atau duplikasi library.
"""

import sys
import os

def check_library_conflicts():
    """Check for potential library conflicts."""
    print("=" * 70)
    print("🔍 CHECKING FOR LIBRARY CONFLICTS ON RASPBERRY PI")
    print("=" * 70)
    print()
    
    issues = []
    warnings = []
    
    # 1. Check NumPy
    print("1️⃣  Checking NumPy...")
    try:
        import numpy as np
        print(f"   ✓ NumPy version: {np.__version__}")
        print(f"   ✓ NumPy location: {np.__file__}")
        
        # Check if it's from system or venv
        if '/usr/lib/' in np.__file__ or '/usr/local/lib/' in np.__file__:
            warnings.append("NumPy is from system packages (not venv). Consider using venv version.")
    except ImportError as e:
        issues.append(f"NumPy import failed: {e}")
        print(f"   ✗ NumPy not found!")
    print()
    
    # 2. Check OpenCV
    print("2️⃣  Checking OpenCV...")
    try:
        import cv2
        print(f"   ✓ OpenCV version: {cv2.__version__}")
        print(f"   ✓ OpenCV location: {cv2.__file__}")
        
        # Check if it's from system or venv
        if '/usr/lib/' in cv2.__file__ or '/usr/local/lib/' in cv2.__file__:
            warnings.append("OpenCV is from system packages. This is OK if using --system-site-packages.")
    except ImportError as e:
        issues.append(f"OpenCV import failed: {e}")
        print(f"   ✗ OpenCV not found!")
    print()
    
    # 3. Check TFLite Runtime
    print("3️⃣  Checking TensorFlow Lite Runtime...")
    try:
        import tflite_runtime.interpreter as tflite
        print(f"   ✓ tflite_runtime available")
        # Try to get location
        try:
            import tflite_runtime
            print(f"   ✓ tflite_runtime location: {tflite_runtime.__file__}")
            
            # MUST be from system (apt package)
            if '/usr/lib/' not in tflite_runtime.__file__:
                warnings.append("tflite_runtime is NOT from apt (should be /usr/lib/). May cause issues on RPi.")
        except:
            pass
    except ImportError as e:
        issues.append(f"tflite_runtime not found: {e}")
        print(f"   ✗ tflite_runtime not available!")
        print(f"   → Install with: sudo apt install python3-tflite-runtime")
    print()
    
    # 4. Check TensorFlow (should NOT exist)
    print("4️⃣  Checking TensorFlow (should NOT be installed)...")
    try:
        import tensorflow
        warnings.append(f"TensorFlow is installed! Version: {tensorflow.__version__}. This may cause segfaults on RPi.")
        print(f"   ⚠️  TensorFlow found: {tensorflow.__version__}")
        print(f"   ⚠️  Location: {tensorflow.__file__}")
        print(f"   ⚠️  RECOMMENDATION: Uninstall TensorFlow on RPi to avoid segfaults")
        print(f"   → pip uninstall tensorflow")
    except ImportError:
        print(f"   ✓ TensorFlow not installed (GOOD!)")
    print()
    
    # 5. Check RPi.GPIO
    print("5️⃣  Checking RPi.GPIO...")
    try:
        import RPi.GPIO as GPIO
        print(f"   ✓ RPi.GPIO available")
        print(f"   ✓ RPi.GPIO location: {GPIO.__file__}")
    except (ImportError, RuntimeError) as e:
        if sys.platform != 'linux':
            print(f"   ℹ️  RPi.GPIO not available (expected on non-RPi systems)")
        else:
            warnings.append(f"RPi.GPIO not found on Linux system: {e}")
            print(f"   ⚠️  RPi.GPIO not found: {e}")
    print()
    
    # 6. Check Adafruit Libraries
    print("6️⃣  Checking Adafruit Libraries...")
    adafruit_libs = [
        ('adafruit_blinka', 'Blinka'),
        ('adafruit_pca9685', 'PCA9685'),
        ('adafruit_servokit', 'ServoKit'),
    ]
    
    for module_name, display_name in adafruit_libs:
        try:
            module = __import__(module_name)
            print(f"   ✓ {display_name} available")
            if hasattr(module, '__file__'):
                print(f"     Location: {module.__file__}")
        except ImportError:
            warnings.append(f"Adafruit {display_name} not installed (optional for servo control)")
            print(f"   ⚠️  {display_name} not available (optional)")
    print()
    
    # 7. Check for duplicate motor libraries
    print("7️⃣  Checking for duplicate motor libraries...")
    has_motor = False
    has_servokit = False
    try:
        import adafruit_motor
        has_motor = True
        print(f"   ℹ️  adafruit_motor found")
    except ImportError:
        pass
    
    try:
        import adafruit_servokit
        has_servokit = True
        print(f"   ℹ️  adafruit_servokit found")
    except ImportError:
        pass
    
    if has_motor and has_servokit:
        warnings.append("Both adafruit_motor and adafruit_servokit installed. ServoKit already includes motor functionality.")
        print(f"   ⚠️  Redundant: Both motor libraries installed")
        print(f"   → ServoKit already includes motor control, adafruit_motor not needed")
    elif not has_motor and not has_servokit:
        print(f"   ℹ️  No motor libraries (OK if not using PCA9685 servos)")
    else:
        print(f"   ✓ No duplicate motor libraries")
    print()
    
    # 8. Verify Virtual Environment
    print("8️⃣  Checking Virtual Environment...")
    venv = os.environ.get('VIRTUAL_ENV')
    if venv:
        print(f"   ✓ Running in virtual environment: {venv}")
    else:
        warnings.append("Not running in virtual environment. Use './start.sh' or 'source .venv/bin/activate'")
        print(f"   ⚠️  Not in virtual environment")
    print()
    
    # Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    if not issues and not warnings:
        print("✅ NO CONFLICTS DETECTED - All libraries are properly configured!")
        return 0
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} WARNING(S):")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    
    if issues:
        print(f"\n❌ {len(issues)} CRITICAL ISSUE(S):")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n🔧 RECOMMENDED ACTION:")
        print("   Run: ./install.sh")
        return 1
    
    if warnings and not issues:
        print("\n✅ No critical issues, but review warnings above.")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(check_library_conflicts())
