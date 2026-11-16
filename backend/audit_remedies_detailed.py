import json
from pathlib import Path

REMEDIES_PATH = Path(r"C:\Users\DELL\OneDrive\Desktop\Crop-Yield-Predication\CropYieldApp\CropYieldApp\backend\data\disease_remedies.json")

REQUIRED_SECTIONS = [
    "crop_name", "plant_part", "disease_name", "causal_organism", "description",
    "symptoms", "causes", "favourable_conditions", "disease_spread", "severity",
    "prevention", "organic_control", "chemical_control", "precautions", "when_to_consult_expert"
]

ALL_42_MODEL_CLASSES = [
    "Apple___Apple_scab", "Apple___Black_rot", "Apple___Cedar_apple_rust", "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew", "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot", "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight", "Corn_(maize)___healthy",
    "Cotton___Bacterial_blight", "Cotton___Powdery_mildew", "Cotton___Target_spot", "Cotton___healthy",
    "Grape___Black_rot", "Grape___Esca_(Black_Measles)", "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)", "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot", "Peach___healthy",
    "Pepper,_bell___Bacterial_spot", "Pepper,_bell___healthy",
    "Potato___Early_blight", "Potato___Late_blight", "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch", "Strawberry___healthy",
    "Tomato___Bacterial_spot", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot", "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot", "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___Tomato_mosaic_virus", "Tomato___healthy"
]

ADVISORY_ONLY_CLASSES = [
    "Rice___Blast", "Wheat___Stripe_rust", "Soybean___Rust", "Groundnut___Tikka_leaf_spot"
]

ALL_46_TARGET_CLASSES = ALL_42_MODEL_CLASSES + ADVISORY_ONLY_CLASSES

def audit_remedies():
    if not REMEDIES_PATH.exists():
        print(f"[ERROR] {REMEDIES_PATH} does not exist!")
        return

    with open(REMEDIES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Total records in current disease_remedies.json: {len(data)}")
    
    # Check completeness of existing records
    existing_complete = []
    existing_incomplete = []
    
    for key, val in data.items():
        en_sec = val.get("en", {})
        hi_sec = val.get("hi", {})
        
        missing_en = [s for s in REQUIRED_SECTIONS if s not in en_sec]
        missing_hi = [s for s in REQUIRED_SECTIONS if s not in hi_sec]
        
        if missing_en or missing_hi:
            existing_incomplete.append({
                "class": key,
                "missing_en": missing_en,
                "missing_hi": missing_hi
            })
        else:
            existing_complete.append(key)
            
    print(f"\n[OK] Fully complete 15-section bilingual existing records: {len(existing_complete)}/16")
    for c in existing_complete:
        print(f"  + {c}")
        
    if existing_incomplete:
        print(f"\n[WARN] Incomplete existing records: {len(existing_incomplete)}")
        for inc in existing_incomplete:
            print(f"  - {inc['class']}: missing EN {inc['missing_en']}, missing HI {inc['missing_hi']}")
            
    # Check against the 46 target classes
    present_in_db = [c for c in ALL_46_TARGET_CLASSES if c in data]
    missing_from_db = [c for c in ALL_46_TARGET_CLASSES if c not in data]
    
    print(f"\nTarget 46 classes status:")
    print(f"  - Present in remedies DB: {len(present_in_db)}/46")
    print(f"  - Genuinely missing (must be authored): {len(missing_from_db)}/46")
    
    print("\nMissing 30 classes requiring verified 15-section bilingual records:")
    for idx, c in enumerate(missing_from_db, 1):
        is_healthy = "healthy" in c.lower()
        htype = "HEALTHY (General vigor guidance)" if is_healthy else "DISEASED (ICAR/SAU verified)"
        print(f"  [{idx:2d}] {c:<50} -> {htype}")

if __name__ == "__main__":
    audit_remedies()
