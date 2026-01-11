@echo off
REM Installationsskript für Windows
echo === Coffee Tally Installation ===
echo.

REM Prüfe ob Python installiert ist
python --version >nul 2>&1
if errorlevel 1 (
    echo FEHLER: Python ist nicht installiert oder nicht im PATH!
    echo Bitte installieren Sie Python von https://www.python.org/
    pause
    exit /b 1
)

echo Python gefunden.
echo.

REM Erstelle virtuelles Environment
echo Erstelle virtuelles Environment...
python -m venv venv
if errorlevel 1 (
    echo FEHLER: Konnte virtuelles Environment nicht erstellen!
    pause
    exit /b 1
)

echo Aktiviere virtuelles Environment...
call venv\Scripts\activate.bat

echo Installiere Python-Pakete...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo FEHLER: Installation der Pakete fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo === Installation erfolgreich abgeschlossen! ===
echo.
echo Naechste Schritte:
echo 1. Bearbeiten Sie config.json mit Ihren Datenbank- und Kartenleser-Einstellungen
echo 2. Fuehren Sie database_setup.py aus, um die Datenbank einzurichten
echo 3. Starten Sie die Anwendung mit: python main.py
echo.
pause
