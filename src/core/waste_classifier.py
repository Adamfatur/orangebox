"""
Waste Classification Module
Modul AI untuk mengklasifikasikan sampah organik dan anorganik
menggunakan TensorFlow Lite model.
"""

import os
from typing import Dict

import cv2
import numpy as np


class WasteClassifier:
    """
    Modul klasifikasi sampah yang menerima frame gambar dan
    mengembalikan prediksi klasifikasi (ORGANIC/ANORGANIC).
    """

    def __init__(self, model_path: str = "model.tflite", labels_path: str = "labels.txt"):
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
        NOTE: Menghindari import tensorflow in-process di RPi (rawan segfault).
        """
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file tidak ditemukan: {self.model_path}")

        # Sanity check ukuran file
        try:
            file_size = os.path.getsize(self.model_path)
            if file_size < 1024:
                raise ValueError(f"Model file too small ({file_size} bytes) - kemungkinan corrupt")
        except Exception:
            pass

        # Memory barrier: beri waktu kamera stabil dan GC sebelum alokasi besar
        try:
            import time, gc
            print("[WasteClassifier] Waiting for camera resource stabilization...")
            time.sleep(0.5)
            gc.collect()
            print("[WasteClassifier] Memory barrier cleared")
        except Exception:
            pass

        # Prefer tflite_runtime (APT package di Raspberry Pi)
        try:
            print("[WasteClassifier] Trying tflite_runtime...")
            import tflite_runtime.interpreter as tflite
            self.interpreter = tflite.Interpreter(model_path=self.model_path)
            try:
                # Konservatif: 1 thread untuk kestabilan di perangkat kecil
                self.interpreter.set_num_threads(1)
            except Exception:
                pass
            print("[WasteClassifier] ✓ Using tflite_runtime")
        except Exception as e:
            # Jangan import tensorflow di proses utama pada RPi → arahkan pengguna instal tflite-runtime
            raise RuntimeError(
                "Tidak dapat memuat TFLite interpreter. Harap instal tflite-runtime (disarankan di Raspberry Pi):\n"
                "  sudo apt update && sudo apt install -y python3-tflite-runtime\n"
                f"Detail: {e}"
            )

        # Alokasi tensors
        print("[WasteClassifier] Allocating tensors...")
        self.interpreter.allocate_tensors()

        # Input/output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_shape = self.input_details[0]['shape']
        print("[WasteClassifier] ✓ Model loaded successfully")
        print(f"[WasteClassifier]   Input shape: {self.input_shape}")

    def _load_labels(self):
        if not os.path.exists(self.labels_path):
            print(f"[WARNING] Labels file tidak ditemukan: {self.labels_path}")
            print("[WARNING] Menggunakan default labels: ['ORGANIC', 'ANORGANIC']")
            self.labels = ['ORGANIC', 'ANORGANIC']
            return
        with open(self.labels_path, 'r') as f:
            self.labels = [line.strip() for line in f.readlines()]
        if self.labels and ' ' in self.labels[0]:
            self.labels = [label.split(' ', 1)[1] for label in self.labels]
        print(f"[WasteClassifier] Labels loaded: {self.labels}")

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        # Target size dari input tensor (1, H, W, C)
        height = int(self.input_shape[1])
        width = int(self.input_shape[2])
        image_resized = cv2.resize(image, (width, height))
        image_rgb = cv2.cvtColor(image_resized, cv2.COLOR_BGR2RGB)
        image_normalized = (image_rgb.astype(np.float32) / 127.5) - 1.0
        return np.expand_dims(image_normalized, axis=0)

    def predict(self, image: np.ndarray) -> Dict[str, any]:
        processed_image = self._preprocess_image(image)
        self.interpreter.set_tensor(self.input_details[0]['index'], processed_image)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        sigmoid_value = float(output_data[0][0])

        # Inverted mapping sesuai training: <0.5 ORGANIC, >=0.5 ANORGANIC
        if sigmoid_value < 0.5:
            predicted_index = 0  # ORGANIC
            confidence = 1.0 - sigmoid_value
        else:
            predicted_index = 1  # ANORGANIC
            confidence = sigmoid_value

        label = self.labels[predicted_index] if predicted_index < len(self.labels) else f"Class_{predicted_index}"
        return {"label": label, "confidence": confidence}

    def predict_with_all_scores(self, image: np.ndarray) -> Dict[str, any]:
        base = self.predict(image)
        # Hitung ulang sigmoid untuk skor lengkap
        processed_image = self._preprocess_image(image)
        self.interpreter.set_tensor(self.input_details[0]['index'], processed_image)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        sigmoid_value = float(output_data[0][0])

        all_scores = {
            (self.labels[0] if len(self.labels) > 0 else 'ORGANIC'): 1.0 - sigmoid_value,
            (self.labels[1] if len(self.labels) > 1 else 'ANORGANIC'): sigmoid_value,
        }
        base["all_scores"] = all_scores
        base["raw_sigmoid"] = sigmoid_value
        return base


if __name__ == "__main__":
    # Simple self-test helper
    print("Testing WasteClassifier init...")
    if not os.path.exists("model.tflite"):
        print("⚠️  model.tflite not found in current dir; this is expected in dev.")
    try:
        wc = WasteClassifier()
        print("✓ Initialized. Input shape:", wc.input_shape)
    except Exception as e:
        print("✗ Init failed:", e)
