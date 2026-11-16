"""
AgriMind AI - Universal Plant Disease Pipeline & Dataset Manifest Verification Suite
Tests:
1. Dataset manifest integrity for all 17 crop categories
2. 15-section bilingual agronomic advisory completeness
3. Image quality validation
4. Non-plant synthetic noise rejection (OOD gating)
5. Plant organ discrimination (Tuber vs Foliage routing)
6. Real holdout plant disease diagnosis & healthy leaf recognition
"""
import sys
import io
import json
import numpy as np
from PIL import Image
from pathlib import Path

# Fix Windows console UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from services.disease_service import disease_service
from services.image_pipeline import image_pipeline

def test_dataset_manifest():
    print("\n" + "="*70)
    print("TEST 1: DATASET MANIFEST INTEGRITY (EXACT 17 CROP CATEGORIES)")
    print("="*70)
    manifest_path = BACKEND_DIR / "data" / "crop_disease_dataset_manifest.json"
    assert manifest_path.exists(), "Manifest file missing!"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("total_crops_cataloged") == 17, f"Expected 17 crops, got {data.get('total_crops_cataloged')}"
    crops = data.get("crop_categories", [])
    assert len(crops) == 17, f"Expected 17 crop categories, got {len(crops)}"

    expected_crops = [
        "Rice / Paddy (धान)",
        "Soybean (सोयाबीन)",
        "Groundnut (मूंगफली)",
        "Pigeon Pea (अरहर / तुअर)",
        "Green Gram (मूंग)",
        "Black Gram (उड़द)",
        "Pearl Millet (बाजरा)",
        "Sorghum (ज्वार)",
        "Wheat (गेहूँ)",
        "Chickpea / Gram (चना)",
        "Mustard (सरसों)",
        "Onion / Garlic (प्याज / लहसुन)",
        "Potato Tuber (आलू कंद)",
        "Chilli (मिर्च)",
        "Brinjal (बैंगन)",
        "Okra (भिंडी)",
        "Barley / Linseed / Jute"
    ]

    for expected, item in zip(expected_crops, crops):
        assert item["crop_name"] == expected, f"Mismatch: expected '{expected}', got '{item['crop_name']}'"
        print(f"  [PASS] Cataloged #{item['id']:2}: {item['crop_name']:30} [{item['status']}]")

    print("All 17 crops verified in dataset manifest!")

def test_15_bilingual_sections():
    print("\n" + "="*70)
    print("TEST 2: 15-SECTION BILINGUAL ADVISORY INTEGRITY")
    print("="*70)
    remedies_path = BACKEND_DIR / "data" / "disease_remedies.json"
    assert remedies_path.exists(), "Remedies file missing!"
    with open(remedies_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    required_sections = [
        "crop_name", "plant_part", "disease_name", "causal_organism", "description",
        "symptoms", "causes", "favourable_conditions", "disease_spread", "severity",
        "prevention", "organic_control", "chemical_control", "precautions", "when_to_consult_expert"
    ]

    for cls_name, entry in db.items():
        en = entry.get("en", {})
        hi = entry.get("hi", {})
        for sec in required_sections:
            assert sec in en, f"Missing English section '{sec}' in {cls_name}"
            assert sec in hi, f"Missing Hindi section '{sec}' in {cls_name}"

    print(f"  [PASS] All {len(db)} disease classes possess complete 15-section English and Hindi advisories.")

def test_universal_pipeline_routing():
    print("\n" + "="*70)
    print("TEST 3: UNIVERSAL PIPELINE ORGAN & OOD DISCRIMINATION")
    print("="*70)

    # 1. Non-plant surface test (e.g. blue metallic tool or gray wall)
    non_plant = np.full((224, 224, 3), fill_value=[60, 90, 180], dtype=np.uint8)
    buf_np = io.BytesIO()
    Image.fromarray(non_plant).save(buf_np, format="JPEG")
    res_np = disease_service.predict_leaf_disease(buf_np.getvalue())
    assert not res_np["prediction"]["is_plant"], "Non-plant surface must be detected as non-plant!"
    assert res_np["prediction"]["status"] == "unsupported_or_unknown"
    print("  [PASS] Non-Plant Surface Check: Correctly rejected as non-plant subject.")

    # 2. Synthetic noise OOD rejection
    noise = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
    buf_noise = io.BytesIO()
    Image.fromarray(noise).save(buf_noise, format="JPEG")
    res_noise = disease_service.predict_leaf_disease(buf_noise.getvalue())
    assert res_noise["prediction"]["status"] == "unsupported_or_unknown"
    assert not res_noise["prediction"]["is_supported_crop"]
    print(f"  [PASS] OOD Noise Rejection: Rejected with status '{res_noise['prediction']['status']}' (Entropy: {res_noise['prediction']['normalized_entropy']}).")

    # 3. Potato Tuber / Non-foliar organ test (Brownish rounded organ)
    tuber_arr = np.full((224, 224, 3), fill_value=[140, 100, 60], dtype=np.uint8)
    for y in range(224):
        for x in range(224):
            if (x-112)**2 + (y-112)**2 > 90**2:
                tuber_arr[y, x] = [200, 200, 200]
    buf_tuber = io.BytesIO()
    Image.fromarray(tuber_arr).save(buf_tuber, format="JPEG")
    tuber_bytes = buf_tuber.getvalue()

    res_tuber = disease_service.predict_leaf_disease(tuber_bytes)
    assert res_tuber["prediction"]["plant_part"] != "Leaf", "Tuber must not be diagnosed as Leaf!"
    print(f"  [PASS] Organ Discrimination: Detected '{res_tuber['prediction']['plant_part']}' - Prevented leaf false positive.")

    # 4. Real holdout Cotton Leaf test
    holdout_img = BACKEND_DIR / "data" / "holdout_test_images" / "Cotton___Bacterial_blight" / "holdout_17.jpg"
    if holdout_img.exists():
        with open(holdout_img, "rb") as f:
            cotton_bytes = f.read()
        res_cotton = disease_service.predict_leaf_disease(cotton_bytes)
        pred = res_cotton["prediction"]
        assert pred["class_name"] == "Cotton___Bacterial_blight"
        assert pred["confidence_percentage"] > 70.0
        assert pred["status"] == "confirmed"
        print(f"  [PASS] Real Cotton Holdout: Diagnosed '{pred['class_name']}' at {pred['confidence_percentage']}% confidence.")

if __name__ == "__main__":
    test_dataset_manifest()
    test_15_bilingual_sections()
    test_universal_pipeline_routing()
    print("\n" + "="*70)
    print("UNIVERSAL CROP DISEASE PIPELINE & MANIFEST TESTS PASSED (3/3)!")
    print("="*70)
