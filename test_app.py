"""
test_app.py
Automated test suite for Raasta — Hyderabad's Smart Civic Problem Solver.
Tests all requirements:
1. Rule-based classification for English & Roman Urdu
2. Severity calculation & explainability
3. Duplicate detection
4. Database persistence & timeline updates
5. Flask HTTP endpoints & Admin session security
"""

import unittest
import json
import os
import sys

# Ensure project directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rule_engine import classify_complaint, estimate_severity, check_for_duplicates, analyze_complaint
from database import init_db, add_complaint, get_all_complaints, get_complaint_by_tracking_id, update_complaint_status, get_timeline_for_complaint
from app import app, ADMIN_USERNAME, ADMIN_PASSWORD

class TestRaastaApplication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        app.config["TESTING"] = True
        cls.client = app.test_client()

    # -------------------------------------------------------------
    # 1. TEST BILINGUAL RULE ENGINE CLASSIFICATION
    # -------------------------------------------------------------
    def test_bilingual_classification(self):
        # English: Drainage
        cat, conf, kw = classify_complaint("Severe drainage overflow on main street with foul smell")
        self.assertEqual(cat, "Drainage")

        # Roman Urdu: Drainage
        cat, conf, kw = classify_complaint("Gutter ubal raha hai aur naali choke ho gayi hai")
        self.assertEqual(cat, "Drainage")

        # English: Garbage
        cat, conf, kw = classify_complaint("Garbage dump accumulating near residential gate")
        self.assertEqual(cat, "Garbage")

        # Roman Urdu: Garbage
        cat, conf, kw = classify_complaint("Kachra dabba toot gaya aur kooda bikhar gaya safai nahi hui")
        self.assertEqual(cat, "Garbage")

        # English: Streetlight
        cat, conf, kw = classify_complaint("Streetlight pole is flickering and street is pitch dark")
        self.assertEqual(cat, "Streetlight")

        # Roman Urdu: Streetlight
        cat, conf, kw = classify_complaint("Light band hai pura andhera hai bijli pole pe bulb nahi jal raha")
        self.assertEqual(cat, "Streetlight")

        # English: Roads
        cat, conf, kw = classify_complaint("Massive pothole in the middle of the road damaging cars")
        self.assertEqual(cat, "Roads")

        # Roman Urdu: Roads
        cat, conf, kw = classify_complaint("Sadak pe bada khaddha hai rasta kharab ho gaya")
        self.assertEqual(cat, "Roads")

        # English: Water Supply
        cat, conf, kw = classify_complaint("Drinking water pipeline burst and clean water leaking")
        self.assertEqual(cat, "Water Supply")

        # Roman Urdu: Water Supply
        cat, conf, kw = classify_complaint("Peene ka pani teen din se nahi aaya nal band hai")
        self.assertEqual(cat, "Water Supply")

    # -------------------------------------------------------------
    # 2. TEST TRANSPARENT SEVERITY ESTIMATION
    # -------------------------------------------------------------
    def test_severity_estimation(self):
        # Critical trigger (open manhole)
        sev_crit = estimate_severity("Open manhole on busy road causing fatal accident risk", "Drainage")
        self.assertEqual(sev_crit["level"], "Critical")
        self.assertIn("Immediate safety", sev_crit["reason"])

        # Roman Urdu Critical (current lag sakta hai)
        sev_crit_urdu = estimate_severity("Bijli ka pole tar latak raha hai current ka khatra hai", "Streetlight")
        self.assertEqual(sev_crit_urdu["level"], "Critical")

        # High trigger (3 days)
        sev_high = estimate_severity("Water supply cutoff for 3 days completely blocked", "Water Supply")
        self.assertEqual(sev_high["level"], "High")

        # Low trigger
        sev_low = estimate_severity("Minor paint scraped on curb signboard", "Other")
        self.assertEqual(sev_low["level"], "Low")

    # -------------------------------------------------------------
    # 3. TEST DUPLICATE DETECTION
    # -------------------------------------------------------------
    def test_duplicate_detection(self):
        existing_list = [{
            "id": 99,
            "tracking_id": "HYD-TEST-99",
            "locality": "Mehdipatnam",
            "category": "Roads",
            "status": "Reported",
            "raw_description": "Bada khaddha sadak pe gaadi chalana mushkil"
        }]

        # Similar description in same locality
        is_dup, match, score = check_for_duplicates(
            "Sadak pe bada khaddha hai gaadi chalana bohot mushkil",
            "Mehdipatnam",
            "Roads",
            existing_list
        )
        self.assertTrue(is_dup)
        self.assertEqual(match["tracking_id"], "HYD-TEST-99")
        self.assertGreater(score, 45.0)

        # Different locality -> Not duplicate
        is_dup_other_loc, _, _ = check_for_duplicates(
            "Sadak pe bada khaddha hai gaadi chalana bohot mushkil",
            "Kukatpally",
            "Roads",
            existing_list
        )
        self.assertFalse(is_dup_other_loc)

    # -------------------------------------------------------------
    # 4. TEST FLASK HTTP ROUTES & API
    # -------------------------------------------------------------
    def test_homepage_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Raasta", response.data)
        self.assertIn(b"Civic Simulation", response.data)

    def test_report_page_route(self):
        response = self.client.get("/report")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hyderabad Locality", response.data)

    def test_complaints_page_route(self):
        response = self.client.get("/complaints")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Public Grievance Registry", response.data)

    def test_map_page_route(self):
        response = self.client.get("/map")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Hyderabad Civic Map", response.data)

    def test_preview_api(self):
        payload = {
            "description": "Sadak pe bohot bada khaddha hai",
            "locality": "Charminar"
        }
        res = self.client.post("/api/preview", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["category"], "Roads")
        self.assertIn("severity", data)

    def test_complaint_creation_and_timeline(self):
        payload = {
            "citizen_name": "Test Citizen",
            "citizen_phone": "9876543210",
            "locality": "Charminar",
            "landmark": "Near Mecca Masjid",
            "description": "Streetlight pole wiring hanging dangerously and causing spark",
            "latitude": 17.3616,
            "longitude": 78.4747
        }
        res = self.client.post("/api/complaints", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        tracking_id = data["complaint"]["tracking_id"]

        # Verify single complaint API
        get_res = self.client.get(f"/api/complaint/{tracking_id}")
        self.assertEqual(get_res.status_code, 200)
        comp_detail = get_res.get_json()
        self.assertEqual(comp_detail["complaint"]["locality"], "Charminar")
        self.assertGreater(len(comp_detail["timeline"]), 0)

    # -------------------------------------------------------------
    # 5. TEST ADMIN AUTHENTICATION & STATUS UPDATE
    # -------------------------------------------------------------
    def test_admin_auth_and_status_update(self):
        # 1. Access admin without login -> shows login page
        res = self.client.get("/admin")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Civic Officer Portal", res.data)

        # 2. Login with valid credentials
        login_res = self.client.post("/admin/login", data={
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Civic Grievance Admin Console", login_res.data)

        # 3. Create a test complaint to update
        complaints = get_all_complaints()
        self.assertGreater(len(complaints), 0)
        target_id = complaints[0]["id"]

        # 4. Update status as admin
        update_res = self.client.post("/api/admin/status", json={
            "complaint_id": target_id,
            "status": "Action Taken",
            "admin_note": "Inspection completed and repair unit dispatched.",
            "officer_name": "Chief Ward Engineer"
        })
        self.assertEqual(update_res.status_code, 200)
        update_data = update_res.get_json()
        self.assertEqual(update_data["complaint"]["status"], "Action Taken")

        # 5. Verify timeline entry was appended
        timelines = get_timeline_for_complaint(target_id)
        latest_timeline = timelines[-1]
        self.assertEqual(latest_timeline["status"], "Action Taken")
        self.assertEqual(latest_timeline["updated_by"], "Chief Ward Engineer")


if __name__ == "__main__":
    unittest.main()
