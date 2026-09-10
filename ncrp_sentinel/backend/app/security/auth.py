from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

security = HTTPBearer(auto_error=False)

# In-memory OTP storage for demo: {aadhaar: {"otp": str, "expires_at": datetime}}
ACTIVE_OTPS: Dict[str, Dict[str, Any]] = {}

# Authorized LEA Officer Directory for tactical access
AUTHORIZED_LEA_OFFICERS = {
    "I4C-DEL-892": {
        "password": "Sentinel@2026",
        "name": "Inspector Vikram Malhotra",
        "rank": "Cyber Intelligence Unit Lead",
        "agency": "I4C / Ministry of Home Affairs",
        "jurisdiction": "National / North Zone"
    },
    "LEA-MUM-441": {
        "password": "Sentinel@2026",
        "name": "ACP Ananya Deshmukh",
        "rank": "Cyber Financial Crime Officer",
        "agency": "Maharashtra Cyber Police",
        "jurisdiction": "Western Zone"
    },
    "LEA-HYD-318": {
        "password": "Sentinel@2026",
        "name": "DSP R. K. Varma",
        "rank": "Special Operations Commander",
        "agency": "Telangana Cyber Security Bureau",
        "jurisdiction": "Southern Zone"
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please re-authenticate."
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid security token credentials."
        )

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided."
        )
    return decode_access_token(credentials.credentials)

def require_lea_officer(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "LEA_OFFICER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted. Law Enforcement Officer credentials required."
        )
    return user
