# Coffee Tally

Eine moderne Python-Anwendung zur Verwaltung von Kaffeeguthaben mit Kartenleser-Support. Die Anwendung läuft im Vollbild-Kiosk-Modus und ermöglicht das Aufladen und Abziehen von Kaffeeguthaben über RFID-Karten.

## Funktionen

- **Guthaben abziehen**: Automatisches Abziehen von Guthaben bei Kartenpräsentation
- **Guthaben aufladen**: Aufladen von Guthaben in konfigurierbaren Beträgen
- **Guthaben anzeigen**: Anzeige des aktuellen Guthabens
- **Vollbild-Kiosk-Modus**: Moderne UI im Vollbildmodus
- **Kartenleser-Integration**: Unterstützung für Eltatec TWN4 Kartenleser über COM-Port
- **MySQL-Datenbank**: Speicherung der Benutzerdaten und Guthabenstände

## Voraussetzungen

- Python 3.8 oder höher
- MySQL-Server 5.7 oder höher
- Eltatec TWN4 Kartenleser (optional, für Testmodus)
- Windows 10/11 oder Linux (Raspberry Pi getestet)

## Installation

### Windows

1. Öffnen Sie eine Eingabeaufforderung (cmd) oder PowerShell
2. Navigieren Sie zum Projektverzeichnis
3. Führen Sie das Installationsskript aus:
   ```cmd
   install.bat
   ```
4. Das Skript erstellt automatisch ein virtuelles Environment und installiert alle notwendigen Pakete

### Linux / Raspberry Pi

1. Öffnen Sie ein Terminal
2. Navigieren Sie zum Projektverzeichnis
3. Machen Sie das Installationsskript ausführbar (falls nötig):
   ```bash
   chmod +x install.sh
   ```
4. Führen Sie das Installationsskript aus:
   ```bash
   ./install.sh
   ```
5. Das Skript erstellt automatisch ein virtuelles Environment und installiert alle notwendigen Pakete

### Manuelle Installation

Falls Sie die Installationsskripte nicht verwenden möchten:

```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Linux / Raspberry Pi
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Konfiguration

1. Bearbeiten Sie die Datei `config.json` mit Ihren Einstellungen:

```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "IhrPasswort",
    "database": "coffee_tally"
  },
  "card_reader": {
    "port": "COM3",
    "baudrate": 9600,
    "timeout": 0.1
  }
}
```

**Wichtig**: 
- Unter Windows verwenden Sie `COM1`, `COM2`, etc. für den Kartenleser-Port
- Unter Linux verwenden Sie `/dev/ttyUSB0`, `/dev/ttyACM0`, etc. für den Kartenleser-Port
- Der korrekte Port kann mit `dmesg | grep tty` oder über die Geräteverwaltung ermittelt werden

## Datenbank-Setup

1. Stellen Sie sicher, dass MySQL-Server läuft
2. Aktivieren Sie das virtuelle Environment:
   - Windows: `venv\Scripts\activate`
   - Linux: `source venv/bin/activate`
3. Führen Sie das Datenbank-Setup-Skript aus:
   ```bash
   python database_setup.py
   ```
4. Das Skript erstellt automatisch die Datenbank und die notwendigen Tabellen

### Testbenutzer hinzufügen

Nach dem Datenbank-Setup können Sie Testbenutzer hinzufügen:

```sql
USE coffee_tally;
INSERT INTO users (card_id, name, credit) VALUES ('CARD123', 'Max Mustermann', 10);
INSERT INTO users (card_id, name, credit) VALUES ('CARD456', 'Anna Schmidt', 5);
```

**Hinweis**: `card_id` ist die ID, die vom Kartenleser gelesen wird. Diese muss eindeutig sein.

## Verwendung

### Entwicklungsumgebung starten

1. Aktivieren Sie das virtuelle Environment:
   - Windows: `venv\Scripts\activate`
   - Linux: `source venv/bin/activate`
2. Starten Sie die Anwendung:
   ```bash
   python main.py
   ```
3. Zum Beenden drücken Sie `ESC` oder schließen das Fenster

### Produktionsumgebung (Vollbild-Kiosk)

1. Stellen Sie sicher, dass die Anwendung korrekt konfiguriert ist
2. Für automatischen Start erstellen Sie ein Startup-Skript:

**Windows** (`start_coffee_tally.bat`):
```batch
@echo off
cd /d "C:\Pfad\zum\Projekt"
call venv\Scripts\activate.bat
python main.py
```

**Linux** (`start_coffee_tally.sh`):
```bash
#!/bin/bash
cd /pfad/zum/projekt
source venv/bin/activate
python main.py
```

3. Machen Sie das Skript ausführbar (Linux):
   ```bash
   chmod +x start_coffee_tally.sh
   ```
4. Fügen Sie das Skript zur Autostart-Konfiguration hinzu

### Raspberry Pi Autostart

1. Erstellen Sie eine Desktop-Datei:
   ```bash
   sudo nano ~/.config/autostart/coffee-tally.desktop
   ```
2. Fügen Sie folgenden Inhalt ein:
   ```ini
   [Desktop Entry]
   Type=Application
   Name=Coffee Tally
   Exec=/pfad/zum/projekt/start_coffee_tally.sh
   Hidden=false
   NoDisplay=false
   X-GNOME-Autostart-enabled=true
   ```
3. Machen Sie das Startup-Skript ausführbar

## Bedienung

### Hauptbildschirm

- Die Anwendung zeigt standardmäßig den Text "Show card to deduct coffee credit." / "Karte vorhalten um Kaffeeguthaben abzubuchen"
- **Charge credit / Guthaben laden**: Öffnet Dialog zum Aufladen von Guthaben
- **Show credit / Guthaben anzeigen**: Zeigt aktuelles Guthaben an

### Guthaben abziehen

1. Halten Sie eine Karte an den Kartenleser
2. Die Anwendung erkennt die Karte automatisch
3. Wenn die Karte gefunden wird und Guthaben vorhanden ist, wird 1 Guthaben abgezogen
4. Name und verbleibendes Guthaben werden für 5 Sekunden angezeigt

### Guthaben aufladen

1. Klicken Sie auf "Charge credit / Guthaben laden"
2. Wählen Sie die Anzahl der Kaffees mit +/- Buttons
3. Klicken Sie auf "OK"
4. Halten Sie die Karte an den Kartenleser
5. Das Guthaben wird aufgeladen und für 5 Sekunden angezeigt

### Guthaben anzeigen

1. Klicken Sie auf "Show credit / Guthaben anzeigen"
2. Halten Sie die Karte an den Kartenleser
3. Name und aktuelles Guthaben werden für 5 Sekunden angezeigt

## Fehlerbehebung

### Kartenleser wird nicht erkannt

1. Prüfen Sie den COM-Port in der `config.json`
2. Stellen Sie sicher, dass der Port nicht von anderen Programmen verwendet wird
3. Unter Linux benötigen Sie möglicherweise Berechtigungen:
   ```bash
   sudo usermod -a -G dialout $USER
   # Danach neu einloggen
   ```

### Datenbankverbindung fehlgeschlagen

1. Prüfen Sie ob MySQL-Server läuft
2. Überprüfen Sie die Verbindungsdaten in `config.json`
3. Stellen Sie sicher, dass die Datenbank existiert (führen Sie `database_setup.py` aus)

### Anwendung startet nicht im Vollbild

- Die Anwendung verwendet automatisch den Vollbildmodus
- Zum Beenden drücken Sie `ESC`

## Technische Details

- **UI-Framework**: PyGame 2.6.1
- **Datenbank**: MySQL (mysql-connector-python)
- **Serielle Kommunikation**: pyserial
- **Kartenleser-Protokoll**: Eltatec TWN4 (einfaches ASCII-Protokoll)

## Lizenz

Dieses Projekt ist für den internen Gebrauch bestimmt.

## Support

Bei Problemen oder Fragen erstellen Sie bitte ein Issue im Projekt-Repository.
