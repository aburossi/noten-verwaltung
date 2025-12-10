#!/bin/bash
# Wechselt in das Verzeichnis, in dem dieses Skript liegt
cd "$(dirname "$0")"

echo "=========================================="
echo "🍏 BBW Notenverwaltung (Mac Launcher)"
echo "=========================================="
echo ""

# Prüfen ob Python 3 installiert ist
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 wurde nicht gefunden!"
    echo "Bitte installieren Sie Python von python.org."
    exit 1
fi

# Bibliotheken installieren (falls nötig)
echo "📦 Prüfe Bibliotheken..."
pip3 install -r requirements.txt

# App starten
echo "🚀 Starte App..."
python3 run_app.py