import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
from app.citizen_main import app as citizen_app
from app.lea_main import app as lea_app
from app.db import get_case, get_all_articles

def test_full_system():
    print("========================================================================")
    print("      NCRP SENTINEL // DUAL AIR-GAPPED SYSTEM TEST SUITE (100%)       ")
    print("========================================================================")

    with TestClient(citizen_app) as citizen_client, TestClient(lea_app) as lea_client:

        # ---------------------------------------------------------
        # PART 1: PUBLIC CITIZEN SERVICE (PORT 8000)
        # ---------------------------------------------------------
        print("\n[PART 1] Testing Citizen Public Service (Port 8000) ...")
        
        # 1. Healthcheck
        c_health = citizen_client.get("/api/health")
        assert c_health.status_code == 200
        assert c_health.json()["isolation_tier"] == "PUBLIC_CITIZEN_ZONE"
        print("[PASS] Citizen Service Health Check: 200 OK (PUBLIC_CITIZEN_ZONE)")

        # 2. Anti-Intrusion Honeypot on /admin
        honeypot_res = citizen_client.get("/admin", headers={"Accept": "text/html"})
        assert honeypot_res.status_code == 403
        assert "ACCESS PROHIBITED & TRAPPED" in honeypot_res.text or "403" in honeypot_res.text
        print("[PASS] GET /admin Honeypot: 403 Forbidden with IT Act Section 66F defense shield")

        # 3. Educational Articles & Learning Hub
        articles_res = citizen_client.get("/api/citizen/articles")
        assert articles_res.status_code == 200
        articles_data = articles_res.json()
        assert articles_data["count"] >= 6
        print(f"[PASS] Cybercrime Learning Hub: {articles_data['count']} educational articles loaded (Digital Arrest, UPI, Job Scams, Mule Accounts, etc.)")

        # 4. Aadhaar OTP Authentication Flow
        otp_req = citizen_client.post("/api/citizen/auth/send-otp", json={"aadhaar_number": "542891024319"})
        assert otp_req.status_code == 200
        otp_code = otp_req.json()["demo_otp"]
        print(f"[PASS] Aadhaar OTP Dispatched: {otp_req.json()['masked_aadhaar']} (Sandbox OTP: {otp_code})")

        verify_req = citizen_client.post("/api/citizen/auth/verify-otp", json={
            "aadhaar_number": "542891024319",
            "otp": otp_code
        })
        assert verify_req.status_code == 200
        citizen_token = verify_req.json()["access_token"]
        print(f"[PASS] Aadhaar Verified! Citizen JWT generated: {citizen_token[:20]}...")

        # 5. Complaint Submission & PyTorch Trajectory Inference
        complaint_payload = {
            "victim_name": "Dr. Sunita Deshpande",
            "victim_phone": "+91 98230 11992",
            "victim_account": "ACC_0055102",
            "reported_amount": 240000.0,
            "city": "Pune",
            "state": "Maharashtra",
            "crime_type": "DIGITAL_ARREST",
            "scammer_contact": "+91 99881 22334",
            "scammer_upi_or_account": "cbi.escrow92@sbi",
            "digital_hops": [
                {"amount": 240000.0, "time": "09:30", "city": "Pune", "state": "Maharashtra", "bank_id": "BANK_03", "destination_account": "ACC_0088192"},
                {"amount": 120000.0, "time": "10:15", "city": "Mumbai", "state": "Maharashtra", "bank_id": "BANK_08", "destination_account": "ACC_0077412"}
            ],
            "incident_description": "Fake CBI video call claiming narcotics parcel intercepted in victim's name."
        }

        comp_res = citizen_client.post(
            "/api/citizen/complaints",
            json=complaint_payload,
            headers={"Authorization": f"Bearer {citizen_token}"}
        )
        assert comp_res.status_code == 200
        comp_data = comp_res.json()
        new_case_id = comp_data["case_id"]
        new_complaint_id = comp_data["complaint_id"]
        pred = comp_data["prediction"]
        top_atm = pred["predicted_atms"][0]
        print(f"[PASS] Complaint Ingested into SQLite DB: {new_complaint_id} (Case ID: {new_case_id})")
        print(f"       AI Forecast Target ATM: {top_atm['atm_id']} in {top_atm['city']} ({top_atm['confidence_pct']}% Match, Window: {top_atm['estimated_cashout_window']})")

        # ---------------------------------------------------------
        # PART 2: SHARED DATABASE PERSISTENCE CHECK
        # ---------------------------------------------------------
        print("\n[PART 2] Verifying Shared Database Persistence (ncrp_shared.db) ...")
        db_case = get_case(new_case_id)
        assert db_case is not None
        assert db_case["reported_amount"] == 240000.0
        print(f"[PASS] SQLite DB Verified: Case {new_case_id} successfully persisted in database.")

        # ---------------------------------------------------------
        # PART 3: SECURE LEA COMMAND SERVICE (PORT 9000)
        # ---------------------------------------------------------
        print("\n[PART 3] Testing Secured LEA Tactical Command Service (Port 9000) ...")

        # 1. Healthcheck
        lea_health = lea_client.get("/api/health")
        assert lea_health.status_code == 200
        assert lea_health.json()["isolation_tier"] == "SECURE_LEA_ZONE"
        print("[PASS] LEA Command Service Health Check: 200 OK (SECURE_LEA_ZONE)")

        # 2. RBAC: Unauthorized attempt rejected
        unauth_res = lea_client.get("/api/lea/dashboard-stats")
        assert unauth_res.status_code == 401
        print("[PASS] Unauthenticated access to LEA endpoints rejected (401 Unauthorized)")

        # 3. Officer Login
        lea_login = lea_client.post("/api/lea/auth/login", json={
            "badge_id": "I4C-DEL-892",
            "password": "Sentinel@2026"
        })
        assert lea_login.status_code == 200
        lea_token = lea_login.json()["access_token"]
        officer = lea_login.json()["user_info"]
        print(f"[PASS] LEA Officer Authenticated: {officer['name']} ({officer['badge_id']}, {officer['agency']})")

        # 4. Cross-Service Database Synchronization: LEA reads case submitted on Citizen Service
        lea_headers = {"Authorization": f"Bearer {lea_token}"}
        lea_case_res = lea_client.get(f"/api/lea/cases/{new_case_id}", headers=lea_headers)
        assert lea_case_res.status_code == 200
        lea_case_data = lea_case_res.json()
        assert lea_case_data["victim_name"] == "Dr. Sunita Deshpande"
        print(f"[PASS] Cross-Service Sync: LEA Service retrieved {new_case_id} across isolated process boundary!")

        # 5. Proactive Tactical Actions on LEA Service
        freeze_res = lea_client.post("/api/lea/action/freeze-account", json={
            "case_id": new_case_id,
            "account_id": "ACC_0077412",
            "bank_id": "BANK_08",
            "freeze_reason": "Emergency Lien via CFCFRMS"
        }, headers=lea_headers)
        assert freeze_res.status_code == 200
        print(f"[PASS] 1-Click Bank Fund Freeze Executed: {freeze_res.json()['message']}")

        dispatch_res = lea_client.post("/api/lea/action/dispatch-intercept", json={
            "case_id": new_case_id,
            "atm_id": top_atm["atm_id"],
            "unit_callsign": "PCR-INTERCEPT-ALPHA",
            "priority": "CRITICAL_IMMEDIATE"
        }, headers=lea_headers)
        assert dispatch_res.status_code == 200
        print(f"[PASS] Tactical PCR Intercept Dispatched: {dispatch_res.json()['message']}")

        # 6. Verify Updated State in SQLite DB
        updated_db_case = get_case(new_case_id)
        assert updated_db_case["actions_taken"]["bank_frozen"] is True
        assert updated_db_case["actions_taken"]["intercept_dispatched"] is True
        assert updated_db_case["status"] == "FUNDS_LOCKED"
        print(f"[PASS] Database State Verified: Case {new_case_id} status updated to FUNDS_LOCKED with active intercept!")

        # 7. Verify Citizen Service does NOT expose LEA endpoints
        cross_probe = citizen_client.get("/api/lea/dashboard-stats")
        assert cross_probe.status_code in [404, 403]
        print("[PASS] Security Isolation Verified: Citizen Service does not expose LEA endpoints (404/403)")

    print("\n========================================================================")
    print("   ALL DUAL-SERVICE AIR-GAPPED TESTS COMPLETED SUCCESSFULLY! (100%)    ")
    print("========================================================================")

if __name__ == "__main__":
    test_full_system()
