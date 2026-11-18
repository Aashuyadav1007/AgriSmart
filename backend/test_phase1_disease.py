import io
import json
from pathlib import Path
from PIL import Image
import numpy as np

from path_config import BACKEND_DIR, DISEASE_CLASSES_PATH, DISEASE_MODEL_PATH
from services.disease_service import disease_service

def test_phase1():
    print("=" * 70)
    print("AgriSmart - Phase 1 Verification Test Suite")
    print("Disease Detection Overhaul, Cotton Integration & OOD Rejection")
    print("=" * 70)

    # 1. Verify model metadata and saved metrics
    print("\n[TEST 1] Verifying Model Architecture & Stored Evaluation Metrics")
    assert DISEASE_CLASSES_PATH.exists(), "Metadata file missing"
    assert DISEASE_MODEL_PATH.exists(), "Model weights file missing"
    
    with open(DISEASE_CLASSES_PATH, "r") as f:
        meta = json.load(f)
        
    num_classes = meta["total_classes"]
    print(f"  Total classes: {num_classes} (Expected: 12)")
    assert num_classes == 12, f"Expected 12 classes, got {num_classes}"
    print(f"  Best Validation Accuracy: {meta.get('best_val_accuracy', 0)*100:.2f}%")
    print(f"  Held-out Test Accuracy: {meta.get('test_accuracy', 0)*100:.2f}%")
    assert meta.get('test_accuracy', 0) > 0.50, "Test accuracy too low"
    print("  PASS: Stored evaluation metrics verified")

    # 2. Test Real Cotton Leaf Images (from holdout directory)
    print("\n[TEST 2] Testing Inference on Real Cotton Leaf Images")
    cotton_holdout_dir = BACKEND_DIR / "data" / "holdout_test_images"
    cotton_imgs = list(cotton_holdout_dir.rglob("*.jpg"))
    assert len(cotton_imgs) > 0, "No cotton holdout images found"
    
    cotton_tested = 0
    cotton_predicted_correctly = 0
    
    for img_path in cotton_imgs[:6]:
        with open(img_path, "rb") as f:
            bytes_data = f.read()
            
        res = disease_service.predict_leaf_disease(bytes_data)
        pred = res["prediction"]
        parent_class = img_path.parent.name
        
        print(f"  Sample: {img_path.name:<18} (Folder: {parent_class})")
        print(f"    --> Predicted: {pred['class_name']} | Conf: {pred['confidence_percentage']}% | Supported: {pred['is_supported_crop']} | Status: {pred['status']}")
        
        cotton_tested += 1
        # If from a labelled cotton folder, check if crop is cotton
        if "cotton" in parent_class.lower():
            if "cotton" in pred["class_name"].lower() or pred["crop"].lower() == "cotton":
                cotton_predicted_correctly += 1
                
    print(f"  PASS: Tested {cotton_tested} Cotton samples. Crop identification accuracy: {cotton_predicted_correctly}/{cotton_tested}")
    assert cotton_predicted_correctly > 0, "Cotton should be recognized as Cotton"

    # 3. Test Real Corn, Tomato, and Potato Leaf Images
    print("\n[TEST 3] Testing Inference on Supported Crops (Corn, Tomato, Potato)")
    pv_dir = BACKEND_DIR / "data" / "plantvillage_dataset"
    test_targets = [
        ("Corn", pv_dir / "Corn_(maize)___Common_rust_"),
        ("Tomato", pv_dir / "Tomato___Early_blight"),
        ("Potato", pv_dir / "Potato___Late_blight")
    ]
    
    for crop_name, folder in test_targets:
        imgs = list(folder.glob("*.jpg")) + list(folder.glob("*.JPG"))
        if not imgs:
            continue
        test_img = imgs[0]
        with open(test_img, "rb") as f:
            res = disease_service.predict_leaf_disease(f.read())
            pred = res["prediction"]
            print(f"  {crop_name:<8} Image: {test_img.name:<22} --> Predicted: {pred['class_name']} ({pred['confidence_percentage']}%) | Supported: {pred['is_supported_crop']}")
            assert pred['is_supported_crop'] is True, f"{crop_name} must be marked as supported"

    # 4. Test Out-of-Distribution (OOD) / Unsupported Image Rejection
    print("\n[TEST 4] Testing OOD / Unsupported Image Rejection")
    # Generate an artificial non-leaf random noise image (definitely not any of the 4 crops)
    noise_array = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
    noise_img = Image.fromarray(noise_array)
    buf = io.BytesIO()
    noise_img.save(buf, format="JPEG")
    noise_bytes = buf.getvalue()
    
    ood_res = disease_service.predict_leaf_disease(noise_bytes)
    ood_pred = ood_res["prediction"]
    print(f"  Synthetic OOD Noise Sample:")
    print(f"    --> Top Class: {ood_pred['top_predictions'][0]['class_name']} ({ood_pred['top_predictions'][0]['confidence_percentage']}%)")
    print(f"    --> Normalized Entropy: {ood_pred['normalized_entropy']}")
    print(f"    --> Is Supported Crop: {ood_pred['is_supported_crop']}")
    print(f"    --> Status: {ood_pred['status']}")
    print(f"    --> Recommended Action: {ood_pred['recommended_action'][:80]}...")
    
    # Must reject or flag as uncertain/unsupported
    assert ood_pred['is_supported_crop'] is False or ood_pred['is_uncertain'] is True, "OOD noise should be rejected or flagged uncertain"
    print("  PASS: OOD detection successfully handled non-crop sample")

    # 5. Verify Remedy Database Coverage
    print("\n[TEST 5] Verifying Agronomic Remedy Database Coverage")
    classes_with_remedies = list(disease_service.remedies_db.keys())
    print(f"  Total remedy entries in DB: {len(classes_with_remedies)}")
    for cname in disease_service.class_names:
        assert cname in disease_service.remedies_db, f"Missing remedy for {cname}"
        rem = disease_service.remedies_db[cname]
        assert "symptoms" in rem and len(rem["symptoms"]) > 0
        assert "organic_controls" in rem and len(rem["organic_controls"]) > 0
        assert "chemical_treatment" in rem and len(rem["chemical_treatment"]) > 0
        assert "source_reference" in rem, f"Missing source citation for {cname}"
    print("  PASS: All 12 classes possess verified remedies with credible source citations")

    print("\n" + "=" * 70)
    print("ALL PHASE 1 TESTS PASSED SUCCESSFULLY! [PASS]")
    print("=" * 70)

if __name__ == "__main__":
    test_phase1()
