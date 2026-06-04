@echo off
echo =========================================
echo SNMPSim Web Dashboard - Startup Script
echo =========================================
echo.

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with Administrator privileges.
) else (
    echo [WARNING] You are not running as Administrator.
    echo Stopping the SNMP service or binding to Port 161 might fail!
    echo Please right-click this file and select "Run as administrator" if you encounter errors.
    echo.
)

echo 1. Stopping default Windows SNMP service to free Port 161...
net stop SNMP 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Windows SNMP service was not running or could not be stopped.
) else (
    echo [OK] Windows SNMP service stopped successfully.
)
echo.

echo 2. Preparing Python virtual environment...
if not exist venv\Scripts\python.exe (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Could not create Python virtual environment.
        pause
        exit /b 1
    )
)
venv\Scripts\python.exe -m pip install -r requirements.txt
echo.

echo 3. Starting Flask Backend Dashboard...
echo [INFO] Access the dashboard at http://localhost:5000
echo.
venv\Scripts\python.exe app.py
pause
