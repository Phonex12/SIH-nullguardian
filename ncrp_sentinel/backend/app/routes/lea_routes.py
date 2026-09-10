from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..security.auth import require_lea_officer
from ..ml.hotspot_engine import HotspotEngine
from ..ml.predictor import ATMPredictor
from ..models.schemas import (
    FreezeAccountRequest,
    DispatchUnitRequest,
    SurveillanceAlertRequest
)
from .case_store import LIVE_CASES, TACTICAL_LOGS, add_tactical_log

router = APIRouter(prefix="/api/lea", tags=["Law Enforcement Tactical Command"])

@router.get("/dashboard-stats")
def get_dashboard_stats(user: dict = Depends(require_lea_officer)):
    engine = HotspotEngine.get_instance()
    stats = engine.get_tactical_stats()

    # Calculate live case statistics
    live_count = len(LIVE_CASES)
    total_stolen = sum(c.get("reported_amount", 0.0) for c in LIVE_CASES.values())
    frozen_cases = sum(1 for c in LIVE_CASES.values() if c.get("actions_taken", {}).get("bank_frozen"))
    dispatched_cases = sum(1 for c in LIVE_CASES.values() if c.get("actions_taken", {}).get("intercept_dispatched"))

    stats.update({
        "active_live_cases": live_count,
        "total_stolen_inr_active": total_stolen,
        "accounts_frozen_count": frozen_cases,
        "units_dispatched_count": dispatched_cases,
        "officer": {
            "name": user.get("name"),
            "badge_id": user.get("badge_id"),
            "rank": user.get("rank"),
            "agency": user.get("agency"),
            "jurisdiction": user.get("jurisdiction")
        }
    })
    return stats

@router.get("/heatmap")
def get_heatmap_points(
    state: Optional[str] = Query("all"),
    city: Optional[str] = Query("all"),
    min_risk: int = Query(0),
    user: dict = Depends(require_lea_officer)
):
    engine = HotspotEngine.get_instance()
    points = engine.get_heatmap_points(state=state, city=city, min_risk=min_risk)
    return {
        "count": len(points),
        "state_filter": state,
        "city_filter": city,
        "points": points
    }

@router.get("/atm-markers")
def get_atm_markers(
    state: Optional[str] = Query("all"),
    city: Optional[str] = Query("all"),
    limit: int = Query(150),
    user: dict = Depends(require_lea_officer)
):
    engine = HotspotEngine.get_instance()
    markers = engine.get_atm_markers(state=state, city=city, limit=limit)
    return {
        "count": len(markers),
        "markers": markers
    }

@router.get("/cases")
def get_all_cases(user: dict = Depends(require_lea_officer)):
    cases_list = list(LIVE_CASES.values())
    # Sort reverse chronological
    return {
        "total_cases": len(cases_list),
        "cases": cases_list
    }

@router.get("/cases/{case_id}")
def get_case_detail(case_id: str, user: dict = Depends(require_lea_officer)):
    case = LIVE_CASES.get(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case file not found.")
    return case

@router.post("/action/freeze-account")
def freeze_account(req: FreezeAccountRequest, user: dict = Depends(require_lea_officer)):
    case = LIVE_CASES.get(req.case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case file not found.")

    case["actions_taken"]["bank_frozen"] = True
    case["actions_taken"]["bank_freeze_timestamp"] = "JUST NOW"
    case["status"] = "FUNDS_LOCKED"

    add_tactical_log(
        event_type="BANK_FUND_FREEZE_TRIGGERED",
        message=f"CFCFRMS Lien instruction issued for account {req.account_id} at {req.bank_id} by {user.get('name')}.",
        meta={"case_id": req.case_id, "account_id": req.account_id, "bank_id": req.bank_id}
    )

    return {
        "status": "success",
        "message": f"Emergency Lien placed on mule account {req.account_id}. Bank node acknowledged freeze.",
        "case_id": req.case_id,
        "actions_taken": case["actions_taken"]
    }

@router.post("/action/dispatch-intercept")
def dispatch_intercept(req: DispatchUnitRequest, user: dict = Depends(require_lea_officer)):
    case = LIVE_CASES.get(req.case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case file not found.")

    case["actions_taken"]["intercept_dispatched"] = True
    case["actions_taken"]["dispatched_unit"] = req.unit_callsign
    case["actions_taken"]["dispatch_eta"] = "8-12 minutes"

    add_tactical_log(
        event_type="INTERCEPT_UNIT_DISPATCHED",
        message=f"Unit {req.unit_callsign} dispatched to target ATM {req.atm_id} (ETA: 8-12 min) by {user.get('name')}.",
        meta={"case_id": req.case_id, "atm_id": req.atm_id, "unit": req.unit_callsign}
    )

    return {
        "status": "success",
        "message": f"Tactical unit {req.unit_callsign} dispatched to cordon {req.atm_id}.",
        "eta": "8-12 minutes",
        "case_id": req.case_id,
        "actions_taken": case["actions_taken"]
    }

@router.post("/action/surveillance-alert")
def trigger_surveillance(req: SurveillanceAlertRequest, user: dict = Depends(require_lea_officer)):
    case = LIVE_CASES.get(req.case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case file not found.")

    case["actions_taken"]["surveillance_alert"] = True

    add_tactical_log(
        event_type="SURVEILLANCE_ALERT_ACTIVE",
        message=f"ATM {req.atm_id} surveillance camera feeds flagged for facial recognition trigger.",
        meta={"case_id": req.case_id, "atm_id": req.atm_id}
    )

    return {
        "status": "success",
        "message": f"Surveillance cameras & security guards at {req.atm_id} notified.",
        "case_id": req.case_id,
        "actions_taken": case["actions_taken"]
    }

@router.get("/tactical-logs")
def get_tactical_logs(user: dict = Depends(require_lea_officer)):
    return {
        "logs": TACTICAL_LOGS
    }
