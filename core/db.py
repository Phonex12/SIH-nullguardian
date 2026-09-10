import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from .config import DB_PATH

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=20.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    """Initializes tables and seeds demo cases, cyber articles, and tactical logs."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Cases Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cases (
        case_id TEXT PRIMARY KEY,
        complaint_id TEXT UNIQUE NOT NULL,
        registered_at TEXT NOT NULL,
        victim_name TEXT NOT NULL,
        victim_phone TEXT NOT NULL,
        victim_account TEXT NOT NULL,
        reported_amount REAL NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        crime_type TEXT NOT NULL,
        scammer_contact TEXT,
        scammer_upi_or_account TEXT,
        incident_description TEXT,
        status TEXT NOT NULL DEFAULT 'LIVE_THREAT',
        digital_hops_json TEXT NOT NULL,
        prediction_json TEXT NOT NULL,
        actions_taken_json TEXT NOT NULL
    );
    """)

    # 2. Tactical Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tactical_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        event_type TEXT NOT NULL,
        message TEXT NOT NULL,
        meta_json TEXT
    );
    """)

    # 3. Active OTPs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS active_otps (
        aadhaar TEXT PRIMARY KEY,
        otp_code TEXT NOT NULL,
        expires_at TEXT NOT NULL
    );
    """)

    # 4. Educational Articles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        read_time TEXT NOT NULL,
        badge TEXT NOT NULL,
        summary TEXT NOT NULL,
        content_md TEXT NOT NULL,
        red_flags_json TEXT NOT NULL,
        prevention_tips_json TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    conn.commit()
    _seed_initial_data(conn)
    _seed_cybercrime_articles(conn)
    conn.close()

def _seed_initial_data(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cases;")
    if cursor.fetchone()[0] == 0:
        sample_cases = [
            {
                "complaint_id": "NCRP-2026-094101",
                "case_id": "CASE_94101",
                "registered_at": "12 mins ago",
                "victim_name": "Rajesh Sharma",
                "victim_phone": "+91 98201 44819",
                "victim_account": "SBIN0004921-998231",
                "reported_amount": 148500.0,
                "city": "Mumbai",
                "state": "Maharashtra",
                "crime_type": "Electricity Bill Update Phishing APK",
                "scammer_contact": "+91 81023 99201",
                "scammer_upi_or_account": "quickbill.support@sbi",
                "incident_description": "Victim received SMS threatening immediate power cut. Downloaded APK which captured NetBanking OTP.",
                "status": "LIVE_THREAT",
                "digital_hops": [
                    {"hop_seq": 1, "account_id": "SBIN0004921-998231", "bank_id": "SBIN", "city": "Mumbai", "state": "Maharashtra", "amount": 148500.0, "time": "14:15", "type": "SOURCE_VICTIM"},
                    {"hop_seq": 2, "account_id": "HDFC0001092-441029", "bank_id": "HDFC", "city": "Pune", "state": "Maharashtra", "amount": 140000.0, "time": "14:22", "type": "MULE_LAYER_1"},
                    {"hop_seq": 3, "account_id": "ICIC0009912-771823", "bank_id": "ICIC", "city": "Surat", "state": "Gujarat", "amount": 135000.0, "time": "14:31", "type": "MULE_LAYER_2"}
                ],
                "prediction": {
                    "mathematical_coords": {"latitude": 21.1702, "longitude": 72.8311},
                    "primary_target_city": "Surat",
                    "primary_target_state": "Gujarat",
                    "threat_level": "CRITICAL",
                    "predicted_atms": [
                        {"rank": 1, "atm_id": "ATM_GJ_SRT_041", "bank_id": "SBIN", "city": "Surat", "state": "Gujarat", "latitude": 21.17024, "longitude": 72.83106, "distance_km": 0.42, "confidence_pct": 94.2, "operating_24x7": True, "baseline_volume": 420, "risk_zone": 91, "estimated_cashout_window": "15-35 mins"},
                        {"rank": 2, "atm_id": "ATM_GJ_SRT_109", "bank_id": "HDFC", "city": "Surat", "state": "Gujarat", "latitude": 21.17511, "longitude": 72.83680, "distance_km": 1.15, "confidence_pct": 82.7, "operating_24x7": True, "baseline_volume": 310, "risk_zone": 84, "estimated_cashout_window": "20-40 mins"}
                    ]
                },
                "actions_taken": [
                    {"action": "AI Trajectory Calculated", "timestamp": "14:31:05", "operator": "SYSTEM_AI", "details": "High risk cashout predicted at Surat Ring Road ATM cluster."}
                ]
            },
            {
                "complaint_id": "NCRP-2026-094102",
                "case_id": "CASE_94102",
                "registered_at": "35 mins ago",
                "victim_name": "Pooja Hegde",
                "victim_phone": "+91 97412 88310",
                "victim_account": "KKBK0008129-112094",
                "reported_amount": 75000.0,
                "city": "Bengaluru",
                "state": "Karnataka",
                "crime_type": "Digital Arrest / Fake CBI Video Call",
                "scammer_contact": "+91 99014 33219",
                "scammer_upi_or_account": "cbi.clearance.dept@icici",
                "incident_description": "Scammer posed as DCP Crime Branch on WhatsApp video call, demanding immediate security deposit.",
                "status": "PCR_DISPATCHED",
                "digital_hops": [
                    {"hop_seq": 1, "account_id": "KKBK0008129-112094", "bank_id": "KKBK", "city": "Bengaluru", "state": "Karnataka", "amount": 75000.0, "time": "13:40", "type": "SOURCE_VICTIM"},
                    {"hop_seq": 2, "account_id": "AXIS0004910-332198", "bank_id": "UTIB", "city": "Hosur", "state": "Tamil Nadu", "amount": 72000.0, "time": "13:55", "type": "MULE_LAYER_1"}
                ],
                "prediction": {
                    "mathematical_coords": {"latitude": 12.7409, "longitude": 77.8253},
                    "primary_target_city": "Hosur",
                    "primary_target_state": "Tamil Nadu",
                    "threat_level": "HIGH",
                    "predicted_atms": [
                        {"rank": 1, "atm_id": "ATM_TN_HSR_019", "bank_id": "UTIB", "city": "Hosur", "state": "Tamil Nadu", "latitude": 12.7412, "longitude": 77.8260, "distance_km": 0.88, "confidence_pct": 88.5, "operating_24x7": True, "baseline_volume": 250, "risk_zone": 79, "estimated_cashout_window": "10-30 mins"}
                    ]
                },
                "actions_taken": [
                    {"action": "Mule Account Auto-Flagged", "timestamp": "13:56:10", "operator": "SYSTEM_I4C", "details": "Account AXIS0004910-332198 flagged under NCRP Section 43."},
                    {"action": "PCR Unit Dispatched", "timestamp": "14:02:15", "operator": "OFFICER_DELHI_007", "details": "PCR Unit Delta-4 redirected to Hosur Bus Stand SBI/Axis ATM."}
                ]
            }
        ]

        for case in sample_cases:
            cursor.execute("""
            INSERT INTO cases (
                case_id, complaint_id, registered_at, victim_name, victim_phone,
                victim_account, reported_amount, city, state, crime_type,
                scammer_contact, scammer_upi_or_account, incident_description,
                status, digital_hops_json, prediction_json, actions_taken_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                case["case_id"],
                case["complaint_id"],
                case["registered_at"],
                case["victim_name"],
                case["victim_phone"],
                case["victim_account"],
                case["reported_amount"],
                case["city"],
                case["state"],
                case["crime_type"],
                case["scammer_contact"],
                case["scammer_upi_or_account"],
                case["incident_description"],
                case["status"],
                json.dumps(case["digital_hops"]),
                json.dumps(case["prediction"]),
                json.dumps(case["actions_taken"])
            ))

        # Initial Tactical Logs
        cursor.execute("""
        INSERT INTO tactical_logs (timestamp, event_type, message, meta_json)
        VALUES 
        (?, 'SYS_INIT', 'NCRP Sentinel Engine initialized with AI Trajectory Inference active.', '{}'),
        (?, 'CASE_INGEST', 'Live threat case CASE_94101 ingested from Mumbai Cyber Cell.', '{"case_id": "CASE_94101"}'),
        (?, 'PATROL_DISPATCH', 'PCR Delta-4 dispatched to predicted ATM in Hosur.', '{"case_id": "CASE_94102"}');
        """, (
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()

def _seed_cybercrime_articles(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles;")
    if cursor.fetchone()[0] == 0:
        articles = [
            {
                "slug": "digital-arrest-scam-modality",
                "title": "Anatomy of Digital Arrest Scams: Modus Operandi & Verification",
                "category": "High Threat Advisory",
                "read_time": "4 min read",
                "badge": "CRITICAL",
                "summary": "Fraudsters impersonate Law Enforcement Agencies (CBI, ED, State Police) over WhatsApp/Skype video calls to extort money.",
                "content_md": "### Modus Operandi\n\n1. **The Intimidation Call**: Fraudsters contact victims claiming a parcel containing narcotics or illegal IDs has been seized at customs.\n2. **Fake Police Setup**: Video calls are initiated showing a fake police backdrop, uniforms, and forged warrant documents.\n3. **Isolation & Coercion**: The victim is forced to remain on video call ('digital custody') and transfer funds to a 'government verification account'.\n\n### Official Clarification\nIndian Law Enforcement Agencies and Judicial Courts **NEVER** conduct arrests, investigations, or demand security deposits over video calls.",
                "red_flags": [
                    "Demands to stay on continuous video call in a closed room",
                    "Threats of immediate arrest without physical summons",
                    "Demands for money transfer to verify account legitimacy"
                ],
                "prevention_tips": [
                    "Immediately disconnect video calls claiming to be from CBI or Police",
                    "Call 1930 Cyber Helpline or local police station directly",
                    "Never share bank credentials or transfer funds to any 'verification' account"
                ]
            },
            {
                "slug": "mule-account-recruitment-prevention",
                "title": "Mule Accounts: How Cyber Syndicates Weaponize Bank Accounts",
                "category": "Awareness & Law",
                "read_time": "3 min read",
                "badge": "LEGAL RISK",
                "summary": "Renting out or selling your bank account makes you an active accomplice in cybercrime under Indian IT Act & PMLA.",
                "content_md": "### What is a Money Mule Account?\nA money mule is someone who transfers illegally acquired money on behalf of others.\n\n### How Victims are Trapped\n- Fake work-from-home job offers promising commission on receiving and forwarding UPI transfers.\n- Telegram crypto investment groups asking for bank details for 'P2P arbitrage'.\n\n### Legal Consequences\nAccount holders face freezing of all personal accounts, CIBIL blacklisting, and arrest under Section 66D IT Act.",
                "red_flags": [
                    "Offers to pay commission for receiving funds in your personal UPI",
                    "Unknown individuals asking to use your ATM card for high-value withdrawals",
                    "Job offers requiring you to pass through company payments via personal account"
                ],
                "prevention_tips": [
                    "Never allow anyone else to operate your bank account or ATM card",
                    "Report any unsolicited credit in your bank account immediately to your bank",
                    "Refuse all commission-based fund routing offers on social media"
                ]
            }
        ]

        for art in articles:
            cursor.execute("""
            INSERT INTO articles (
                slug, title, category, read_time, badge, summary,
                content_md, red_flags_json, prevention_tips_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                art["slug"], art["title"], art["category"], art["read_time"], art["badge"],
                art["summary"], art["content_md"], json.dumps(art["red_flags"]),
                json.dumps(art["prevention_tips"]), datetime.now(timezone.utc).isoformat()
            ))
        conn.commit()

# --- Database Access API ---

def get_all_cases() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases ORDER BY rowid DESC;")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "case_id": r["case_id"],
            "complaint_id": r["complaint_id"],
            "registered_at": r["registered_at"],
            "victim_name": r["victim_name"],
            "victim_phone": r["victim_phone"],
            "victim_account": r["victim_account"],
            "reported_amount": r["reported_amount"],
            "city": r["city"],
            "state": r["state"],
            "crime_type": r["crime_type"],
            "scammer_contact": r["scammer_contact"],
            "scammer_upi_or_account": r["scammer_upi_or_account"],
            "incident_description": r["incident_description"],
            "status": r["status"],
            "digital_hops": json.loads(r["digital_hops_json"]),
            "prediction": json.loads(r["prediction_json"]),
            "actions_taken": json.loads(r["actions_taken_json"])
        })
    return results

def get_case_by_id(case_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE case_id = ? OR complaint_id = ?;", (case_id, case_id))
    r = cursor.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "case_id": r["case_id"],
        "complaint_id": r["complaint_id"],
        "registered_at": r["registered_at"],
        "victim_name": r["victim_name"],
        "victim_phone": r["victim_phone"],
        "victim_account": r["victim_account"],
        "reported_amount": r["reported_amount"],
        "city": r["city"],
        "state": r["state"],
        "crime_type": r["crime_type"],
        "scammer_contact": r["scammer_contact"],
        "scammer_upi_or_account": r["scammer_upi_or_account"],
        "incident_description": r["incident_description"],
        "status": r["status"],
        "digital_hops": json.loads(r["digital_hops_json"]),
        "prediction": json.loads(r["prediction_json"]),
        "actions_taken": json.loads(r["actions_taken_json"])
    }

def create_case(case_data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO cases (
        case_id, complaint_id, registered_at, victim_name, victim_phone,
        victim_account, reported_amount, city, state, crime_type,
        scammer_contact, scammer_upi_or_account, incident_description,
        status, digital_hops_json, prediction_json, actions_taken_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        case_data["case_id"],
        case_data["complaint_id"],
        case_data.get("registered_at", "Just now"),
        case_data["victim_name"],
        case_data["victim_phone"],
        case_data["victim_account"],
        case_data["reported_amount"],
        case_data["city"],
        case_data["state"],
        case_data["crime_type"],
        case_data.get("scammer_contact", ""),
        case_data.get("scammer_upi_or_account", ""),
        case_data.get("incident_description", ""),
        case_data.get("status", "LIVE_THREAT"),
        json.dumps(case_data.get("digital_hops", [])),
        json.dumps(case_data.get("prediction", {})),
        json.dumps(case_data.get("actions_taken", []))
    ))

    # Log ingestion event
    cursor.execute("""
    INSERT INTO tactical_logs (timestamp, event_type, message, meta_json)
    VALUES (?, 'CASE_CREATED', ?, ?);
    """, (
        datetime.now(timezone.utc).isoformat(),
        f"New cyber complaint {case_data['complaint_id']} filed for ₹{case_data['reported_amount']:,.2f}.",
        json.dumps({"case_id": case_data["case_id"], "city": case_data["city"]})
    ))

    conn.commit()
    conn.close()
    return case_data

def update_case_action(case_id: str, new_status: str, action_entry: Dict[str, Any]) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT actions_taken_json FROM cases WHERE case_id = ?;", (case_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    actions = json.loads(row["actions_taken_json"])
    actions.append(action_entry)

    cursor.execute("""
    UPDATE cases
    SET status = ?, actions_taken_json = ?
    WHERE case_id = ?;
    """, (new_status, json.dumps(actions), case_id))

    cursor.execute("""
    INSERT INTO tactical_logs (timestamp, event_type, message, meta_json)
    VALUES (?, 'INTERVENTION_TRIGGERED', ?, ?);
    """, (
        datetime.now(timezone.utc).isoformat(),
        f"Action '{action_entry.get('action')}' executed on {case_id}: {action_entry.get('details')}",
        json.dumps({"case_id": case_id, "operator": action_entry.get("operator")})
    ))

    conn.commit()
    conn.close()
    return True

def store_otp(aadhaar: str, otp_code: str, expires_at: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO active_otps (aadhaar, otp_code, expires_at)
    VALUES (?, ?, ?);
    """, (aadhaar, otp_code, expires_at))
    conn.commit()
    conn.close()

def verify_and_clear_otp(aadhaar: str, otp_code: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT otp_code, expires_at FROM active_otps WHERE aadhaar = ?;", (aadhaar,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    stored_code = row["otp_code"]
    expires_at = datetime.fromisoformat(row["expires_at"])
    now = datetime.now(timezone.utc)

    if stored_code == otp_code and now <= expires_at:
        cursor.execute("DELETE FROM active_otps WHERE aadhaar = ?;", (aadhaar,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def get_tactical_logs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tactical_logs ORDER BY id DESC LIMIT ?;", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r["id"],
            "timestamp": r["timestamp"],
            "event_type": r["event_type"],
            "message": r["message"],
            "meta": json.loads(r["meta_json"] or "{}")
        }
        for r in rows
    ]

def get_articles() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles ORDER BY id ASC;")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "slug": r["slug"],
            "title": r["title"],
            "category": r["category"],
            "read_time": r["read_time"],
            "badge": r["badge"],
            "summary": r["summary"],
            "content_md": r["content_md"],
            "red_flags": json.loads(r["red_flags_json"]),
            "prevention_tips": json.loads(r["prevention_tips_json"]),
            "updated_at": r["updated_at"]
        }
        for r in rows
    ]
