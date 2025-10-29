#!/usr/bin/env python3
"""
Export inference-only TFLite model (no augmentation, no Flex ops)
- Rebuilds architecture without Keras preprocessing layers that introduce Select TF Ops
- Copies trained head weights from best_model.h5
- Converts to TFLite with builtin ops only
"""
import os
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
H5_PATH = MODELS_DIR / "best_model.h5"
SAVED_PATH = MODELS_DIR / "best_model_saved"
OUT_SAVED = MODELS_DIR / "inference_saved"
OUT_FLOAT = MODELS_DIR / "model_float32_infer.tflite"
OUT_QUANT = MODELS_DIR / "model_quant_infer.tflite"
IMG_SIZE = (224, 224)

print("== Exporting inference-only model ==")
print(f"Models dir: {MODELS_DIR}")

if not (H5_PATH.exists() or SAVED_PATH.exists()):
    raise FileNotFoundError("best_model.h5 or best_model_saved/ not found. Run training first.")

# 1) Build inference-only model (no augmentation)
inputs = keras.Input(shape=(*IMG_SIZE, 3), name="input")
# IMPORTANT: Do not add keras preprocessing/augmentation layers to avoid Flex ops.
# We will preprocess in application code (WasteClassifier) to [-1,1].
# Here the network expects already preprocessed inputs.
# If your app preprocesses to [-1,1], remove this Lambda; otherwise keep preprocess_input here but it may add ops.
# We'll keep a minimal Lambda that does identity; real preprocess happens in runtime.
x = inputs

# Base model
base_model = MobileNetV2(input_shape=(*IMG_SIZE, 3), include_top=False, weights='imagenet')
base_model.trainable = False
x = base_model(x, training=False)

# Head
x = layers.GlobalAveragePooling2D(name='gap')(x)
x = layers.Dropout(0.2, name='dropout')(x)
outputs = layers.Dense(1, activation='sigmoid', name='predictions')(x)
export_model = keras.Model(inputs, outputs, name='waste_classifier_infer')

# 2) Load trained head weights from best_model.h5
print("Loading trained model to copy head weights...")
copied = False
pred_layer = export_model.get_layer('predictions')

# Try: load from SavedModel via TFSMLayer to fetch output-only (cannot read weights) -> skip
# Try: load from H5 using h5py to extract Dense weights directly
if H5_PATH.exists():
    try:
        import h5py
        with h5py.File(H5_PATH, 'r') as f:
            # Keras stores under 'model_weights' group typically
            root = f
            if 'model_weights' in f:
                root = f['model_weights']
            kernel = [None]
            bias = [None]
            expected_kshape = tuple(pred_layer.weights[0].shape)
            def visit(name, obj):
                if isinstance(obj, h5py.Dataset):
                    ds_name = name.split('/')[-1]
                    # Look for kernel and bias with expected shapes
                    if ds_name in ('kernel', 'kernel:0') and obj.shape == expected_kshape:
                        # store reference to group path (without dataset)
                        kernel[0] = (name, obj[()])
                    elif ds_name in ('bias', 'bias:0') and obj.shape == (1,):
                        bias[0] = (name, obj[()])
            root.visititems(visit)
            # If multiple found, try to match same parent group prefix
            if kernel[0] is not None and bias[0] is not None:
                k_path, k_val = kernel[0]
                b_path, b_val = bias[0]
                # Prefer bias in same parent as kernel if multiple; naive check
                k_parent = '/'.join(k_path.split('/')[:-1])
                b_parent = '/'.join(b_path.split('/')[:-1])
                if k_parent != b_parent:
                    # Fallback: accept as-is
                    pass
                pred_layer.set_weights([k_val, b_val])
                copied = True
                print("Copied Dense(1) weights from H5 via h5py.")
    except Exception as e:
        print(f"Warning: h5py extraction failed: {e}")

if not copied:
    raise RuntimeError("Failed to copy trained head weights. Cannot export inference model.")

# 3) Save SavedModel
if OUT_SAVED.exists():
    import shutil
    shutil.rmtree(OUT_SAVED)
print(f"Saving SavedModel to: {OUT_SAVED}")
export_model.export(str(OUT_SAVED))

# 4) Convert to TFLite (builtin ops only)
print("Converting to TFLite (Float32)...")
converter = tf.lite.TFLiteConverter.from_saved_model(str(OUT_SAVED))
# Builtin ops only; do NOT include SELECT_TF_OPS to avoid Flex
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
tflite_float32 = converter.convert()
OUT_FLOAT.write_bytes(tflite_float32)
print(f"Saved: {OUT_FLOAT} ({len(tflite_float32)/1024:.1f} KB)")

print("Converting to TFLite (Dynamic Range Quantization)...")
converter = tf.lite.TFLiteConverter.from_saved_model(str(OUT_SAVED))
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
tflite_quant = converter.convert()
OUT_QUANT.write_bytes(tflite_quant)
print(f"Saved: {OUT_QUANT} ({len(tflite_quant)/1024:.1f} KB)")

print("\n✅ Export complete. Use model_quant_infer.tflite in the app.")
