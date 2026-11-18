"""
Automated Test Suite for Indian District Coordinates & Location Service
AgriSmart - Stage 5 Step 5 Verification
"""

import sys
import unittest
from pathlib import Path

# Add backend to Python path
sys.path.append(str(Path(__file__).resolve().parent))

from services.location_service import location_service

class TestDistrictCoordinates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.service = location_service
        cls.mp_districts = cls.service.get_districts_for_state("Madhya Pradesh")
        print("\n" + "="*70)
        print("RUNNING STEP 5 DISTRICT COORDINATES & LOCATION SERVICE TEST SUITE")
        print(f"Total MP Districts in DB: {len(cls.mp_districts)}")
        print(f"Total States in DB: {len(cls.service.get_supported_states())}")
        print("="*70)

    def test_01_all_55_mp_districts_resolve(self):
        """Verify that every single verified district in Madhya Pradesh resolves successfully."""
        self.assertGreaterEqual(len(self.mp_districts), 55, "Madhya Pradesh should have at least 55 official districts cataloged.")
        
        failed_districts = []
        for dist in self.mp_districts:
            res = self.service.resolve_district("Madhya Pradesh", dist)
            if not res.get("success"):
                failed_districts.append((dist, res.get("error")))
            else:
                lat = res["latitude"]
                lon = res["longitude"]
                # Strict MP bounds check: Lat 21.0 - 26.9, Lon 74.0 - 82.8
                in_bounds = (21.0 <= lat <= 26.9) and (74.0 <= lon <= 82.8)
                if not in_bounds:
                    failed_districts.append((dist, f"Out of MP bounds: ({lat}, {lon})"))

        self.assertEqual(len(failed_districts), 0, f"Some MP districts failed resolution or bounds check: {failed_districts}")
        print(f"[PASS] All {len(self.mp_districts)} Madhya Pradesh districts resolved within strict geographical borders.")

    def test_02_newly_formed_mp_districts_present(self):
        """Verify that newly formed districts (Niwari 2018, Mauganj 2023, Maihar 2023, Pandhurna 2023) are present."""
        new_districts = ["Niwari", "Mauganj", "Maihar", "Pandhurna", "Agar Malwa"]
        for dist in new_districts:
            res = self.service.resolve_district("Madhya Pradesh", dist)
            self.assertTrue(res.get("success"), f"New district '{dist}' failed to resolve.")
            self.assertIn("lat", str(res))
            self.assertIn("source", res)
            print(f"  [OK] Verified New MP District: {dist} -> Lat: {res['latitude']}, Lon: {res['longitude']} ({res['source']})")
        print("[PASS] Verified all recently created Madhya Pradesh administrative districts.")

    def test_03_major_agricultural_districts_across_india(self):
        """Verify key agricultural districts across Maharashtra, Punjab, Haryana, UP, Gujarat."""
        sample_queries = [
            ("Maharashtra", "Nagpur"),
            ("Maharashtra", "Yavatmal"),
            ("Punjab", "Ludhiana"),
            ("Punjab", "Bathinda"),
            ("Haryana", "Karnal"),
            ("Uttar Pradesh", "Varanasi"),
            ("Uttar Pradesh", "Agra"),
            ("Gujarat", "Rajkot"),
            ("Rajasthan", "Kota"),
            ("Karnataka", "Dharwad"),
            ("Tamil Nadu", "Coimbatore"),
            ("Andhra Pradesh", "Guntur")
        ]
        for state, dist in sample_queries:
            res = self.service.resolve_district(state, dist)
            self.assertTrue(res.get("success"), f"Failed to resolve {dist}, {state}")
            self.assertTrue(8.0 <= res["latitude"] <= 37.0, f"Lat out of India bounds: {res['latitude']}")
            self.assertTrue(68.0 <= res["longitude"] <= 97.5, f"Lon out of India bounds: {res['longitude']}")

        print(f"[PASS] Verified {len(sample_queries)} major agricultural districts across India.")

    def test_04_input_normalization_and_casing(self):
        """Verify case-insensitivity, whitespace trimming, and punctuation normalization."""
        variations = [
            ("  madhya pradesh  ", "  bhopal  "),
            ("MADHYA PRADESH", "INDORE"),
            ("madhya pradesh", "jabalpur"),
            ("Uttar Pradesh", "kanpur nagar"),
        ]
        for state, dist in variations:
            res = self.service.resolve_district(state, dist)
            self.assertTrue(res.get("success"), f"Failed for variation: state='{state}', dist='{dist}'")
            self.assertIn("latitude", res)
        print("[PASS] Input normalization and case-insensitivity test passed.")

    def test_05_alias_resolution(self):
        """Verify common district aliases resolve to their canonical entities."""
        aliases_to_test = [
            ("Madhya Pradesh", "Narmadapuram", "Hoshangabad"),
            ("Madhya Pradesh", "East Nimar", "Khandwa"),
            ("Madhya Pradesh", "West Nimar", "Khargone"),
            ("Karnataka", "Bangalore", "Bengaluru Urban"),
            ("Maharashtra", "Aurangabad", "Chhatrapati Sambhajinagar"),
            ("Uttar Pradesh", "Allahabad", "Prayagraj")
        ]
        for state, query, expected_canonical in aliases_to_test:
            res = self.service.resolve_district(state, query)
            self.assertTrue(res.get("success"), f"Alias '{query}' failed to resolve.")
            self.assertEqual(res["district"], expected_canonical, f"Expected canonical '{expected_canonical}' but got '{res['district']}'")
            print(f"  [OK] Alias '{query}' correctly resolved to '{res['district']}' ({res['state']})")
        print("[PASS] District alias resolution test passed.")

    def test_06_unknown_district_graceful_handling(self):
        """Verify that non-existent/bogus districts return a clean failure without silent falsification."""
        res = self.service.resolve_district("Madhya Pradesh", "NonExistentFictionalDistrictXYZ123")
        self.assertFalse(res.get("success"), "Non-existent district should fail resolution.")
        self.assertIn("error", res)
        self.assertNotIn("latitude", res, "Should not return arbitrary coordinates for fake district.")
        self.assertIn("suggested_districts", res)
        print("[PASS] Non-existent district rejected safely with helpful error suggestion.")

    def test_07_bounds_validator(self):
        """Verify geographical bounds validator rejects coordinates outside India or MP."""
        # Outside India (London coords)
        valid, msg = self.service.validate_bounds(51.5074, -0.1278)
        self.assertFalse(valid)
        self.assertIn("outside India", msg)

        # Inside India but outside MP (Delhi coords checking under MP)
        valid_mp, msg_mp = self.service.validate_bounds(28.6139, 77.2090, state="Madhya Pradesh")
        self.assertFalse(valid_mp)
        self.assertIn("outside Madhya Pradesh", msg_mp)

        # Valid Bhopal coords under MP
        valid_bhopal, _ = self.service.validate_bounds(23.2599, 77.4126, state="Madhya Pradesh")
        self.assertTrue(valid_bhopal)
        print("[PASS] Geographic bounds checking verified.")

    def test_08_caching_behavior(self):
        """Verify caching works and returns identical result instantly."""
        # First call
        res1 = self.service.resolve_district("Madhya Pradesh", "Ujjain")
        # Second call
        res2 = self.service.resolve_district("Madhya Pradesh", "Ujjain")
        self.assertEqual(res1, res2)
        cache_key = "madhya pradesh:ujjain"
        self.assertIn(cache_key, self.service.cache)
        print("[PASS] In-memory coordinate cache verified.")

if __name__ == "__main__":
    unittest.main(verbosity=2)
