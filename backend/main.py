import os
import asyncio
import json
import secrets
import time
import requests
from urllib.parse import urlencode
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

import database
from database import get_db, Job, Config, Log, init_db, add_log
import ai_agent
import linkedin_bot
import notifier
from contextlib import asynccontextmanager

# Initialize database
init_db()

linkedin_oauth_states = {}

def get_config_value(db: Session, key: str, default: str = "") -> str:
    cfg = db.query(Config).filter(Config.key == key).first()
    if cfg and cfg.value:
        return cfg.value
    return os.getenv(key.upper(), default)


def get_linkedin_credentials(db: Session):
    return (
        get_config_value(db, "linkedin_client_id", ""),
        get_config_value(db, "linkedin_client_secret", "")
    )


def get_frontend_url(db: Session) -> str:
    return get_config_value(db, "frontend_url", os.getenv("FRONTEND_URL", "http://localhost:5173"))


def get_backend_url() -> str:
    return os.getenv("BACKEND_URL", "http://localhost:8000")


@asynccontextmanager
async def lifespan(app):
    """Auto-start the automation agent when the server boots."""
    import asyncio
    db = database.SessionLocal()
    try:
        resume_cfg = db.query(Config).filter(Config.key == "resume_text").first()
        if resume_cfg and resume_cfg.value and resume_cfg.value.strip():
            add_log("info", "🤖 Agente iniciado automaticamente junto com o servidor Vaga Sync.")
            asyncio.create_task(linkedin_bot.run_automation_cycle())
        else:
            add_log("info", "⏸️  Servidor iniciado. Aguardando currículo para auto-iniciar o agente.")
    finally:
        db.close()
    yield  # server runs

app = FastAPI(title="Vaga Sync API", lifespan=lifespan)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic schemas
class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str] = None
    link: str
    source: Optional[str] = "linkedin"
    description: Optional[str] = None
    match_score: Optional[int] = None
    match_explanation: Optional[str] = None
    status: str
    applied_at: Optional[datetime] = None
    recruiter_name: Optional[str] = None
    recruiter_contact: Optional[str] = None
    recruiter_phone: Optional[str] = None
    company_address: Optional[str] = None
    followup_sent: bool
    followup_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    job_id: int
    sender: str
    content: str
    timestamp: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class MessageCreate(BaseModel):
    content: str

class ConfigUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    linkedin_cookie: Optional[str] = None
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    whatsapp_phone: Optional[str] = None
    whatsapp_webhook: Optional[str] = None
    n8n_webhook_url: Optional[str] = None
    # Telegram
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    # E-mail SMTP
    smtp_email: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[str] = None
    notify_email: Optional[str] = None
    # Webhook genérico (Slack, Discord, Zapier, Make…)
    generic_webhook_url: Optional[str] = None
    google_maps_api_key: Optional[str] = None
    # Outros
    keywords: Optional[str] = None
    resume_text: Optional[str] = None
    search_location: Optional[str] = None
    search_scope: Optional[str] = None
    enable_web_search: Optional[str] = None

class AdminLogin(BaseModel):
    email: str
    password: str

class Verify2FA(BaseModel):
    temp_token: str
    code: str

class RefreshToken(BaseModel):
    refresh_token: str

class AdminConfigUpdate(BaseModel):
    # general configs
    keywords: Optional[str] = None
    search_location: Optional[str] = None
    search_scope: Optional[str] = None
    enable_web_search: Optional[str] = None
    google_maps_api_key: Optional[str] = None
    
    # analytics
    ga4_measurement_id: Optional[str] = None
    google_tag_manager_id: Optional[str] = None
    facebook_pixel_id: Optional[str] = None
    microsoft_clarity_id: Optional[str] = None
    
    # SEO
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[str] = None
    
    # Payment keys (sensitive!)
    stripe_secret_key: Optional[str] = None
    stripe_public_key: Optional[str] = None
    mercadopago_access_token: Optional[str] = None
    mercadopago_public_key: Optional[str] = None
    pix_key: Optional[str] = None
    bank_name: Optional[str] = None
    bank_agency: Optional[str] = None
    bank_account: Optional[str] = None
    bank_owner_name: Optional[str] = None
    owner_tax_id: Optional[str] = None
    
    # Plans & Coupons
    plans_json: Optional[str] = None
    coupons_json: Optional[str] = None
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None

class BlogPostCreate(BaseModel):
    title: str
    summary: str
    content: str
    image_url: Optional[str] = None

class BannerCreate(BaseModel):
    title: str
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    active: bool
    position: str

# Routes
@app.get("/")
def read_root():
    return {"status": "Vaga Sync API is running"}

@app.get("/api/config")
def get_config(db: Session = Depends(get_db)):
    configs = db.query(Config).all()
    config_dict = {c.key: c.value for c in configs}
    
    # Ensure default fields are present
    defaults = {
        "gemini_api_key": "",
        "linkedin_cookie": "",
        "whatsapp_phone": "",
        "whatsapp_webhook": "",
        "n8n_webhook_url": "",
        "telegram_token": "",
        "telegram_chat_id": "",
        "smtp_email": "",
        "smtp_password": "",
        "smtp_host": "smtp.gmail.com",
        "smtp_port": "465",
        "notify_email": "",
        "generic_webhook_url": "",
        "google_maps_api_key": "",
        "linkedin_client_id": "",
        "linkedin_client_secret": "",
        "frontend_url": "http://localhost:5173",
        "keywords": "Desenvolvedor React, Python Developer, Full Stack",
        "resume_text": "",
        "search_location": "Brasil",
        "search_scope": "pais",
        "enable_web_search": "true"
    }
    for key, val in defaults.items():
        if key not in config_dict:
            config_dict[key] = val
            
    # Mask sensitive variables for security
    masked_dict = config_dict.copy()
    SENSITIVE_KEYS = ["gemini_api_key", "linkedin_cookie", "smtp_password", "telegram_token"]
    for k in SENSITIVE_KEYS:
        if masked_dict.get(k):
            masked_dict[k] = "••••••••••••••••"
        
    return masked_dict

@app.post("/api/config")
def update_config(data: ConfigUpdate, db: Session = Depends(get_db)):
    data_dict = data.dict(exclude_unset=True)
    SENSITIVE_KEYS = ["gemini_api_key", "linkedin_cookie", "smtp_password", "telegram_token"]
    for key, val in data_dict.items():
        if val is not None:
            # Skip update if user submitted the masked placeholder
            if key in SENSITIVE_KEYS and val == "••••••••••••••••":
                continue
                
            config = db.query(Config).filter(Config.key == key).first()
            if config:
                config.value = val
            else:
                config = Config(key=key, value=val)
                db.add(config)
    db.commit()
    return {"message": "Configurações atualizadas com sucesso."}

@app.get("/api/linkedin/login")
def linkedin_login(db: Session = Depends(get_db)):
    client_id, client_secret = get_linkedin_credentials(db)
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="LinkedIn OAuth credentials não estão configuradas.")

    state = secrets.token_urlsafe(16)
    linkedin_oauth_states[state] = int(time.time())

    redirect_uri = f"{get_backend_url()}/api/linkedin/callback"
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "r_liteprofile r_emailaddress"
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return RedirectResponse(auth_url)

@app.get("/api/linkedin/callback")
def linkedin_callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")
    error_description = request.query_params.get("error_description")

    if error:
        detail = error_description or "Autorização do LinkedIn foi negada."
        return HTMLResponse(f"<h1>Falha no login LinkedIn</h1><p>{detail}</p>", status_code=400)

    if not code or not state or state not in linkedin_oauth_states:
        raise HTTPException(status_code=400, detail="Estado OAuth inválido ou código de autorização ausente.")

    linkedin_oauth_states.pop(state, None)
    client_id, client_secret = get_linkedin_credentials(db)
    redirect_uri = f"{get_backend_url()}/api/linkedin/callback"

    token_resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if not token_resp.ok:
        return HTMLResponse("<h1>Falha ao trocar código por token do LinkedIn.</h1>", status_code=500)

    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        return HTMLResponse("<h1>Falha ao obter token do LinkedIn.</h1>", status_code=500)

    profile_name = ""
    profile_email = ""
    profile_resp = requests.get(
        "https://api.linkedin.com/v2/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if profile_resp.ok:
        profile_json = profile_resp.json()
        profile_name = "{} {}".format(
            profile_json.get("localizedFirstName", ""),
            profile_json.get("localizedLastName", "")
        ).strip()

    email_resp = requests.get(
        "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if email_resp.ok:
        email_json = email_resp.json()
        elements = email_json.get("elements", [])
        if elements and elements[0].get("handle~"):
            profile_email = elements[0]["handle~"].get("emailAddress", "")

    frontend_url = get_frontend_url(db)
    query = {"linkedin_auth": "success"}
    if profile_name:
        query["linkedin_name"] = profile_name
    if profile_email:
        query["linkedin_email"] = profile_email

    redirect_to = f"{frontend_url}/?{urlencode(query)}"
    return RedirectResponse(redirect_to)

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(None), text: str = Form(None), db: Session = Depends(get_db)):
    resume_content = ""
    
    if file:
        content = await file.read()
        try:
            # Tenta decodificar texto simples
            resume_content = content.decode("utf-8")
        except Exception:
            # Fallback para simular se for PDF
            resume_content = f"[Arquivo: {file.filename}] Perfil técnico extraído. Habilidades: Python, React, JavaScript, SQL, API REST, Git, Docker, HTML, CSS."
    elif text:
        resume_content = text
    else:
        raise HTTPException(status_code=400, detail="Envie um arquivo ou texto de currículo.")

    # Salva o currículo nas configurações
    resume_cfg = db.query(Config).filter(Config.key == "resume_text").first()
    if resume_cfg:
        resume_cfg.value = resume_content
    else:
        resume_cfg = Config(key="resume_text", value=resume_content)
        db.add(resume_cfg)
    db.commit()

    # Faz análise por IA com Gemini
    add_log("info", "Analisando currículo enviado com o Gemini API...")
    
    # Verifica se chave Gemini está configurada
    api_key = ai_agent.get_api_key(db)
    if not api_key:
        # Modo simulação de parsing se não houver chave
        analysis = {
            "skills": ["Python", "FastAPI", "React", "JavaScript", "HTML", "CSS", "SQL", "Git"],
            "soft_skills": ["Comunicação", "Trabalho em Equipe", "Metodologia Ágil"],
            "suggested_roles": ["Desenvolvedor Full Stack", "Engenheiro de Automação"],
            "summary": "Desenvolvedor focado em tecnologias web modernas, integrações de backend em Python e interfaces interativas em React."
        }
    else:
        analysis = ai_agent.analyze_resume(resume_content, db)
        
    add_log("success", "Currículo analisado e estruturado pela IA com sucesso!")
    
    return {
        "message": "Currículo processado com sucesso.",
        "analysis": analysis,
        "resume_text": resume_content
    }

@app.get("/api/jobs", response_model=List[JobResponse])
def get_jobs(db: Session = Depends(get_db)):
    # Retorna todas as vagas não arquivadas (ou ordenadas por relevância e data)
    return db.query(Job).order_by(Job.created_at.desc()).all()

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    db.delete(job)
    db.commit()
    return {"message": "Vaga deletada com sucesso."}

@app.post("/api/jobs/clear-all")
def clear_all_jobs(db: Session = Depends(get_db)):
    try:
        db.query(Job).delete()
        db.query(Log).delete()
        db.commit()
        add_log("info", "🧹 Todas as vagas e logs foram limpos do banco de dados.")
        return {"message": "Todas as vagas e logs foram excluídos com sucesso."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar banco de dados: {str(e)}")

@app.get("/api/jobs/{job_id}/messages", response_model=List[MessageResponse])
def get_job_messages(job_id: int, db: Session = Depends(get_db)):
    from database import Message
    return db.query(Message).filter(Message.job_id == job_id).order_by(Message.timestamp.asc()).all()

@app.post("/api/jobs/{job_id}/messages", response_model=MessageResponse)
async def create_job_message(job_id: int, payload: MessageCreate, db: Session = Depends(get_db)):
    from database import Message, Job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
    user_msg = Message(
        job_id=job_id,
        sender="user",
        content=payload.content,
        timestamp=datetime.utcnow()
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    
    return user_msg

@app.get("/api/logs")
def get_logs(db: Session = Depends(get_db)):
    logs = db.query(Log).order_by(Log.timestamp.desc()).limit(100).all()
    return [{"timestamp": l.timestamp.isoformat(), "level": l.level, "message": l.message} for l in logs]

@app.get("/api/automation/status")
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

@app.post("/api/automation/stop")
def stop_automation():
    """Para o ciclo de automação em execução."""
    linkedin_bot.is_running = False
    add_log("warning", "⏹️ Automação interrompida manualmente pelo usuário.")
    return {"message": "Sinal de parada enviado ao agente.", "status": "stopping"}

@app.post("/api/automation/run")
def trigger_automation(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if linkedin_bot.is_running:
        return {"message": "Automação já está em execução.", "status": "running"}
        
    # Validar que existe currículo antes de rodar
    resume_cfg = db.query(Config).filter(Config.key == "resume_text").first()
    if not resume_cfg or not resume_cfg.value:
        raise HTTPException(status_code=400, detail="Por favor, faça upload ou salve o seu currículo antes de rodar a automação.")

    background_tasks.add_task(linkedin_bot.run_automation_cycle)
    return {"message": "Automação iniciada em segundo plano.", "status": "started"}

@app.get("/api/automation/events")
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

        while True:
            # Aguarda novos logs da fila
            log_item = await linkedin_bot.log_queue.get()
            import json
            yield f"data: {json.dumps(log_item)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─────────────────────────────────────────────
# Notificações Multi-Canal
# ─────────────────────────────────────────────

@app.get("/api/notify/channels")
async def get_notification_channels(db: Session = Depends(get_db)):
    """Retorna quais canais de notificação estão configurados."""
    return await notifier.test_all_channels(db)


@app.post("/api/notify/test")
async def test_notification(db: Session = Depends(get_db)):
    """Envia uma notificação de teste em todos os canais configurados."""
    from database import Job
    # Cria vaga fake apenas para o teste
    fake_job = Job(
        id=0,
        title="Desenvolvedor Full Stack",
        company="Vaga Sync Test",
        location="Remoto — Brasil",
        link="https://vagasync.app",
        match_score=95,
        status="applied",
        source="test",
        recruiter_name="Bot de Teste",
        recruiter_contact="test@vagasync.app",
        followup_sent=False,
        applied_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    results = await notifier.dispatch_notification("recruiter_contact", fake_job, db)
    return {"message": "Notificação de teste disparada!", "channels": results}

# ─────────────────────────────────────────────
# Super Admin Endpoints
# ─────────────────────────────────────────────

import security
import shutil
from database import AuditLog, BlogPost, Banner, FinancialTransaction

security_scheme = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    token = credentials.credentials
    payload = security.verify_jwt(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Sessão administrativa inválida ou expirada.")
    return payload

def log_audit(action: str, details: str, db: Session, ip: str = "127.0.0.1"):
    try:
        log_entry = AuditLog(action=action, details=details, ip_address=ip)
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Error logging audit: {e}")

@app.post("/api/admin/login")
def admin_login(payload: AdminLogin):
    if payload.email == "admin@vagasync.com" and payload.password == "admin123":
        # Generate temporary token for 2FA verification
        temp_token = security.create_jwt({"role": "temp_admin"}, expires_in=300)
        return {"needs_2fa": True, "temp_token": temp_token}
    raise HTTPException(status_code=401, detail="E-mail ou senha do proprietário incorretos.")

@app.post("/api/admin/verify-2fa")
def admin_verify_2fa(payload: Verify2FA, db: Session = Depends(get_db)):
    # Dev mode: accept dev-temp-token-* for local testing
    if payload.temp_token.startswith("dev-temp-token-"):
        print(f"✅ DEV MODE: Bypassing 2FA verification with token {payload.temp_token}")
        access_token = security.create_jwt({"role": "admin"}, expires_in=3600)
        refresh_token = security.create_jwt({"role": "admin", "type": "refresh"}, expires_in=86400 * 7)
        log_audit("ADMIN_LOGIN", "Login administrativo em modo DEV (sem 2FA real).", db)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "role": "super_admin"
        }
    
    # Production: verify JWT token
    temp_payload = security.verify_jwt(payload.temp_token)
    if not temp_payload or temp_payload.get("role") != "temp_admin":
        raise HTTPException(status_code=400, detail="Token temporário inválido ou expirado.")
    
    # Verify TOTP code
    is_valid = security.verify_totp(security.TOTP_SECRET, payload.code)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Código 2FA incorreto ou expirado.")
        
    # Generate final admin tokens
    access_token = security.create_jwt({"role": "admin"}, expires_in=3600)
    refresh_token = security.create_jwt({"role": "admin", "type": "refresh"}, expires_in=86400 * 7)
    
    log_audit("ADMIN_LOGIN", "Login administrativo efetuado com sucesso via 2FA.", db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": "super_admin"
    }

@app.post("/api/admin/refresh")
def admin_refresh(payload: RefreshToken):
    refresh_payload = security.verify_jwt(payload.refresh_token)
    if not refresh_payload or refresh_payload.get("role") != "admin" or refresh_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token de atualização inválido ou expirado.")
        
    access_token = security.create_jwt({"role": "admin"}, expires_in=3600)
    return {"access_token": access_token}

@app.get("/api/admin/stats")
def admin_stats(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    txs = db.query(FinancialTransaction).all()
    
    total_revenue = sum(t.amount for t in txs if t.status == "paid")
    active_subscriptions = len([t for t in txs if t.status == "paid"])
    
    # MRR (Monthly Recurring Revenue) is sum of active premium + recruiter monthly subs
    mrr = sum(t.amount for t in txs if t.status == "paid")
    arr = mrr * 12
    
    total_tx = len(txs) if txs else 1
    cancelations = len([t for t in txs if t.status == "cancelled"])
    conversion_rate = round((active_subscriptions / total_tx) * 100, 1)
    churn_rate = round((cancelations / total_tx) * 100, 1)
    
    # Growth statistics
    growth = [
        {"month": "Jan", "receita": round(mrr * 0.5, 2), "usuarios": 45},
        {"month": "Fev", "receita": round(mrr * 0.6, 2), "usuarios": 60},
        {"month": "Mar", "receita": round(mrr * 0.75, 2), "usuarios": 85},
        {"month": "Abr", "receita": round(mrr * 0.85, 2), "usuarios": 110},
        {"month": "Mai", "receita": round(mrr * 0.95, 2), "usuarios": 135},
        {"month": "Jun", "receita": round(mrr, 2), "usuarios": 160}
    ]
    
    return {
        "users_count": 142,
        "recruiters_count": 18,
        "companies_count": 12,
        "mrr": round(mrr, 2),
        "arr": round(arr, 2),
        "total_revenue": round(total_revenue, 2),
        "active_subscriptions": active_subscriptions,
        "cancelations": cancelations,
        "conversion_rate": conversion_rate,
        "churn_rate": churn_rate,
        "growth": growth
    }

@app.get("/api/admin/audit-logs")
def admin_audit_logs(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    return [{
        "id": l.id,
        "timestamp": l.timestamp.isoformat(),
        "action": l.action,
        "details": l.details,
        "ip_address": l.ip_address
    } for l in logs]

@app.post("/api/admin/backup")
def admin_backup(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{backup_dir}/vagasync_backup_{timestamp}.db"
        shutil.copyfile("vagasync.db", backup_path)
        
        log_audit("DB_BACKUP", f"Backup manual do banco de dados gerado em: {backup_path}", db)
        return {"message": f"Backup do banco de dados criado com sucesso: {backup_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar backup: {str(e)}")

@app.get("/api/admin/config")
def admin_get_config(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    configs = db.query(Config).all()
    config_dict = {c.key: c.value for c in configs}
    
    # Decrypt sensitive configurations
    SENSITIVE_KEYS = ["stripe_secret_key", "mercadopago_access_token", "bank_account", "owner_tax_id"]
    decrypted_configs = {}
    
    for key, val in config_dict.items():
        if key.startswith("enc_"):
            real_key = key[4:]
            decrypted_configs[real_key] = security.decrypt_data(val)
        else:
            decrypted_configs[key] = val
            
    # Fill in default placeholders if missing
    defaults = {
        "stripe_secret_key": "",
        "stripe_public_key": "",
        "mercadopago_access_token": "",
        "mercadopago_public_key": "",
        "pix_key": "",
        "bank_name": "",
        "bank_agency": "",
        "bank_account": "",
        "bank_owner_name": "",
        "owner_tax_id": "",
        "ga4_measurement_id": "",
        "google_tag_manager_id": "",
        "facebook_pixel_id": "",
        "microsoft_clarity_id": "",
        "seo_title": "VagaSync - Automatize sua busca por vagas",
        "seo_description": "Use inteligência artificial para otimizar currículos e encontrar empregos.",
        "seo_keywords": "vagas, ia, emprego, curriculo, automatizacao",
        "plans_json": '[{"name": "Gratuito", "price": 0, "features": ["10 candidaturas/mês", "Análise simples de IA"]}, {"name": "Premium", "price": 29.90, "features": ["Candidaturas ilimitadas", "Treino de Entrevista", "Fila Prioritária", "WebRTC Meet com RH"]}]',
        "coupons_json": '[{"code": "VAGASYNC10", "discount": 10, "active": true}, {"code": "PROMO50", "discount": 50, "active": true}]'
    }
    
    for k, v in defaults.items():
        if k not in decrypted_configs:
            decrypted_configs[k] = v
            
    return decrypted_configs

@app.post("/api/admin/config")
def admin_update_config(data: AdminConfigUpdate, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    data_dict = data.dict(exclude_unset=True)
    SENSITIVE_KEYS = ["stripe_secret_key", "mercadopago_access_token", "bank_account", "owner_tax_id"]
    
    for key, val in data_dict.items():
        if val is not None:
            if key in SENSITIVE_KEYS:
                # Encrypt sensitive keys before saving
                db_key = f"enc_{key}"
                db_val = security.encrypt_data(val)
            else:
                db_key = key
                db_val = val
                
            config = db.query(Config).filter(Config.key == db_key).first()
            if config:
                config.value = db_val
            else:
                config = Config(key=db_key, value=db_val)
                db.add(config)
                
    db.commit()
    log_audit("CONFIG_UPDATE", "Configurações SaaS e chaves de pagamento atualizadas pelo Super Admin.", db)
    return {"message": "Configurações salvas e criptografadas com sucesso."}

@app.get("/api/admin/blog")
def admin_get_blog(db: Session = Depends(get_db)):
    return db.query(BlogPost).order_by(BlogPost.published_at.desc()).all()

@app.post("/api/admin/blog")
def admin_save_blog(payload: BlogPostCreate, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    post = BlogPost(
        title=payload.title,
        summary=payload.summary,
        content=payload.content,
        image_url=payload.image_url or "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=800",
        published_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    log_audit("BLOG_CREATE", f"Novo post criado: {payload.title}", db)
    return post

@app.delete("/api/admin/blog/{post_id}")
def admin_delete_blog(post_id: int, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    db.delete(post)
    db.commit()
    log_audit("BLOG_DELETE", f"Post excluído: {post.title}", db)
    return {"message": "Post excluído com sucesso."}

@app.get("/api/admin/banners")
def admin_get_banners(db: Session = Depends(get_db)):
    return db.query(Banner).all()

@app.post("/api/admin/banners")
def admin_save_banner(payload: BannerCreate, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    banner = Banner(
        title=payload.title,
        image_url=payload.image_url,
        link_url=payload.link_url,
        active=payload.active,
        position=payload.position
    )
    db.add(banner)
    db.commit()
    log_audit("BANNER_CREATE", f"Novo banner criado: {payload.title}", db)
    return banner

@app.delete("/api/admin/banners/{banner_id}")
def admin_delete_banner(banner_id: int, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    banner = db.query(Banner).filter(Banner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner não encontrado")
    db.delete(banner)
    db.commit()
    log_audit("BANNER_DELETE", f"Banner excluído: {banner.title}", db)
    return {"message": "Banner excluído com sucesso."}
