@echo off
title FinRecon - SQLite Web Dashboard
echo ========================================================
echo   FinRecon - SQLite Web Database Dashboard
echo ========================================================
echo   Database: backend\data\finrecon_local.db
echo   Opening in your default browser at http://127.0.0.1:8080 ...
echo ========================================================
echo.
cd /d "%~dp0"
python -c "from sqlite_web.sqlite_web import main; import sys; sys.argv=['sqlite_web', 'backend/data/finrecon_local.db', '--port=8080', '--browser']; main()"
pause
