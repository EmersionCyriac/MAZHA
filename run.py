#!/usr/bin/env python3
"""
MAZHA Local Server Launcher
Starts the FastAPI Digital Twin application on http://127.0.0.1:8000
"""

import sys
import uvicorn

if __name__ == "__main__":
    print("=" * 65)
    print("💧 Starting MAZHA AI-Enabled Water Banking Digital Twin")
    print("📍 Region: Meenachil Basin (Pala, Kottayam, Kerala)")
    print("🌐 URL: http://127.0.0.1:8000")
    print("=" * 65)
    
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            ws="none"
        )
    except KeyboardInterrupt:
        print("\nMAZHA server stopped.")
        sys.exit(0)
