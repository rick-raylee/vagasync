from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request, Response
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.background import BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import time
import os
import sys

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from database import get_db, Job, Config, Log, init_db, add_log, Assessment, AssessmentSubmission, TalentBank, Notification, User, AuditLog, BlogPost, BlogComment, FinancialTransaction, FinancialExpense
import security
import ai_agent
import linkedin_bot
import notifier
from schemas import *
from deps import *

# Rate Limiter
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

import shutil

# Local rate limiters for routers
_login_attempts = {}
_reset_code_attempts = {}
_reset_attempts = {}

# Simple config bearer dependency
_config_bearer = HTTPBearer(auto_error=False)

def _require_valid_token(credentials: HTTPAuthorizationCredentials = Depends(_config_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token de autenticação obrigatório.")
    import security as _sec
    payload = _sec.verify_jwt(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
    return payload

def _check_reset_rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 900  # 15 minutos
    max_attempts = 3
    attempts = _reset_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < window]
    if len(attempts) >= max_attempts:
        retry_after = int(window - (now - attempts[0]))
        raise HTTPException(
            status_code=429,
            detail=f"Muitas solicitações de código. Aguarde {retry_after} segundos.",
            headers={"Retry-After": str(retry_after)}
        )
    attempts.append(now)
    _reset_attempts[ip] = attempts

def _check_login_rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 600  # 10 minutos
    max_attempts = 5
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < window]
    if len(attempts) >= max_attempts:
        retry_after = int(window - (now - attempts[0]))
        raise HTTPException(
            status_code=429,
            detail=f"Muitas tentativas de login. Tente novamente em {retry_after} segundos.",
            headers={"Retry-After": str(retry_after)}
        )
    attempts.append(now)
    _login_attempts[ip] = attempts

def get_config_value(db: Session, key: str, default: str = "") -> str:
    cfg = db.query(Config).filter(Config.key == key).first()
    if cfg:
        return cfg.value
    return default

def log_audit(action: str, details: str, db: Session, ip_address: str = "127.0.0.1"):
    try:
        log_entry = AuditLog(
            timestamp=datetime.utcnow(),
            action=action,
            details=details,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Erro ao salvar audit log: {e}")


@router.get("/api/logs")
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(Log).order_by(Log.timestamp.desc()).limit(100).all()
    return [{"timestamp": l.timestamp.isoformat(), "level": l.level, "message": l.message} for l in logs]



@router.get("/api/automation/status")
def get_automation_status(db: Session = Depends(get_db)):
    """Retorna o status da automação e quais fontes de busca estão ativas."""
    # Verificar quais fontes estão configuradas
    gemini_key  = ai_agent.get_api_key(db)
    cookie_cfg  = db.query(Config).filter(Config.key == "linkedin_cookie").first()
    web_cfg     = db.query(Config).filter(Config.key == "enable_web_search").first()

    has_gemini  = bool(gemini_key)
    has_cookie  = bool(cookie_cfg and cookie_cfg.value and len(cookie_cfg.value) > 20)
    enable_web  = (web_cfg.value == "true") if web_cfg else False

    active_sources = []
    if has_gemini:
        active_sources.append("🌐 Gemini Web (Indeed, Gupy, Catho...)")
        active_sources.append("💼 Gemini LinkedIn (busca por IA)")
    if has_cookie and linkedin_bot.PLAYWRIGHT_AVAILABLE:
        active_sources.append("🤖 Playwright LinkedIn (Easy Apply)")

    return {
        "is_running": linkedin_bot.is_running,
        "sources": {
            "gemini_web":           has_gemini,
            "gemini_linkedin":      has_gemini,
            "playwright_linkedin":  has_cookie and linkedin_bot.PLAYWRIGHT_AVAILABLE,
        },
        "active_sources": active_sources,
        "playwright_available": linkedin_bot.PLAYWRIGHT_AVAILABLE,
    }



@router.post("/api/automation/stop")
def stop_automation():
    """Para o ciclo de automação em execução."""
    linkedin_bot.is_running = False
    add_log("warning", "⏹️ Automação interrompida manualmente pelo usuário.")
    return {"message": "Sinal de parada enviado ao agente.", "status": "stopping"}



@router.post("/api/automation/run")
def trigger_automation(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if linkedin_bot.is_running:
        return {"message": "Automação já está em execução.", "status": "running"}
        
    # Validar que existe currículo antes de rodar
    resume_cfg = db.query(Config).filter(Config.key == "resume_text").first()
    if not resume_cfg or not resume_cfg.value:
        raise HTTPException(status_code=400, detail="Por favor, faça upload ou salve o seu currículo antes de rodar a automação.")

    background_tasks.add_task(linkedin_bot.run_automation_cycle)
    return {"message": "Automação iniciada em segundo plano.", "status": "started"}



@router.get("/api/automation/events")
async def get_automation_events():
    """
    Server-Sent Events (SSE) endpoint para transmitir logs de automação
    para o painel em tempo real.
    """
    async def event_generator():
        # Envia logs recentes ao conectar
        db = database.SessionLocal()
        try:
            recent_logs = db.query(Log).order_by(Log.timestamp.desc()).limit(15).all()
            for log in reversed(recent_logs):
                yield f"data: {{\"timestamp\": \"{log.timestamp.isoformat()}\", \"level\": \"{log.level}\", \"message\": \"{log.message}\"}}\n\n"
        finally:
            db.close()

        import asyncio
        while True:
            try:
                log_item = await asyncio.wait_for(linkedin_bot.log_queue.get(), timeout=15.0)
                import json
                yield f"data: {json.dumps(log_item)}\n\n"
            except asyncio.TimeoutError:
                # Keep-alive ping to prevent Nginx upstream timeouts
                yield "data: {\"ping\": true}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


