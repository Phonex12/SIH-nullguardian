import uvicorn

if __name__ == "__main__":
    print("================================================================")
    print("   NCRP SENTINEL // PUBLIC CITIZEN SERVICE (PORT 8000)")
    print("================================================================")
    print("Citizen Portal & Learning Hub: http://127.0.0.1:8000/")
    print("Admin Honeypot Trap:           http://127.0.0.1:8000/admin (Blocked)")
    print("================================================================")
    uvicorn.run("app.citizen_main:app", host="127.0.0.1", port=8000, reload=False)
