"""
Main Application - Orange Box System
Entry point untuk menjalankan sistem pemilah sampah cerdas lengkap.

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

import os
import sys
import argparse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import config
import config

from core.waste_classifier import WasteClassifier
from core.main_controller import MainController

# Auto-select hardware interface based on config
if config.PLATFORM == 'rpi':
    from hardware.hardware_interface_rpi import HardwareInterface
else:
    from hardware.hardware_interface_mock import HardwareInterface


def check_model_files():
    """Check apakah file model tersedia."""
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    model_path = os.path.join(model_dir, 'model.tflite')
    labels_path = os.path.join(model_dir, 'labels.txt')
    
    model_exists = os.path.exists(model_path)
    labels_exists = os.path.exists(labels_path)
    
    if not model_exists:
        print("\n❌ ERROR: File 'model.tflite' tidak ditemukan!")
        print(f"\n� Letakkan model di folder: {model_dir}/")
        print("\n�📋 Langkah-langkah untuk mendapatkan model:")
        print("1. Buka Google Teachable Machine: https://teachablemachine.withgoogle.com/")
        print("2. Pilih 'Image Project' → 'Standard image model'")
        print("3. Buat 2 class: 'ORGANIC' dan 'ANORGANIC'")
        print("4. Kumpulkan dataset (minimal 100+ gambar per class)")
        print("5. Train model dan export sebagai TensorFlow Lite")
        print(f"6. Download dan letakkan 'model.tflite' dan 'labels.txt' di: {model_dir}/")
        print("\nAtau gunakan --test mode untuk testing dengan mock classifier")
        return False
    
    if not labels_exists:
        print("\n⚠️  WARNING: File 'labels.txt' tidak ditemukan!")
        print("Program akan menggunakan default labels: ['ORGANIC', 'ANORGANIC']")
    
    return True


def print_banner():
    """Print banner aplikasi."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║               🧡 ORANGE BOX SYSTEM 🧡                        ║
    ║        Intelligent Waste Classification & Sorting           ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main function untuk menjalankan aplikasi."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Orange Box System - Intelligent Waste Classification')
    parser.add_argument('--test', action='store_true', 
                       help='Run in test mode with mock classifier (tanpa model file)')
    parser.add_argument('--camera', type=int, default=None, 
                       help='Camera index (default: auto-detect, use 0-4 for manual selection)')
    parser.add_argument('--confidence', type=float, default=config.CONFIDENCE_THRESHOLD, 
                       help=f'Minimum confidence threshold (default: {config.CONFIDENCE_THRESHOLD})')
    parser.add_argument('--model', type=str, default='models/model.tflite', 
                       help='Path to TFLite model file (default: models/model.tflite)')
    parser.add_argument('--labels', type=str, default='models/labels.txt', 
                       help='Path to labels file (default: models/labels.txt)')
    
    args = parser.parse_args()
    
    # Convert relative paths to absolute
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(args.model):
        args.model = os.path.join(script_dir, args.model)
    if not os.path.isabs(args.labels):
        args.labels = os.path.join(script_dir, args.labels)
    
    # Print banner
    print_banner()
    
    try:
        # Initialize components
        print("🔧 Initializing components...\n")
        
        # Initialize hardware interface
        if args.camera is None:
            print(f"[1/3] Initializing Hardware Interface (Auto-detect camera)...")
        else:
            print(f"[1/3] Initializing Hardware Interface (Camera {args.camera})...")
        hw = HardwareInterface(camera_index=args.camera)
        print("      ✓ Hardware Interface initialized\n")
        
        # Initialize classifier
        print("[2/3] Initializing Waste Classifier...")
        
        if args.test:
            print("      ⚠️  TEST MODE: Using mock classifier (random predictions)")
            
            # Mock classifier untuk testing
            class MockClassifier:
                def __init__(self):
                    self.labels = ['ORGANIC', 'ANORGANIC']
                    print("      ✓ Mock Classifier initialized")
                
                def predict_with_all_scores(self, image):
                    import random
                    import time
                    time.sleep(0.1)  # Simulasi inference time
                    
                    is_organic = random.choice([True, False])
                    confidence = random.uniform(0.65, 0.98)
                    
                    if is_organic:
                        return {
                            'label': 'ORGANIC',
                            'confidence': confidence,
                            'all_scores': {
                                'ORGANIC': confidence, 
                                'ANORGANIC': 1.0 - confidence
                            }
                        }
                    else:
                        return {
                            'label': 'ANORGANIC',
                            'confidence': confidence,
                            'all_scores': {
                                'ORGANIC': 1.0 - confidence,
                                'ANORGANIC': confidence
                            }
                        }
            
            classifier = MockClassifier()
        else:
            # Real classifier
            if not os.path.exists(args.model):
                print(f"\n❌ ERROR: Model file tidak ditemukan: {args.model}")
                print("\n� Opsi:")
                print("1. Gunakan model yang ada:")
                models_dir = os.path.join(script_dir, 'models')
                if os.path.exists(models_dir):
                    tflite_files = [f for f in os.listdir(models_dir) if f.endswith('.tflite')]
                    if tflite_files:
                        for tf in tflite_files:
                            print(f"   python3 main.py --model models/{tf}")
                print("2. Train model baru: python3 train_model.py")
                print("3. Test tanpa model: python3 main.py --test")
                return 1
            
            classifier = WasteClassifier(model_path=args.model, labels_path=args.labels)
            print("      ✓ Waste Classifier initialized")
        
        print()
        
        # Initialize main controller
        print("[3/3] Initializing Main Controller...")
        controller = MainController(classifier, hw)
        controller.confidence_threshold = args.confidence
        print("      ✓ Main Controller initialized")
        
        print("\n" + "="*70)
        print("✓ All components initialized successfully!")
        print("="*70)
        
        # Print system info
        print("\n📊 System Configuration:")
        print(f"   Mode: {'TEST (Mock Classifier)' if args.test else 'PRODUCTION'}")
        if hasattr(hw, 'camera_config') and hw.camera_config:
            print(f"   Camera: {hw.camera_config['name']} ({hw.camera_config.get('resolution', 'N/A')})")
        elif args.camera is not None:
            print(f"   Camera Index: {args.camera}")
        else:
            print(f"   Camera: Auto-detected")
        print(f"   Confidence Threshold: {args.confidence:.0%}")
        if not args.test:
            print(f"   Model: {args.model}")
            print(f"   Labels: {classifier.labels}")
        print()
        
        # Run system
        print("🚀 Starting Orange Box System...")
        print("   Press 't' to trigger sorting")
        print("   Press 'q' to quit")
        print()
        
        controller.run()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user (Ctrl+C)")
        if 'hw' in locals():
            hw.cleanup()
        return 0
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        if 'hw' in locals():
            hw.cleanup()
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
