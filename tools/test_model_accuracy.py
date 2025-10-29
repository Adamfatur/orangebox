"""
Test model accuracy dengan sample images dari dataset
"""
import numpy as np
import cv2
import tensorflow as tf
from pathlib import Path

def preprocess_image(image_path):
    """Preprocessing sama seperti di waste_classifier.py"""
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        return None
    
    # BGR to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Resize to 224x224
    image_resized = cv2.resize(image_rgb, (224, 224))
    
    # Normalize to [-1, 1] (MobileNetV2 preprocessing)
    image_normalized = (image_resized.astype(np.float32) / 127.5) - 1.0
    
    # Add batch dimension
    image_batch = np.expand_dims(image_normalized, axis=0)
    
    return image_batch

def test_model():
    """Test model dengan sample images"""
    model_path = "models/model_quant_infer.tflite"
    
    # Load TFLite model
    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    print("="*70)
    print("TESTING MODEL ACCURACY")
    print("="*70)
    print(f"Model: {model_path}")
    print(f"Input shape: {input_details[0]['shape']}")
    print(f"Output shape: {output_details[0]['shape']}")
    print()
    
    # Test images dari dataset
    dataset_path = Path("dataset")
    
    test_samples = [
        ("ORGANIC", list((dataset_path / "O").glob("*.jpg"))[:5]),
        ("ANORGANIC", list((dataset_path / "R").glob("*.jpg"))[:5])
    ]
    
    for true_label, image_paths in test_samples:
        print(f"\n{'='*70}")
        print(f"Testing {true_label} samples:")
        print(f"{'='*70}")
        
        correct = 0
        total = 0
        
        for img_path in image_paths:
            # Preprocess
            processed = preprocess_image(img_path)
            if processed is None:
                print(f"❌ Failed to load: {img_path.name}")
                continue
            
            # Inference
            interpreter.set_tensor(input_details[0]['index'], processed)
            interpreter.invoke()
            output = interpreter.get_tensor(output_details[0]['index'])
            
            # Binary classification - INVERTED LOGIC!
            # < 0.5 = ORGANIC, >= 0.5 = ANORGANIC
            sigmoid_value = float(output[0][0])
            
            if sigmoid_value < 0.5:
                predicted_label = "ORGANIC"
                confidence = 1.0 - sigmoid_value
            else:
                predicted_label = "ANORGANIC"
                confidence = sigmoid_value
            
            is_correct = (predicted_label == true_label)
            if is_correct:
                correct += 1
            total += 1
            
            # Print result
            status = "✅" if is_correct else "❌"
            print(f"{status} {img_path.name}: {predicted_label} ({confidence:.2%}) | sigmoid: {sigmoid_value:.4f}")
        
        accuracy = (correct / total * 100) if total > 0 else 0
        print(f"\nAccuracy for {true_label}: {correct}/{total} = {accuracy:.1f}%")
    
    print("\n" + "="*70)
    print("DONE")
    print("="*70)

if __name__ == "__main__":
    test_model()
