import os
import sys
import json
import torch
import numpy as np
from PIL import Image

sys.path.append(r'C:\Users\DELL\OneDrive\Desktop\Crop-Yield-Predication\CropYieldApp\CropYieldApp\backend')
from services.disease_service import disease_service as service

print("="*75)
print("             PHASE 1 FINAL VERIFICATION & EMPIRICAL REPORT")
print("="*75)

base_pv = r"C:\Users\DELL\OneDrive\Desktop\Crop-Yield-Predication\CropYieldApp\CropYieldApp\backend\data\plantvillage_dataset"
base_holdout = r"C:\Users\DELL\OneDrive\Desktop\Crop-Yield-Predication\CropYieldApp\CropYieldApp\backend\data\holdout_test_images"

# 1. Real Leaf Tests
test_leaves = [
    ("Cotton Bacterial Blight (Holdout)", os.path.join(base_holdout, "Cotton___Bacterial_blight", "holdout_17.jpg")),
    ("Cotton Powdery Mildew (Holdout)", os.path.join(base_holdout, "Cotton___Powdery_mildew", "holdout_17.jpg")),
    ("Cotton Target Spot (Holdout)", os.path.join(base_holdout, "Cotton___Target_spot", "holdout_17.jpg")),
    ("Cotton Healthy (Holdout)", os.path.join(base_holdout, "Cotton___healthy", "holdout_19.jpg")),
    ("Corn Common Rust", os.path.join(base_pv, "Corn_(maize)___Common_rust_", os.listdir(os.path.join(base_pv, "Corn_(maize)___Common_rust_"))[0])),
    ("Potato Late Blight", os.path.join(base_pv, "Potato___Late_blight", os.listdir(os.path.join(base_pv, "Potato___Late_blight"))[0])),
    ("Tomato Bacterial Spot", os.path.join(base_pv, "Tomato___Bacterial_spot", os.listdir(os.path.join(base_pv, "Tomato___Bacterial_spot"))[0])),
    ("Tomato Healthy", os.path.join(base_pv, "Tomato___healthy", os.listdir(os.path.join(base_pv, "Tomato___healthy"))[0])),
]

print("\n--- 1. INDIVIDUAL REAL LEAF TEST RESULTS ---")
for label, p in test_leaves:
    with open(p, "rb") as f:
        res = service.predict_leaf_disease(f.read())
    pred = res["prediction"]
    top3_str = ", ".join([f"{tp['class_name'].split('___')[-1]} ({tp['confidence_percentage']}%)" for tp in pred['top_predictions'][:3]])
    print(f"[{label}]")
    print(f"   Image Path : ...\\{os.path.basename(os.path.dirname(p))}\\{os.path.basename(p)}")
    print(f"   Predicted  : {pred['class_name']} ({pred['crop']} - {pred['condition']})")
    print(f"   Confidence : {pred['confidence_percentage']}% | Status: {pred['status']}")
    print(f"   Entropy    : {pred['normalized_entropy']} | Top 3: [{top3_str}]")

# 2. OOD Evaluation
print("\n--- 2. OUT-OF-DISTRIBUTION (OOD) & REJECTION EVALUATION ---")
# Generate test images
noise_path = r"C:\Users\DELL\OneDrive\Desktop\Crop-Yield-Predication\CropYieldApp\CropYieldApp\backend\data\ood_noise.jpg"
Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)).save(noise_path)

gray_path = r"C:\Users\DELL\OneDrive\Desktop\Crop-Yield-Predication\CropYieldApp\CropYieldApp\backend\data\ood_gray.jpg"
Image.fromarray(np.full((224, 224, 3), 128, dtype=np.uint8)).save(gray_path)

weird_arr = np.zeros((224, 224, 3), dtype=np.uint8)
weird_arr[:, :, 2] = 220
weird_arr[50:180, 50:180, 0] = 240
weird_arr[50:180, 50:180, 1] = 120
weird_path = r"C:\Users\DELL\OneDrive\Desktop\Crop-Yield-Predication\CropYieldApp\CropYieldApp\backend\data\ood_weird.jpg"
Image.fromarray(weird_arr).save(weird_path)

ood_tests = [
    ("Synthetic Non-Crop Noise", noise_path),
    ("Uniform Gray Surface (Non-plant)", gray_path),
    ("Non-Agricultural Pattern (Blue/Orange)", weird_path),
]

for label, p in ood_tests:
    with open(p, "rb") as f:
        res = service.predict_leaf_disease(f.read())
    pred = res["prediction"]
    print(f"[{label}]")
    print(f"   Status     : {pred['status']}")
    print(f"   Crop       : {pred['crop']}")
    print(f"   Confidence : {pred['confidence_percentage']}% | Entropy: {pred['normalized_entropy']}")
    print(f"   Action Rec : {pred['recommended_action'][:110]}...")

for p in [noise_path, gray_path, weird_path]:
    if os.path.exists(p):
        os.remove(p)

# 3. Cotton Remedy Details
print("\n--- 3. COTTON REMEDY SOURCES & DETAILS ---")
with open(r"C:\Users\DELL\OneDrive\Desktop\Crop-Yield-Predication\CropYieldApp\CropYieldApp\backend\data\disease_remedies.json") as f:
    rem = json.load(f)

for k in sorted(rem.keys()):
    if "Cotton" in k:
        entry = rem[k]
        print(f"\n* Class: {k}")
        print(f"  Condition        : {entry['condition']}")
        print(f"  Pathogen         : {entry['pathogen']}")
        print(f"  Source Reference : {entry['source_reference']}")
        print(f"  Organic Controls : {entry['organic_controls'][:2]}")
        print(f"  Chemical Controls: {entry['chemical_treatment'][:2]}")
