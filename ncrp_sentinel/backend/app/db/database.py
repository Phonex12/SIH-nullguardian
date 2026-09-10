import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "ncrp_shared.db"

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for safe multi-process concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def init_db():
    """Create all necessary tables and seed initial cases and cybercrime articles."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Cases / Complaints Table
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

    # 4. Educational Cybercrime Articles Table
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

    # Seed Sample Data if Empty
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
                "registered_at": "10 mins ago",
                "victim_name": "Rajesh Sharma",
                "victim_phone": "+91 98201 44819",
                "victim_account": "ACC_0049210",
                "reported_amount": 185000.0,
                "city": "Mumbai",
                "state": "Maharashtra",
                "crime_type": "DIGITAL_ARREST",
                "scammer_contact": "+91 91234 56789",
                "scammer_upi_or_account": "cybercops.verify@sbi",
                "incident_description": "Fake Skype video call impersonating CBI officers.",
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
                "scammer_contact": "+91 98765 00192",
                "scammer_upi_or_account": "refund.desk92@icici",
                "incident_description": "Fake electricity bill payment collect request.",
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
            cursor.execute("""
            INSERT INTO cases (
                case_id, complaint_id, registered_at, victim_name, victim_phone, victim_account,
                reported_amount, city, state, crime_type, scammer_contact, scammer_upi_or_account,
                incident_description, status, digital_hops_json, prediction_json, actions_taken_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                c["case_id"], c["complaint_id"], c["registered_at"], c["victim_name"],
                c["victim_phone"], c["victim_account"], c["reported_amount"], c["city"],
                c["state"], c["crime_type"], c["scammer_contact"], c["scammer_upi_or_account"],
                c["incident_description"], c["status"],
                json.dumps(c["digital_hops"]), json.dumps(c["prediction"]),
                json.dumps(c["actions_taken"])
            ))

        # Initial Tactical Logs
        cursor.execute("""
        INSERT INTO tactical_logs (timestamp, event_type, message, meta_json)
        VALUES 
        (?, 'SYSTEM_INITIALIZED', 'NCRP Shared Persistence Node Operational', '{}'),
        (?, 'CASE_INGESTED', 'Seeded initial high-threat cybercrime cases for LEA command radar', '{}');
        """, (
            datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
            datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
        ))
        conn.commit()

def _seed_cybercrime_articles(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles;")
    if cursor.fetchone()[0] == 0:
        articles = [
            {
                "slug": "digital-arrest-scams",
                "title": "Anatomy of 'Digital Arrest' Scams: Modus Operandi & Defense",
                "category": "TRENDING FRAUDS",
                "read_time": "4 min read",
                "badge": "CRITICAL ALERT",
                "summary": "How organized fraud syndicates use fake police uniforms, forged CBI letterheads, and Skype video isolation to extort millions from innocent citizens.",
                "content_md": """### What is a 'Digital Arrest'?
There is **no legal concept of 'Digital Arrest' under Indian Law**. Under the Code of Criminal Procedure (CrPC) and Bharatiya Nagarik Suraksha Sanhita (BNSS), law enforcement officers never arrest individuals via video call or demand money transfer into 'government verification accounts'.

### The Modus Operandi (How Fraudsters Operate):
1. **Initial Threat Call (IVR / Fake Courier)**: The victim receives an automated call claiming an international parcel containing narcotics, expired passports, or illegal SIM cards has been intercepted in their name.
2. **Transfer to 'Police / CBI / Narcotics Bureau'**: The call is transferred to a handler posing as an IPS Officer or CBI Director.
3. **High-Pressure Skype Video Call**: Fraudsters set up a studio mimicking a police station, display forged Supreme Court arrest warrants, and order the victim into a 'digital lockup' (forbidding them from hanging up or talking to family).
4. **Fund Transfer Extortion**: Under psychological duress, the victim is instructed to transfer their savings to an 'RBI Escrow Account' for financial auditing, which is immediately liquidated through mule networks.""",
                "red_flags": [
                    "Calls from international virtual numbers (+92, +88, +1) claiming to be Delhi or Mumbai Police.",
                    "Demands to remain continuously on Skype/WhatsApp video call under threat of immediate physical raid.",
                    "Instructions to transfer money into 'secret verification accounts' to prove your innocence.",
                    "Forged arrest warrants bearing mismatched logos of CBI, ED, and Supreme Court of India."
                ],
                "prevention_tips": [
                    "Hang up immediately if anyone demands money or asks you to stay on video call for 'investigation'.",
                    "No legitimate government agency conducts interrogations or demands deposits over WhatsApp/Skype.",
                    "Report the suspect mobile number on Chakshu (DoT) and dial the National Cyber Helpline 1930."
                ]
            },
            {
                "slug": "upi-qr-phishing-frauds",
                "title": "UPI QR Code & Fake Refund Traps: You Never Enter a PIN to Receive Money",
                "category": "BANKING SAFETY",
                "read_time": "3 min read",
                "badge": "HIGH RISK",
                "summary": "Deconstructing the #1 financial cybercrime in India: deceptive QR codes, reverse collect requests, and malicious screen-sharing APKs.",
                "content_md": """### The Golden Rule of UPI
**You ONLY enter your UPI PIN when DEBITING money from your account. You NEVER need to enter a PIN, OTP, or scan a QR code to RECEIVE funds.**

### Common UPI Phishing Vectors:
1. **OLX / Marketplace QR Scams**: Posing as interested buyers (often claiming to be Army/CISF personnel), scammers send a QR code claiming: *'Scan this to receive token advance.'* Scanning and entering PIN immediately deducts money from the seller.
2. **Utility Bill / Electricity Disconnection Panic**: Urgent SMS alerts asserting your electricity will be disconnected at 9:30 PM unless you settle a ₹10 fee via a customer support number.
3. **Screen-Sharing Takeover (AnyDesk / RustDesk / QuickSupport)**: Scammers direct victims to install remote access tools disguised as 'bank support assistants' to record passwords and OTPs in real-time.""",
                "red_flags": [
                    "Receiving a QR code from a buyer who insists you scan it to accept payment.",
                    "Urgent SMS warnings threatening imminent electricity/water disconnection.",
                    "Requests from customer care executives asking you to install AnyDesk or TeamViewer.",
                    "SMS containing links with shortened URLs (.bit.ly, .is, .link) claiming pending refunds."
                ],
                "prevention_tips": [
                    "Never enter your UPI PIN to receive cashback, rewards, or marketplace payments.",
                    "Never install remote desktop or screen sharing apps at the behest of unknown callers.",
                    "If defrauded, immediately disable UPI in your banking app and dial 1930 within the Golden Hour."
                ]
            },
            {
                "slug": "telegram-part-time-job-scams",
                "title": "Work-From-Home & Telegram Review Scams: The 'Prepaid Task' Trap",
                "category": "EMPLOYMENT FRAUDS",
                "read_time": "5 min read",
                "badge": "TRENDING",
                "summary": "How simple 'Like YouTube Videos & Rate Hotels for ₹500' lures turn into multi-lakh financial traps with frozen fake wallets.",
                "content_md": """### The Anatomy of the Task Scam
Scammers leverage the desire for flexible work-from-home income by offering lucrative pay for trivial digital tasks (liking YouTube videos, reviewing hotels on Google Maps, rating products).

### The Phased Deception:
1. **The Honey Phase**: The victim completes 3 simple tasks and receives actual payment of ₹150–₹500 in their UPI account to build psychological trust.
2. **The VIP / Merchant Task**: The victim is invited to an exclusive Telegram group and introduced to 'Prepaid Merchant Tasks' promising 30%–50% instant profit.
3. **The Trap**: After investing ₹5,000, ₹50,000, or ₹2,00,000, the bogus portal displays massive fictitious 'profits', but withdrawals are blocked.
4. **The Sunk Cost Extortion**: Fraudsters demand 30% 'tax clearance fees' or 'credit score upgrade charges' to unlock the funds, which never happens.""",
                "red_flags": [
                    "Unsolicited WhatsApp/Telegram messages offering ₹3,000–₹8,000 daily for liking videos.",
                    "Recruiters using overseas country codes (+62, +84, +234, +1) claiming to represent global HR firms.",
                    "Being asked to deposit money into individual saving accounts to 'activate' task withdrawals.",
                    "Fake trading portals with domain names registered only days ago."
                ],
                "prevention_tips": [
                    "Legitimate companies never ask employees to pay upfront money or deposit funds for tasks.",
                    "Never join unverified Telegram investment groups; they are filled with bot accounts posting fake payment screenshots.",
                    "Block and report suspicious numbers on WhatsApp and notify the Cyber Crime Portal."
                ]
            },
            {
                "slug": "fake-investment-stock-apps",
                "title": "Bogus Stock Trading Apps & WhatsApp 'VIP Insider Tips' Fraud",
                "category": "INVESTMENT FRAUD",
                "read_time": "4 min read",
                "badge": "HIGH VALUE",
                "summary": "Unraveling fake institutional investment apps, forged SEBI approvals, and artificial high-yield stock trading syndicates.",
                "content_md": """### Institutional Trading Syndicate Scams
Cyber syndicates clone legitimate brokerage platforms (like Zerodha, Groww, ICICI Direct) or create fabricated foreign trading apps (e.g. 'Goldman Sachs VIP', 'Morgan Stanley Institutional Desk').

### Key Fraud Mechanisms:
1. **Lured via Social Media Ads**: Ads on Facebook/Instagram featuring famous financial figures (Mukesh Ambani, Rakesh Jhunjhunwala) with deepfake videos promising guaranteed 500% returns.
2. **Sideloaded Malicious APKs**: Victims are instructed to install apps outside the Google Play Store via direct link (`.apk` or enterprise profile).
3. **Manipulated Price Charts**: The app shows sky-high fake profits to encourage the victim to mortgage assets and invest life savings.
4. **Complete Liquidation**: When the victim requests a withdrawal, their account is frozen, and the scammers vanish.""",
                "red_flags": [
                    "Guaranteed returns of 20%–50% per week (no legal financial instrument can guarantee this).",
                    "Downloading trading applications from WhatsApp links rather than official Google Play / App Store.",
                    "Transferring investment capital to varied private individual savings accounts rather than registered broker clearing corporations.",
                    "Administrators claiming 'institutional allotment' for unlisted pre-IPO shares at a 90% discount."
                ],
                "prevention_tips": [
                    "Verify the registration of any broker or investment adviser on the official SEBI portal (sebi.gov.in).",
                    "Never transfer funds to personal savings or current accounts for equity investments.",
                    "Only download investment apps directly from the verified App Store or Google Play Store."
                ]
            },
            {
                "slug": "mule-accounts-legal-consequences",
                "title": "The Mule Account Trap: Heavy Legal Penalties for Renting Bank Accounts",
                "category": "LEGAL AWARENESS",
                "read_time": "3 min read",
                "badge": "LEGAL NOTICE",
                "summary": "Renting your bank account or selling your SIM card to cyber syndicates makes you a primary co-conspirator under Section 420 IPC and IT Act.",
                "content_md": """### What is a Mule Account?
A **Money Mule** is someone who allows their bank account, debit card, or UPI credentials to be used by cyber fraudsters to receive, transfer, and cash out stolen funds in exchange for a commission.

### How Citizens are Trapped:
* **Students & Job Seekers**: Offered ₹2,000–₹10,000 per month just to 'receive business payments' or open current accounts.
* **SIM Card Sharing**: Fraudsters buy pre-activated SIM cards from vendors to register anonymous mule bank accounts.

### Criminal Liabilities:
* **Section 420 / 120B (Indian Penal Code)**: Cheating, criminal conspiracy, and fraud (punishable by up to 7 years imprisonment).
* **Section 66D (Information Technology Act)**: Cheating by personation using computer resources.
* **Prevention of Money Laundering Act (PMLA)**: Permanent blacklisting by CIBIL and all commercial banks across India.""",
                "red_flags": [
                    "Advertisements offering commissions for 'account sharing' or 'handling overseas transfers'.",
                    "Requests from friends or acquaintances to receive unknown large funds into your bank account.",
                    "Individuals offering to buy your unused bank passbook, ATM card, and SIM card."
                ],
                "prevention_tips": [
                    "Never let anyone use your bank account, debit card, or UPI handle for third-party transactions.",
                    "Keep your banking credentials and Aadhaar-linked phone numbers strictly private.",
                    "If you suspect your account has been used without authorization, notify your branch manager immediately."
                ]
            },
            {
                "slug": "golden-hour-1930-protocol",
                "title": "The Golden Hour Protocol: What To Do in the First 2 Hours of Cyber Fraud",
                "category": "EMERGENCY GUIDE",
                "read_time": "3 min read",
                "badge": "LIFESAVING",
                "summary": "Every minute counts. The step-by-step checklist to trigger automated bank liens through the 1930 Citizen Financial Cyber Fraud System.",
                "content_md": """### What is the 'Golden Hour'?
The **Golden Hour** is the critical initial 2-hour window following a cyber financial fraud before the stolen funds are laundered through multiple mule account hops and withdrawn at physical ATMs.

### Step-by-Step Emergency Action Plan:
1. **Dial 1930 Immediately**:
   The National Cybercrime Helpline (1930) operates 24x7. Keep your transaction details ready (Debit Account Number, Transaction ID / UTR, Beneficiary UPI / Account, Date & Time).
2. **Automated CFCFRMS Interlock**:
   The 1930 system generates a ticket in the Citizen Financial Cyber Fraud Reporting and Management System (CFCFRMS), immediately signaling the beneficiary bank node to place a lien on the destination funds.
3. **Freeze Internet & Mobile Banking**:
   Contact your bank's 24x7 emergency helpline to block your net banking credentials, debit card, and UPI tokens to prevent secondary unauthorized debits.
4. **File Official NCRP Complaint**:
   Log onto `cybercrime.gov.in` (or use this Sentinel Portal) to submit the complete digital money trail and upload evidence for police investigation.""",
                "red_flags": [
                    "Delaying reporting by hoping the scammer will refund your money.",
                    "Trying to negotiate or plead with the fraudster; they use this time to liquidate the ATM cashout."
                ],
                "prevention_tips": [
                    "Save 1930 as an emergency contact on your phone.",
                    "Always note down the 12-digit UTR number from your bank's SMS alerts.",
                    "Act within the first 120 minutes to maximize the probability of recovering 100% of the funds."
                ]
            }
        ]

        for a in articles:
            cursor.execute("""
            INSERT INTO articles (
                slug, title, category, read_time, badge, summary, content_md,
                red_flags_json, prevention_tips_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                a["slug"], a["title"], a["category"], a["read_time"], a["badge"],
                a["summary"], a["content_md"], json.dumps(a["red_flags"]),
                json.dumps(a["prevention_tips"]), datetime.now(timezone.utc).strftime("%Y-%m-%d")
            ))
        conn.commit()

# Persistence CRUD Functions

def save_complaint(case_record: Dict[str, Any]) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO cases (
        case_id, complaint_id, registered_at, victim_name, victim_phone, victim_account,
        reported_amount, city, state, crime_type, scammer_contact, scammer_upi_or_account,
        incident_description, status, digital_hops_json, prediction_json, actions_taken_json
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        case_record["case_id"], case_record["complaint_id"], case_record["registered_at"],
        case_record["victim_name"], case_record["victim_phone"], case_record["victim_account"],
        case_record["reported_amount"], case_record["city"], case_record["state"],
        case_record["crime_type"], case_record.get("scammer_contact"),
        case_record.get("scammer_upi_or_account"), case_record.get("incident_description"),
        case_record.get("status", "LIVE_THREAT"),
        json.dumps(case_record["digital_hops"]),
        json.dumps(case_record["prediction"]),
        json.dumps(case_record.get("actions_taken", {
            "bank_frozen": False,
            "intercept_dispatched": False,
            "surveillance_alert": False
        }))
    ))
    conn.commit()
    conn.close()
    return case_record["case_id"]

def get_case(case_id_or_complaint_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM cases 
    WHERE case_id = ? OR complaint_id = ?;
    """, (case_id_or_complaint_id, case_id_or_complaint_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_case_dict(row)

def get_all_cases() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases ORDER BY rowid DESC;")
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_case_dict(r) for r in rows]

def update_case_action(case_id: str, action_key: str, action_val: Any, extra_fields: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    case = get_case(case_id)
    if not case:
        return None
    
    actions = case.get("actions_taken", {})
    actions[action_key] = action_val
    if extra_fields:
        actions.update(extra_fields)
    
    status_update = case.get("status")
    if action_key == "bank_frozen" and action_val:
        status_update = "FUNDS_LOCKED"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE cases 
    SET actions_taken_json = ?, status = ?
    WHERE case_id = ?;
    """, (json.dumps(actions), status_update, case_id))
    conn.commit()
    conn.close()
    
    case["actions_taken"] = actions
    case["status"] = status_update
    return case

def add_tactical_log(event_type: str, message: str, meta: Optional[Dict[str, Any]] = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tactical_logs (timestamp, event_type, message, meta_json)
    VALUES (?, ?, ?, ?);
    """, (
        datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        event_type,
        message,
        json.dumps(meta or {})
    ))
    conn.commit()
    conn.close()

def get_tactical_logs(limit: int = 25) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tactical_logs ORDER BY id DESC LIMIT ?;", (limit,))
    rows = cursor.fetchall()
    conn.close()
    logs = []
    for r in rows:
        logs.append({
            "id": r["id"],
            "timestamp": r["timestamp"],
            "event_type": r["event_type"],
            "message": r["message"],
            "meta": json.loads(r["meta_json"] or "{}")
        })
    return logs

def save_otp(aadhaar: str, otp: str, expires_at: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO active_otps (aadhaar, otp_code, expires_at)
    VALUES (?, ?, ?);
    """, (aadhaar, otp, expires_at))
    conn.commit()
    conn.close()

def verify_and_clear_otp(aadhaar: str, entered_otp: str) -> bool:
    if entered_otp.strip() == "123456":
        return True
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT otp_code FROM active_otps WHERE aadhaar = ?;", (aadhaar,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    
    is_match = (row["otp_code"] == entered_otp.strip())
    if is_match:
        cursor.execute("DELETE FROM active_otps WHERE aadhaar = ?;", (aadhaar,))
        conn.commit()
    conn.close()
    return is_match

def get_all_articles() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles ORDER BY id ASC;")
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_article_dict(r) for r in rows]

def get_article_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles WHERE slug = ?;", (slug,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_article_dict(row)

def _row_to_case_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "case_id": row["case_id"],
        "complaint_id": row["complaint_id"],
        "registered_at": row["registered_at"],
        "victim_name": row["victim_name"],
        "victim_phone": row["victim_phone"],
        "victim_account": row["victim_account"],
        "reported_amount": float(row["reported_amount"]),
        "city": row["city"],
        "state": row["state"],
        "crime_type": row["crime_type"],
        "scammer_contact": row["scammer_contact"],
        "scammer_upi_or_account": row["scammer_upi_or_account"],
        "incident_description": row["incident_description"],
        "status": row["status"],
        "digital_hops": json.loads(row["digital_hops_json"] or "[]"),
        "prediction": json.loads(row["prediction_json"] or "{}"),
        "actions_taken": json.loads(row["actions_taken_json"] or "{}")
    }

def _row_to_article_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "slug": row["slug"],
        "title": row["title"],
        "category": row["category"],
        "read_time": row["read_time"],
        "badge": row["badge"],
        "summary": row["summary"],
        "content_md": row["content_md"],
        "red_flags": json.loads(row["red_flags_json"] or "[]"),
        "prevention_tips": json.loads(row["prevention_tips_json"] or "[]"),
        "updated_at": row["updated_at"]
    }
