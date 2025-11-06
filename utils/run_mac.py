"""
Simplified launcher for macOS development
Bypasses venv check for easier testing on macOS
"""

import sys
import os

# Skip venv check for macOS
os.environ['SKIP_VENV_CHECK'] = '1'

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import argparse
import config
from dotenv import load_dotenv

def main():
    """Main function untuk menjalankan aplikasi."""
    
    # Import dependencies
    try:
        from core.waste_classifier import WasteClassifier
        from core.mock_classifier import MockClassifier
        from core.main_controller import MainController
    except ModuleNotFoundError as e:
        print(f"\n❌ Dependency error: {e}")
        print("\n💡 Quick fix:")
        print("   pip3 install -r requirements.txt")
        return 1
    
    # Auto-select hardware interface based on config
    if config.PLATFORM == 'rpi':
        from hardware.hardware_interface_rpi import HardwareInterface
    else:
        from hardware.hardware_interface_mock import HardwareInterface
    
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

    # Helper: auto-select model if missing
    def _auto_select_model(base_dir: str) -> str:
        models_dir = os.path.join(base_dir, 'models')
        preferred = [
            'model_quant_infer.tflite',
            'model_quant.tflite',
            'model_float32_infer.tflite',
            'model.tflite'
        ]
        for name in preferred:
            candidate = os.path.join(models_dir, name)
            if os.path.exists(candidate):
                return candidate
        if os.path.exists(models_dir):
            for f in os.listdir(models_dir):
                if f.endswith('.tflite'):
                    return os.path.join(models_dir, f)
        return None
    
    # Print banner
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║               🧡 ORANGE BOX SYSTEM 🧡                        ║
    ║        Intelligent Waste Classification & Sorting           ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    
    # Initialize components
    print("🔧 Initializing components...\n")
    
    try:
        # Initialize hardware interface
        if args.camera is None:
            print(f"[1/3] Initializing Hardware Interface (Auto-detect camera)...")
        else:
            print(f"[1/3] Initializing Hardware Interface (Camera {args.camera})...")
        
        # Force camera init before any TFLite operations
        print("      → Camera initialization starting...")
        hw = HardwareInterface(camera_index=args.camera)
        print("      ✓ Hardware Interface initialized")
        print("      ✓ Camera locked and ready\n")
    except Exception as e:
        print(f"\n❌ Failed to initialize hardware interface: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    try:
        # Now safe to load TFLite model (camera already allocated)
        print("[2/3] Initializing Waste Classifier...")
        
        if args.test:
            print("      ⚠️  TEST MODE: Using mock classifier (random predictions)")
            classifier = MockClassifier()
            print("      ✓ Mock Classifier initialized")
        else:
            # Real classifier dengan auto-fallback
            auto_selected = False
            if not os.path.exists(args.model):
                selected = _auto_select_model(script_dir)
                if selected:
                    rel = os.path.relpath(selected, script_dir)
                    print(f"      ℹ️  Model tidak ditemukan di path yang diberikan.")
                    print(f"      🔎 Auto-selected model: {rel}")
                    args.model = selected
                    auto_selected = True
                else:
                    print("      ⚠️  Tidak ada file model ditemukan. Beralih ke TEST mode (Mock).")
                    args.test = True
            
            if args.test:
                # Fallback ke mock jika model tidak ada
                classifier = MockClassifier()
                print("      ✓ Mock Classifier initialized (auto-fallback)")
            else:
                # Try to initialize real classifier
                try:
                    classifier = WasteClassifier(model_path=args.model, labels_path=args.labels)
                    print("      ✓ Waste Classifier initialized")
                except Exception as e:
                    print(f"      ⚠️  WasteClassifier failed: {e}")
                    print("      → Falling back to TEST mode (Mock Classifier)")
                    classifier = MockClassifier()
                    print("      ✓ Mock Classifier initialized (auto-fallback)")
                    args.test = True
        
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
            print(f"   Camera: Auto-detect")

        print("\n🚀 Starting main application loop... Press 'q' in the camera window to exit.")
        controller.run()

    except KeyboardInterrupt:
        print("\n\n🛑 User interrupted. Shutting down gracefully...")
        if 'hw' in locals() and hw:
            hw.cleanup()
        print("Goodbye!")
        return 0
    except Exception as e:
        print(f"\n❌ An unhandled error occurred during runtime: {e}")
        import traceback
        traceback.print_exc()
        if 'hw' in locals() and hw:
            hw.cleanup()
        return 1


if __name__ == "__main__":
    sys.exit(main())
