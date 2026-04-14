@echo off
REM Coffee Tally - Installation Script for Windows
echo ========================================
echo Coffee Tally - Installation
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo Python found:
python --version
echo.

REM Create virtual environment
echo Creating Python virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Could not create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created successfully
echo.

REM Activate virtual environment and install packages
echo Installing required packages...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Could not install required packages
    pause
    exit /b 1
)
echo.

REM Create config.json from template if it doesn't exist
if not exist config.json (
    echo Creating config.json from template...
    copy config.json.template config.json
    echo.
    echo IMPORTANT: Please edit config.json and configure:
    echo   - Database provider (mysql or cosmos)
    echo   - Database connection settings (MySQL or Azure Cosmos DB)
    echo   - Card reader COM port
    echo.
) else (
    echo config.json already exists, skipping template copy
    echo.
)

echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Edit config.json with your database provider and COM port settings
echo 2. Set up your database (MySQL or Azure Cosmos DB - see README.md)
echo 3. Run the application with: run.bat
echo.
pause
