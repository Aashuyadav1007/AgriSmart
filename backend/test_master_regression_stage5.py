"""
Master Regression Test Suite for AgriMind AI - Stage 5
Covers all modules:
A. Crop Yield Prediction (Random Forest, TensorFlow DNN, Legacy /predict, Dual /api/yield/predict)
B. Plant Disease Detection (12 classes, Cotton classes, OOD rejection, Remedies & Citations)
C. AI Farming Assistant (Knowledge Base, /api/chat error handling)
D. Weather & Smart Dashboard (Current, Forecast, Historical, Crop Suitability, Summary)
"""

import sys
import unittest
import json
import numpy as np
from PIL import Image
import io
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app import app, load_all_models
from services.location_service import location_service

class TestMasterRegressionStage5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*75)
        print("          AGRIMIND AI - MASTER REGRESSION TEST SUITE (STAGE 5)")
        print("="*75)
        # Explicitly initialize all models and metrics for test client
        load_all_models()
        cls.client = TestClient(app)

    # ------------------------------------------------------------------------
    # MODULE A: CROP YIELD PREDICTION
    # ------------------------------------------------------------------------
    def test_A1_yield_metrics_endpoint(self):
        """Verify model comparison metrics are available."""
        resp = self.client.get("/api/yield/metrics")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("models", data)
        self.assertIn("random_forest", data["models"])
        self.assertIn("tensorflow_dnn", data["models"])
        rf = data["models"]["random_forest"]
        tf = data["models"]["tensorflow_dnn"]
        self.assertGreater(rf.get("r2_score", 0), 0.85)
        self.assertGreater(tf.get("r2_score", 0), 0.85)
        print(f"  [PASS] Yield Metrics: RF R²={rf.get('r2_score'):.4f}, TF R²={tf.get('r2_score'):.4f}")

    def test_A2_legacy_predict_endpoint(self):
        """Verify legacy /predict endpoint backwards compatibility."""
        payload = {
            "Region": "North",
            "Soil_Type": "Loam",
            "Crop": "Wheat",
            "Rainfall_mm": 500.0,
            "Temperature_Celsius": 22.0,
            "Fertilizer_Used": True,
            "Irrigation_Used": True,
            "Weather_Condition": "Sunny",
            "Days_to_Harvest": 120
        }
        resp = self.client.post("/predict", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("predicted_yield_tons_per_hectare", data)
        self.assertGreater(data["predicted_yield_tons_per_hectare"], 0)
        print(f"  [PASS] Legacy /predict returned: {data['predicted_yield_tons_per_hectare']:.2f} t/ha")

    def test_A3_dual_yield_predict_endpoint(self):
        """Verify dual RF + TensorFlow prediction endpoint."""
        payload = {
            "Region": "West",
            "Soil_Type": "Clay",
            "Crop": "Cotton",
            "Rainfall_mm": 700.0,
            "Temperature_Celsius": 28.0,
            "Fertilizer_Used": True,
            "Irrigation_Used": True,
            "Weather_Condition": "Sunny",
            "Days_to_Harvest": 150
        }
        resp = self.client.post("/api/yield/predict", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("random_forest", data["predictions"])
        self.assertIn("tensorflow_dnn", data["predictions"])
        self.assertIn("ensemble_consensus", data["predictions"])
        rf_val = data["predictions"]["random_forest"]["yield_tons_per_ha"]
        tf_val = data["predictions"]["tensorflow_dnn"]["yield_tons_per_ha"]
        print(f"  [PASS] Dual Yield: RF={rf_val} t/ha, TF={tf_val} t/ha")

    # ------------------------------------------------------------------------
    # MODULE B: PLANT DISEASE DETECTION
    # ------------------------------------------------------------------------
    def test_B1_disease_classes_12_supported(self):
        """Verify 12 disease classes including 4 Cotton classes."""
        resp = self.client.get("/api/disease/classes")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["total_classes"], 12)
        cotton_classes = [c for c in data["classes"] if "Cotton" in c]
        self.assertEqual(len(cotton_classes), 4)
        print(f"  [PASS] Disease Classes: 12 total, including {len(cotton_classes)} Cotton classes.")

    def test_B2_real_cotton_leaf_detection(self):
        """Verify real Cotton Bacterial Blight holdout leaf is correctly diagnosed."""
        leaf_path = Path(__file__).resolve().parent / "data" / "holdout_test_images" / "Cotton___Bacterial_blight" / "holdout_17.jpg"
        self.assertTrue(leaf_path.exists(), f"Holdout image missing: {leaf_path}")
        with open(leaf_path, "rb") as f:
            resp = self.client.post("/api/disease/detect", files={"file": ("leaf.jpg", f.read(), "image/jpeg")})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        pred = data["prediction"]
        self.assertEqual(pred["class_name"], "Cotton___Bacterial_blight")
        self.assertEqual(pred["crop"], "Cotton")
        self.assertGreater(pred["confidence_percentage"], 90.0)
        self.assertEqual(pred["status"], "confirmed")
        self.assertIn("ICAR-CICR", data["pathology_and_remedies"]["source_reference"])
        print(f"  [PASS] Cotton Holdout Diagnosis: {pred['class_name']} ({pred['confidence_percentage']}%, Status: {pred['status']})")

    def test_B3_ood_rejection_on_non_plant_noise(self):
        """Verify synthetic non-plant noise is rejected as unsupported_or_unknown."""
        noise_arr = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        img = Image.fromarray(noise_arr)
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        resp = self.client.post("/api/disease/detect", files={"file": ("noise.jpg", buf.read(), "image/jpeg")})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        pred = data["prediction"]
        self.assertEqual(pred["status"], "unsupported_or_unknown")
        self.assertFalse(pred["is_supported_crop"])
        print(f"  [PASS] OOD Rejection: Non-crop noise rejected (Status: {pred['status']}, Entropy: {pred['normalized_entropy']})")

    # ------------------------------------------------------------------------
    # MODULE C: AI FARMING ASSISTANT
    # ------------------------------------------------------------------------
    def test_C1_agri_knowledge_base_present(self):
        """Verify agricultural RAG knowledge base exists and is valid JSON."""
        kb_path = Path(__file__).resolve().parent / "data" / "agri_knowledge_base.json"
        self.assertTrue(kb_path.exists(), "agri_knowledge_base.json missing")
        with open(kb_path, "r", encoding="utf-8") as f:
            kb = json.load(f)
        self.assertIsInstance(kb, list)
        self.assertGreater(len(kb), 10)
        print(f"  [PASS] Agricultural Knowledge Base: {len(kb)} topics verified.")

    def test_C2_chat_missing_key_graceful_handling(self):
        """Verify /api/chat returns structured HTTP 503 instructions when GEMINI_API_KEY is not configured."""
        resp = self.client.post("/api/chat", json={"message": "What is the best fertilizer for wheat?", "history": []})
        self.assertIn(resp.status_code, [200, 503])
        if resp.status_code == 503:
            detail = resp.json()["detail"]
            self.assertIn("GEMINI_API_KEY", detail["error"])
            print("  [PASS] AI Chat: Graceful 503 setup instructions when GEMINI_API_KEY is unset.")
        else:
            print("  [PASS] AI Chat: Live Gemini API responded successfully.")

    # ------------------------------------------------------------------------
    # MODULE D: WEATHER & SMART DASHBOARD BACKEND
    # ------------------------------------------------------------------------
    def test_D1_location_service_mp_districts(self):
        """Verify all 55 MP districts resolve correctly."""
        mp_districts = location_service.get_districts_for_state("Madhya Pradesh")
        self.assertEqual(len(mp_districts), 55)
        res = location_service.resolve_district("Madhya Pradesh", "Bhopal")
        self.assertTrue(res["success"])
        self.assertEqual(res["latitude"], 23.2599)
        self.assertEqual(res["longitude"], 77.4126)
        print(f"  [PASS] Location Service: {len(mp_districts)} MP districts verified, Bhopal coords: ({res['latitude']}, {res['longitude']})")

    def test_D2_open_meteo_weather_and_forecast(self):
        """Verify live weather and 7-day forecast from Open-Meteo."""
        cur = self.client.get("/api/weather/current", params={"state": "Madhya Pradesh", "district": "Bhopal"})
        self.assertEqual(cur.status_code, 200, f"Current weather failed: {cur.text}")
        cur_data = cur.json()
        self.assertIn("temperature_celsius", cur_data)
        self.assertIn("relative_humidity_percent", cur_data)

        fc = self.client.get("/api/weather/forecast", params={"state": "Madhya Pradesh", "district": "Bhopal", "days": 7})
        self.assertEqual(fc.status_code, 200, f"Forecast failed: {fc.text}")
        fc_data = fc.json()
        self.assertEqual(len(fc_data["daily_forecast"]), 7)
        print(f"  [PASS] Weather & Forecast: Bhopal live temp={cur_data['temperature_celsius']}°C, 7-day forecast points={len(fc_data['daily_forecast'])}")

    def test_D3_historical_rainfall_and_crop_suitability(self):
        """Verify historical rainfall archive and crop suitability engine."""
        hist = self.client.get("/api/weather/history", params={"state": "Madhya Pradesh", "district": "Bhopal", "period": "30d"})
        self.assertEqual(hist.status_code, 200, f"Historical rainfall failed: {hist.text}")
        hist_data = hist.json()
        self.assertGreater(hist_data["total_records"], 25)

        suit = self.client.get("/api/dashboard/crop-suitability", params={"state": "Madhya Pradesh", "district": "Bhopal"})
        self.assertEqual(suit.status_code, 200, f"Crop suitability failed: {suit.text}")
        suit_data = suit.json()
        self.assertGreaterEqual(suit_data["crops_assessed_count"], 6)
        print(f"  [PASS] Historical Rainfall & Suitability: 30d records={hist_data['total_records']}, Crops assessed={suit_data['crops_assessed_count']}")

    def test_D4_dashboard_summary_aggregation(self):
        """Verify consolidated dashboard summary endpoint."""
        summ = self.client.get("/api/dashboard/summary", params={"state": "Madhya Pradesh", "district": "Bhopal"})
        self.assertEqual(summ.status_code, 200, f"Dashboard summary failed: {summ.text}")
        summ_data = summ.json()
        self.assertEqual(summ_data["status"], "success")
        self.assertIn("current_weather", summ_data)
        self.assertIn("forecast_7d", summ_data)
        self.assertIn("crop_suitability", summ_data)
        print("  [PASS] Dashboard Summary: Complete aggregated payload verified.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
