from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# In-memory case registry storing recent and newly submitted cybercrime incidents
# Initialized with sample real cases from datasets for demonstration
LIVE_CASES: Dict[str, Dict[str, Any]] = {}
TACTICAL_LOGS: List[Dict[str, Any]] = []

def init_sample_cases():
    """Seed initial high-risk incidents for LEA tactical radar."""
    if LIVE_CASES:
        return

    sample_cases = [
        {
            "complaint_id": "NCRP-2026-094101",
            "case_id": "CASE_94101",
            "registered_at": "10 mins ago",
            "victim_name": "Rajesh Sharma",
            "victim_phone": "+91 98201 44819",
            "victim_account": "ACC_0049210",
            "reported_amount": 185000.0,
            "city": "Mumbai",
            "state": "Maharashtra",
            "crime_type": "DIGITAL_ARREST",
            "scammer_upi_or_account": "cybercops.verify@sbi",
            "status": "LIVE_THREAT",
            "digital_hops": [
                {"amount": 185000.0, "time": "10:15", "city": "Mumbai", "state": "Maharashtra", "bank_id": "BANK_01", "destination_account": "ACC_0078129"},
                {"amount": 90000.0, "time": "10:32", "city": "Pune", "state": "Maharashtra", "bank_id": "BANK_03", "destination_account": "ACC_0099412"},
                {"amount": 45000.0, "time": "10:48", "city": "Nashik", "state": "Maharashtra", "bank_id": "BANK_08", "destination_account": "ACC_0012390"}
            ],
            "prediction": {
                "mathematical_coords": {"latitude": 19.9975, "longitude": 73.7898},
                "primary_target_city": "Nashik",
                "primary_target_state": "Maharashtra",
                "threat_level": "CRITICAL",
                "predicted_atms": [
                    {
                        "rank": 1,
                        "atm_id": "ATM_000005",
                        "bank_id": "BANK_02",
                        "city": "Nashik",
                        "state": "Maharashtra",
                        "latitude": 20.030363,
                        "longitude": 73.776081,
                        "distance_km": 3.9,
                        "confidence_pct": 91.4,
                        "operating_24x7": False,
                        "baseline_volume": 1447,
                        "risk_zone": 45,
                        "estimated_cashout_window": "15-35 mins"
                    },
                    {
                        "rank": 2,
                        "atm_id": "ATM_000769",
                        "bank_id": "BANK_05",
                        "city": "Nashik",
                        "state": "Maharashtra",
                        "latitude": 19.982104,
                        "longitude": 73.811422,
                        "distance_km": 5.2,
                        "confidence_pct": 82.1,
                        "operating_24x7": True,
                        "baseline_volume": 1120,
                        "risk_zone": 62,
                        "estimated_cashout_window": "20-40 mins"
                    }
                ]
            },
            "actions_taken": {
                "bank_frozen": False,
                "intercept_dispatched": False,
                "surveillance_alert": False
            }
        },
        {
            "complaint_id": "NCRP-2026-088320",
            "case_id": "CASE_88320",
            "registered_at": "28 mins ago",
            "victim_name": "Pooja Hegde",
            "victim_phone": "+91 94401 23091",
            "victim_account": "ACC_0019348",
            "reported_amount": 78000.0,
            "city": "Hyderabad",
            "state": "Telangana",
            "crime_type": "UPI_FRAUD",
            "scammer_upi_or_account": "refund.desk92@icici",
            "status": "MONITORING",
            "digital_hops": [
                {"amount": 78000.0, "time": "09:40", "city": "Hyderabad", "state": "Telangana", "bank_id": "BANK_02", "destination_account": "ACC_0066211"},
                {"amount": 35000.0, "time": "10:02", "city": "Hyderabad", "state": "Telangana", "bank_id": "BANK_06", "destination_account": "ACC_0033109"}
            ],
            "prediction": {
                "mathematical_coords": {"latitude": 17.3850, "longitude": 78.4867},
                "primary_target_city": "Hyderabad",
                "primary_target_state": "Telangana",
                "threat_level": "HIGH",
                "predicted_atms": [
                    {
                        "rank": 1,
                        "atm_id": "ATM_000004",
                        "bank_id": "BANK_02",
                        "city": "Hyderabad",
                        "state": "Telangana",
                        "latitude": 17.403901,
                        "longitude": 78.473854,
                        "distance_km": 2.4,
                        "confidence_pct": 87.2,
                        "operating_24x7": True,
                        "baseline_volume": 1666,
                        "risk_zone": 61,
                        "estimated_cashout_window": "15-35 mins"
                    }
                ]
            },
            "actions_taken": {
                "bank_frozen": True,
                "intercept_dispatched": False,
                "surveillance_alert": True
            }
        }
    ]

    for c in sample_cases:
        LIVE_CASES[c["case_id"]] = c

def add_tactical_log(event_type: str, message: str, meta: Optional[Dict[str, Any]] = None):
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        "event_type": event_type,
        "message": message,
        "meta": meta or {}
    }
    TACTICAL_LOGS.insert(0, entry)
    if len(TACTICAL_LOGS) > 100:
        TACTICAL_LOGS.pop()
