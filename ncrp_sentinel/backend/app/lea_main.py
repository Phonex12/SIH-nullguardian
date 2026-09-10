from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import FRONTEND_DIR
from .security.auth import (
    create_access_token,
    require_lea_officer,
    AUTHORIZED_LEA_OFFICERS
)
from .models.schemas import (
    LEALoginRequest,
    AuthTokenResponse,
    FreezeAccountRequest,
    DispatchUnitRequest,
    SurveillanceAlertRequest
)
from .ml.hotspot_engine import HotspotEngine
from .db import (
    init_db,
    get_case,
    get_all_cases,
    update_case_action,
    add_tactical_log,
    get_tactical_logs
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[LEA COMMAND SERVICE] Connecting to Shared Database...")
    init_db()
    print("[LEA COMMAND SERVICE] Pre-loading Tactical GIS Hotspot Engine...")
    HotspotEngine.get_instance()
    print("[LEA COMMAND SERVICE READY] Secure Command Center active on Port 9000.")
    yield

app = FastAPI(
    title="NCRP Sentinel - LEA & I4C Tactical Command Terminal",
    description="Secured Command Center for Law Enforcement Agencies, I4C officers, and Cyber Financial Crime mitigation units.",
    version="2.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Assets
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# LEA Tactical API Router
lea_api = APIRouter(prefix="/api/lea", tags=["Law Enforcement Command API"])

@lea_api.post("/auth/login", response_model=AuthTokenResponse)
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
    add_tactical_log(
        event_type="OFFICER_AUTHENTICATED",
        message=f"{officer['name']} ({badge}) initialized command session.",
        meta={"badge_id": badge, "agency": officer["agency"]}
    )

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

@lea_api.get("/dashboard-stats")
def get_dashboard_stats(user: dict = Depends(require_lea_officer)):
    engine = HotspotEngine.get_instance()
    stats = engine.get_tactical_stats()

    cases = get_all_cases()
    live_count = len(cases)
    total_stolen = sum(c.get("reported_amount", 0.0) for c in cases)
    frozen_cases = sum(1 for c in cases if c.get("actions_taken", {}).get("bank_frozen"))
    dispatched_cases = sum(1 for c in cases if c.get("actions_taken", {}).get("intercept_dispatched"))

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

@lea_api.get("/heatmap")
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

@lea_api.get("/atm-markers")
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

@lea_api.get("/cases")
def get_all_active_cases(user: dict = Depends(require_lea_officer)):
    cases = get_all_cases()
    return {
        "total_cases": len(cases),
        "cases": cases
    }

@lea_api.get("/cases/{case_id}")
def get_case_detail(case_id: str, user: dict = Depends(require_lea_officer)):
    case = get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case file not found.")
    return case

@lea_api.post("/action/freeze-account")
def freeze_account(req: FreezeAccountRequest, user: dict = Depends(require_lea_officer)):
    updated_case = update_case_action(
        case_id=req.case_id,
        action_key="bank_frozen",
        action_val=True,
        extra_fields={"bank_freeze_timestamp": "JUST NOW"}
    )
    if not updated_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case file not found.")

    add_tactical_log(
        event_type="BANK_FUND_FREEZE_TRIGGERED",
        message=f"CFCFRMS Lien instruction issued for account {req.account_id} at {req.bank_id} by {user.get('name')}.",
        meta={"case_id": req.case_id, "account_id": req.account_id, "bank_id": req.bank_id}
    )

    return {
        "status": "success",
        "message": f"Emergency Lien placed on mule account {req.account_id}. Bank node acknowledged freeze.",
        "case_id": req.case_id,
        "actions_taken": updated_case["actions_taken"]
    }

@lea_api.post("/action/dispatch-intercept")
def dispatch_intercept(req: DispatchUnitRequest, user: dict = Depends(require_lea_officer)):
    updated_case = update_case_action(
        case_id=req.case_id,
        action_key="intercept_dispatched",
        action_val=True,
        extra_fields={
            "dispatched_unit": req.unit_callsign,
            "dispatch_eta": "8-12 minutes"
        }
    )
    if not updated_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case file not found.")

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
        "actions_taken": updated_case["actions_taken"]
    }

@lea_api.post("/action/surveillance-alert")
def trigger_surveillance(req: SurveillanceAlertRequest, user: dict = Depends(require_lea_officer)):
    updated_case = update_case_action(
        case_id=req.case_id,
        action_key="surveillance_alert",
        action_val=True
    )
    if not updated_case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case file not found.")

    add_tactical_log(
        event_type="SURVEILLANCE_ALERT_ACTIVE",
        message=f"ATM {req.atm_id} surveillance camera feeds flagged for facial recognition trigger.",
        meta={"case_id": req.case_id, "atm_id": req.atm_id}
    )

    return {
        "status": "success",
        "message": f"Surveillance cameras & security guards at {req.atm_id} notified.",
        "case_id": req.case_id,
        "actions_taken": updated_case["actions_taken"]
    }

@lea_api.get("/tactical-logs")
def get_logs(user: dict = Depends(require_lea_officer)):
    return {
        "logs": get_tactical_logs(limit=40)
    }

# Live Alerts Polling
@app.get("/api/alerts/live")
def get_live_alerts():
    cases = get_all_cases()
    recent_critical = [
        c for c in cases
        if c.get("prediction", {}).get("threat_level") in ["CRITICAL", "HIGH"]
    ]
    return {
        "critical_count": len(recent_critical),
        "alerts": recent_critical[:10],
        "recent_tactical_events": get_tactical_logs(limit=15)
    }

app.include_router(lea_api)

# UI Serving
@app.get("/", tags=["UI"])
def serve_lea_terminal():
    return FileResponse(FRONTEND_DIR / "lea" / "index.html")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "LEA Tactical Command Service",
        "port": 9000,
        "isolation_tier": "SECURE_LEA_ZONE",
        "auth_required": True
    }
