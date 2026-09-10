import uvicorn

if __name__ == "__main__":
    print("================================================================")
    print("   NCRP SENTINEL // LEA TACTICAL COMMAND SERVICE (PORT 9000)")
    print("================================================================")
    print("LEA Tactical Command Terminal: http://127.0.0.1:9000/")
    print("Isolated Command Zone:         Secured & Air-Gapped")
    print("================================================================")
    uvicorn.run("app.lea_main:app", host="127.0.0.1", port=9000, reload=False)
