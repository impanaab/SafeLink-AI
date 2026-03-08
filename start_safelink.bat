@echo off
REM SafeLink AI Auto-Start Script
REM Place this file in: shell:startup (Windows Startup folder)

echo Starting SafeLink AI Security Monitor...

REM Navigate to project directory
cd /d "c:\Users\Admin\OneDrive\Documents\Sentinelssx\SafeLinkAI"

REM Start SafeLink AI
python safelink_ai_face_recognition.py

REM Keep window open if error occurs
if errorlevel 1 (
    echo.
    echo Error occurred. Press any key to exit...
    pause > nul
)
