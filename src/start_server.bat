@echo off
echo ===== Starting Steam Playtime Server =====
echo Current directory: %CD%

REM Kill any existing Python processes and wait for them to fully stop
echo Checking for existing Python servers...
tasklist /FI "IMAGENAME eq python.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo Found running Python processes. Stopping them...
    taskkill /F /IM python.exe
    echo Waiting for processes to stop...
    timeout /t 3 /nobreak >nul
)

REM Check if port 8080 is in use
echo Checking if port 8080 is available...
netstat -ano | findstr :8080 >nul
if %errorlevel% equ 0 (
    echo Port 8080 is in use. Attempting to free it...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do (
        echo Killing process using port 8080 (PID: %%a)
        taskkill /F /PID %%a
    )
    echo Waiting for port to be freed...
    timeout /t 3 /nobreak >nul
)

REM Get the full path to server.py
set "SERVER_PATH=%CD%\server.py"
echo Running server from: %SERVER_PATH%

REM Verify server.py exists
if not exist "%SERVER_PATH%" (
    echo Error: server.py not found at %SERVER_PATH%
    pause
    exit /b 1
)

REM Start the server in a new window
echo Starting server...
start "Steam Playtime Server" cmd /k "python "%SERVER_PATH%""

REM Wait for server to start
echo Waiting for server to start...
timeout /t 3 /nobreak >nul

REM Try to open Edge with the URL
echo Opening browser...
start msedge.exe "http://localhost:8080/fetch.html"

echo.
echo Server is running in a separate window.
echo If the browser didn't open, please manually open:
echo http://localhost:8080/fetch.html
echo.
echo To stop the server, close the server window or run:
echo taskkill /F /IM python.exe
echo.
echo Press any key to close this window...
pause >nul 