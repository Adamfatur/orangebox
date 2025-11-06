"""
Test Classifier - Script untuk testing WasteClassifier secara independen
Sesuai dengan Guide 1: Langkah 4 - Pengujian Lokal di Host (Mac)
"""

import cv2
import numpy as np
import time
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.waste_classifier import WasteClassifier


def main():
    """
    Script pengujian untuk WasteClassifier dengan webcam lokal.
    """
    print("="*70)
    print("WASTE CLASSIFIER - TEST SCRIPT")
    print("="*70)
    print("\nInstruksi:")
    print("  - Tunjukkan objek organik (sayur, buah, sisa makanan) ke kamera")
    print("  - Tunjukkan objek anorganik (plastik, kertas, kaleng) ke kamera")
    print("  - Tekan 'q' untuk keluar")
    print("  - Tekan 's' untuk screenshot hasil")
    print("="*70 + "\n")
    
    # Check apakah model file ada
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    # Support command line argument for model path
    if len(sys.argv) >= 2:
        model_path = sys.argv[1]
        if not os.path.isabs(model_path):
            model_path = os.path.join(project_root, model_path)
    else:
        # Default to model_quant.tflite (recommended)
        model_path = os.path.join(project_root, "models", "model_quant.tflite")
        # Fallback to model.tflite for backward compatibility
        if not os.path.exists(model_path):
            model_path = os.path.join(project_root, "models", "model.tflite")
    
    labels_path = os.path.join(project_root, "models", "labels.txt")
    
    if not os.path.exists(model_path):
        print(f"\n❌ ERROR: File model tidak ditemukan di: {model_path}")
        print("\n📋 Model yang tersedia:")
        models_dir = os.path.join(project_root, "models")
        if os.path.exists(models_dir):
            tflite_files = [f for f in os.listdir(models_dir) if f.endswith('.tflite')]
            if tflite_files:
                print(f"   Gunakan: python3 scripts/test_classifier.py models/<model>.tflite")
                for f in tflite_files:
                    print(f"   - {f}")
            else:
                print(f"   Tidak ada file .tflite di {models_dir}")
        print("\n📋 Atau latih model baru:")
        print("   python3 train_model.py")
        print("   python3 export_model.py")
        print(f"8. Letakkan kedua file di folder: {os.path.dirname(model_path)}/")
        print("\n" + "="*70)
        return
    
    try:
        # Inisialisasi classifier
        print("Loading classifier...")
        classifier = WasteClassifier(model_path=model_path, labels_path=labels_path)
        print("✓ Classifier loaded successfully!\n")
        
        # Inisialisasi kamera
        print("Initializing camera...")
        camera = cv2.VideoCapture(0)
        
        if not camera.isOpened():
            print("❌ ERROR: Tidak dapat membuka kamera!")
            print("Pastikan webcam terhubung dan tidak digunakan aplikasi lain.")
            return
        
        # Set resolusi kamera
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("✓ Camera initialized!\n")
        print("Starting live classification... (Tekan 'q' untuk keluar)\n")
        
        # Window name
        window_name = "Waste Classifier Test"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        # FPS calculation
        fps_start_time = time.time()
        fps_frame_count = 0
        current_fps = 0
        
        # Statistics
        frame_count = 0
        screenshot_count = 0
        
        while True:
            # Capture frame
            ret, frame = camera.read()
            
            if not ret or frame is None:
                print("❌ ERROR: Gagal membaca frame dari kamera")
                break
            
            frame_count += 1
            
            # Run classification setiap frame
            prediction = classifier.predict_with_all_scores(frame)
            
            label = prediction['label']
            confidence = prediction['confidence']
            all_scores = prediction.get('all_scores', {})
            
            # Calculate FPS
            fps_frame_count += 1
            elapsed_time = time.time() - fps_start_time
            if elapsed_time > 1.0:
                current_fps = fps_frame_count / elapsed_time
                fps_frame_count = 0
                fps_start_time = time.time()
            
            # Prepare display frame
            display_frame = frame.copy()
            height, width = display_frame.shape[:2]
            
            # Tentukan warna dan emoji berdasarkan label
            if 'ORGANIC' in label.upper():
                color = (0, 255, 0)  # Green
                emoji = "🌱"
                bg_color = (0, 100, 0)
            else:
                color = (0, 165, 255)  # Orange (BGR format)
                emoji = "♻️"
                bg_color = (0, 80, 130)
            
            # Draw semi-transparent overlay untuk header
            overlay = display_frame.copy()
            cv2.rectangle(overlay, (0, 0), (width, 120), bg_color, -1)
            cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0, display_frame)
            
            # Draw prediction result (large text)
            font = cv2.FONT_HERSHEY_BOLD
            pred_text = f"{emoji} {label}"
            cv2.putText(display_frame, pred_text, (10, 45), font, 1.2, (255, 255, 255), 3)
            
            # Draw confidence bar
            conf_text = f"Confidence: {confidence:.1%}"
            cv2.putText(display_frame, conf_text, (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (255, 255, 255), 2)
            
            # Draw confidence bar
            bar_width = int(400 * confidence)
            cv2.rectangle(display_frame, (10, 90), (410, 110), (100, 100, 100), 2)
            cv2.rectangle(display_frame, (10, 90), (10 + bar_width, 110), color, -1)
            
            # Draw all scores (small text di bawah)
            y_offset = 140
            cv2.putText(display_frame, "All Scores:", (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 20
            
            for class_label, score in all_scores.items():
                score_text = f"  {class_label}: {score:.2%}"
                cv2.putText(display_frame, score_text, (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                y_offset += 20
            
            # Draw FPS and frame count
            info_text = f"FPS: {current_fps:.1f} | Frame: {frame_count}"
            cv2.putText(display_frame, info_text, (10, height - 40), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Draw instructions
            instructions = "Press 'q' to quit | 's' to screenshot"
            cv2.putText(display_frame, instructions, (10, height - 15), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            
            # Show frame
            cv2.imshow(window_name, display_frame)
            
            # Check keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n🛑 Quit command received")
                break
            elif key == ord('s'):
                # Save screenshot
                screenshot_count += 1
                filename = f"screenshot_{screenshot_count}_{label}_{confidence:.0%}.jpg"
                cv2.imwrite(filename, display_frame)
                print(f"📸 Screenshot saved: {filename}")
            
        # Cleanup
        print("\n" + "="*70)
        print("STATISTICS")
        print("="*70)
        print(f"Total frames processed: {frame_count}")
        print(f"Screenshots taken: {screenshot_count}")
        print(f"Average FPS: {frame_count / (time.time() - fps_start_time + 1):.1f}")
        print("="*70)
        
        camera.release()
        cv2.destroyAllWindows()
        print("\n✓ Cleanup complete. Goodbye!")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user (Ctrl+C)")
        camera.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        if 'camera' in locals():
            camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
