"""
Waste Classification Module
Modul AI untuk mengklasifikasikan sampah organik dan anorganik
menggunakan TensorFlow Lite model.
"""

import numpy as np
import cv2
from typing import Dict, Optional
import os


class WasteClassifier:
    """
    Modul klasifikasi sampah yang menerima frame gambar dan 
    mengembalikan prediksi klasifikasi (ORGANIC/ANORGANIC).
    """
    
    def __init__(self, model_path: str = "model.tflite", labels_path: str = "labels.txt"):
        """
        Inisialisasi classifier dengan model TFLite.
        
        Args:
            model_path: Path ke file model.tflite
            labels_path: Path ke file labels.txt
        """
        self.model_path = model_path
        self.labels_path = labels_path
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.labels = []
        self.input_shape = None
        
        self._load_model()
        self._load_labels()
    
    def _load_model(self):
        """
        Load TensorFlow Lite model dan setup interpreter.
        
        CRITICAL: This can segfault if:
        - Model file is corrupt
        - Incompatible TFLite version
        - Memory allocation fails
        """
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file tidak ditemukan: {self.model_path}")
        
        # Check model file size (sanity check)
        file_size = os.path.getsize(self.model_path)
        if file_size < 1000:  # Less than 1KB is suspicious
            raise ValueError(f"Model file too small ({file_size} bytes) - possibly corrupt")
        
        print(f"[WasteClassifier] Loading model: {self.model_path} ({file_size} bytes)")
        
        # CRITICAL: Add delay to ensure camera resources are fully initialized
        # This prevents memory conflict segfaults between libcamera and TFLite
        import time
        import gc
        print("[WasteClassifier] Waiting for camera resource stabilization...")
        time.sleep(0.5)  # 500ms delay
        gc.collect()  # Force garbage collection before heavy allocation
        print("[WasteClassifier] Memory barrier cleared")
        
        # Try tflite_runtime first (lighter, recommended for Raspberry Pi)
        interpreter_loaded = False
        last_error = None
        
        try:
            print("[WasteClassifier] Trying tflite_runtime...")
            import tflite_runtime.interpreter as tflite
            
            # Load interpreter (can segfault here!)
            self.interpreter = tflite.Interpreter(model_path=self.model_path)
            interpreter_loaded = True
            print("[WasteClassifier] ✓ Using tflite_runtime")
            
        except (ImportError, AttributeError) as e:
            print(f"[WasteClassifier] tflite_runtime not available: {e}")
            last_error = e
            
        except Exception as e:
            # Catch other errors (including potential pre-segfault exceptions)
            print(f"[WasteClassifier] tflite_runtime failed: {e}")
            last_error = e
        
        # Fallback to TensorFlow Lite
        if not interpreter_loaded:
            # Check if tensorflow package metadata exists without importing
            try:
                import importlib.util
                spec = importlib.util.find_spec("tensorflow")
            except Exception:
                spec = None

            if spec is None:
                # No tensorflow package found -- instruct user to install tflite-runtime or tensorflow
                raise RuntimeError(
                    f"Cannot load TFLite interpreter. Install either:\n"
                    f"  1. tflite-runtime (recommended on Raspberry Pi): sudo apt install python3-tflite-runtime\n"
                    f"  2. tensorflow (pip): pip install tensorflow\n"
                    f"Previous errors: {last_error}"
                )

            # tensorflow package exists; but importing it in-process may SEGFAULT on some systems.
            # To avoid crashing the main process, test tensorflow + Interpreter creation in a subprocess first.
            import subprocess
            import sys
            from shlex import quote

            print("[WasteClassifier] tensorflow package detected; testing import in isolated subprocess...")
            test_cmd = [
                sys.executable,
                "-c",
                (
                    "import tensorflow as tf, sys\n"
                    "try:\n"
                    "  tf.lite.Interpreter(model_path=\"" + self.model_path.replace('"', '\\"') + "\")\n"
                    "  print('TF_OK')\n"
                    "except Exception as e:\n"
                    "  sys.stderr.write(str(e))\n"
                    "  sys.exit(2)\n"
                ),
            ]

            try:
                proc = subprocess.run(test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
                if proc.returncode != 0:
                    stderr = proc.stderr.decode(errors='replace')[:1000]
                    stdout = proc.stdout.decode(errors='replace')[:1000]
                    print(f"[WasteClassifier] tensorflow subprocess test failed (rc={proc.returncode})\nstdout={stdout}\nstderr={stderr}")
                    raise RuntimeError("tensorflow detected but failed to initialize Interpreter in subprocess")
                else:
                    print("[WasteClassifier] tensorflow subprocess test OK")
                    # Now safe-ish to import in-process (best-effort). If this still crashes, it will be a hard crash.
                    try:
                        import tensorflow as tf
                        self.interpreter = tf.lite.Interpreter(model_path=self.model_path)
                        interpreter_loaded = True
                        print("[WasteClassifier] ✓ Using tensorflow.lite")
                    except Exception as e:
                        raise RuntimeError(f"tensorflow available but failed to import in-process: {e}")

            except subprocess.TimeoutExpired:
                raise RuntimeError("tensorflow subprocess test timed out; skipping tensorflow import to avoid segfault")
            except Exception as e:
                raise RuntimeError(f"tensorflow fallback failed: {e}")
        
        if not interpreter_loaded:
            raise RuntimeError("Failed to load interpreter with any available runtime")
        
        # Allocate tensors (CRITICAL: can segfault if model is corrupt!)
        try:
            print("[WasteClassifier] Allocating tensors...")
            self.interpreter.allocate_tensors()
            print("[WasteClassifier] ✓ Tensors allocated")
        except Exception as e:
            raise RuntimeError(
                f"Failed to allocate tensors (model may be corrupt): {e}\n"
                f"Try re-downloading the model or using a different model file."
            )
        
        # Get input dan output details
        try:
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            # Get input shape (biasanya [1, height, width, channels])
            self.input_shape = self.input_details[0]['shape']
            
            print(f"[WasteClassifier] ✓ Model loaded successfully")
            print(f"[WasteClassifier]   Input shape: {self.input_shape}")
            print(f"[WasteClassifier]   Output shape: {self.output_details[0]['shape']}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to get model details: {e}")
    
    def _load_labels(self):
        """Load labels dari file labels.txt."""
        if not os.path.exists(self.labels_path):
            print(f"[WARNING] Labels file tidak ditemukan: {self.labels_path}")
            print(f"[WARNING] Menggunakan default labels: ['ORGANIC', 'ANORGANIC']")
            self.labels = ['ORGANIC', 'ANORGANIC']
            return
        
        with open(self.labels_path, 'r') as f:
            self.labels = [line.strip() for line in f.readlines()]
        
        # Jika format labels adalah "0 ORGANIC", ambil hanya labelnya
        if self.labels and ' ' in self.labels[0]:
            self.labels = [label.split(' ', 1)[1] for label in self.labels]
        
        print(f"[WasteClassifier] Labels loaded: {self.labels}")
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocessing gambar untuk memenuhi spesifikasi input model.
        PENTING: Harus sama dengan preprocessing saat training (MobileNetV2)
        
        Args:
            image: Frame gambar dari OpenCV (BGR format)
            
        Returns:
            Processed image array ready for inference
        """
        # Get target size dari input shape (biasanya 224x224)
        height = self.input_shape[1]
        width = self.input_shape[2]
        
        # Resize image
        image_resized = cv2.resize(image, (width, height))
        
        # Convert BGR to RGB (OpenCV uses BGR, model expects RGB)
        image_rgb = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)
        
        # MobileNetV2 preprocessing: normalize to [-1, 1]
        # Formula: (pixel / 127.5) - 1.0
        image_normalized = (image_rgb.astype(np.float32) / 127.5) - 1.0
        
        # Add batch dimension: (height, width, channels) -> (1, height, width, channels)
        image_batch = np.expand_dims(image_normalized, axis=0)
        
        return image_batch
    
    def predict(self, image: np.ndarray) -> Dict[str, any]:
        """
        Melakukan inferensi pada gambar dan mengembalikan prediksi.
        
        Args:
            image: Frame gambar dari OpenCV (numpy array)
            
        Returns:
            Dictionary dengan format:
            {
                "label": "ORGANIC" atau "ANORGANIC",
                "confidence": 0.95 (float antara 0-1)
            }
        """
        # Preprocessing
        processed_image = self._preprocess_image(image)
        
        # Set input tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], processed_image)
        
        # Run inference
        self.interpreter.invoke()
        
        # Get output tensor (prediction scores)
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        
        # Binary classification: single sigmoid output
        # Output shape is (1, 1) - single value between 0 and 1
        predictions = output_data[0]
        
        # INVERTED LOGIC - Model trained with swapped labels!
        # < 0.5 = ORGANIC, >= 0.5 = ANORGANIC
        sigmoid_value = float(predictions[0])
        
        if sigmoid_value < 0.5:
            predicted_index = 0  # ORGANIC
            confidence = 1.0 - sigmoid_value
        else:
            predicted_index = 1  # ANORGANIC
            confidence = sigmoid_value
        
        # Get label
        label = self.labels[predicted_index] if predicted_index < len(self.labels) else f"Class_{predicted_index}"
        
        result = {
            "label": label,
            "confidence": confidence
        }
        
        return result
    
    def predict_with_all_scores(self, image: np.ndarray) -> Dict[str, any]:
        """
        Melakukan inferensi dan mengembalikan semua confidence scores.
        
        Args:
            image: Frame gambar dari OpenCV
            
        Returns:
            Dictionary dengan format:
            {
                "label": "ORGANIC",
                "confidence": 0.95,
                "all_scores": {"ORGANIC": 0.95, "ANORGANIC": 0.05},
                "raw_sigmoid": 0.95
            }
        """
        result = self.predict(image)
        
        # Get raw sigmoid output
        processed_image = self._preprocess_image(image)
        self.interpreter.set_tensor(self.input_details[0]['index'], processed_image)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        sigmoid_value = float(output_data[0][0])
        
        # Create dictionary of all scores for binary classification
        # INVERTED LOGIC - sigmoid < 0.5 = ORGANIC, >= 0.5 = ANORGANIC
        all_scores = {
            self.labels[0]: 1.0 - sigmoid_value,  # ORGANIC (inverted)
            self.labels[1]: sigmoid_value  # ANORGANIC
        }
        
        result["all_scores"] = all_scores
        result["raw_sigmoid"] = sigmoid_value
        
        return result


# Test function
def main():
    """
    Test function untuk memverifikasi WasteClassifier berfungsi dengan baik.
    """
    print("Testing WasteClassifier...")
    
    # Check jika model file ada
    if not os.path.exists("model.tflite"):
        print("\n[ERROR] File 'model.tflite' tidak ditemukan!")
        print("Silakan:")
        print("1. Train model menggunakan Google Teachable Machine")
        print("2. Export sebagai TensorFlow Lite")
        print("3. Letakkan file 'model.tflite' dan 'labels.txt' di folder ini")
        return
    
    try:
        classifier = WasteClassifier()
        print("\n[SUCCESS] WasteClassifier berhasil diinisialisasi!")
        print(f"Model path: {classifier.model_path}")
        print(f"Labels: {classifier.labels}")
        print(f"Input shape: {classifier.input_shape}")
    except Exception as e:
        print(f"\n[ERROR] Gagal menginisialisasi classifier: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
