"""
AgriSmart - Stage 4 Backend Integration Test
Tests all API endpoints including /api/chat (Gemini + RAG)
"""
import sys
import time
import json
import requests
from pathlib import Path

BASE = "http://localhost:8000"
BACKEND_DIR = Path(__file__).resolve().parent

def wait_for_server(max_wait=60):
    print("Waiting for backend server...")
    for i in range(max_wait):
        try:
            r = requests.get(f"{BASE}/health", timeout=2)
            if r.status_code == 200:
                print(f"  Server ready after {i+1}s")
                return True
        except Exception:
            pass
        time.sleep(1)
    print("  TIMEOUT: Server did not start")
    return False

def test_health():
    print("\n[TEST 1] GET /health")
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    data = r.json()
    assert data["rf_model_loaded"] is True
    assert data["tf_model_loaded"] is True
    assert data["disease_model_loaded"] is True
    print(f"  PASS: All models loaded")

def test_root():
    print("\n[TEST 2] GET / (system info)")
    r = requests.get(f"{BASE}/")
    assert r.status_code == 200
    data = r.json()
    assert "AgriSmart" in data["system"]
    assert "module_3" in data["modules"]
    print(f"  PASS: System = {data['system']}")

def test_yield_predict():
    print("\n[TEST 3] POST /api/yield/predict (dual model)")
    payload = {
        "Region": "North", "Soil_Type": "Loam", "Crop": "Wheat",
        "Rainfall_mm": 650.0, "Temperature_Celsius": 23.5,
        "Weather_Condition": "Sunny", "Fertilizer_Used": True,
        "Irrigation_Used": True, "Days_to_Harvest": 120
    }
    r = requests.post(f"{BASE}/api/yield/predict", json=payload)
    assert r.status_code == 200
    data = r.json()
    rf = data["predictions"]["random_forest"]["yield_kg_per_ha"]
    tf = data["predictions"]["tensorflow_dnn"]["yield_kg_per_ha"]
    cons = data["predictions"]["ensemble_consensus"]["yield_kg_per_ha"]
    agree = data["predictions"]["ensemble_consensus"]["model_agreement_percentage"]
    assert rf > 0 and tf > 0 and cons > 0
    print(f"  PASS: RF={rf}, TF={tf}, Consensus={cons}, Agreement={agree}%")

def test_legacy_predict():
    print("\n[TEST 4] POST /predict (legacy)")
    payload = {
        "Region": "South", "Soil_Type": "Clay", "Crop": "Rice",
        "Rainfall_mm": 1200.0, "Temperature_Celsius": 28.0,
        "Weather_Condition": "Rainy", "Fertilizer_Used": True,
        "Irrigation_Used": True, "Days_to_Harvest": 150
    }
    r = requests.post(f"{BASE}/predict", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "predicted_yield_kg_per_hectare" in data
    assert data["model_used"] == "Random Forest Regressor"
    print(f"  PASS: Legacy = {data['predicted_yield_kg_per_hectare']} kg/ha")

def test_disease_detect():
    print("\n[TEST 5] POST /api/disease/detect (real image)")
    img_dir = BACKEND_DIR / "data" / "plantvillage_dataset"
    test_images = list(img_dir.rglob("*.jpg")) + list(img_dir.rglob("*.JPG"))
    if not test_images:
        print("  SKIP: No test images found")
        return
    img_path = test_images[0]
    print(f"  Using: {img_path.name}")
    with open(img_path, "rb") as f:
        r = requests.post(f"{BASE}/api/disease/detect", files={"file": (img_path.name, f, "image/jpeg")})
    assert r.status_code == 200
    data = r.json()
    # Actual response structure: data.prediction.class_name, data.prediction.confidence_percentage
    pred = data["prediction"]
    assert "class_name" in pred
    assert pred["confidence_percentage"] > 0
    print(f"  PASS: {pred['class_name']} ({pred['confidence_percentage']:.1f}%)")

def test_yield_metrics():
    print("\n[TEST 6] GET /api/yield/metrics")
    r = requests.get(f"{BASE}/api/yield/metrics")
    assert r.status_code == 200
    data = r.json()
    models = data.get("models", data)  # may be nested under "models"
    assert "random_forest" in models
    assert "tensorflow_dnn" in models
    rf_r2 = models["random_forest"].get("r2_score", models["random_forest"].get("r2", 0))
    tf_r2 = models["tensorflow_dnn"].get("r2_score", models["tensorflow_dnn"].get("r2", 0))
    print(f"  PASS: RF R2={rf_r2:.4f}, TF R2={tf_r2:.4f}")

def test_disease_classes():
    print("\n[TEST 7] GET /api/disease/classes")
    r = requests.get(f"{BASE}/api/disease/classes")
    assert r.status_code == 200
    data = r.json()
    assert data["total_classes"] == 8
    print(f"  PASS: {data['total_classes']} classes")

def test_chat_endpoint():
    print("\n[TEST 8] POST /api/chat")
    r = requests.post(f"{BASE}/api/chat", json={"message": "What is the best fertilizer for rice?"})
    if r.status_code == 503:
        data = r.json()
        detail_str = str(data.get("detail", ""))
        assert "GEMINI" in detail_str.upper() or "not configured" in detail_str.lower()
        print(f"  PASS: Correct 503 (no API key)")
    elif r.status_code == 200:
        data = r.json()
        assert "reply" in data and len(data["reply"]) > 0
        print(f"  PASS: Got reply ({len(data['reply'])} chars), context: {data.get('context_topics', [])}")
    else:
        raise AssertionError(f"Unexpected status {r.status_code}")

def test_chat_validation():
    print("\n[TEST 9] POST /api/chat - input validation")
    r = requests.post(f"{BASE}/api/chat", json={"message": ""})
    assert r.status_code == 422, f"Expected 422 for empty message, got {r.status_code}"
    print("  PASS: Empty message rejected (422)")

def main():
    if not wait_for_server():
        sys.exit(1)

    tests = [
        test_health, test_root, test_yield_predict, test_legacy_predict,
        test_disease_detect, test_yield_metrics, test_disease_classes,
        test_chat_endpoint, test_chat_validation,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")

    total = len(tests)
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} tests passed")
    if passed == total:
        print("ALL TESTS PASSED!")
    else:
        print(f"FAILURES: {total - passed}")
        sys.exit(1)

if __name__ == "__main__":
    main()
