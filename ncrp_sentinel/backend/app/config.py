import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "ncrp_sentinel" / "frontend"

# ML & Data Artifact Paths
MODEL_WEIGHTS_PATH = BASE_DIR / "atm_trajectory_lstm.pth"
SPATIAL_ARTIFACTS_PATH = BASE_DIR / "spatial_artifacts.pkl"
ATMS_CSV_PATH = BASE_DIR / "atms.csv"
COMPLAINTS_CSV_PATH = BASE_DIR / "complaints.csv"
FRAUD_CASES_CSV_PATH = BASE_DIR / "fraud_cases.csv"
FRAUD_TRANSACTIONS_CSV_PATH = BASE_DIR / "fraud_transactions.csv"
ACCOUNTS_CSV_PATH = BASE_DIR / "accounts.csv"

# Auth / JWT Config
SECRET_KEY = os.environ.get("NCRP_SECRET_KEY", "ncrp_i4c_sentinel_hypersecure_token_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12 # 12 hours

# Server Config
HOST = "127.0.0.1"
PORT = 8000
