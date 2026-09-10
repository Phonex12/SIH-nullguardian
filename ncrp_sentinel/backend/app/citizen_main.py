import random
import re
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import FRONTEND_DIR
from .security.honeypot import HoneypotMiddleware
from .security.auth import create_access_token
from .models.schemas import (
    AadhaarSendOTPRequest,
    AadhaarVerifyOTPRequest,
    ComplaintSubmissionRequest,
    ComplaintSubmissionResponse
)
from .ml.predictor import ATMPredictor
from .db import (
    init_db,
    save_complaint,
    get_case,
    add_tactical_log,
    save_otp,
    verify_and_clear_otp,
    get_all_articles,
    get_article_by_slug
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[CITIZEN SERVICE] Initializing Shared Database...")
    init_db()
    print("[CITIZEN SERVICE] Pre-loading PyTorch ATM Trajectory LSTM...")
    ATMPredictor.get_instance()
    print("[CITIZEN SERVICE READY] Public Citizen Portal active on Port 8000.")
    yield

app = FastAPI(
    title="NCRP Sentinel - Citizen Cybercrime Portal & Awareness Hub",
    description="Public citizen-facing complaint ingestion, AI ATM cashout trajectory analysis, and educational cybercrime defense articles.",
    version="2.1.0",
    lifespan=lifespan
)

# 1. Register Anti-Intrusion Honeypot (traps /admin)
app.add_middleware(HoneypotMiddleware)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount Static Assets
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# 4. Public Citizen API Routes
citizen_api = APIRouter(prefix="/api/citizen", tags=["Citizen Portal API"])

@citizen_api.post("/auth/send-otp")
def send_citizen_otp(req: AadhaarSendOTPRequest):
    cleaned = re.sub(r"\s+|-", "", req.aadhaar_number)
    if not re.fullmatch(r"\d{12}", cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Aadhaar format. Must be a 12-digit numeric identifier."
        )

    otp = f"{random.randint(100000, 999999)}"
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
    save_otp(cleaned, otp, expires_at)

    masked_aadhaar = f"XXXX-XXXX-{cleaned[-4:]}"
    return {
        "status": "success",
        "message": f"OTP successfully dispatched to UIDAI registered mobile linked with {masked_aadhaar}.",
        "masked_aadhaar": masked_aadhaar,
        "demo_otp": otp
    }

@citizen_api.post("/auth/verify-otp")
def verify_citizen_otp(req: AadhaarVerifyOTPRequest):
    cleaned = re.sub(r"\s+|-", "", req.aadhaar_number)
    if not verify_and_clear_otp(cleaned, req.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. Please check and try again."
        )

    masked = f"XXXX-XXXX-{cleaned[-4:]}" if len(cleaned) >= 4 else "XXXX-XXXX-0000"
    payload = {
        "sub": f"aadhaar_{cleaned}",
        "role": "CITIZEN",
        "aadhaar_masked": masked,
        "name": "Verified Citizen User"
    }

    token = create_access_token(payload)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "CITIZEN",
        "user_info": {
            "name": "Verified Citizen User",
            "aadhaar_masked": masked,
            "auth_provider": "UIDAI Aadhaar OTP Gateway"
        }
    }

@citizen_api.get("/reference-data")
def get_reference_data():
    predictor = ATMPredictor.get_instance()
    options = predictor.get_reference_options()
    options["crime_types"] = [
        {"id": "DIGITAL_ARREST", "label": "Digital Arrest / Fake Law Enforcement Video Call"},
        {"id": "UPI_FRAUD", "label": "UPI QR Code / Phishing Collect Request"},
        {"id": "JOB_FRAUD", "label": "Work From Home / Telegram Task Part-Time Scam"},
        {"id": "INVESTMENT_FRAUD", "label": "Fake Trading App / High-Yield Stock Investment"},
        {"id": "ROMANCE_FRAUD", "label": "Social Media Honeytrap / Customs Parcel Scam"},
        {"id": "CRYPTO_FRAUD", "label": "Unauthorized Crypto Asset Transfer"}
    ]
    return options

@citizen_api.post("/complaints", response_model=ComplaintSubmissionResponse)
def submit_complaint(req: ComplaintSubmissionRequest):
    if not req.digital_hops:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one digital transaction hop is required to run the AI trajectory analysis."
        )

    random_seq = random.randint(100000, 999999)
    complaint_id = f"NCRP-2026-{random_seq}"
    case_id = f"CASE_{random_seq}"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Run PyTorch Trajectory Inference
    predictor = ATMPredictor.get_instance()
    hops_data = [hop.model_dump() for hop in req.digital_hops]
    prediction = predictor.predict_atm_trajectory(hops_data, top_k=3)

    case_record = {
        "complaint_id": complaint_id,
        "case_id": case_id,
        "registered_at": now_str,
        "victim_name": req.victim_name,
        "victim_phone": req.victim_phone,
        "victim_account": req.victim_account,
        "reported_amount": req.reported_amount,
        "city": req.city,
        "state": req.state,
        "crime_type": req.crime_type,
        "scammer_contact": req.scammer_contact,
        "scammer_upi_or_account": req.scammer_upi_or_account,
        "incident_description": req.incident_description,
        "status": "LIVE_THREAT",
        "digital_hops": hops_data,
        "prediction": prediction,
        "actions_taken": {
            "bank_frozen": False,
            "intercept_dispatched": False,
            "surveillance_alert": False
        }
    }

    # Write to shared SQLite DB
    save_complaint(case_record)

    primary_atm = prediction["predicted_atms"][0] if prediction["predicted_atms"] else None
    atm_id = primary_atm["atm_id"] if primary_atm else "UNKNOWN"
    atm_city = primary_atm["city"] if primary_atm else "UNKNOWN"

    add_tactical_log(
        event_type="NEW_COMPLAINT_INGESTED",
        message=f"Case {case_id} registered (₹{req.reported_amount:,.2f}, {req.crime_type}). AI predicted cashout at {atm_id} ({atm_city}).",
        meta={"case_id": case_id, "amount": req.reported_amount, "target_atm": atm_id}
    )

    emergency_guidance = {
        "helpline_1930": "Call the National Cybercrime Helpline 1930 immediately to register your Golden Hour ticket.",
        "cfcfrms_status": "Automated lien/freeze request generated and queued for destination bank nodes.",
        "steps_to_follow": [
            "Do NOT engage or transfer further funds under any pretext.",
            "Contact your home bank branch manager to freeze internet/UPI banking credentials on your compromised account.",
            "Preserve all transaction receipts, WhatsApp/SMS transcripts, and call audio logs as evidence."
        ]
    }

    return {
        "status": "success",
        "complaint_id": complaint_id,
        "case_id": case_id,
        "registered_at": now_str,
        "message": "Complaint successfully registered on the National Cybercrime Reporting Portal.",
        "reported_amount": req.reported_amount,
        "crime_type": req.crime_type,
        "prediction": prediction,
        "emergency_guidance": emergency_guidance
    }

@citizen_api.get("/complaints/{complaint_id}")
def get_complaint_status(complaint_id: str):
    case = get_case(complaint_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' was not found in official records."
        )
    return {
        "status": "success",
        "case": case
    }

# Cybercrime Educational Awareness Articles
@citizen_api.get("/articles")
def list_articles():
    return {
        "status": "success",
        "count": len(get_all_articles()),
        "articles": get_all_articles()
    }

@citizen_api.get("/articles/{slug}")
def get_article(slug: str):
    article = get_article_by_slug(slug)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found.")
    return {
        "status": "success",
        "article": article
    }

app.include_router(citizen_api)

# 5. UI Page Serving
@app.get("/", tags=["UI"])
def serve_citizen_portal():
    return FileResponse(FRONTEND_DIR / "citizen" / "index.html")

@app.get("/learn", tags=["UI"])
def serve_learning_hub_alias():
    return FileResponse(FRONTEND_DIR / "citizen" / "index.html")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Citizen Public Service",
        "port": 8000,
        "isolation_tier": "PUBLIC_CITIZEN_ZONE",
        "admin_access": "RESTRICTED"
    }
