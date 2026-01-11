#!/bin/bash
# Installationsskript für Linux/Raspberry Pi

echo "=== Coffee Tally Installation ==="
echo ""

# Prüfe ob Python installiert ist
if ! command -v python3 &> /dev/null; then
    echo "FEHLER: Python 3 ist nicht installiert!"
    echo "Installieren Sie Python 3 mit: sudo apt-get install python3 python3-pip python3-venv"
    exit 1
fi

echo "Python 3 gefunden."
echo ""

# Erstelle virtuelles Environment
echo "Erstelle virtuelles Environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "FEHLER: Konnte virtuelles Environment nicht erstellen!"
    exit 1
fi

echo "Aktiviere virtuelles Environment..."
source venv/bin/activate

echo "Installiere Python-Pakete..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "FEHLER: Installation der Pakete fehlgeschlagen!"
    exit 1
fi

echo ""
echo "=== Installation erfolgreich abgeschlossen! ==="
echo ""
echo "Nächste Schritte:"
echo "1. Bearbeiten Sie config.json mit Ihren Datenbank- und Kartenleser-Einstellungen"
echo "2. Führen Sie database_setup.py aus, um die Datenbank einzurichten"
echo "3. Starten Sie die Anwendung mit: python main.py"
echo ""
