import os
import socket
from pathlib import Path

# Base Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "ncrp_shared.db"

# ML & Dataset Artifacts
MODEL_WEIGHTS_PATH = ROOT_DIR / "atm_trajectory_lstm.pth"
SPATIAL_ARTIFACTS_PATH = ROOT_DIR / "spatial_artifacts.pkl"
ATMS_CSV_PATH = ROOT_DIR / "atms.csv"
COMPLAINTS_CSV_PATH = ROOT_DIR / "complaints.csv"
FRAUD_CASES_CSV_PATH = ROOT_DIR / "fraud_cases.csv"

# Security / JWT Secrets
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "NCRP_SENTINEL_SECRET_KEY_2026_I4C_SECURE")
JWT_ALGORITHM = "HS256"

# Port & Server Configuration
CITIZEN_PORT = int(os.getenv("CITIZEN_PORT", "8000"))
ADMIN_PORT = int(os.getenv("ADMIN_PORT", "9000"))
HOST = "0.0.0.0"

def get_local_ip() -> str:
    """Finds the LAN IP address of this machine for multi-device demos over Wi-Fi / Hotspot."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()
