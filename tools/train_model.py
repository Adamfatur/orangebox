#!/usr/bin/env python3
"""
Training Script - Waste Classification Model
Melatih model klasifikasi Organik vs Unorganik menggunakan TensorFlow + Metal acceleration
"""

import os
import json
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from pathlib import Path
from datetime import datetime
import shutil

print("="*70)
print("🎓 WASTE CLASSIFICATION MODEL TRAINING")
print("="*70)
print(f"TensorFlow version: {tf.__version__}")
print(f"GPU Available: {len(tf.config.list_physical_devices('GPU')) > 0}")
print("="*70)

# ============================================
# CONFIGURATION
# ============================================

# Paths
BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR / "dataset"
OUTPUT_DIR = BASE_DIR / "models"
OUTPUT_DIR.mkdir(exist_ok=True)

# Hyperparameters
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 20
INITIAL_LR = 1e-4
VALIDATION_SPLIT = 0.2

# Class names
CLASS_O = "ORGANIC"      # dari folder O
CLASS_R = "ANORGANIC"    # dari folder R

print(f"\n📁 Dataset: {DATASET_DIR}")
print(f"📁 Output: {OUTPUT_DIR}")
print(f"🔧 Image size: {IMG_SIZE}")
print(f"🔧 Batch size: {BATCH_SIZE}")
print(f"🔧 Epochs: {EPOCHS}")
print(f"🔧 Learning rate: {INITIAL_LR}")

# ============================================
# DATA LOADING & PREPROCESSING
# ============================================

print("\n" + "="*70)
print("📊 LOADING DATASET")
print("="*70)

# Data augmentation for training
data_augmentation = keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
], name="data_augmentation")

# Load training dataset
train_ds = keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=VALIDATION_SPLIT,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode='binary'  # Binary classification
)

# Load validation dataset
val_ds = keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=VALIDATION_SPLIT,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode='binary'
)

# Get class names
class_names = train_ds.class_names
print(f"\n✅ Classes detected: {class_names}")
print(f"   - {class_names[0]} → {CLASS_O}")
print(f"   - {class_names[1]} → {CLASS_R}")

# Count samples
train_size = tf.data.experimental.cardinality(train_ds).numpy() * BATCH_SIZE
val_size = tf.data.experimental.cardinality(val_ds).numpy() * BATCH_SIZE

print(f"\n📈 Dataset split:")
print(f"   Training: ~{train_size} images")
print(f"   Validation: ~{val_size} images")

# Performance optimization
AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.cache().prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.cache().prefetch(buffer_size=AUTOTUNE)

# ============================================
# MODEL BUILDING
# ============================================

print("\n" + "="*70)
print("🏗️  BUILDING MODEL")
print("="*70)

def create_model():
    """Create model using MobileNetV2 with transfer learning"""
    
    # Input layer
    inputs = keras.Input(shape=(*IMG_SIZE, 3))
    
    # Data augmentation (only for training)
    x = data_augmentation(inputs)
    
    # Preprocessing for MobileNetV2
    x = keras.applications.mobilenet_v2.preprocess_input(x)
    
    # Base model - MobileNetV2
    base_model = MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze base model
    base_model.trainable = False
    
    # Pass through base model
    x = base_model(x, training=False)
    
    # Classification head
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(1, activation='sigmoid')(x)  # Binary classification
    
    # Create model
    model = keras.Model(inputs, outputs, name='waste_classifier')
    
    return model, base_model

model, base_model = create_model()

print(f"✅ Model created: {model.name}")
print(f"   Base model: MobileNetV2")
print(f"   Total params: {model.count_params():,}")
print(f"   Trainable params: {sum([tf.size(w).numpy() for w in model.trainable_weights]):,}")

# ============================================
# COMPILE MODEL
# ============================================

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=INITIAL_LR),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')]
)

print("\n✅ Model compiled")
print(f"   Optimizer: Adam (lr={INITIAL_LR})")
print(f"   Loss: binary_crossentropy")
print(f"   Metrics: accuracy, AUC")

# ============================================
# CALLBACKS
# ============================================

print("\n" + "="*70)
print("⚙️  SETTING UP CALLBACKS")
print("="*70)

# Early stopping
early_stopping = EarlyStopping(
    monitor='val_loss',
    patience=5,
    restore_best_weights=True,
    verbose=1
)

# Model checkpoint
checkpoint_path = OUTPUT_DIR / "best_model.h5"
model_checkpoint = ModelCheckpoint(
    filepath=str(checkpoint_path),
    monitor='val_accuracy',
    mode='max',
    save_best_only=True,
    verbose=1
)

# Reduce learning rate on plateau
reduce_lr = ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,
    patience=3,
    min_lr=1e-7,
    verbose=1
)

callbacks = [early_stopping, model_checkpoint, reduce_lr]

print("✅ Callbacks configured:")
print("   - EarlyStopping (patience=5)")
print("   - ModelCheckpoint (save best)")
print("   - ReduceLROnPlateau (factor=0.5, patience=3)")

# ============================================
# TRAINING
# ============================================

print("\n" + "="*70)
print("🚀 TRAINING START")
print("="*70)

start_time = datetime.now()

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=callbacks,
    verbose=1
)

end_time = datetime.now()
training_duration = (end_time - start_time).total_seconds()

print("\n" + "="*70)
print("✅ TRAINING COMPLETE")
print("="*70)
print(f"Duration: {training_duration/60:.2f} minutes")

# Get final metrics
final_train_acc = history.history['accuracy'][-1]
final_val_acc = history.history['val_accuracy'][-1]
final_train_loss = history.history['loss'][-1]
final_val_loss = history.history['val_loss'][-1]
best_val_acc = max(history.history['val_accuracy'])

print(f"\n📊 Final Metrics:")
print(f"   Train Accuracy: {final_train_acc:.4f}")
print(f"   Val Accuracy: {final_val_acc:.4f}")
print(f"   Best Val Accuracy: {best_val_acc:.4f}")
print(f"   Train Loss: {final_train_loss:.4f}")
print(f"   Val Loss: {final_val_loss:.4f}")

# ============================================
# SAVE SAVEDMODEL FORMAT
# ============================================

print("\n" + "="*70)
print("💾 SAVING MODEL")
print("="*70)

# Use the model from training (already has best weights via callback)
print("Using model with best weights (automatically restored by EarlyStopping)")

# Save in SavedModel format
saved_model_dir = OUTPUT_DIR / "best_model_saved"

# Remove old if exists
if saved_model_dir.exists():
    import shutil
    shutil.rmtree(saved_model_dir)

print(f"\nExporting as SavedModel: {saved_model_dir}")
model.export(str(saved_model_dir))
print(f"✅ SavedModel saved")

# ============================================
# CONVERT TO TFLITE
# ============================================

print("\n" + "="*70)
print("🔄 CONVERTING TO TFLITE")
print("="*70)

# 1. Float32 TFLite (no quantization)
print("\n1️⃣  Converting to Float32 TFLite...")
converter = tf.lite.TFLiteConverter.from_saved_model(str(saved_model_dir))
converter.target_spec.supported_ops = [
    tf.lite.OpsSet.TFLITE_BUILTINS,
    tf.lite.OpsSet.SELECT_TF_OPS
]
tflite_model_float32 = converter.convert()

float32_path = OUTPUT_DIR / "model_float32.tflite"
float32_path.write_bytes(tflite_model_float32)
print(f"✅ Float32 model saved: {float32_path}")
print(f"   Size: {len(tflite_model_float32) / 1024:.2f} KB")

# 2. Dynamic Range Quantization (recommended)
print("\n2️⃣  Converting with Dynamic Range Quantization...")
converter = tf.lite.TFLiteConverter.from_saved_model(str(saved_model_dir))
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_ops = [
    tf.lite.OpsSet.TFLITE_BUILTINS,
    tf.lite.OpsSet.SELECT_TF_OPS
]
tflite_model_quant = converter.convert()

quant_path = OUTPUT_DIR / "model_quant.tflite"
quant_path.write_bytes(tflite_model_quant)
print(f"✅ Quantized model saved: {quant_path}")
print(f"   Size: {len(tflite_model_quant) / 1024:.2f} KB")
print(f"   Compression: {(1 - len(tflite_model_quant)/len(tflite_model_float32))*100:.1f}%")

# ============================================
# CREATE LABELS.TXT
# ============================================

print("\n" + "="*70)
print("📝 CREATING OUTPUT FILES")
print("="*70)

# labels.txt
labels_path = OUTPUT_DIR / "labels.txt"
with open(labels_path, 'w') as f:
    f.write(f"0 {CLASS_O}\n")
    f.write(f"1 {CLASS_R}\n")
print(f"✅ Labels saved: {labels_path}")

# ============================================
# CREATE METADATA.JSON
# ============================================

metadata = {
    "model_name": "waste_classifier",
    "version": "1.0",
    "created_at": datetime.now().isoformat(),
    "training_duration_seconds": training_duration,
    "hyperparameters": {
        "image_size": IMG_SIZE,
        "batch_size": BATCH_SIZE,
        "epochs": EPOCHS,
        "initial_learning_rate": INITIAL_LR,
        "validation_split": VALIDATION_SPLIT
    },
    "architecture": {
        "base_model": "MobileNetV2",
        "input_shape": [*IMG_SIZE, 3],
        "total_params": int(model.count_params())
    },
    "dataset": {
        "train_samples": int(train_size),
        "val_samples": int(val_size),
        "classes": [CLASS_O, CLASS_R]
    },
    "metrics": {
        "final_train_accuracy": float(final_train_acc),
        "final_val_accuracy": float(final_val_acc),
        "best_val_accuracy": float(best_val_acc),
        "final_train_loss": float(final_train_loss),
        "final_val_loss": float(final_val_loss)
    },
    "output_files": {
        "savedmodel": str(saved_model_dir.name),
        "h5_checkpoint": str(checkpoint_path.name),
        "tflite_float32": str(float32_path.name),
        "tflite_quantized": str(quant_path.name),
        "labels": str(labels_path.name)
    }
}

metadata_path = OUTPUT_DIR / "metadata.json"
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"✅ Metadata saved: {metadata_path}")

# ============================================
# FINAL SUMMARY
# ============================================

print("\n" + "="*70)
print("🎉 TRAINING PIPELINE COMPLETE!")
print("="*70)

print(f"\n📦 Output files di: {OUTPUT_DIR}")
print(f"\nModel files:")
print(f"   ✅ {saved_model_dir.name}/ (SavedModel)")
print(f"   ✅ {checkpoint_path.name} (Keras H5)")
print(f"   ✅ {float32_path.name} ({len(tflite_model_float32)/1024:.1f} KB)")
print(f"   ✅ {quant_path.name} ({len(tflite_model_quant)/1024:.1f} KB) ⭐ Recommended")
print(f"\nSupporting files:")
print(f"   ✅ {labels_path.name}")
print(f"   ✅ {metadata_path.name}")

print(f"\n📊 Model Performance:")
print(f"   Best Validation Accuracy: {best_val_acc*100:.2f}%")
if best_val_acc >= 0.90:
    print(f"   ✅ Target achieved (>90%)")
else:
    print(f"   ⚠️  Below target (aim for >90%)")

print(f"\n🚀 Next Steps:")
print(f"   1. Test model: python3 scripts/test_classifier.py")
print(f"   2. Run system: ./start.sh")
print(f"   3. Model siap deploy ke edge device!")

print("\n" + "="*70)
