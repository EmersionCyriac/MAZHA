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
    # Retrieve current path and any Vercel proxy headers
    current_path = request.scope.get("path", "")
    matched_path = request.headers.get("x-matched-path", "")
    forwarded_uri = request.headers.get("x-forwarded-uri", "")

    # Priority candidate for actual requested route
    target_path = None
    for candidate in [matched_path, forwarded_uri, current_path]:
        if candidate and candidate != "/api/index.py" and candidate != "/api/index":
            target_path = candidate
            break

    if target_path:
        # Strip query string if present in candidate
        target_path = target_path.split("?")[0]
        # Clean up /api/index prefix if present
        if target_path.startswith("/api/index/"):
            target_path = target_path.replace("/api/index", "", 1)
        elif target_path == "/api/index":
            target_path = "/"
        
        # Ensure it matches registered FastAPI routes
        # Some routes might start with /api/...
        registered_paths = [r.path for r in app.routes if hasattr(r, "path")]
        
        if target_path in registered_paths:
            request.scope["path"] = target_path
        elif f"/api{target_path}" in registered_paths:
            request.scope["path"] = f"/api{target_path}"
        elif target_path.startswith("/api") and target_path[4:] in registered_paths:
            request.scope["path"] = target_path[4:]
        else:
            request.scope["path"] = target_path

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

