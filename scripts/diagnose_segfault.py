#!/usr/bin/env python3
"""
Diagnostic Script for Segmentation Fault
Tests each component separately to identify crash source
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_opencv():
    """Test OpenCV import"""
    print("=" * 60)
    print("TEST 1: OpenCV Import")
    print("=" * 60)
    try:
        import cv2
        print(f"✓ OpenCV version: {cv2.__version__}")
        return True
    except Exception as e:
        print(f"✗ OpenCV FAILED: {e}")
        return False

def test_picamera2():
    """Test PiCamera2 import and init"""
    print("\n" + "=" * 60)
    print("TEST 2: PiCamera2")
    print("=" * 60)
    try:
        from picamera2 import Picamera2
        print("✓ PiCamera2 import OK")
        
        # Try to initialize
        print("  Initializing camera...")
        cam = Picamera2()
        print(f"✓ PiCamera2 initialized")
        
        # Configure
        config = cam.create_still_configuration(main={"size": (640, 480)})
        cam.configure(config)
        print("✓ PiCamera2 configured")
        
        # Start (this might segfault!)
        cam.start()
        print("✓ PiCamera2 started")
        
        # Capture test
        import time
        time.sleep(1)
        frame = cam.capture_array()
        print(f"✓ Frame captured: {frame.shape}")
        
        cam.stop()
        cam.close()
        print("✓ PiCamera2 test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ PiCamera2 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tflite_import():
    """Test TFLite runtime import"""
    print("\n" + "=" * 60)
    print("TEST 3: TFLite Runtime Import")
    print("=" * 60)
    
    # Try tflite_runtime
    try:
        import tflite_runtime.interpreter as tflite
        print("✓ tflite_runtime available")
        return True, 'tflite_runtime'
    except ImportError as e:
        print(f"✗ tflite_runtime not available: {e}")
    
    # Try tensorflow
    try:
        import tensorflow as tf
        print(f"✓ tensorflow available: {tf.__version__}")
        return True, 'tensorflow'
    except ImportError as e:
        print(f"✗ tensorflow not available: {e}")
        return False, None

def test_tflite_model():
    """Test loading TFLite model"""
    print("\n" + "=" * 60)
    print("TEST 4: TFLite Model Loading")
    print("=" * 60)
    
    model_paths = [
        'models/model.tflite',
        'models/model_quant_infer.tflite',
        'models/model_float32_infer.tflite'
    ]
    
    # Find model
    model_path = None
    for path in model_paths:
        if os.path.exists(path):
            model_path = path
            break
    
    if not model_path:
        print(f"✗ No model file found in: {model_paths}")
        return False
    
    print(f"  Model: {model_path}")
    print(f"  Size: {os.path.getsize(model_path)} bytes")
    
    # Try tflite_runtime first
    try:
        import tflite_runtime.interpreter as tflite
        print("  Using tflite_runtime...")
        
        interpreter = tflite.Interpreter(model_path=model_path)
        print("✓ Model loaded with tflite_runtime")
        
        interpreter.allocate_tensors()
        print("✓ Tensors allocated")
        
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print(f"✓ Input shape: {input_details[0]['shape']}")
        print(f"✓ Output shape: {output_details[0]['shape']}")
        
        return True
        
    except Exception as e:
        print(f"✗ tflite_runtime FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    # Fallback to tensorflow
    try:
        import tensorflow as tf
        print("  Using tensorflow.lite...")
        
        interpreter = tf.lite.Interpreter(model_path=model_path)
        print("✓ Model loaded with tensorflow.lite")
        
        interpreter.allocate_tensors()
        print("✓ Tensors allocated")
        
        return True
        
    except Exception as e:
        print(f"✗ tensorflow.lite FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gpio():
    """Test GPIO"""
    print("\n" + "=" * 60)
    print("TEST 5: GPIO")
    print("=" * 60)
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        print("✓ GPIO initialized")
        GPIO.cleanup()
        return True
    except Exception as e:
        print(f"✗ GPIO FAILED: {e}")
        return False

def test_full_classifier():
    """Test full WasteClassifier initialization"""
    print("\n" + "=" * 60)
    print("TEST 6: WasteClassifier Full Init")
    print("=" * 60)
    
    try:
        from src.core.waste_classifier import WasteClassifier
        
        model_paths = [
            'models/model.tflite',
            'models/model_quant_infer.tflite',
            'models/model_float32_infer.tflite'
        ]
        
        model_path = None
        for path in model_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if not model_path:
            print("✗ No model file found")
            return False
        
        print(f"  Initializing classifier with {model_path}...")
        classifier = WasteClassifier(model_path=model_path, labels_path='models/labels.txt')
        print("✓ WasteClassifier initialized")
        
        # Test prediction with dummy image
        import numpy as np
        dummy_image = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        
        print("  Testing prediction...")
        result = classifier.predict_with_all_scores(dummy_image)
        print(f"✓ Prediction OK: {result['label']} ({result['confidence']:.2%})")
        
        return True
        
    except Exception as e:
        print(f"✗ WasteClassifier FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("SEGMENTATION FAULT DIAGNOSTIC")
    print("=" * 60)
    print("\nTesting components individually...\n")
    
    results = {}
    
    # Run tests
    results['OpenCV'] = test_opencv()
    results['PiCamera2'] = test_picamera2()
    
    tflite_ok, tflite_type = test_tflite_import()
    results['TFLite Import'] = tflite_ok
    
    if tflite_ok:
        results['TFLite Model'] = test_tflite_model()
    else:
        results['TFLite Model'] = False
        print("\n⚠️  Skipping model test (no TFLite runtime)")
    
    results['GPIO'] = test_gpio()
    results['Full Classifier'] = test_full_classifier()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:12} {test_name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed!")
        print("Segfault might be timing or memory issue.")
        print("\nTry:")
        print("  1. Disable PiCamera2 (use OpenCV webcam)")
        print("  2. Use smaller model (quantized)")
        print("  3. Increase swap memory")
    else:
        print("\n✗ Some tests failed!")
        print("Fix the failed components first.")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗✗✗ DIAGNOSTIC CRASHED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
