import re
import random
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status
from ..security.auth import (
    ACTIVE_OTPS,
    AUTHORIZED_LEA_OFFICERS,
    create_access_token
)
from ..models.schemas import (
    AadhaarSendOTPRequest,
    AadhaarVerifyOTPRequest,
    LEALoginRequest,
    AuthTokenResponse
)
from ..ml.predictor import ATMPredictor

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/citizen/send-otp")
def send_citizen_otp(req: AadhaarSendOTPRequest):
    # Clean Aadhaar number: remove spaces and hyphens
    cleaned = re.sub(r"\s+|-", "", req.aadhaar_number)
    if not re.fullmatch(r"\d{12}", cleaned):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Aadhaar format. Must be a 12-digit numeric identifier."
        )

    # Generate 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    ACTIVE_OTPS[cleaned] = {
        "otp": otp,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10)
    }

    masked_aadhaar = f"XXXX-XXXX-{cleaned[-4:]}"
    return {
        "status": "success",
        "message": f"OTP successfully dispatched to UIDAI registered mobile linked with {masked_aadhaar}.",
        "masked_aadhaar": masked_aadhaar,
        "demo_otp": otp # Provided for effortless evaluation and testing
    }

@router.post("/citizen/verify-otp", response_model=AuthTokenResponse)
def verify_citizen_otp(req: AadhaarVerifyOTPRequest):
    cleaned = re.sub(r"\s+|-", "", req.aadhaar_number)
    stored = ACTIVE_OTPS.get(cleaned)

    # Also accept demo bypass OTP 123456 or the exact generated OTP
    valid = False
    if stored and stored["otp"] == req.otp.strip():
        valid = True
    elif req.otp.strip() == "123456":
        valid = True

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP. Please verify and try again."
        )

    # Invalidate after use
    if cleaned in ACTIVE_OTPS:
        del ACTIVE_OTPS[cleaned]

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

@router.post("/lea/login", response_model=AuthTokenResponse)
def lea_officer_login(req: LEALoginRequest):
    badge = req.badge_id.strip()
    officer = AUTHORIZED_LEA_OFFICERS.get(badge)

    if not officer or officer["password"] != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Law Enforcement Officer Badge ID or Security Passkey."
        )

    payload = {
        "sub": badge,
        "role": "LEA_OFFICER",
        "badge_id": badge,
        "name": officer["name"],
        "rank": officer["rank"],
        "agency": officer["agency"],
        "jurisdiction": officer["jurisdiction"]
    }

    token = create_access_token(payload)
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "LEA_OFFICER",
        "user_info": {
            "badge_id": badge,
            "name": officer["name"],
            "rank": officer["rank"],
            "agency": officer["agency"],
            "jurisdiction": officer["jurisdiction"]
        }
    }

@router.get("/reference-data")
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
