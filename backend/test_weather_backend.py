"""
Automated Integration & Unit Test Suite for Step 6:
Open-Meteo Weather APIs, Historical Rainfall & Crop Suitability Backend
"""

import sys
import unittest
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestWeatherAndAgricultureBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n" + "="*70)
        print("RUNNING STEP 6 WEATHER, RAINFALL & CROP SUITABILITY TEST SUITE")
        print("="*70)

    def test_01_current_weather_bhopal_and_districts(self):
        """Test current weather endpoint on at least three districts including Bhopal."""
        districts_to_test = [
            ("Madhya Pradesh", "Bhopal"),
            ("Madhya Pradesh", "Indore"),
            ("Maharashtra", "Nagpur")
        ]
        for state, dist in districts_to_test:
            resp = client.get(f"/api/weather/current?state={state}&district={dist}")
            self.assertEqual(resp.status_code, 200, f"Current weather failed for {dist}, {state}: {resp.text}")
            data = resp.json()
            
            # Assert schema & fields
            self.assertEqual(data["location"]["district"], dist)
            self.assertIn("temperature_celsius", data)
            self.assertIn("relative_humidity_percent", data)
            self.assertIn("precipitation_mm", data)
            self.assertIn("wind_speed_kmh", data)
            self.assertIn("weather_condition", data)
            self.assertIn("Open-Meteo", data["attribution"])
            print(f"  [OK] Current Weather: {dist} ({state}) -> {data['temperature_celsius']}°C, {data['relative_humidity_percent']}% RH, {data['weather_condition']}")

        print("[PASS] Current weather endpoint verified across multiple districts.")

    def test_02_weather_forecast_endpoint(self):
        """Test 7-day weather forecast endpoint."""
        resp = client.get("/api/weather/forecast?state=Madhya Pradesh&district=Bhopal&days=7")
        self.assertEqual(resp.status_code, 200, f"Forecast failed: {resp.text}")
        data = resp.json()

        self.assertEqual(data["forecast_days"], 7)
        self.assertEqual(len(data["daily_forecast"]), 7)
        first_day = data["daily_forecast"][0]
        self.assertIn("date", first_day)
        self.assertIn("temp_max_celsius", first_day)
        self.assertIn("temp_min_celsius", first_day)
        self.assertIn("precipitation_mm", first_day)
        self.assertIn("weather_condition", first_day)
        print(f"  [OK] Forecast for Bhopal 7 days: Day 1 ({first_day['date']}) -> Max: {first_day['temp_max_celsius']}°C, Min: {first_day['temp_min_celsius']}°C, Precip: {first_day['precipitation_mm']} mm")
        print("[PASS] Weather forecast endpoint verified.")

    def test_03_historical_rainfall_periods(self):
        """Test historical rainfall archive for selectable periods: 30d, 90d, 12m."""
        for period in ["30d", "90d", "12m"]:
            resp = client.get(f"/api/weather/history?state=Madhya Pradesh&district=Bhopal&period={period}")
            self.assertEqual(resp.status_code, 200, f"Historical rainfall failed for {period}: {resp.text}")
            data = resp.json()
            
            stats = data["summary_statistics"]
            self.assertIn("cumulative_rainfall_mm", stats)
            self.assertIn("rainy_days_count", stats)
            self.assertGreater(data["total_records"], 25)
            self.assertIn("Open-Meteo", data["attribution"])
            print(f"  [OK] Period '{period}': {data['total_records']} daily records, Cumulative: {stats['cumulative_rainfall_mm']} mm, Rainy Days: {stats['rainy_days_count']}")

        print("[PASS] Historical rainfall endpoint verified across 30d, 90d, and 12m.")

    def test_04_crop_suitability_endpoint(self):
        """Test crop suitability assessment engine and transparent disclaimer."""
        resp = client.get("/api/dashboard/crop-suitability?state=Madhya Pradesh&district=Bhopal")
        self.assertEqual(resp.status_code, 200, f"Crop suitability failed: {resp.text}")
        data = resp.json()

        self.assertGreaterEqual(data["crops_assessed_count"], 6)
        rankings = data["suitability_rankings"]
        for r in rankings:
            self.assertIn("crop_name", r)
            self.assertTrue(0 <= r["suitability_score"] <= 100)
            self.assertIn(r["suitability_level"], ["Highly Suitable", "Moderately Suitable", "Marginal", "Unsuitable"])
            self.assertIsInstance(r["limiting_factors"], list)
            self.assertIsInstance(r["favorable_factors"], list)

        # Verify transparent disclaimer
        self.assertIn("disclaimer_and_limitations", data)
        self.assertIn("soil pH", data["disclaimer_and_limitations"])
        top_crop = rankings[0]
        print(f"  [OK] Top Suitable Crop in Bhopal: {top_crop['crop_name']} ({top_crop['suitability_score']}/100, {top_crop['suitability_level']})")
        print("[PASS] Crop suitability engine verified with documented agronomic thresholds and disclosures.")

    def test_05_dashboard_summary_endpoint(self):
        """Test aggregated dashboard summary endpoint."""
        resp = client.get("/api/dashboard/summary?state=Madhya Pradesh&district=Bhopal")
        self.assertEqual(resp.status_code, 200, f"Dashboard summary failed: {resp.text}")
        data = resp.json()

        self.assertEqual(data["status"], "success")
        self.assertIn("current_weather", data)
        self.assertIn("forecast_7d", data)
        self.assertIn("historical_rainfall_30d", data)
        self.assertIn("crop_suitability", data)
        self.assertIn("system_status", data)
        print("[PASS] Aggregated dashboard summary endpoint verified.")

    def test_06_invalid_district_rejection(self):
        """Test that non-existent district returns clean HTTP 400 without crashing."""
        resp = client.get("/api/weather/current?state=Madhya Pradesh&district=InvalidFakeDistrict999")
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn("detail", data)
        print(f"  [OK] Invalid district safely rejected: {data['detail'][:60]}...")
        print("[PASS] Invalid location handling verified.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
