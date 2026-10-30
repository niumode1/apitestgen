@echo off
title APITestGen
echo ============================================
echo   APITestGen - API Test Generation Platform
echo ============================================
echo.

cd /d %~dp0

echo [1/4] Starting BookStore Demo API on port 9002...
start "BookStore" cmd /c "cd backend && .venv\Scripts\python demo_api_full.py"

echo [2/4] Starting Backend on port 8000...
start "Backend" cmd /c "cd backend && .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [3/4] Starting Demo Users API on port 9001...
start "DemoUsers" cmd /c "cd backend && .venv\Scripts\python demo_api.py"

echo [4/4] Starting Frontend on port 5173...
start "Frontend" cmd /c "cd frontend && npm run dev"

timeout /t 6 /nobreak >nul

echo.
echo ============================================
echo   BookStore API:  http://localhost:9002/docs
echo   Demo Users API: http://localhost:9001/docs
echo   Backend:        http://localhost:8000/docs
echo   Frontend:       http://localhost:5173
echo ============================================
echo.
echo Press any key to open frontend ...
pause >nul
start http://localhost:5173
