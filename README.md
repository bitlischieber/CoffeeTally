# Coffee Tally

A touchscreen-friendly coffee credit management system with card reader support for Windows and Linux (Raspberry Pi).

## Features

- 🖥️ **Full-screen kiosk mode** for touchscreen displays
- 💳 **Card reader support** - Eltatec TWN4 via serial/COM port
- 🗄️ **MySQL database** - Stores user cards and credits
- 🌍 **Bilingual interface** - English and German
- 📱 **Modern UI** - Built with Kivy and KivyMD
- ⚡ **Cross-platform** - Works on Windows and Linux/Raspberry Pi

## System Requirements

### Windows
- Python 3.8 or higher
- MySQL Server
- Eltatec TWN4 card reader (connected via COM port)

### Linux/Raspberry Pi
- Python 3.8 or higher
- MySQL Server or MariaDB
- Eltatec TWN4 card reader (connected via USB serial)
- Additional system libraries (installed automatically by install.sh)

## Installation

## Quick Start (5 Minutes)

### Step 1: Installation
**Windows:**
```cmd
cd c:\work\Vario\coffeetally\src
install.bat
```

**Linux/Raspberry Pi:**
```bash
cd /path/to/coffeetally/src
chmod +x install.sh run.sh
./install.sh
```

### Step 2: Database Setup
1. Start MySQL/MariaDB server
2. Run the SQL setup script:
   ```bash
   mysql -u root -p < database_setup.sql
   ```

### Step 3: Configuration
1. Edit `config.json` (created from template):
   - Set MySQL username and password
   - Set card reader port (Windows: COM10, Linux: /dev/ttyUSB0)

### Step 4: Test Card Reader (Optional)
**Windows:**
```cmd
venv\Scripts\activate
python test_card_reader.py
```

**Linux:**
```bash
source venv/bin/activate
python test_card_reader.py
```

### Step 5: Add Users
**Windows:**
```cmd
venv\Scripts\activate
python manage_users.py
```

**Linux:**
```bash
source venv/bin/activate
python manage_users.py
```

### Step 6: Run the Application
**Windows:**
```cmd
run.bat
```

**Linux/Raspberry Pi:**
```bash
./run.sh
```

### Development Environment Setup

#### Windows

1. **Install Python**
   - Download Python 3.8+ from [python.org](https://www.python.org/)
   - Make sure to check "Add Python to PATH" during installation

2. **Install MySQL**
   - Download MySQL Community Server from [mysql.com](https://dev.mysql.com/downloads/mysql/)
   - Or use XAMPP/WAMP for easier setup

3. **Clone/Download the project**
   ```cmd
   cd c:\work\Vario\coffeetally\src
   ```

4. **Run installation script**
   ```cmd
   install.bat
   ```

5. **Configure the application**
   - Edit `config.json` with your settings:
     - Database credentials
     - COM port for card reader (e.g., COM10)

#### Linux/Raspberry Pi

1. **Install Python and dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip python3-venv
   ```

2. **Install MySQL/MariaDB**
   ```bash
   sudo apt-get install mariadb-server
   sudo mysql_secure_installation
   ```

3. **Navigate to project folder**
   ```bash
   cd /path/to/coffeetally/src
   ```

4. **Run installation script**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

5. **Configure the application**
   - Edit `config.json` with your settings:
     - Database credentials
     - Serial port for card reader (e.g., /dev/ttyUSB0)

### Database Setup

1. **Create the database and table**

   Connect to MySQL:
   ```bash
   mysql -u root -p
   ```

   Create database and table:
   ```sql
   CREATE DATABASE coffee_tally;
   USE coffee_tally;

   CREATE TABLE users (
       id INT AUTO_INCREMENT PRIMARY KEY,
       card_id VARCHAR(50) UNIQUE NOT NULL,
       name VARCHAR(100) NOT NULL,
       credit INT DEFAULT 0,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
   );
   ```

      You can also run the included SQL script instead:
      ```bash
      mysql -u root -p < database_setup.sql
      ```

2. **Add test users (optional)**
   ```sql
   INSERT INTO users (card_id, name, credit) VALUES
   ('04A1B2C3D4E5F6', 'John Doe', 10),
   ('04F6E5D4C3B2A1', 'Jane Smith', 5);
   ```

3. **Create MySQL user for the application**
   ```sql
   CREATE USER 'coffee_user'@'localhost' IDENTIFIED BY 'your_secure_password';
   GRANT ALL PRIVILEGES ON coffee_tally.* TO 'coffee_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

### Configuration

Edit `config.json` with your settings:

```json
{
  "database": {
    "host": "localhost",
    "port": 3306,
    "user": "coffee_user",
    "password": "your_secure_password",
    "database": "coffee_tally",
    "table": "users"
  },
  "card_reader": {
    "port": "COM10",          // Windows e.g.: "COM10", Linux: "ttyACM0"
    "baudrate": 9600,
    "timeout": 0.1
  }
}
```

#### Finding the Card Reader Port

**Windows:**
- Open Device Manager
- Look under "Ports (COM & LPT)"
- Find your card reader (e.g., "USB Serial Port (COM10)")

**Linux:**
- List serial devices: `ls /dev/tty*`
- Common ports: `/dev/ttyUSB0`, `/dev/ttyACM0`
- Check with: `dmesg | grep tty` after plugging in the reader

## Running the Application

### Windows
```cmd
run.bat
```

### Linux/Raspberry Pi
```bash
./run.sh
```

### Manual Run (Development)
```bash
# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux:
source venv/bin/activate

# Run the app
python main.py
```

## Utilities

### Test Card Reader
```bash
python test_card_reader.py
```

### Manage Users
```bash
python manage_users.py
```

## Usage

### Main Screen
- **Default view**: Shows instruction text in English and German
- Presents a card to deduct one coffee credit
- Card holder name and remaining credit shown for 5 seconds after successful scan

### Charge Credit
1. Click "Charge credit / Guthaben laden" button
2. Use +/- buttons to set the amount
3. Click OK
4. Present card to add credit

### Show Credit
1. Click "Show credit / Guthaben anzeigen" button
2. Present card
3. Current credit is displayed for 5 seconds

## Production Deployment

### Windows Service Setup
For production, you may want to run the app as a Windows service or use Task Scheduler:

1. **Create a startup shortcut**
   - Create a shortcut to `run.bat`
   - Place in: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`

2. **Auto-login (Kiosk mode)**
   - Press Win+R, type `netplwiz`
   - Uncheck "Users must enter a username..."
   - Set account to auto-login

### Raspberry Pi Kiosk Setup

1. **Install minimal desktop (if using Raspberry Pi OS Lite)**
   ```bash
   sudo apt-get install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox
   ```

2. **Create autostart script**
   ```bash
   mkdir -p ~/.config/openbox
   nano ~/.config/openbox/autostart
   ```

   Add:
   ```bash
   #!/bin/bash
   # Disable screen blanking
   xset s off
   xset -dpms
   xset s noblank
   
   # Hide cursor
   unclutter -idle 0 &
   
   # Start Coffee Tally
   cd /path/to/coffeetally/src
   ./run.sh
   ```

3. **Auto-start X on boot**
   ```bash
   nano ~/.bash_profile
   ```

   Add:
   ```bash
   if [ -z "$DISPLAY" ] && [ $(tty) = /dev/tty1 ]; then
       startx
   fi
   ```

4. **Install unclutter (hides mouse cursor)**
   ```bash
   sudo apt-get install unclutter
   ```

## Troubleshooting

### Script Line Endings (Linux)
- If you see `/bin/bash^M: bad interpreter`, convert scripts to LF line endings:
   ```bash
   sed -i 's/\r$//' install.sh run.sh
   ```
   Alternatively, use `dos2unix install.sh run.sh` if available.

### Card Reader Not Working
- **Check COM port**: Verify the port in Device Manager (Windows) or `ls /dev/tty*` (Linux)
- **Permissions (Linux)**: Add user to dialout group: `sudo usermod -a -G dialout $USER` (logout/login required)
- **Test connection**: Try a serial terminal program to verify the reader responds

### Database Connection Issues
- Verify MySQL is running: `systemctl status mysql` (Linux) or check Services (Windows)
- Test credentials: `mysql -u coffee_user -p`
- Check firewall settings if using remote database

### Kivy Installation Issues
**Linux/Raspberry Pi:**
- If Kivy installation fails, ensure all system dependencies are installed
- Run `install.sh` which installs necessary SDL libraries

**Windows:**
- Update pip: `python -m pip install --upgrade pip`
- Install Visual C++ Build Tools if needed

### Display Issues
- **Fullscreen not working**: Edit main.py, change `Window.fullscreen = 'auto'` to `Window.fullscreen = True`
- **Touch not working**: Check Kivy documentation for touch configuration
- **Resolution issues**: Set window size before fullscreen in main.py

## File Structure

```
src/
├── main.py                 # Main application file
├── card_reader.py          # Card reader communication module
├── database.py             # Database operations module
├── config.json             # Configuration (create from template)
├── config.json.template    # Configuration template
├── requirements.txt        # Python dependencies
├── install.bat             # Windows installation script
├── install.sh              # Linux installation script
├── run.bat                 # Windows run script
├── run.sh                  # Linux run script
├── vs_back.png             # Background image
├── venv/                   # Virtual environment (created during install)
└── README.md               # This file
```

## Card Reader Protocol

The application uses the Eltatec TWN4 card reader with a simple protocol:

- **Search command**: `050020\r`
- **Response**: 
  - `0000` = No card present
  - Card data = Contains card ID in hex format
- **Beep command**: `04074B600964006400\r`

## Development

### Adding New Features
The application is structured in modules:
- `main.py` - UI and application logic
- `card_reader.py` - Card reader communication
- `database.py` - Database operations

### Modifying UI
- Edit `main.py`
- Kivy uses dynamic layouts - see [Kivy documentation](https://kivy.org/doc/stable/)
- KivyMD provides Material Design components - see [KivyMD documentation](https://kivymd.readthedocs.io/)

### Database Schema
You can extend the users table with additional fields as needed:
```sql
ALTER TABLE users ADD COLUMN email VARCHAR(100);
```

## License

This project is for internal use. Modify as needed for your requirements.

## Support

For issues or questions:
1. Check this README
2. Review the source code comments
3. Check Kivy/KivyMD documentation
4. Verify hardware connections and configurations

## Version History

- **v0.1.0** - Initial Kivy version
  - Full-screen kiosk mode
  - Card reader integration
  - MySQL database support
  - Charge and show credit features

- **v0.1.1** - Bug fixes
  - Add version info bottom right
  - Fix reader beep
  - Can close app by tapping 5 time on the version info text

- **v0.1.2** - Logging and show update date
  - Optional logging to `error.log` file
  - Show last credit update date, when showing credit

- **v0.1.3** - Performance improvements and UI fixes
  - Avoid thread blocking: Card reader operations now run in background thread
  - Unified dialog button sizes: OK buttons now match Cancel button size
