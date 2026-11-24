import os
import sys

# Ensure project root is in sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.main import app

# Normalizing middleware for Vercel Serverless routing
@app.middleware("http")
async def normalize_vercel_paths(request, call_next):
    path = request.scope.get("path", "")
    
    # 1. Strip /api/index prefix if present
    if path.startswith("/api/index/"):
        path = path.replace("/api/index", "", 1)
        request.scope["path"] = path
    elif path == "/api/index":
        request.scope["path"] = "/"
        path = "/"
    
    # 2. If Vercel stripped /api, restore it if /api<path> is a registered route
    if not path.startswith("/api") and path != "/":
        api_candidate = f"/api{path}"
        for route in app.routes:
            if hasattr(route, "path") and route.path == api_candidate:
                request.scope["path"] = api_candidate
                break

    return await call_next(request)
