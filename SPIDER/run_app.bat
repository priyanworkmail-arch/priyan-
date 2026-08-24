@echo off
echo ============================================
echo  Smart Emergency Medical Service (SEMS)
echo ============================================
echo.
cd /d "%~dp0"

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt -q

echo.
echo Starting SEMS website at http://127.0.0.1:5001
echo Press Ctrl+C to stop the server
echo.
python app.py
pause
