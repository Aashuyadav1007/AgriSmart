import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
import joblib
from pathlib import Path

from path_config import DATASET_PATH, RF_MODEL_PATH

def train(sample_size: int = None):
    print(f"Loading data from {DATASET_PATH}...")
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
    
    if sample_size:
        print(f"Reading sample of {sample_size} records...")
        df = pd.read_csv(DATASET_PATH, nrows=sample_size)
    else:
        df = pd.read_csv(DATASET_PATH)
    
    # Feature columns and target
    target = 'Yield_tons_per_hectare'
    X = df.drop(columns=[target])
    y = df[target]

    # Handle boolean types
    X['Fertilizer_Used'] = X['Fertilizer_Used'].astype(int)
    X['Irrigation_Used'] = X['Irrigation_Used'].astype(int)

    numeric_features = ['Rainfall_mm', 'Temperature_Celsius', 'Days_to_Harvest', 'Fertilizer_Used', 'Irrigation_Used']
    categorical_features = ['Region', 'Soil_Type', 'Crop', 'Weather_Condition']

    num_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    cat_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', num_pipeline, numeric_features),
            ('cat', cat_pipeline, categorical_features)
        ])

    print(f"Building pipeline for {len(X)} records...")
    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('model', RandomForestRegressor(n_estimators=20, max_depth=10, random_state=42, n_jobs=-1))
    ])

    print("Splitting data (reproducible seed 42)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest model...")
    pipeline.fit(X_train, y_train)

    train_score = pipeline.score(X_train, y_train)
    test_score = pipeline.score(X_test, y_test)
    print(f"Train R2: {train_score:.4f}")
    print(f"Test R2: {test_score:.4f}")

    print(f"Saving model to {RF_MODEL_PATH}...")
    joblib.dump(pipeline, RF_MODEL_PATH)
    print("Done!")

if __name__ == '__main__':
    train(sample_size=100000)
