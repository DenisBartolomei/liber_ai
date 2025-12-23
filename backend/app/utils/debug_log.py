import json
import os
import time


# In Docker, we mount the repo's `.cursor/` into `/app/.cursor/`
# Try host path first, then Docker path
_host_log_path = r"c:\Users\utente\OneDrive - UNIVERSITA' CARLO CATTANEO - LIUC\Desktop\Bacco Sommelier AI\.cursor\debug.log"
_docker_log_path = "/app/.cursor/debug.log"
LOG_PATH = os.getenv("LIBER_DEBUG_LOG_PATH", _host_log_path if os.path.exists(os.path.dirname(_host_log_path)) else _docker_log_path)


def dbg(hypothesisId: str, location: str, message: str, data: dict | None = None, runId: str = "pre-fix"):
    try:
        payload = {
            "sessionId": "debug-session",
            "runId": runId,
            "hypothesisId": hypothesisId,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # Never crash the app because of debug logging
        pass


