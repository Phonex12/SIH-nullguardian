import sys
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_all import run_citizen_service, run_lea_service
import multiprocessing

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
