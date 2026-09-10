from datetime import datetime, timezone
from fastapi import APIRouter
from .case_store import LIVE_CASES, TACTICAL_LOGS

router = APIRouter(prefix="/api/alerts", tags=["Live Tactical Alerts"])

@router.get("/live")
def get_live_alerts():
    """
    Returns high-priority alerts for tactical command display.
    """
    recent_critical_cases = [
        c for c in LIVE_CASES.values()
        if c.get("prediction", {}).get("threat_level") in ["CRITICAL", "HIGH"]
    ]
    return {
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        "critical_count": len(recent_critical_cases),
        "alerts": recent_critical_cases[:10],
        "recent_tactical_events": TACTICAL_LOGS[:15]
    }
