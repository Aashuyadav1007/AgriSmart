"""
Open-Meteo Weather Service for AgriMind AI
Handles:
- District-based current weather observations
- 7-day weather forecasts
- Historical rainfall analysis (30 days, 90 days, 12 months)
- In-memory TTL caching
- WMO weather code translations
- Comprehensive error handling and Open-Meteo attribution
"""

import time
import urllib.request
import urllib.parse
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from services.location_service import location_service

# Weather code descriptions according to WMO
WMO_CODE_MAP = {
    0: {"condition": "Clear sky", "icon": "clear"},
    1: {"condition": "Mainly clear", "icon": "mostly_clear"},
    2: {"condition": "Partly cloudy", "icon": "partly_cloudy"},
    3: {"condition": "Overcast", "icon": "overcast"},
    45: {"condition": "Fog", "icon": "fog"},
    48: {"condition": "Depositing rime fog", "icon": "fog"},
    51: {"condition": "Light drizzle", "icon": "drizzle"},
    53: {"condition": "Moderate drizzle", "icon": "drizzle"},
    55: {"condition": "Dense drizzle", "icon": "drizzle"},
    61: {"condition": "Slight rain", "icon": "rain"},
    63: {"condition": "Moderate rain", "icon": "rain"},
    65: {"condition": "Heavy rain", "icon": "rain"},
    66: {"condition": "Light freezing rain", "icon": "freezing_rain"},
    67: {"condition": "Heavy freezing rain", "icon": "freezing_rain"},
    71: {"condition": "Slight snow fall", "icon": "snow"},
    73: {"condition": "Moderate snow fall", "icon": "snow"},
    75: {"condition": "Heavy snow fall", "icon": "snow"},
    77: {"condition": "Snow grains", "icon": "snow"},
    80: {"condition": "Slight rain showers", "icon": "showers"},
    81: {"condition": "Moderate rain showers", "icon": "showers"},
    82: {"condition": "Violent rain showers", "icon": "showers"},
    85: {"condition": "Slight snow showers", "icon": "snow"},
    86: {"condition": "Heavy snow showers", "icon": "snow"},
    95: {"condition": "Thunderstorm", "icon": "thunderstorm"},
    96: {"condition": "Thunderstorm with slight hail", "icon": "hail"},
    99: {"condition": "Thunderstorm with heavy hail", "icon": "hail"}
}

def decode_wmo_code(code: Optional[int]) -> Dict[str, str]:
    if code is None:
        return {"condition": "Unknown", "icon": "unknown"}
    return WMO_CODE_MAP.get(code, {"condition": f"Weather code {code}", "icon": "cloud"})

class WeatherService:
    def __init__(self):
        # Cache dictionaries: key -> (timestamp, data)
        self._current_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
        self._forecast_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
        self._history_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
        
        # TTLs in seconds
        self.CURRENT_TTL = 900       # 15 minutes
        self.FORECAST_TTL = 1800     # 30 minutes
        self.HISTORY_TTL = 21600     # 6 hours

    def _get_coordinates(self, state: str, district: str) -> Dict[str, Any]:
        """Resolves district to coordinates using LocationService."""
        loc = location_service.resolve_district(state, district)
        if not loc.get("success"):
            raise ValueError(loc.get("error", f"Could not resolve location for '{district}', '{state}'."))
        return loc

    def get_current_weather(self, state: str, district: str) -> Dict[str, Any]:
        """Fetches live current weather observations for a district."""
        loc = self._get_coordinates(state, district)
        cache_key = f"{loc['state']}:{loc['district']}".lower()

        now = time.time()
        if cache_key in self._current_cache:
            ts, cached_data = self._current_cache[cache_key]
            if now - ts < self.CURRENT_TTL:
                return cached_data

        lat = loc["latitude"]
        lon = loc["longitude"]

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure&"
            f"daily=temperature_2m_max,temperature_2m_min,precipitation_sum&"
            f"timezone=auto"
        )

        req = urllib.request.Request(url, headers={"User-Agent": "AgriMind-AI/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        current = data.get("current", {})
        daily = data.get("daily", {})

        wmo = decode_wmo_code(current.get("weather_code"))

        result = {
            "location": {
                "state": loc["state"],
                "district": loc["district"],
                "latitude": lat,
                "longitude": lon,
                "elevation_m": loc.get("elevation_m", 0),
                "headquarters": loc.get("headquarters", loc["district"])
            },
            "observation_time": current.get("time"),
            "data_category": "current_observation",
            "temperature_celsius": current.get("temperature_2m"),
            "apparent_temperature_celsius": current.get("apparent_temperature"),
            "relative_humidity_percent": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation", 0.0),
            "rain_mm": current.get("rain", 0.0),
            "wind_speed_kmh": current.get("wind_speed_10m"),
            "wind_direction_degrees": current.get("wind_direction_10m"),
            "surface_pressure_hpa": current.get("surface_pressure"),
            "weather_condition": wmo["condition"],
            "weather_icon": wmo["icon"],
            "weather_code": current.get("weather_code"),
            "today_forecast": {
                "temp_max_celsius": daily.get("temperature_2m_max", [None])[0],
                "temp_min_celsius": daily.get("temperature_2m_min", [None])[0],
                "expected_precipitation_mm": daily.get("precipitation_sum", [0.0])[0]
            },
            "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)"
        }

        self._current_cache[cache_key] = (now, result)
        return result

    def get_forecast(self, state: str, district: str, days: int = 7) -> Dict[str, Any]:
        """Fetches upcoming weather forecast (up to 7-14 days)."""
        loc = self._get_coordinates(state, district)
        days = min(max(days, 1), 14)
        cache_key = f"{loc['state']}:{loc['district']}:{days}".lower()

        now = time.time()
        if cache_key in self._forecast_cache:
            ts, cached_data = self._forecast_cache[cache_key]
            if now - ts < self.FORECAST_TTL:
                return cached_data

        lat = loc["latitude"]
        lon = loc["longitude"]

        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&forecast_days={days}&"
            f"daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max&"
            f"timezone=auto"
        )

        req = urllib.request.Request(url, headers={"User-Agent": "AgriMind-AI/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        daily = data.get("daily", {})
        times = daily.get("time", [])
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        precip_prob = daily.get("precipitation_probability_max", [])
        wind_max = daily.get("wind_speed_10m_max", [])
        codes = daily.get("weather_code", [])

        forecast_list = []
        for i in range(len(times)):
            code = codes[i] if i < len(codes) else None
            wmo = decode_wmo_code(code)
            forecast_list.append({
                "date": times[i],
                "temp_max_celsius": temp_max[i] if i < len(temp_max) else None,
                "temp_min_celsius": temp_min[i] if i < len(temp_min) else None,
                "precipitation_mm": precip[i] if i < len(precip) else 0.0,
                "precipitation_probability_percent": precip_prob[i] if i < len(precip_prob) else None,
                "wind_speed_max_kmh": wind_max[i] if i < len(wind_max) else None,
                "weather_condition": wmo["condition"],
                "weather_icon": wmo["icon"],
                "weather_code": code
            })

        result = {
            "location": {
                "state": loc["state"],
                "district": loc["district"],
                "latitude": lat,
                "longitude": lon,
                "headquarters": loc.get("headquarters", loc["district"])
            },
            "data_category": "numerical_weather_prediction_forecast",
            "forecast_days": len(forecast_list),
            "daily_forecast": forecast_list,
            "attribution": "Weather data by Open-Meteo.com (CC BY 4.0)"
        }

        self._forecast_cache[cache_key] = (now, result)
        return result

    def get_historical_rainfall(self, state: str, district: str, period: str = "30d") -> Dict[str, Any]:
        """
        Fetches historical rainfall data for selectable periods: '30d', '90d', '12m'.
        Uses Forecast API past_days for 30d/90d, and Archive API for 12m.
        """
        loc = self._get_coordinates(state, district)
        period = period.lower().strip()
        if period not in ["30d", "90d", "12m"]:
            period = "30d"

        cache_key = f"{loc['state']}:{loc['district']}:{period}".lower()

        now = time.time()
        if cache_key in self._history_cache:
            ts, cached_data = self._history_cache[cache_key]
            if now - ts < self.HISTORY_TTL:
                return cached_data

        lat = loc["latitude"]
        lon = loc["longitude"]

        if period in ["30d", "90d"]:
            days_count = 30 if period == "30d" else 90
            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}&past_days={days_count}&forecast_days=0&"
                f"daily=precipitation_sum,temperature_2m_mean&timezone=auto"
            )
        else: # 12m (365 days from Archive API)
            today = datetime.now()
            end_date = (today - timedelta(days=5)).strftime("%Y-%m-%d")
            start_date = (today - timedelta(days=370)).strftime("%Y-%m-%d")
            url = (
                f"https://archive-api.open-meteo.com/v1/archive?"
                f"latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&"
                f"daily=precipitation_sum,temperature_2m_mean&timezone=auto"
            )

        req = urllib.request.Request(url, headers={"User-Agent": "AgriMind-AI/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        precip = daily.get("precipitation_sum", [])
        temp_mean = daily.get("temperature_2m_mean", [])

        # Process statistics
        daily_records = []
        valid_precip = []
        monthly_aggregation = {}

        for i in range(len(dates)):
            p_val = precip[i] if (i < len(precip) and precip[i] is not None) else 0.0
            t_val = temp_mean[i] if (i < len(temp_mean) and temp_mean[i] is not None) else None
            d_str = dates[i]
            
            daily_records.append({
                "date": d_str,
                "precipitation_mm": round(p_val, 2),
                "temperature_mean_celsius": round(t_val, 1) if t_val is not None else None
            })
            valid_precip.append(p_val)

            # Monthly bucket for aggregated visualization
            month_key = d_str[:7] # YYYY-MM
            if month_key not in monthly_aggregation:
                monthly_aggregation[month_key] = {"month": month_key, "total_rainfall_mm": 0.0, "rainy_days": 0}
            monthly_aggregation[month_key]["total_rainfall_mm"] += p_val
            if p_val >= 2.5: # IMD definition of a rainy day
                monthly_aggregation[month_key]["rainy_days"] += 1

        for m in monthly_aggregation.values():
            m["total_rainfall_mm"] = round(m["total_rainfall_mm"], 1)

        total_rainfall = round(sum(valid_precip), 2)
        avg_daily = round(total_rainfall / max(len(valid_precip), 1), 2)
        max_daily = round(max(valid_precip) if valid_precip else 0.0, 2)
        rainy_days_count = sum(1 for p in valid_precip if p >= 2.5)

        result = {
            "location": {
                "state": loc["state"],
                "district": loc["district"],
                "latitude": lat,
                "longitude": lon,
                "headquarters": loc.get("headquarters", loc["district"])
            },
            "period": period,
            "data_category": "historical_reanalysis_observation",
            "start_date": dates[0] if dates else None,
            "end_date": dates[-1] if dates else None,
            "total_records": len(daily_records),
            "summary_statistics": {
                "cumulative_rainfall_mm": total_rainfall,
                "average_daily_rainfall_mm": avg_daily,
                "maximum_single_day_rainfall_mm": max_daily,
                "rainy_days_count": rainy_days_count,
                "dry_days_count": len(valid_precip) - rainy_days_count
            },
            "monthly_breakdown": list(monthly_aggregation.values()),
            "daily_records": daily_records,
            "attribution": "Historical Weather Archive by Open-Meteo.com (CC BY 4.0)"
        }

        self._history_cache[cache_key] = (now, result)
        return result

# Global singleton
weather_service = WeatherService()
