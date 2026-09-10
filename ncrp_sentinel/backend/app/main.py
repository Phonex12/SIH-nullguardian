from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import FRONTEND_DIR
from .security.honeypot import HoneypotMiddleware
from .routes import (
    auth_router,
    citizen_router,
    lea_router,
    alert_router,
    init_sample_cases
)
from .ml.predictor import ATMPredictor
from .ml.hotspot_engine import HotspotEngine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warmup AI models and dataset caches
    print("[STARTUP] Pre-loading PyTorch ATM Trajectory LSTM and KD-Tree...")
    ATMPredictor.get_instance()
    print("[STARTUP] Pre-loading Hotspot Engine and ATM Geospatial records...")
    HotspotEngine.get_instance()
    print("[STARTUP] Seeding initial tactical cybercrime cases...")
    init_sample_cases()
    print("[READY] NCRP Sentinel AI Defense System is operational.")
    yield

app = FastAPI(
    title="NCRP Sentinel - Proactive Cybercrime Mitigation Framework (I4C)",
    description="AI/ML-driven predictive framework forecasting physical ATM cashout locations from cybercrime mule hops to empower Law Enforcement Agencies & Financial Institutions.",
    version="2.0.0",
    lifespan=lifespan
)

# 1. Register Anti-Intrusion Honeypot Middleware (Must be before routes)
app.add_middleware(HoneypotMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Register API Routers
app.include_router(auth_router)
app.include_router(citizen_router)
app.include_router(lea_router)
app.include_router(alert_router)

# 4. Mount Static Frontend Assets
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# 5. Serve User Interfaces
@app.get("/", tags=["UI"])
def serve_citizen_portal():
    return FileResponse(FRONTEND_DIR / "citizen" / "index.html")

@app.get("/citizen", tags=["UI"])
def serve_citizen_alias():
    return FileResponse(FRONTEND_DIR / "citizen" / "index.html")

@app.get("/lea-terminal", tags=["UI"])
def serve_lea_terminal():
    return FileResponse(FRONTEND_DIR / "lea" / "index.html")

@app.get("/i4c-command", tags=["UI"])
def serve_i4c_alias():
    return FileResponse(FRONTEND_DIR / "lea" / "index.html")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "NCRP Sentinel Engine",
        "version": "2.0.0",
        "i4c_protocol": "ACTIVE"
    }
