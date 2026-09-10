import random
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from ..models.schemas import (
    ComplaintSubmissionRequest,
    ComplaintSubmissionResponse,
    TrajectoryPredictionResponse
)
from ..ml.predictor import ATMPredictor
from .case_store import LIVE_CASES, add_tactical_log

router = APIRouter(prefix="/api/citizen", tags=["Citizen Complaints"])

@router.post("/complaints", response_model=ComplaintSubmissionResponse)
def submit_complaint(req: ComplaintSubmissionRequest):
    if not req.digital_hops:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one digital transaction hop is required to run the AI trajectory analysis."
        )

    # 1. Generate Official Incident Identifiers
    random_seq = random.randint(100000, 999999)
    complaint_id = f"NCRP-2026-{random_seq}"
    case_id = f"CASE_{random_seq}"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 2. Run PyTorch Trajectory Inference
    predictor = ATMPredictor.get_instance()
    hops_data = [hop.model_dump() for hop in req.digital_hops]
    prediction = predictor.predict_atm_trajectory(hops_data, top_k=3)

    # 3. Store Case in Live Intelligence Registry
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
    LIVE_CASES[case_id] = case_record

    primary_atm = prediction["predicted_atms"][0] if prediction["predicted_atms"] else None
    atm_id = primary_atm["atm_id"] if primary_atm else "UNKNOWN"
    atm_city = primary_atm["city"] if primary_atm else "UNKNOWN"

    # 4. Dispatch Tactical Broadcast Log
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

@router.get("/complaints/{complaint_id}")
def get_complaint_status(complaint_id: str):
    for case in LIVE_CASES.values():
        if case["complaint_id"] == complaint_id or case["case_id"] == complaint_id:
            return {
                "status": "success",
                "case": case
            }
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Complaint with ID '{complaint_id}' was not found in active records."
    )
