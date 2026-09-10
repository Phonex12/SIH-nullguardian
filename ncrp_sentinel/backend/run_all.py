import sys
import multiprocessing
import uvicorn
from pathlib import Path

def run_citizen_service():
    print("[INIT] Launching Public Citizen Portal on http://127.0.0.1:8000 ...")
    uvicorn.run("app.citizen_main:app", host="127.0.0.1", port=8000, log_level="info")

def run_lea_service():
    print("[INIT] Launching Secure LEA Command Terminal on http://127.0.0.1:9000 ...")
    uvicorn.run("app.lea_main:app", host="127.0.0.1", port=9000, log_level="info")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    print("========================================================================")
    print("   NCRP SENTINEL // DUAL AIR-GAPPED ISOLATED ARCHITECTURE RUNNER")
    print("========================================================================")
    print("   Zone 1 (Public): Citizen Portal & Learning Hub -> http://127.0.0.1:8000/")
    print("   Zone 2 (Secure): LEA Command Terminal          -> http://127.0.0.1:9000/")
    print("   Persistence:     Shared SQLite DB (ncrp_shared.db with WAL mode)")
    print("========================================================================")

    p1 = multiprocessing.Process(target=run_citizen_service)
    p2 = multiprocessing.Process(target=run_lea_service)

    p1.start()
    p2.start()

    try:
        p1.join()
        p2.join()
    except KeyboardInterrupt:
        print("\nStopping all services...")
        p1.terminate()
        p2.terminate()
        p1.join()
        p2.join()
        print("Services stopped.")
