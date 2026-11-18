import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib

# Suppress excessive TensorFlow logs
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers, callbacks

from path_config import DATASET_PATH, RF_MODEL_PATH, TF_MODEL_PATH, METRICS_PATH, MODELS_DIR

def train_and_benchmark(sample_size: int = 100000, epochs: int = 25, batch_size: int = 128):
    print("=" * 60)
    print("AgriSmart - Module 1: Crop Yield Model Training & Benchmarking")
    print("=" * 60)
    
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Random Forest Pipeline to extract preprocessor and baseline model
    print(f"\n[1/6] Loading existing Random Forest pipeline from {RF_MODEL_PATH}...")
    rf_pipeline = joblib.load(RF_MODEL_PATH)
    preprocessor = rf_pipeline.named_steps['preprocessor']
    rf_estimator = rf_pipeline.named_steps['model']
    
    # 2. Load dataset
    print(f"\n[2/6] Loading dataset from {DATASET_PATH} (sample size: {sample_size:,})...")
    df = pd.read_csv(DATASET_PATH, nrows=sample_size)
    print(f"Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    
    target_col = 'Yield_tons_per_hectare'
    X = df.drop(columns=[target_col])
    y = df[target_col].values
    
    # Ensure boolean encoding matches existing pipeline
    X['Fertilizer_Used'] = X['Fertilizer_Used'].astype(int)
    X['Irrigation_Used'] = X['Irrigation_Used'].astype(int)
    
    # 3. Reproducible train/test split (80/20, seed=42)
    print("\n[3/6] Performing reproducible 80/20 train/test split (seed=42)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Train samples: {len(X_train):,}, Test samples: {len(X_test):,}")
    
    # 4. Transform features using exact preprocessor
    print("\n[4/6] Transforming features through preprocessor...")
    X_train_trans = preprocessor.transform(X_train)
    X_test_trans = preprocessor.transform(X_test)
    
    if hasattr(X_train_trans, 'toarray'):
        X_train_trans = X_train_trans.toarray()
        X_test_trans = X_test_trans.toarray()
    
    input_dim = X_train_trans.shape[1]
    print(f"Feature dimension after encoding: {input_dim}")
    
    # 5. Build and train TensorFlow Neural Network
    print("\n[5/6] Building TensorFlow/Keras Deep Neural Network...")
    tf.random.set_seed(42)
    np.random.seed(42)
    
    model = keras.Sequential([
        layers.Input(shape=(input_dim,)),
        layers.Dense(128, activation='relu', kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.Dropout(0.2),
        layers.Dense(64, activation='relu', kernel_regularizer=regularizers.l2(1e-4)),
        layers.BatchNormalization(),
        layers.Dropout(0.15),
        layers.Dense(32, activation='relu'),
        layers.Dense(1, activation='linear')
    ], name="AgriSmart_Yield_Forecaster")
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.002),
        loss='mse',
        metrics=['mae']
    )
    model.summary()
    
    early_stop = callbacks.EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True,
        verbose=1
    )
    reduce_lr = callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=2,
        min_lr=1e-5,
        verbose=1
    )
    
    print("\nTraining Neural Network...")
    start_time = time.time()
    history = model.fit(
        X_train_trans, y_train,
        validation_split=0.15,
        epochs=epochs,
        batch_size=batch_size,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )
    train_duration = time.time() - start_time
    print(f"Neural Network training finished in {train_duration:.2f} seconds.")
    
    # Save the trained Keras model
    print(f"Saving TensorFlow model to {TF_MODEL_PATH}...")
    model.save(TF_MODEL_PATH)
    
    # 6. Comprehensive Benchmark Evaluation on the EXACT SAME test set
    print("\n[6/6] Evaluating Random Forest and TensorFlow on exact same test set...")
    
    # Predictions
    rf_preds = rf_pipeline.predict(X_test)
    tf_preds = model.predict(X_test_trans).flatten()
    
    # Metrics calculation (tons/ha)
    rf_r2 = float(r2_score(y_test, rf_preds))
    rf_mae = float(mean_absolute_error(y_test, rf_preds))
    rf_rmse = float(np.sqrt(mean_squared_error(y_test, rf_preds)))
    
    tf_r2 = float(r2_score(y_test, tf_preds))
    tf_mae = float(mean_absolute_error(y_test, tf_preds))
    tf_rmse = float(np.sqrt(mean_squared_error(y_test, tf_preds)))
    
    # Also calculate metrics in kg/ha (tons * 1000)
    rf_mae_kg = round(rf_mae * 1000, 2)
    rf_rmse_kg = round(rf_rmse * 1000, 2)
    tf_mae_kg = round(tf_mae * 1000, 2)
    tf_rmse_kg = round(tf_rmse * 1000, 2)
    
    comparison = {
        "benchmark_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_sample_size": sample_size,
        "test_sample_size": len(X_test),
        "random_state": 42,
        "feature_count": input_dim,
        "models": {
            "random_forest": {
                "name": "Random Forest Regressor",
                "r2_score": round(rf_r2, 4),
                "mae_tons_per_ha": round(rf_mae, 4),
                "rmse_tons_per_ha": round(rf_rmse, 4),
                "mae_kg_per_ha": rf_mae_kg,
                "rmse_kg_per_ha": rf_rmse_kg
            },
            "tensorflow_dnn": {
                "name": "TensorFlow Deep Neural Network",
                "r2_score": round(tf_r2, 4),
                "mae_tons_per_ha": round(tf_mae, 4),
                "rmse_tons_per_ha": round(tf_rmse, 4),
                "mae_kg_per_ha": tf_mae_kg,
                "rmse_kg_per_ha": tf_rmse_kg,
                "epochs_trained": len(history.history['loss']),
                "training_time_seconds": round(train_duration, 2)
            }
        },
        "winner": "Random Forest Regressor" if rf_r2 >= tf_r2 else "TensorFlow Deep Neural Network"
    }
    
    with open(METRICS_PATH, 'w') as f:
        json.dump(comparison, f, indent=2)
    print(f"Benchmark comparison saved to {METRICS_PATH}")
    
    print("\n" + "=" * 60)
    print("FINAL BENCHMARK COMPARISON REPORT:")
    print("=" * 60)
    print(f"Metric             | Random Forest       | TensorFlow DNN")
    print(f"-------------------|---------------------|--------------------")
    print(f"R² Score           | {rf_r2:.4f}              | {tf_r2:.4f}")
    print(f"MAE (tons/ha)      | {rf_mae:.4f}              | {tf_mae:.4f}")
    print(f"RMSE (tons/ha)     | {rf_rmse:.4f}              | {tf_rmse:.4f}")
    print(f"MAE (kg/ha)        | {rf_mae_kg:,.2f} kg/ha       | {tf_mae_kg:,.2f} kg/ha")
    print(f"RMSE (kg/ha)       | {rf_rmse_kg:,.2f} kg/ha       | {tf_rmse_kg:,.2f} kg/ha")
    print("=" * 60)
    print(f"Selected Best Performer on R²: {comparison['winner']}\n")
    
    return comparison

if __name__ == '__main__':
    train_and_benchmark(sample_size=100000, epochs=15, batch_size=256)
