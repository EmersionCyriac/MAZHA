#!/bin/bash
# MAZHA Local Server Runner
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================="
echo "💧 Starting MAZHA AI Water Banking Digital Twin Platform"
echo "📍 Study Basin: Meenachil River Basin (Pala, Kerala)"
echo "🌐 Opening at: http://127.0.0.1:8000"
echo "================================================================="

python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --ws none
