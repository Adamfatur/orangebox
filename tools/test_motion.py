"""
Test Motion Detection - Untuk test sistem tanpa ganggu training
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import config
from src.core.waste_classifier import WasteClassifier

# Import hardware interface berdasarkan platform
if config.PLATFORM == 'mac':
    from src.hardware.hardware_interface_mock import HardwareInterfaceMock as HardwareInterface
else:
    from src.hardware.hardware_interface_rpi import HardwareInterfaceRPi as HardwareInterface

from src.core.main_controller import MainController

def main():
    """Main function untuk test motion detection."""
    
    print("="*70)
    print("🧪 MOTION DETECTION TEST - OrangeBox")
    print("="*70)
    print(f"Platform: {config.PLATFORM}")
    print(f"Motion Threshold: {config.MOTION_THRESHOLD} pixels")
    print(f"Stabilization Frames: {config.STABILIZATION_FRAMES}")
    print(f"Confidence Threshold: {config.CONFIDENCE_THRESHOLD}")
    print("="*70)
    print("\n💡 INSTRUKSI:")
    print("   1. Biarkan background kosong dulu (sistem akan initialize)")
    print("   2. Letakkan sampah di depan kamera")
    print("   3. Sistem akan auto-detect objek dan klasifikasi")
    print("   4. Tekan 'q' untuk quit")
    print("="*70)
    print()
    
    # Gunakan model dummy dulu (nanti ganti setelah training selesai)
    model_path = "models/backup_v1/model_quant.tflite"
    if not os.path.exists(model_path):
        print(f"⚠️  Model tidak ditemukan: {model_path}")
        print("   Sistem akan tetap jalan dengan motion detection saja")
        model_path = None
    
    try:
        # Initialize classifier
        if model_path:
            classifier = WasteClassifier(model_path)
            print("✅ Classifier initialized")
        else:
            classifier = None
            print("⚠️  Running without classifier (motion detection only)")
        
        # Initialize hardware
        hardware = HardwareInterface()
        print("✅ Hardware initialized")
        
        # Initialize controller
        controller = MainController(classifier, hardware)
        print("✅ Controller initialized")
        print()
        
        # Start system
        controller.start()
        
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'controller' in locals():
            controller.stop()
        print("\n✅ Test selesai")

if __name__ == "__main__":
    main()
