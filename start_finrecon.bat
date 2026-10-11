@echo off
echo ============================================================
echo Starting FinRecon Platform (Backend + Frontend)
echo ============================================================
echo.

echo Starting FastAPI Backend Server on http://127.0.0.1:8000 ...
start "FinRecon Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 >nul

echo Starting React Frontend Dashboard on http://localhost:5173 ...
start "FinRecon Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Both services launched! 
echo Open your browser at http://localhost:5173
echo.
pause
