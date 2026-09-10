import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse

HONEYPOT_PATHS = [
    "/admin",
    "/admin/",
    "/wp-admin",
    "/administrator",
    "/admin.php",
    "/admin/login",
    "/api/admin"
]

class HoneypotMiddleware(BaseHTTPMiddleware):
    """
    Traps and neutralizes unauthorized attempts to access `/admin` or administrative
    endpoints, logging the incident and rendering an authoritative security block screen.
    """
    async def dispatch(self, request: Request, call_next):
        path = request.url.path.lower()
        if any(path == p or path.startswith(p + "/") for p in HONEYPOT_PATHS):
            client_ip = request.client.host if request.client else "127.0.0.1"
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            
            # If browser request expecting HTML
            accept = request.headers.get("accept", "")
            if "text/html" in accept:
                html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>403 FORBIDDEN | Government of India - I4C Security Shield</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background-color: #0d1117;
            color: #f0f6fc;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }}
        .shield-card {{
            background: linear-gradient(145deg, #161b22, #0d1117);
            border: 2px solid #da3633;
            border-radius: 12px;
            max-width: 620px;
            width: 100%;
            padding: 40px;
            box-shadow: 0 20px 45px rgba(218, 54, 51, 0.25);
            text-align: center;
        }}
        .badge {{
            display: inline-block;
            background: rgba(218, 54, 51, 0.15);
            color: #f85149;
            border: 1px solid #da3633;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1.5px;
            margin-bottom: 20px;
            text-transform: uppercase;
        }}
        .warning-icon {{
            font-size: 64px;
            margin-bottom: 16px;
            color: #da3633;
        }}
        h1 {{
            font-size: 26px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 12px;
            letter-spacing: -0.5px;
        }}
        p.subtitle {{
            color: #8b949e;
            font-size: 15px;
            line-height: 1.6;
            margin-bottom: 24px;
        }}
        .telemetry-box {{
            background: #090d13;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px;
            text-align: left;
            font-family: 'Consolas', monospace;
            font-size: 13px;
            color: #79c0ff;
            margin-bottom: 24px;
            line-height: 1.8;
        }}
        .stat-label {{ color: #8b949e; }}
        .legal-notice {{
            background: rgba(218, 54, 51, 0.08);
            border-left: 3px solid #da3633;
            padding: 12px 16px;
            text-align: left;
            font-size: 12px;
            color: #f85149;
            margin-bottom: 28px;
            line-height: 1.5;
        }}
        .btn {{
            display: inline-block;
            background: #238636;
            color: #ffffff;
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            transition: background 0.2s;
        }}
        .btn:hover {{ background: #2ea043; }}
    </style>
</head>
<body>
    <div class="shield-card">
        <div class="badge">DEFENSE SHIELD ACTIVE</div>
        <div class="warning-icon">🛡️ 403</div>
        <h1>ACCESS PROHIBITED &amp; TRAPPED</h1>
        <p class="subtitle">
            The requested administrative resource <code style="color: #ff7b72;">{path}</code> is restricted. Unauthorized access attempts to National Cyber Crime Infrastructure are actively monitored and logged.
        </p>

        <div class="telemetry-box">
            <div><span class="stat-label">ORIGIN IP:</span> {client_ip}</div>
            <div><span class="stat-label">TIMESTAMP:</span> {timestamp}</div>
            <div><span class="stat-label">EVENT CLASSIFICATION:</span> HONEYPOT_INTRUSION_PROBE</div>
            <div><span class="stat-label">INCIDENT TICKET:</span> I4C-SEC-TRAP-{int(time.time())}</div>
        </div>

        <div class="legal-notice">
            <strong>NOTICE UNDER SECTION 66F OF THE IT ACT, 2000:</strong><br>
            Unauthorized entry or probing into critical computer systems is a cognizable offense punishable by law.
        </div>

        <a href="/" class="btn">Return to National Citizen Portal</a>
    </div>
</body>
</html>"""
                return HTMLResponse(content=html_content, status_code=403)

            return JSONResponse(
                status_code=403,
                content={
                    "status": "error",
                    "code": 403,
                    "error": "ACCESS_DENIED_HONEYPOT_TRIGGERED",
                    "message": "Administrative path is strictly prohibited and monitored.",
                    "incident_id": f"I4C-SEC-TRAP-{int(time.time())}",
                    "timestamp": timestamp
                }
            )

        return await call_next(request)
