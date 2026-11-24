import os
import sys
from fastapi import Request
from fastapi.responses import JSONResponse

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.main import app

# Normalizing middleware for Vercel Serverless routing
@app.middleware("http")
async def normalize_vercel_paths(request: Request, call_next):
    scope = request.scope
    current_path = scope.get("path", "")
    
    # 1. Check if rewrite passed the subpath via __path__ query param
    query_string = scope.get("query_string", b"").decode("utf-8")
    extracted_path = None
    if "__path__=" in query_string:
        for param in query_string.split("&"):
            if param.startswith("__path__="):
                sub = param.split("=", 1)[1].split("&")[0]
                extracted_path = f"/{sub.lstrip('/')}"
                break

    matched_hdr = request.headers.get("x-matched-path", "")
    forwarded_hdr = request.headers.get("x-forwarded-uri", "")

    # 2. Gather candidates
    candidates = []
    if extracted_path:
        candidates.extend([extracted_path, f"/api{extracted_path}"])
    for hdr in [matched_hdr, forwarded_hdr]:
        if hdr and "/api/index" not in hdr:
            hdr_clean = hdr.split("?")[0]
            candidates.extend([hdr_clean, f"/api{hdr_clean}"])
    candidates.extend([current_path, f"/api{current_path}"])
    if "/api/index" in current_path:
        stripped = current_path.replace("/api/index.py", "").replace("/api/index", "")
        if stripped:
            candidates.extend([stripped, f"/api{stripped}"])

    registered_paths = {r.path for r in app.routes if hasattr(r, "path")}
    for c in candidates:
        if c in registered_paths:
            scope["path"] = c
            break

    return await call_next(request)

@app.get("/api/debug")
@app.get("/debug")
async def vercel_debug(request: Request):
    return {
        "status": "ok",
        "scope_path": request.scope.get("path"),
        "raw_path": request.scope.get("raw_path", b"").decode("utf-8", errors="ignore"),
        "headers": dict(request.headers),
        "registered_routes": [r.path for r in app.routes if hasattr(r, "path")]
    }


