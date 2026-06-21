@echo off
title Vaga Sync Launcher
echo ==========================================
echo       INICIALIZANDO VAGA SYNC
echo ==========================================
echo.

echo [1/2] Iniciando Servidor Backend (FastAPI)...
start "Vaga Sync - Backend" cmd /k "cd backend && venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"

echo [2/2] Iniciando Servidor Frontend (Vite React)...
start "Vaga Sync - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo O Vaga Sync foi iniciado com sucesso!
echo.
echo - Backend rodando em: http://localhost:8000
echo - Frontend abrindo...
echo ==========================================
pause
