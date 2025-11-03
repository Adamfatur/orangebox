"""
Main Application - Orange Box System
Entry point untuk menjalankan sistem pemilah sampah cerdas lengkap.

Copyright (c) 2025 AF - OrangeBox Project
All rights reserved.
"""

import sys
import os
import argparse
import subprocess

# ==================================================================================
# CRITICAL: Auto-Fix Virtual Environment
# Jika tidak di venv yang benar, otomatis re-launch dengan venv atau install dulu.
# ==================================================================================
def check_and_fix_venv():
    """
    Memeriksa apakah script dijalankan di dalam virtual environment yang benar.
    Jika tidak, akan OTOMATIS re-launch dengan venv atau jalankan install.sh.
    """
    project_dir = os.path.abspath(os.path.dirname(__file__))
    venv_python = os.path.join(project_dir, '.venv', 'bin', 'python3')
    current_python = os.path.abspath(sys.executable)
    
    # Cek apakah current python adalah venv python
    if current_python == venv_python or current_python.startswith(os.path.join(project_dir, '.venv')):
        print("✅ Running in correct virtual environment.")
        return
    
    # Tidak di venv yang benar - coba auto-fix
    print("⚠️  Not running in virtual environment. Auto-fixing...")
    
    # Cek apakah venv ada
    if not os.path.exists(venv_python):
        print("📦 Virtual environment not found. Running install.sh...")
        install_script = os.path.join(project_dir, 'install.sh')
        
        if os.path.exists(install_script):
            try:
                subprocess.run(['bash', install_script], check=True, cwd=project_dir)
            except subprocess.CalledProcessError as e:
                print(f"❌ install.sh failed with code {e.returncode}")
                sys.exit(1)
        else:
            print("="*70)
            print("❌ ERROR: Virtual environment not found and install.sh missing!")
            print("="*70)
            print("Please run install.sh first:")
            print(f"  cd {project_dir}")
            print("  ./install.sh")
            print("="*70)
            sys.exit(1)
    
    # Re-launch dengan venv yang benar
    print(f"🔄 Re-launching with virtual environment: {venv_python}")
    print("")
    
    # Build command dengan semua arguments asli
    cmd = [venv_python, os.path.abspath(__file__)] + sys.argv[1:]
    
    # Replace current process dengan venv version
    os.execv(venv_python, cmd)

check_and_fix_venv()
# ==================================================================================

# Import dependencies after venv check
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import config
import config


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
    
    # CRITICAL: Auto-detect dan auto-install missing dependencies
    import platform
    import subprocess
    import os
    
    missing_deps = []
    
    # Check semua dependencies penting
    try:
        import cv2
    except ModuleNotFoundError:
        missing_deps.append('opencv')
    
    try:
        from adafruit_servokit import ServoKit
    except (ModuleNotFoundError, NotImplementedError):
        # NotImplementedError normal di macOS (adafruit-blinka hanya untuk Linux)
        if platform.system() == 'Linux':
            missing_deps.append('servokit')
    
    # Auto-fix jika ada yang missing di Raspberry Pi
    if missing_deps and platform.system() == 'Linux':
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    print("="*70)
                    print(f"⚠️  Dependencies tidak ditemukan: {', '.join(missing_deps)}")
                    print("="*70)
                    print("📍 Raspberry Pi detected - Auto-fixing...")
                    
                    # Check venv system-site-packages
                    venv_pyvenv = os.path.join(os.path.dirname(sys.executable), '..', 'pyvenv.cfg')
                    has_system_packages = False
                    if os.path.exists(venv_pyvenv):
                        with open(venv_pyvenv, 'r') as f:
                            if 'include-system-site-packages = true' in f.read():
                                has_system_packages = True
                    
                    # Fix venv jika perlu
                    if 'opencv' in missing_deps and not has_system_packages:
                        print("⚠️  Venv tidak punya akses ke system packages!")
                        print("🔧 Recreating venv with --system-site-packages...")
                        
                        venv_dir = os.path.join(os.getcwd(), '.venv')
                        if os.path.exists(venv_dir):
                            import shutil
                            shutil.rmtree(venv_dir)
                        
                        subprocess.run(['python3', '-m', 'venv', '--system-site-packages', '.venv'], check=True)
                        print("✓ Venv recreated")
                        print("\n🚀 Please run again: python3 main.py")
                        return 1
                    
                    # Install missing packages
                    if 'opencv' in missing_deps:
                        print("⚙️  Installing python3-opencv...")
                        subprocess.run(['sudo', 'apt-get', 'update', '-qq'], check=False)
                        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'python3-opencv'], check=False)
                    
                    if 'servokit' in missing_deps:
                        print("⚙️  Installing adafruit-servokit...")
                        subprocess.run([sys.executable, '-m', 'pip', 'install', 
                                      'adafruit-blinka', 
                                      'adafruit-circuitpython-pca9685', 
                                      'adafruit-circuitpython-servokit'], check=True)
                    
                    print("\n✓ Dependencies installed. Please run again: python3 main.py")
                    return 1
        except Exception as e:
            print(f"⚠️  Auto-fix error: {e}")
    
    # Tambahan auto-fix khusus Raspberry Pi untuk TFLite dan Database
    if platform.system() == 'Linux':
        try:
            with open('/proc/cpuinfo', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    # tflite-runtime (gunakan apt, lebih stabil di RPi)
                    try:
                        import tflite_runtime.interpreter as _tfl
                    except Exception:
                        print("⚙️  Installing tflite-runtime (apt)...")
                        subprocess.run(['sudo', 'apt-get', 'update', '-qq'], check=False)
                        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'python3-tflite-runtime'], check=False)
                    
                    # pymysql untuk database logging
                    try:
                        import pymysql  # noqa: F401
                    except Exception:
                        print("⚙️  Installing pymysql (pip)...")
                        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pymysql'], check=False)
        except Exception:
            pass
    
    # CRITICAL: Import dependencies and auto-fix if needed
    try:
        from core.waste_classifier import WasteClassifier
        from core.mock_classifier import MockClassifier
        from core.main_controller import MainController
    except ModuleNotFoundError as e:
        if 'cv2' in str(e) or 'adafruit' in str(e):
            print(f"\n❌ Dependency error: {e}")
            print("\n💡 Quick fix:")
            print("   ./start.sh")
            return 1
        else:
            raise
    
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
    print_banner()
    
    # Initialize components
    print("🔧 Initializing components...\n")
    
    # CRITICAL: Initialize camera FIRST (lightweight) before model (memory-intensive)
    # This prevents memory conflict segfaults between libcamera and TFLite
    
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
                # Try to initialize real classifier. If it fails, attempt other .tflite files in models dir
                tried_models = [args.model]
                classifier = None
                try:
                    classifier = WasteClassifier(model_path=args.model, labels_path=args.labels)
                    print("      ✓ Waste Classifier initialized")
                except Exception as e:
                    print(f"      ⚠️  WasteClassifier failed to initialize with {args.model}: {e}")
                    # Try other .tflite files in models directory (auto-selection)
                    models_dir = os.path.join(script_dir, 'models')
                    candidates = []
                    if os.path.isdir(models_dir):
                        for f in os.listdir(models_dir):
                            if f.endswith('.tflite'):
                                candidates.append(os.path.join(models_dir, f))

                    # Remove the already-tried model
                    candidates = [c for c in candidates if c not in tried_models]

                    for cand in candidates:
                        print(f"      → Attempting alternate model: {os.path.relpath(cand, script_dir)}")
                        try:
                            classifier = WasteClassifier(model_path=cand, labels_path=args.labels)
                            args.model = cand
                            print(f"      ✓ Waste Classifier initialized with {os.path.relpath(cand, script_dir)}")
                            break
                        except Exception as e2:
                            print(f"      ✗ Failed with {os.path.relpath(cand, script_dir)}: {e2}")
                            continue

                    if classifier is None:
                        # All attempts failed; fallback to mock classifier
                        print("      → All model attempts failed. Falling back to TEST mode (Mock Classifier)")
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
