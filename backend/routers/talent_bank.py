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


