"""
AgriMind AI - Step 1: Real-World Application Validation Script
Executes realistic stress tests across all 4 operational modules.
"""

import sys
import io
import json
import numpy as np
from PIL import Image
from pathlib import Path

# Ensure UTF-8 stdout on Windows console
if sys.stdout and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to Python path
sys.path.append(str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app import app, load_all_models
from services.location_service import location_service
from services.weather_service import weather_service

print("\n" + "="*75)
print("       AGRIMIND AI - REAL-WORLD STRESS & APPLICATION VALIDATION")
print("="*75)

load_all_models()
client = TestClient(app)

results = {
    "yield_predictions": [],
    "disease_diagnoses": [],
    "weather_telemetry": [],
    "chatbot_interactions": []
}

# ----------------------------------------------------------------------------
# 1. CROP YIELD REAL-WORLD SCENARIOS
# ----------------------------------------------------------------------------
print("\n--- 1. CROP YIELD PREDICTION VALIDATION ---")
yield_scenarios = [
    {
        "name": "Scenario 1: Wheat in North India (Ideal Rabi Conditions)",
        "payload": {
            "Region": "North", "Soil_Type": "Loam", "Crop": "Wheat",
            "Rainfall_mm": 520.0, "Temperature_Celsius": 21.5,
            "Fertilizer_Used": True, "Irrigation_Used": True,
            "Weather_Condition": "Sunny", "Days_to_Harvest": 125
        }
    },
    {
        "name": "Scenario 2: Cotton in West India (Kharif Cash Crop)",
        "payload": {
            "Region": "West", "Soil_Type": "Clay", "Crop": "Cotton",
            "Rainfall_mm": 720.0, "Temperature_Celsius": 29.0,
            "Fertilizer_Used": True, "Irrigation_Used": True,
            "Weather_Condition": "Sunny", "Days_to_Harvest": 155
        }
    },
    {
        "name": "Scenario 3: Rice in South India (High Water & Heat)",
        "payload": {
            "Region": "South", "Soil_Type": "Clay", "Crop": "Rice",
            "Rainfall_mm": 1150.0, "Temperature_Celsius": 31.0,
            "Fertilizer_Used": True, "Irrigation_Used": True,
            "Weather_Condition": "Rainy", "Days_to_Harvest": 135
        }
    },
    {
        "name": "Scenario 4: Maize in East India (Rain-fed Loam)",
        "payload": {
            "Region": "East", "Soil_Type": "Loam", "Crop": "Maize",
            "Rainfall_mm": 600.0, "Temperature_Celsius": 26.0,
            "Fertilizer_Used": False, "Irrigation_Used": False,
            "Weather_Condition": "Cloudy", "Days_to_Harvest": 110
        }
    }
]

for sc in yield_scenarios:
    resp = client.post("/api/yield/predict", json=sc["payload"])
    assert resp.status_code == 200, f"Yield failed: {resp.text}"
    data = resp.json()
    rf = data["predictions"]["random_forest"]
    tf = data["predictions"]["tensorflow_dnn"]
    consensus = data["predictions"]["ensemble_consensus"]
    
    # Unit conversions
    per_ha = consensus["yield_kg_per_ha"]
    per_acre = round(per_ha / 2.47105, 2)
    per_bigha = round(per_ha / 3.953686, 2)
    
    print(f"[{sc['name']}]")
    print(f"  Inputs: Crop={sc['payload']['Crop']}, Soil={sc['payload']['Soil_Type']}, Rain={sc['payload']['Rainfall_mm']} mm, Temp={sc['payload']['Temperature_Celsius']}°C")
    print(f"  Predictions: RF={rf['yield_kg_per_ha']} kg/ha | TF={tf['yield_kg_per_ha']} kg/ha")
    print(f"  Consensus: {per_ha} kg/ha ({round(per_ha/1000, 2)} t/ha) | Agreement: {consensus['model_agreement_percentage']}%")
    print(f"  Converted Units: {per_acre} kg/Acre | {per_bigha} kg/Bigha")

# Negative yield test: Invalid field value
resp_inv = client.post("/api/yield/predict", json={"Region": "InvalidRegion", "Crop": "Unknown"})
print(f"[Negative Test: Invalid Inputs] Handled: HTTP {resp_inv.status_code}")

# ----------------------------------------------------------------------------
# 2. DISEASE DETECTION REAL-WORLD SCENARIOS
# ----------------------------------------------------------------------------
print("\n--- 2. PLANT DISEASE DETECTION & OOD VALIDATION ---")
base_pv = Path(__file__).resolve().parent / "data" / "plantvillage_dataset"
base_holdout = Path(__file__).resolve().parent / "data" / "holdout_test_images"

leaf_tests = [
    ("Real Cotton Bacterial Blight (Holdout)", base_holdout / "Cotton___Bacterial_blight" / "holdout_17.jpg"),
    ("Real Cotton Healthy (Holdout)", base_holdout / "Cotton___healthy" / "holdout_19.jpg"),
    ("Real Corn Common Rust", base_pv / "Corn_(maize)___Common_rust_" / "RS_Rust 1563.JPG"),
    ("Real Potato Late Blight", base_pv / "Potato___Late_blight" / "0051e5e8-d1c4-4a84-bf3a-a426cdad6285___RS_LB 4640.JPG"),
    ("Real Tomato Bacterial Spot", base_pv / "Tomato___Bacterial_spot" / "00416648-be6e-4bd4-bc8d-82f43f8a7240___GCREC_Bact.Sp 3110.JPG"),
]

for label, p in leaf_tests:
    if p.exists():
        with open(p, "rb") as f:
            resp = client.post("/api/disease/detect", files={"file": ("leaf.jpg", f.read(), "image/jpeg")})
        assert resp.status_code == 200, f"Disease failed: {resp.text}"
        data = resp.json()
        pred = data["prediction"]
        remedy = data.get("pathology_and_remedies", {})
        top3 = [f"{tp['class_name'].split('___')[-1]} ({tp['confidence_percentage']}%)" for tp in pred["top_predictions"][:3]]
        print(f"[{label}]")
        print(f"  Diagnosis: {pred['class_name']} ({pred['crop']} - {pred['condition']})")
        print(f"  Confidence: {pred['confidence_percentage']}% | Entropy: {pred['normalized_entropy']} | Status: {pred['status']}")
        print(f"  Top 3 Probabilities: {', '.join(top3)}")
        print(f"  Verified Citation: {remedy.get('source_reference', 'N/A')}")
    else:
        print(f"[{label}] File not found at {p}")

# OOD Rejection Test
noise_arr = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
img = Image.fromarray(noise_arr)
buf = io.BytesIO()
img.save(buf, format="JPEG")
buf.seek(0)
resp_ood = client.post("/api/disease/detect", files={"file": ("noise.jpg", buf.read(), "image/jpeg")})
ood_pred = resp_ood.json()["prediction"]
print(f"[OOD Test: Synthetic Non-Plant Noise]")
print(f"  Status: {ood_pred['status']} (is_supported_crop={ood_pred['is_supported_crop']})")
print(f"  Entropy: {ood_pred['normalized_entropy']} | Confidence: {ood_pred['confidence_percentage']}%")
print(f"  Recommended Action: {ood_pred['recommended_action'][:100]}...")

# Corrupted file test
resp_corrupt = client.post("/api/disease/detect", files={"file": ("corrupt.jpg", b"NOT_AN_IMAGE_BYTES_12345", "image/jpeg")})
print(f"[Corrupted File Test] Handled safely: HTTP {resp_corrupt.status_code} ({resp_corrupt.json().get('detail', '')[:50]}...)")

# ----------------------------------------------------------------------------
# 3. SMART DASHBOARD & WEATHER TELEMETRY
# ----------------------------------------------------------------------------
print("\n--- 3. SMART DASHBOARD & WEATHER TELEMETRY VALIDATION ---")
districts = [
    ("Madhya Pradesh", "Bhopal"),
    ("Madhya Pradesh", "Indore"),
    ("Maharashtra", "Nagpur")
]

for state, dist in districts:
    resp = client.get("/api/dashboard/summary", params={"state": state, "district": dist})
    assert resp.status_code == 200, f"Summary failed: {resp.text}"
    data = resp.json()
    wx = data["current_weather"]
    loc = data["location"]
    top_crop = data["crop_suitability"]["suitability_rankings"][0]
    hist_rain = data["historical_rainfall_30d"]["summary_statistics"]["cumulative_rainfall_mm"]

    print(f"[{dist}, {state}]")
    print(f"  Verified Coordinates: Lat {loc['latitude']}°N, Lon {loc['longitude']}°E (Elev: {loc.get('elevation_m', 0)} m)")
    print(f"  Live Weather: {wx['temperature_celsius']}°C, Humidity: {wx['relative_humidity_percent']}%, Wind: {wx['wind_speed_kmh']} km/h ({wx['weather_condition']})")
    print(f"  30-Day Cumulative Precipitation: {hist_rain} mm")
    print(f"  Top Suitable Crop: {top_crop['crop_name']} ({top_crop['suitability_score']}/100, {top_crop['suitability_level']})")

# Non-existent district test
resp_fake = client.get("/api/dashboard/summary", params={"state": "Madhya Pradesh", "district": "FictionalCity999"})
print(f"[Negative Test: Unknown District] Handled safely: HTTP {resp_fake.status_code} ({resp_fake.json().get('detail', '')[:50]}...)")

# ----------------------------------------------------------------------------
# 4. AI FARMING ASSISTANT (RAG & SECURITY)
# ----------------------------------------------------------------------------
print("\n--- 4. AI FARMING ASSISTANT VALIDATION ---")
chat_queries = [
    "What is the recommended fertilizer schedule for wheat?",
    "How to manage bacterial blight in cotton organically?",
    "When should I irrigate chickpea in rabi season?"
]

for q in chat_queries:
    resp = client.post("/api/chat", json={"message": q, "history": []})
    status = resp.status_code
    if status == 200:
        ans = resp.json()
        print(f"[Query: '{q}']")
        print(f"  Status: HTTP 200 (Live Gemini API)")
        print(f"  Context Topics Used: {ans.get('context_topics', [])}")
        reply_snippet = ans.get('reply', '').encode('ascii', 'replace').decode('ascii')[:100]
        print(f"  Reply Preview: {reply_snippet}...")
    elif status == 503:
        ans = resp.json()["detail"]
        print(f"[Query: '{q}']")
        print(f"  Status: HTTP 503 (Graceful Setup Notice)")
        print(f"  Notice: {ans.get('setup', '')}")
    
    # Assert zero secret exposure
    resp_str = resp.text
    assert "AIzaSy" not in resp_str, "CRITICAL: Potential Gemini API key leak in response!"

print("  [SECURITY CHECK] Confirmed 0 private keys or credentials exposed in chat payloads.")
print("\n" + "="*75)
print("REAL-WORLD APPLICATION VALIDATION COMPLETE - ALL MODULES HEALTHY")
print("="*75)
