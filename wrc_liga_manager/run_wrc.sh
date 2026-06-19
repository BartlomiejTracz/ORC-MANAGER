#!/bin/bash

# Przejście do katalogu skryptu + zabezpieczenie przed błędem
cd "$(dirname "$0")" || { echo "Błąd: Nie można przejść do katalogu skryptu."; read -p "Naciśnij Enter, aby zamknąć..."; exit 1; }

echo "=========================================="
echo "        Starting WRC League Manager"
echo "=========================================="

# 1. Setup environment (if missing)
# Zmiana: lepiej sprawdzać czy istnieje cały katalog venv
if [ ! -d "venv" ]; then
    echo "[1/3] First time setup: Creating virtual environment..."
    
    # Zabezpieczenie na wypadek braku pakietu python3-venv (częsty problem na Linuxie)
    python3 -m venv venv || { echo "Błąd: Nie udało się utworzyć venv. Upewnij się, że masz zainstalowany pakiet 'python3-venv' (np. sudo apt install python3-venv)."; read -p "Naciśnij Enter, aby zamknąć..."; exit 1; }
    
    source venv/bin/activate
    
    echo "[2/3] Installing required packages (this will take a minute)..."
    pip install -r requirements.txt || { echo "Błąd: Instalacja pakietów z requirements.txt nie powiodła się."; read -p "Naciśnij Enter, aby zamknąć..."; exit 1; }
else
    echo "[1/2] Virtual environment found. Activating..."
    source venv/bin/activate || { echo "Błąd: Nie można aktywować środowiska venv."; read -p "Naciśnij Enter, aby zamknąć..."; exit 1; }
fi

# 2. Run Application
echo "[Final Step] Starting the server! Opening your browser..."
echo "======================================================================"
echo "  [!] DO NOT CLOSE THIS TERMINAL WINDOW WHILE USING THE APP!"
echo "  [!] Closing this window will shut down the server."
echo "======================================================================"

python3 -c "import webbrowser; webbrowser.open('http://127.0.0.1:8000')" &

# Zmiana: Uruchamiamy uvicorn przez python3 -m, co gwarantuje, że użyjemy wersji z venv
python3 -m uvicorn main:app --host 127.0.0.1 --port 8000

# Zatrzymanie okna terminala, jeśli uvicorn wyrzuci błąd (np. błąd w kodzie main.py) lub po prostu wyłączysz serwer (Ctrl+C)
echo ""
echo "======================================================================"
echo "Działanie serwera zakończone lub wystąpił błąd."
read -p "Naciśnij Enter, aby zamknąć okno..."
