"""
Crop Suitability Assessment Engine for AgriMind AI
Evaluates agro-meteorological suitability for major Indian crops based on:
- Live temperature & humidity
- Recent cumulative rainfall
- Seasonality (Kharif, Rabi, Zaid)
- Documented agronomic thresholds (ICAR, TNAU, MP Krishi)

Includes transparent limitations disclosure regarding un-modeled soil parameters.
"""

from datetime import datetime
from typing import Dict, Any, List
from services.weather_service import weather_service

# Documented Agronomic Thresholds
CROP_AGRONOMIC_PROFILES = {
    "Wheat": {
        "season": "Rabi (Winter)",
        "active_months": [10, 11, 12, 1, 2, 3, 4], # Oct to April
        "optimal_temp_c": (15.0, 25.0),
        "tolerable_temp_c": (10.0, 32.0),
        "ideal_water_mm": (400, 650),
        "humidity_optimum": (40, 70),
        "soil_type_ideal": "Well-drained clay-loam to loam",
        "description": "Primary winter staple. Sensitive to terminal heat stress above 32°C during grain filling."
    },
    "Soybean": {
        "season": "Kharif (Monsoon)",
        "active_months": [6, 7, 8, 9, 10], # June to Oct
        "optimal_temp_c": (22.0, 32.0),
        "tolerable_temp_c": (16.0, 38.0),
        "ideal_water_mm": (600, 1000),
        "humidity_optimum": (60, 85),
        "soil_type_ideal": "Deep black soils (Vertisols) with good drainage",
        "description": "Dominant oilseed crop of Madhya Pradesh (the 'Soya State'). Highly vulnerable to prolonged dry spells during flowering."
    },
    "Cotton": {
        "season": "Kharif (Monsoon/Post-Monsoon)",
        "active_months": [5, 6, 7, 8, 9, 10, 11], # May to Nov
        "optimal_temp_c": (21.0, 35.0),
        "tolerable_temp_c": (18.0, 40.0),
        "ideal_water_mm": (500, 850),
        "humidity_optimum": (50, 75),
        "soil_type_ideal": "Deep black cotton soils (Vertisols)",
        "description": "Major commercial cash crop. Needs bright warm days; excessive rain during boll bursting causes fiber staining and shedding."
    },
    "Gram (Chickpea)": {
        "season": "Rabi (Winter)",
        "active_months": [10, 11, 12, 1, 2, 3], # Oct to March
        "optimal_temp_c": (18.0, 26.0),
        "tolerable_temp_c": (12.0, 30.0),
        "ideal_water_mm": (350, 500),
        "humidity_optimum": (35, 65),
        "soil_type_ideal": "Loamy to sandy loam soils",
        "description": "Leading pulse crop in Madhya Pradesh. Requires cool and dry weather; high humidity promotes Ascochyta blight and wilt."
    },
    "Maize (Corn)": {
        "season": "Kharif / Rabi",
        "active_months": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], # Year-round capable
        "optimal_temp_c": (21.0, 30.0),
        "tolerable_temp_c": (15.0, 36.0),
        "ideal_water_mm": (500, 750),
        "humidity_optimum": (50, 80),
        "soil_type_ideal": "Well-drained fertile loams",
        "description": "Versatile cereal crop. Intolerant to waterlogging, particularly in early vegetative stage."
    },
    "Rice (Paddy)": {
        "season": "Kharif (Monsoon)",
        "active_months": [6, 7, 8, 9, 10, 11], # June to Nov
        "optimal_temp_c": (22.0, 34.0),
        "tolerable_temp_c": (18.0, 38.0),
        "ideal_water_mm": (1000, 1600),
        "humidity_optimum": (70, 90),
        "soil_type_ideal": "Heavy clayey soils with high water retention",
        "description": "Staple food crop with intense water requirements. Unsuitable in low-rainfall districts without assured canal/tubewell irrigation."
    },
    "Potato": {
        "season": "Rabi (Winter)",
        "active_months": [10, 11, 12, 1, 2], # Oct to Feb
        "optimal_temp_c": (16.0, 22.0),
        "tolerable_temp_c": (10.0, 28.0),
        "ideal_water_mm": (350, 500),
        "humidity_optimum": (55, 80),
        "soil_type_ideal": "Loose, friable sandy loam rich in organic matter",
        "description": "High-value tuber. High temperatures above 28°C stop tuber formation, while excessive wetness triggers Late Blight."
    },
    "Tomato": {
        "season": "Rabi / Autumn / Spring",
        "active_months": [9, 10, 11, 12, 1, 2, 3, 4], # Sept to April
        "optimal_temp_c": (20.0, 28.0),
        "tolerable_temp_c": (12.0, 34.0),
        "ideal_water_mm": (400, 600),
        "humidity_optimum": (50, 75),
        "soil_type_ideal": "Well-drained sandy loam with pH 6.0-7.0",
        "description": "Sensitive to frost and heavy waterlogging. High nighttime temperature (>25°C) leads to severe blossom drop."
    }
}

class CropSuitabilityService:
    def __init__(self):
        pass

    def evaluate_suitability(self, state: str, district: str) -> Dict[str, Any]:
        """
        Evaluates crop suitability for a selected district based on:
        - Current weather observations
        - 30-day cumulative rainfall
        - Current calendar month / agricultural season
        """
        # 1. Fetch current weather and 30-day rainfall history
        current_wx = weather_service.get_current_weather(state, district)
        history_30d = weather_service.get_historical_rainfall(state, district, period="30d")

        temp = current_wx.get("temperature_celsius")
        humidity = current_wx.get("relative_humidity_percent")
        rainfall_30d = history_30d.get("summary_statistics", {}).get("cumulative_rainfall_mm", 0.0)

        current_month = datetime.now().month

        results = []
        for crop_name, profile in CROP_AGRONOMIC_PROFILES.items():
            score = 100
            limiting_factors = []
            favorable_factors = []

            # A. Seasonality Check
            if current_month in profile["active_months"]:
                favorable_factors.append(f"In-season for {profile['season']}")
            else:
                score -= 30
                limiting_factors.append(f"Off-season: Typically cultivated during {profile['season']}")

            # B. Temperature Scoring
            opt_min, opt_max = profile["optimal_temp_c"]
            tol_min, tol_max = profile["tolerable_temp_c"]

            if temp is not None:
                if opt_min <= temp <= opt_max:
                    favorable_factors.append(f"Current temperature ({temp}°C) is within optimal range ({opt_min}–{opt_max}°C)")
                elif tol_min <= temp < opt_min:
                    penalty = int((opt_min - temp) * 5)
                    score -= min(penalty, 25)
                    limiting_factors.append(f"Sub-optimal coolness: {temp}°C (optimal is {opt_min}–{opt_max}°C)")
                elif opt_max < temp <= tol_max:
                    penalty = int((temp - opt_max) * 5)
                    score -= min(penalty, 25)
                    limiting_factors.append(f"Thermal elevation: {temp}°C exceeds optimal ceiling ({opt_max}°C)")
                else:
                    score -= 40
                    limiting_factors.append(f"Severe temperature stress: {temp}°C is outside tolerable bounds ({tol_min}–{tol_max}°C)")

            # C. Humidity Scoring
            h_min, h_max = profile["humidity_optimum"]
            if humidity is not None:
                if h_min <= humidity <= h_max:
                    favorable_factors.append(f"Humidity ({humidity}%) is well-balanced")
                elif humidity > h_max + 15:
                    score -= 15
                    limiting_factors.append(f"High relative humidity ({humidity}%) increases fungal foliar risk")
                elif humidity < h_min - 15:
                    score -= 10
                    limiting_factors.append(f"Low relative humidity ({humidity}%) accelerates soil moisture depletion")

            # D. Rainfall Context (30-day antecedent moisture)
            ideal_min, ideal_max = profile["ideal_water_mm"]
            # Estimate roughly required monthly water fraction (total / 4 months)
            expected_monthly_water = ideal_min / 4.0
            if rainfall_30d < (expected_monthly_water * 0.3):
                limiting_factors.append(f"Recent rainfall ({rainfall_30d} mm in 30d) is low; supplemental irrigation required")
                # Do not overly penalize irrigated Rabi crops (Wheat/Gram) for dry winter weather
                if "Rabi" in profile["season"]:
                    score -= 5
                else:
                    score -= 20
            elif rainfall_30d > (expected_monthly_water * 2.5):
                limiting_factors.append(f"Recent heavy precipitation ({rainfall_30d} mm in 30d) poses waterlogging risk")
                score -= 15

            # Clamp score 0 to 100
            score = max(0, min(100, score))

            # Categorize
            if score >= 80:
                level = "Highly Suitable"
                badge_color = "emerald"
            elif score >= 60:
                level = "Moderately Suitable"
                badge_color = "amber"
            elif score >= 40:
                level = "Marginal"
                badge_color = "orange"
            else:
                level = "Unsuitable"
                badge_color = "rose"

            results.append({
                "crop_name": crop_name,
                "season": profile["season"],
                "suitability_score": score,
                "suitability_level": level,
                "badge_color": badge_color,
                "limiting_factors": limiting_factors,
                "favorable_factors": favorable_factors,
                "agronomic_recommendation": (
                    f"Recommended for cultivation with standard management."
                    if score >= 75 else
                    f"Feasible if limiting factors ({'; '.join(limiting_factors[:2])}) are managed via irrigation or soil amendments."
                    if score >= 50 else
                    f"Not recommended under current conditions without specialized protective farming."
                )
            })

        # Sort by suitability score descending
        results.sort(key=lambda x: x["suitability_score"], reverse=True)

        return {
            "location": current_wx["location"],
            "assessment_time": current_wx["observation_time"],
            "ambient_conditions": {
                "temperature_celsius": temp,
                "humidity_percent": humidity,
                "recent_30d_rainfall_mm": rainfall_30d
            },
            "crops_assessed_count": len(results),
            "suitability_rankings": results,
            "disclaimer_and_limitations": (
                "Agronomic Disclaimer: This assessment calculates agro-meteorological suitability using live temperature, "
                "humidity, and recent 30-day precipitation. Un-modeled physical parameters—including micro-level soil pH, "
                "texture, soil organic carbon (SOC), drainage class, and specific farm irrigation infrastructure—are critical "
                "for final planting decisions. Always corroborate with a local Krishi Vigyan Kendra (KVK) or soil testing laboratory."
            ),
            "attribution": "Weather inputs by Open-Meteo.com (CC BY 4.0)"
        }

crop_suitability_service = CropSuitabilityService()
