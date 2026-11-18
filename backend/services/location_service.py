"""
Location & District Geocoding Service for AgriSmart
Resolves Indian States and Districts to verified geographical coordinates (lat, lon, elevation).
Features:
- Full coverage for all 55 verified districts of Madhya Pradesh and major agricultural districts across India.
- Input normalization (case-insensitivity, whitespace, punctuation).
- Alias handling (e.g. Narmadapuram -> Hoshangabad, East Nimar -> Khandwa).
- Geographical bounds validation for India (8.0-37.0 N, 68.0-97.5 E) and Madhya Pradesh (21.0-26.9 N, 74.0-82.8 E).
- Dynamic Open-Meteo Geocoding fallback with caching for unlisted Indian districts.
- Explicit error handling without silent coordinate corruption or arbitrary default substitution.
"""

import os
import json
import re
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
COORDINATES_FILE = BASE_DIR / "data" / "district_coordinates.json"

class LocationService:
    def __init__(self):
        self.db: Dict[str, Any] = {}
        self.states_db: Dict[str, Dict[str, Any]] = {}
        self.aliases: Dict[str, Dict[str, str]] = {}
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.load_database()

    def load_database(self):
        """Loads the pre-verified offline database."""
        if COORDINATES_FILE.exists():
            try:
                with open(COORDINATES_FILE, "r", encoding="utf-8") as f:
                    self.db = json.load(f)
                    self.states_db = self.db.get("states", {})
                    self.aliases = self.db.get("aliases", {})
            except Exception as e:
                print(f"[ERROR] Failed to load district coordinates: {e}")
                self.states_db = {}
                self.aliases = {}
        else:
            print(f"[WARNING] District coordinates file not found at {COORDINATES_FILE}")

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalizes names by stripping excess spaces, punctuation, and standardizing casing."""
        if not name:
            return ""
        name = re.sub(r"[^\w\s-]", "", name).strip()
        return " ".join(name.split())

    @staticmethod
    def validate_bounds(lat: float, lon: float, state: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validates if coordinates lie strictly within valid geographic bounds.
        India bounds: Lat 8.0 to 37.0 N, Lon 68.0 to 97.5 E.
        Madhya Pradesh bounds: Lat 21.0 to 26.9 N, Lon 74.0 to 82.8 E.
        """
        # Global India bounds check
        if not (8.0 <= lat <= 37.0 and 68.0 <= lon <= 97.5):
            return False, f"Coordinates ({lat}, {lon}) are outside India's geographic bounds."

        # Madhya Pradesh strict sub-bounding box check
        if state and state.lower() == "madhya pradesh":
            if not (21.0 <= lat <= 26.9 and 74.0 <= lon <= 82.8):
                return False, f"Coordinates ({lat}, {lon}) fall outside Madhya Pradesh state borders."

        return True, "Valid"

    def get_supported_states(self) -> List[str]:
        """Returns list of supported states in offline database."""
        return sorted(list(self.states_db.keys()))

    def get_districts_for_state(self, state: str) -> List[str]:
        """Returns sorted list of verified districts for a given state."""
        norm_state = self.find_matching_state(state)
        if norm_state and norm_state in self.states_db:
            return sorted(list(self.states_db[norm_state].keys()))
        return []

    def find_matching_state(self, state_query: str) -> Optional[str]:
        """Fuzzy matches state name accounting for case and minor spacing differences."""
        if not state_query:
            return None
        norm_query = self.normalize_name(state_query).lower()
        for state in self.states_db.keys():
            if state.lower() == norm_query or norm_query in state.lower():
                return state
        return None

    def resolve_district(self, state: str, district: str) -> Dict[str, Any]:
        """
        Resolves state and district to verified latitude, longitude, and elevation.
        Returns a dictionary with status, coordinates, source, and metadata.
        """
        norm_state_input = self.normalize_name(state)
        norm_district_input = self.normalize_name(district)

        if not norm_district_input:
            return {
                "success": False,
                "error": "District name cannot be empty.",
                "state": norm_state_input,
                "district": norm_district_input
            }

        cache_key = f"{norm_state_input.lower()}:{norm_district_input.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 1. Check Aliases (e.g. Narmadapuram -> Hoshangabad, Bangalore -> Bengaluru Urban)
        district_lower = norm_district_input.lower()
        if district_lower in self.aliases:
            alias_entry = self.aliases[district_lower]
            norm_state_input = alias_entry.get("state", norm_state_input)
            norm_district_input = alias_entry.get("district", norm_district_input)

        # 2. Match State
        matched_state = self.find_matching_state(norm_state_input)
        if not matched_state:
            # Fallback: check if the district alone is a known MP district or alias
            for s_name, d_dict in self.states_db.items():
                for d_name in d_dict.keys():
                    if d_name.lower() == district_lower:
                        matched_state = s_name
                        norm_district_input = d_name
                        break
                if matched_state:
                    break

        # 3. Match District within State Offline Database
        if matched_state and matched_state in self.states_db:
            state_districts = self.states_db[matched_state]
            
            # Exact or case-insensitive match
            for d_name, d_info in state_districts.items():
                if d_name.lower() == norm_district_input.lower():
                    is_valid, reason = self.validate_bounds(d_info["lat"], d_info["lon"], matched_state)
                    if is_valid:
                        res = {
                            "success": True,
                            "state": matched_state,
                            "district": d_name,
                            "latitude": d_info["lat"],
                            "longitude": d_info["lon"],
                            "elevation_m": d_info.get("elevation_m", 0),
                            "headquarters": d_info.get("hq", d_name),
                            "source": d_info.get("source", "Verified District Coordinates Database"),
                            "is_fallback": False
                        }
                        self.cache[cache_key] = res
                        return res

        # 4. Fallback: Dynamic Geocoding via Open-Meteo Geocoding API
        # Only triggered if not found in pre-verified database
        dynamic_res = self._fetch_open_meteo_geocoding(norm_district_input, matched_state or norm_state_input)
        if dynamic_res.get("success"):
            self.cache[cache_key] = dynamic_res
            return dynamic_res

        # 5. Resolution Failed
        available_districts = self.get_districts_for_state(matched_state) if matched_state else []
        return {
            "success": False,
            "error": f"Could not resolve coordinates for district '{district}' in state '{state}'.",
            "state": state,
            "district": district,
            "suggested_districts": available_districts[:10] if available_districts else []
        }

    def _fetch_open_meteo_geocoding(self, district: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Dynamically resolves coordinates via Open-Meteo Geocoding API for uncataloged districts.
        Strictly verifies that returned coordinates lie within Indian borders.
        """
        try:
            query = f"{district}, {state}, India" if state else f"{district}, India"
            encoded_query = urllib.parse.quote(query)
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_query}&count=3&language=en&format=json"

            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AgriSmart/1.0 (Agriculture Decision Support System)"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))

            results = data.get("results", [])
            for item in results:
                country = item.get("country", "")
                if country.lower() == "india":
                    lat = float(item["latitude"])
                    lon = float(item["longitude"])
                    is_valid, _ = self.validate_bounds(lat, lon, state)
                    if is_valid:
                        return {
                            "success": True,
                            "state": item.get("admin1", state or "India"),
                            "district": item.get("name", district),
                            "latitude": round(lat, 4),
                            "longitude": round(lon, 4),
                            "elevation_m": round(float(item.get("elevation", 0)), 1),
                            "headquarters": item.get("name", district),
                            "source": "Open-Meteo Geocoding API (Validated Indian Coordinate)",
                            "is_fallback": True
                        }

            return {"success": False, "error": "Geocoding returned no valid Indian coordinates."}

        except Exception as e:
            return {"success": False, "error": f"Open-Meteo Geocoding failed: {str(e)}"}

# Global singleton instance
location_service = LocationService()
