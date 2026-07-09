@echo off
title Vaga Sync Launcher
echo ==========================================
echo       INICIALIZANDO VAGA SYNC
echo ==========================================
echo.

echo [1/3] Iniciando Servidor Backend (FastAPI)...
start "Vaga Sync - Backend" cmd /k "cd backend && set DEV_MODE=true&& venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"

echo [2/3] Iniciando Servidor Frontend (Vite React)...
start "Vaga Sync - Frontend" cmd /k "cd frontend && npm run dev -- --port 5173 --open"

echo [3/3] Iniciando Painel CEO (Vue)...
start "Vaga Sync - CEO Panel" cmd /k "cd owner-panel && npm run dev -- --port 5174 --open"

echo.
echo ==========================================
echo O Vaga Sync foi iniciado com sucesso!
echo.
echo - Backend rodando em: http://localhost:8000
echo - Frontend abrindo no navegador (Porta 5173)
echo - Painel CEO abrindo no navegador (Porta 5174)
echo ==========================================
pause
