from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Auth Schemas
class AadhaarSendOTPRequest(BaseModel):
    aadhaar_number: str = Field(..., description="12-digit Aadhaar number with or without spaces")

class AadhaarVerifyOTPRequest(BaseModel):
    aadhaar_number: str
    otp: str = Field(..., description="6-digit verification OTP")

class LEALoginRequest(BaseModel):
    badge_id: str
    password: str

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_info: Dict[str, Any]

# Complaint & Trajectory Schemas
class DigitalHopSchema(BaseModel):
    amount: float
    time: str = "12:00"
    city: str
    state: str
    bank_id: str
    destination_account: Optional[str] = None

class ComplaintSubmissionRequest(BaseModel):
    victim_name: str
    victim_phone: str
    victim_account: str
    reported_amount: float
    city: str
    state: str
    crime_type: str
    scammer_contact: Optional[str] = None
    scammer_upi_or_account: Optional[str] = None
    digital_hops: List[DigitalHopSchema]
    incident_description: Optional[str] = None

class PredictedATMDetail(BaseModel):
    rank: int
    atm_id: str
    bank_id: str
    city: str
    state: str
    latitude: float
    longitude: float
    distance_km: float
    confidence_pct: float
    operating_24x7: bool
    baseline_volume: int
    risk_zone: int
    estimated_cashout_window: str

class TrajectoryPredictionResponse(BaseModel):
    mathematical_coords: Dict[str, float]
    primary_target_city: str
    primary_target_state: str
    threat_level: str
    predicted_atms: List[PredictedATMDetail]

class ComplaintSubmissionResponse(BaseModel):
    status: str
    complaint_id: str
    case_id: str
    registered_at: str
    message: str
    reported_amount: float
    crime_type: str
    prediction: TrajectoryPredictionResponse
    emergency_guidance: Dict[str, Any]

# LEA Tactical Action Schemas
class FreezeAccountRequest(BaseModel):
    case_id: str
    account_id: str
    bank_id: str
    freeze_reason: str = "Suspected Cybercrime Mule Account (CFCFRMS Section 1930)"

class DispatchUnitRequest(BaseModel):
    case_id: str
    atm_id: str
    unit_callsign: str = "PCR-INTERCEPT-ALPHA"
    priority: str = "CRITICAL_IMMEDIATE"

class SurveillanceAlertRequest(BaseModel):
    case_id: str
    atm_id: str
    notes: Optional[str] = None
