import os
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

import uvicorn
import jwt
from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add parent directory to path so core package can be imported
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.config import (
    JWT_SECRET_KEY, JWT_ALGORITHM, CITIZEN_PORT, HOST, LOCAL_IP
)
from core.db import (
    init_db, get_case_by_id, create_case, store_otp, verify_and_clear_otp, get_articles
)
from core.ai_ml import ATMPredictor

# Initialize database schema on startup
init_db()

app = FastAPI(
    title="NCRP Sentinel - Citizen Cyber Support Portal",
    description="Citizen-facing proactive cyber fraud reporting and tracking system.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# --- Pydantic Request Models ---

class OTPRequest(BaseModel):
    aadhaar_number: str = Field(..., min_length=12, max_length=12, description="12-digit Aadhaar Number")

class OTPVerify(BaseModel):
    aadhaar_number: str = Field(..., min_length=12, max_length=12)
    otp_code: str = Field(..., min_length=6, max_length=6)

class TransactionHop(BaseModel):
    account_id: str
    bank_id: str
    city: str
    state: str
    amount: float
    time: str

class ComplaintSubmission(BaseModel):
    victim_name: str
    victim_phone: str
    victim_account: str
    reported_amount: float
    city: str
    state: str
    crime_type: str
    scammer_contact: Optional[str] = ""
    scammer_upi_or_account: Optional[str] = ""
    incident_description: Optional[str] = ""
    digital_hops: Optional[List[TransactionHop]] = None

# --- Auth Helpers ---

def create_citizen_token(aadhaar_number: str) -> str:
    payload = {
        "sub": f"aadhaar:{aadhaar_number}",
        "role": "CITIZEN",
        "exp": datetime.now(timezone.utc) + timedelta(hours=4)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_citizen_token(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required. Please login via Aadhaar OTP.")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("role") != "CITIZEN":
            raise HTTPException(status_code=403, detail="Invalid role permissions.")
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please request a new OTP.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def serve_citizen_portal():
    index_file = STATIC_DIR / "index.html"
    return FileResponse(str(index_file))

@app.get("/article", response_class=HTMLResponse)
@app.get("/article/{slug}", response_class=HTMLResponse)
async def serve_article_page(slug: Optional[str] = None):
    article_file = STATIC_DIR / "article.html"
    return FileResponse(str(article_file))

@app.get("/api/citizen/info")
async def get_system_info():
    return {
        "portal": "NCRP Citizen Cyber Support",
        "version": "2.0.0-PROTOTYPE",
        "status": "OPERATIONAL",
        "local_url": f"http://localhost:{CITIZEN_PORT}",
        "network_url": f"http://{LOCAL_IP}:{CITIZEN_PORT}"
    }

@app.post("/api/citizen/auth/request-otp")
async def request_otp(data: OTPRequest):
    aadhaar = data.aadhaar_number.strip()
    if not aadhaar.isdigit() or len(aadhaar) != 12:
        raise HTTPException(status_code=400, detail="Invalid Aadhaar format. Must be exactly 12 digits.")

    # Generate realistic simulated OTP (for prototype demonstration)
    # If using test Aadhaar 999999999999, standard OTP is 123456
    simulated_otp = "123456" if aadhaar == "999999999999" else f"{abs(hash(aadhaar)) % 900000 + 100000}"
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    store_otp(aadhaar, simulated_otp, expires_at)

    masked_phone = f"+91 XXXXX X{aadhaar[-4:]}"
    return {
        "success": True,
        "message": f"OTP successfully dispatched to Aadhaar-linked mobile {masked_phone}.",
        "demo_otp_hint": simulated_otp,  # Displayed in UI for student demo ease
        "expires_in_seconds": 600
    }

@app.post("/api/citizen/auth/verify-otp")
async def verify_otp(data: OTPVerify):
    aadhaar = data.aadhaar_number.strip()
    otp = data.otp_code.strip()

    # Allow master demo OTP 123456 or stored OTP
    is_valid = (otp == "123456") or verify_and_clear_otp(aadhaar, otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Incorrect or expired OTP code.")

    token = create_citizen_token(aadhaar)
    return {
        "success": True,
        "token": token,
        "message": "Citizen identity verified successfully via UIDAI Aadhaar e-KYC."
    }

@app.get("/api/citizen/reference-data")
async def get_reference_data():
    predictor = ATMPredictor.get_instance()
    return predictor.get_reference_options()

@app.post("/api/citizen/complaints")
async def submit_complaint(complaint: ComplaintSubmission):
    try:
        complaint_uuid = uuid.uuid4().hex[:6].upper()
        complaint_id = f"NCRP-2026-{complaint_uuid}"
        case_id = f"CASE_{complaint_uuid}"

        # Build digital hops sequence for AI inference
        digital_trail = []
        if complaint.digital_hops and len(complaint.digital_hops) > 0:
            for idx, hop in enumerate(complaint.digital_hops, start=1):
                digital_trail.append({
                    "hop_seq": idx,
                    "account_id": hop.account_id,
                    "bank_id": hop.bank_id,
                    "city": hop.city,
                    "state": hop.state,
                    "amount": hop.amount,
                    "time": hop.time,
                    "type": "SOURCE_VICTIM" if idx == 1 else f"MULE_LAYER_{idx-1}"
                })
        else:
            # Construct primary hop from complaint data
            digital_trail = [
                {
                    "hop_seq": 1,
                    "account_id": complaint.victim_account,
                    "bank_id": "SBIN",
                    "city": complaint.city,
                    "state": complaint.state,
                    "amount": complaint.reported_amount,
                    "time": datetime.now().strftime("%H:%M"),
                    "type": "SOURCE_VICTIM"
                },
                {
                    "hop_seq": 2,
                    "account_id": complaint.scammer_upi_or_account or "MULE-AUTO-LAYER",
                    "bank_id": "HDFC",
                    "city": complaint.city,
                    "state": complaint.state,
                    "amount": complaint.reported_amount * 0.95,
                    "time": datetime.now().strftime("%H:%M"),
                    "type": "MULE_LAYER_1"
                }
            ]

        # Run PyTorch LSTM AI Model Prediction
        predictor = ATMPredictor.get_instance()
        ai_prediction = predictor.predict_atm_trajectory(digital_trail, top_k=3)

        case_data = {
            "case_id": case_id,
            "complaint_id": complaint_id,
            "registered_at": "Just now",
            "victim_name": complaint.victim_name,
            "victim_phone": complaint.victim_phone,
            "victim_account": complaint.victim_account,
            "reported_amount": complaint.reported_amount,
            "city": complaint.city,
            "state": complaint.state,
            "crime_type": complaint.crime_type,
            "scammer_contact": complaint.scammer_contact,
            "scammer_upi_or_account": complaint.scammer_upi_or_account,
            "incident_description": complaint.incident_description,
            "status": "LIVE_THREAT",
            "digital_hops": digital_trail,
            "prediction": ai_prediction,
            "actions_taken": [
                {
                    "action": "Complaint Registered via Citizen Portal",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "operator": "CITIZEN_SELF",
                    "details": f"Victim reported financial fraud of ₹{complaint.reported_amount:,.2f}."
                },
                {
                    "action": "AI Trajectory Forecast Computed",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "operator": "SYSTEM_AI",
                    "details": f"Primary predicted cashout zone: {ai_prediction['primary_target_city']}, {ai_prediction['primary_target_state']} (Risk: {ai_prediction['threat_level']})."
                }
            ]
        }

        created = create_case(case_data)
        return {
            "success": True,
            "complaint_id": complaint_id,
            "case_id": case_id,
            "message": "Complaint successfully registered on NCRP Sentinel. Case routed to I4C LEA Tactical Grid.",
            "case_summary": {
                "amount": complaint.reported_amount,
                "threat_level": ai_prediction["threat_level"],
                "predicted_city": ai_prediction["primary_target_city"],
                "nearest_atm": ai_prediction["predicted_atms"][0]["atm_id"] if ai_prediction["predicted_atms"] else "N/A"
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Inference or DB error: {str(e)}")

@app.get("/api/citizen/complaints/track/{ack_no}")
async def track_complaint(ack_no: str):
    case = get_case_by_id(ack_no.strip())
    if not case:
        raise HTTPException(status_code=404, detail="No complaint found matching the provided acknowledgment number.")
    return {
        "complaint_id": case["complaint_id"],
        "case_id": case["case_id"],
        "status": case["status"],
        "registered_at": case["registered_at"],
        "victim_name": case["victim_name"],
        "reported_amount": case["reported_amount"],
        "crime_type": case["crime_type"],
        "actions_timeline": case["actions_taken"]
    }

@app.get("/api/citizen/awareness")
async def get_awareness_articles():
    return get_articles()

def run_server():
    print("=" * 65)
    print("🛡️  NCRP SENTINEL — CITIZEN PORTAL (STUDENT PROTOTYPE)")
    print("=" * 65)
    print(f"👉 Local Access:   http://localhost:{CITIZEN_PORT}")
    print(f"👉 LAN Demo Access: http://{LOCAL_IP}:{CITIZEN_PORT}")
    print("=" * 65)
    uvicorn.run("citizen_app.server:app", host=HOST, port=CITIZEN_PORT, reload=False)

if __name__ == "__main__":
    run_server()
