#!/usr/bin/env bash
set -e

echo "============================================================"
echo "  KINETIK // Unix Setup & Environment Launcher"
echo "============================================================"

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 was not found. Please install Python 3.12+."
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment in .venv..."
    python3 -m venv .venv
fi

echo "[INFO] Activating virtual environment..."
source .venv/bin/activate

echo "[INFO] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[INFO] Running test suite..."
pytest tests/ -q

echo "============================================================"
echo "  Setup Complete! Launching KINETIK..."
echo "============================================================"
python main.py
