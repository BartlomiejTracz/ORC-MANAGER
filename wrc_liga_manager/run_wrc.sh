#!/bin/bash
cd "$(dirname "$0")"

echo "=========================================="
echo "       Starting WRC League Manager"
echo "=========================================="

# 1. Setup environment (if missing)
if [ ! -f "venv/bin/activate" ]; then
    echo "[1/3] First time setup: Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "[2/3] Installing required packages (this will take a minute)..."
    pip install -r requirements.txt
else
    echo "[1/2] Virtual environment found. Activating..."
    source venv/bin/activate
fi

# 2. Run Application
echo "[Final Step] Starting the server! Opening your browser..."
echo "======================================================================"
echo "  [!] DO NOT CLOSE THIS TERMINAL WINDOW WHILE USING THE APP!"
echo "  [!] Closing this window will shut down the server."
echo "======================================================================"

python3 -c "import webbrowser; webbrowser.open('http://127.0.0.1:8000')" &
uvicorn main:app --host 127.0.0.1 --port 8000