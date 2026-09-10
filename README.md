# SIH-nullguardian — NCRP Sentinel

> **AI-Driven Proactive Cybercrime Mitigation Framework (I4C & NCRP)**  
> Anticipating and neutralizing physical ATM cashouts from digital cybercrime mule trails before fraud monetization occurs.

---

## 🚀 Quick Start (Run Locally)

### Option 1: One-Click Launch (Windows)
Double-click [`start_portal.bat`](file:///start_portal.bat) in the project root folder.  
This will automatically launch the backend server and open the portal in your default browser.

---

### Option 2: Command Line (PowerShell / Terminal)

1. **Install Dependencies** (if not already installed):
   ```powershell
   pip install -r ncrp_sentinel/backend/requirements.txt
   ```

2. **Start the Platform Server**:
   ```powershell
   python ncrp_sentinel/backend/run.py
   ```

3. **Open in Browser**:
   * **Citizen Cybercrime Reporting Portal**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   * **Law Enforcement (LEA) Command Terminal**: [http://127.0.0.1:8000/lea-terminal](http://127.0.0.1:8000/lea-terminal)
   * **Security Honeypot (/admin Trap)**: [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) *(Returns 403 Forbidden defense screen)*
   * **Interactive API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔑 Test Credentials

### 1. Citizen Portal
* **Aadhaar Number**: Enter any 12 digits (e.g. `5428 9102 4319`).
* **OTP**: Click **"Get OTP"** — the demo sandbox OTP is displayed on screen (or enter `123456`).
* **Autofill Trail**: In Step 3, click **"⚡ Autofill Realistic Case Trail"** to populate a realistic 3-hop money trail (*Mumbai $\rightarrow$ Pune $\rightarrow$ Nashik*).

### 2. Law Enforcement Agency (LEA) Tactical Terminal
* **Officer 1 (I4C / Ministry of Home Affairs)**:
  * Badge ID: `I4C-DEL-892`
  * Passkey: `Sentinel@2026`
* **Officer 2 (Maharashtra Cyber Police)**:
  * Badge ID: `LEA-MUM-441`
  * Passkey: `Sentinel@2026`
* *(Or use the convenient 1-click test login buttons on the login modal)*

---

## 🛡️ Key Features

* **PyTorch ATM Trajectory LSTM**: Forecasts physical ATM cashouts from digital mule transaction hops with KD-Tree nearest neighbor mapping across 7,000 ATMs in India.
* **Citizen Reporting Wizard**: 5-step wizard with Aadhaar OTP authentication, money trail builder, and instant official NCRP complaint generation.
* **Anti-Intrusion Honeypot**: Unauthorized access to `/admin` or administrative endpoints is trapped with a 403 Forbidden warning under Section 66F of the IT Act.
* **LEA Tactical GIS Heatmap**: Interactive Leaflet GIS map with ATM risk heatmap, live incident queue, and trajectory flight paths.
* **Proactive Interventions**:
  1. **1-Click Bank Fund Freeze (CFCFRMS)**
  2. **Dispatch Tactical PCR Intercept**
  3. **ATM Surveillance Camera Alert**

---

## 🧪 Run Automated Verification Tests

To verify the PyTorch model, API routes, security honeypot, and proactive interventions:
```powershell
python ncrp_sentinel/backend/verify_system.py
```
