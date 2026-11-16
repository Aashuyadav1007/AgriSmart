from pathlib import Path
import os

# Root directories
BACKEND_DIR = Path(__file__).resolve().parent
MODELS_DIR = BACKEND_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Function to dynamically resolve project root and files
def resolve_project_root() -> Path:
    for parent in [BACKEND_DIR] + list(BACKEND_DIR.parents):
        if (parent / "CRP dataset" / "crop_yield.csv").exists():
            return parent
        if (parent / "crop_yield.csv").exists():
            return parent
    return BACKEND_DIR.parent.parent

PROJECT_ROOT = resolve_project_root()

def get_dataset_path() -> Path:
    candidates = [
        PROJECT_ROOT / "CRP dataset" / "crop_yield.csv",
        PROJECT_ROOT / "crop_yield.csv",
        BACKEND_DIR / "crop_yield.csv",
        BACKEND_DIR.parent / "crop_yield.csv"
    ]
    for p in candidates:
        if p.exists():
            return p
    return PROJECT_ROOT / "CRP dataset" / "crop_yield.csv"

DATASET_PATH = get_dataset_path()
RF_MODEL_PATH = BACKEND_DIR / "rf_model.joblib"
TF_MODEL_PATH = MODELS_DIR / "tf_yield_model.keras"
METRICS_PATH = MODELS_DIR / "yield_comparison_metrics.json"
DISEASE_MODEL_PATH = MODELS_DIR / "disease_classifier.pth"
DISEASE_CLASSES_PATH = MODELS_DIR / "disease_classes.json"
