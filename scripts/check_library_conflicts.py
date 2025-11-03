#!/usr/bin/env python3
"""
Root Cause Analyzer untuk Segmentation Fault di Raspberry Pi 5
Mengidentifikasi konflik library dan instalasi yang salah

Jalankan dengan: python3 scripts/check_library_conflicts.py
"""

import sys
import os
import subprocess
import importlib.util


def print_section(title):
    print("\n" + "━"*70)
    print(f"  {title}")
    print("━"*70)


def check_venv():
    """Cek apakah berjalan di virtual environment"""
    print_section("1️⃣  VIRTUAL ENVIRONMENT")
    
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version.split()[0]}")
    
    if in_venv:
        print(f"✅ In venv: {sys.prefix}")
        return True
    else:
        print("❌ NOT in venv - CRITICAL ERROR!")
        print("\n💡 SOLUSI:")
        print("   Jangan jalankan dengan global Python")
        print("   Gunakan: python3 main.py (akan auto-fix ke venv)")
        return False


def check_tflite():
    """Cek tflite_runtime installation"""
    print_section("2️⃣  TFLITE_RUNTIME")
    
    try:
        import tflite_runtime.interpreter as tflite
        location = tflite.__file__
        print(f"✅ Found: {location}")
        
        # Harus dari /usr/lib/ (APT), bukan site-packages (pip)
        if '/usr/lib/' in location or '/usr/local/lib/' in location:
            print("✅ Source: APT system package (CORRECT)")
            return True
        elif 'site-packages' in location:
            print("❌ Source: pip package (WRONG - bisa segfault!)")
            print("\n💡 SOLUSI:")
            print("   pip uninstall tflite-runtime")
            print("   sudo apt install python3-tflite-runtime")
            return False
        else:
            print(f"⚠️  Unknown source")
            return None
            
    except ImportError as e:
        print(f"❌ NOT installed: {e}")
        print("\n💡 SOLUSI:")
        print("   sudo apt install python3-tflite-runtime")
        return False


def check_tensorflow():
    """Cek TensorFlow - TIDAK BOLEH ADA!"""
    print_section("3️⃣  TENSORFLOW (Must NOT exist)")
    
    try:
        import tensorflow as tf
        print(f"❌ FOUND: {tf.__file__}")
        print(f"   Version: {tf.__version__}")
        print("\n🚨 CRITICAL: Ini penyebab utama segfault!")
        print("   TensorFlow full package konflik dengan libcamera di RPi5")
        print("\n💡 SOLUSI:")
        print("   pip uninstall tensorflow tensorflow-lite")
        print("   rm -rf ~/.local/lib/python*/site-packages/tensorflow*")
        return False
        
    except ImportError:
        print("✅ Not installed (CORRECT)")
        return True


def check_opencv():
    """Cek OpenCV source dan duplikasi"""
    print_section("4️⃣  OPENCV")
    
    try:
        import cv2
        location = cv2.__file__
        print(f"✅ Found: {location}")
        print(f"   Version: {cv2.__version__}")
        
        # Cek apakah dari pip (benar) atau apt (salah)
        if 'site-packages' in location:
            print("✅ Source: pip in venv (CORRECT)")
            
            # Cek apakah ada duplikat dari apt
            apt_check = subprocess.run(
                ['dpkg', '-l', 'python3-opencv'],
                capture_output=True, text=True
            )
            if 'ii  python3-opencv' in apt_check.stdout:
                print("❌ KONFLIK: python3-opencv juga ada di APT!")
                print("\n💡 SOLUSI:")
                print("   sudo apt remove python3-opencv")
                return False
            else:
                return True
                
        elif '/usr/lib/' in location:
            print("❌ Source: APT system package (WRONG)")
            print("   Ini menyebabkan konflik dengan pip version")
            print("\n💡 SOLUSI:")
            print("   sudo apt remove python3-opencv")
            print("   pip install opencv-python")
            return False
            
    except ImportError as e:
        print(f"❌ NOT installed: {e}")
        return False
    
    return True


def check_numpy():
    """Cek NumPy"""
    print_section("5️⃣  NUMPY")
    
    try:
        import numpy as np
        location = np.__file__
        print(f"✅ Found: {location}")
        print(f"   Version: {np.__version__}")
        
        if 'site-packages' in location:
            print("✅ Source: pip in venv (CORRECT)")
        elif '/usr/lib/' in location:
            print("⚠️  Source: APT (bisa konflik jika opencv dari pip)")
            
        return True
        
    except ImportError as e:
        print(f"❌ NOT installed: {e}")
        return False


def check_adafruit():
    """Cek redundant Adafruit libs"""
    print_section("6️⃣  ADAFRUIT LIBRARIES")
    
    has_servokit = importlib.util.find_spec("adafruit_servokit") is not None
    has_motor = importlib.util.find_spec("adafruit_motor") is not None
    
    print(f"adafruit-servokit: {'✅ Found' if has_servokit else '❌ Not found'}")
    print(f"adafruit-motor: {'✅ Found' if has_motor else '❌ Not found'}")
    
    if has_servokit and has_motor:
        print("\n⚠️  REDUNDANT: servokit sudah include motor library")
        print("💡 SOLUSI:")
        print("   pip uninstall adafruit-motor")
        return False
    elif has_servokit:
        print("✅ Servokit only (CORRECT)")
        return True
    else:
        return None


def test_model_load():
    """Test actual model loading"""
    print_section("7️⃣  MODEL LOAD TEST")
    
    model_path = "models/model_quant_infer.tflite"
    if not os.path.exists(model_path):
        print(f"⚠️  Model not found: {model_path}")
        return None
    
    print(f"Model: {model_path}")
    print(f"Size: {os.path.getsize(model_path):,} bytes")
    
    try:
        print("\n1. Importing tflite_runtime...")
        import tflite_runtime.interpreter as tflite
        print("   ✅ Import OK")
        
        print("2. Creating Interpreter...")
        interpreter = tflite.Interpreter(model_path=model_path)
        print("   ✅ Interpreter created")
        
        print("3. Allocating tensors...")
        interpreter.allocate_tensors()
        print("   ✅ Tensors allocated")
        
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print(f"\n✅ MODEL LOAD SUCCESS!")
        print(f"   Input: {input_details[0]['shape']}")
        print(f"   Output: {output_details[0]['shape']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ MODEL LOAD FAILED!")
        print(f"   Error: {e}")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        return False


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║      🔍 RASPBERRY PI 5 - LIBRARY CONFLICT CHECKER 🔍        ║")
    print("║          Root Cause Analysis untuk Segfault                ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    
    issues = []
    warnings = []
    
    # Run checks
    if not check_venv():
        issues.append("Tidak di virtual environment")
    
    tflite_ok = check_tflite()
    if tflite_ok is False:
        issues.append("tflite_runtime dari pip (harus APT)")
    elif tflite_ok is None:
        issues.append("tflite_runtime tidak terinstall")
    
    if not check_tensorflow():
        issues.append("TensorFlow terdeteksi (CRITICAL)")
    
    if not check_opencv():
        issues.append("OpenCV conflict")
    
    check_numpy()  # Info only
    
    if check_adafruit() is False:
        warnings.append("Adafruit libs redundant")
    
    # Model load test
    model_ok = test_model_load()
    if model_ok is False:
        issues.append("Model gagal load")
    
    # Final summary
    print("\n" + "="*70)
    print("  📊 SUMMARY")
    print("="*70)
    
    if not issues and not warnings:
        print("\n✅ ✅ ✅  SEMUA OK - TIDAK ADA MASALAH!  ✅ ✅ ✅")
        print("\nSegfault seharusnya sudah fixed!")
        print("Silakan jalankan: python3 main.py")
        
    else:
        if issues:
            print(f"\n🚨 {len(issues)} CRITICAL ISSUE(S):")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} Warning(s):")
            for i, warn in enumerate(warnings, 1):
                print(f"   {i}. {warn}")
        
        print("\n💡 SOLUSI LENGKAP:")
        print("   cd /home/orangebox/ob-main/orangebox-1.1")
        print("   bash deployment/fix_raspberry.sh")
    
    print("\n")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
