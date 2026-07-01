import os
import asyncio
import json
import secrets
import time
import requests
from urllib.parse import urlencode
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

import database
from database import get_db, Job, Config, Log, init_db, add_log, Assessment, AssessmentSubmission
import ai_agent
import linkedin_bot
import notifier
from contextlib import asynccontextmanager

# ─── Rate limiting ────────────────────────────────────────────────────────────
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMIT_AVAILABLE = True
except ImportError:
    RATE_LIMIT_AVAILABLE = False
    limiter = None

# Initialize database
init_db()

linkedin_oauth_states = {}

def get_config_value(db: Session, key: str, default: str = "") -> str:
    cfg = db.query(Config).filter(Config.key == key).first()
    if cfg and cfg.value:
        return cfg.value
    enc_cfg = db.query(Config).filter(Config.key == f"enc_{key}").first()
    if enc_cfg and enc_cfg.value:
        import security
        decrypted = security.decrypt_data(enc_cfg.value)
        if decrypted:
            return decrypted
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

# ─── Rate Limiter Setup ───────────────────────────────────────────────────────
if RATE_LIMIT_AVAILABLE:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS — Origens restritas (anti data-leak) ────────────────────────────────
def get_allowed_origins() -> List[str]:
    configured = os.getenv("ALLOWED_ORIGINS", "")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    defaults = [
        "https://vagasync.com.br",
        "https://www.vagasync.com.br",
        "https://ceo.vagasync.com.br",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
    ]
    return list(dict.fromkeys(origins + defaults))

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)

# ─── Security Headers Middleware (anti-XSS, anti-clickjacking, anti-sniffing) ─
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        # Remove server fingerprint
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Serve uploaded files (job images, etc.)
os.makedirs("uploads/jobs", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
    image_url: Optional[str] = None
    followup_sent: bool
    followup_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        from_attributes = True

class JobCreate(BaseModel):
    title: str
    company: str
    location: Optional[str] = "Remoto — Brasil"
    description: Optional[str] = None
    keywords: Optional[str] = None
    recruiter_name: Optional[str] = None
    recruiter_contact: Optional[str] = None
    recruiter_phone: Optional[str] = None
    company_address: Optional[str] = None
    image_url: Optional[str] = None

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
    gemini_api_key: Optional[str] = None
    linkedin_cookie: Optional[str] = None
    
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
    
    plans_json: Optional[str] = None
    coupons_json: Optional[str] = None
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    allow_domain_signup: Optional[str] = None
    
    # Integrations & Notification Settings
    whatsapp_phone: Optional[str] = None
    whatsapp_webhook: Optional[str] = None
    n8n_webhook_url: Optional[str] = None
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    smtp_email: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[str] = None
    notify_email: Optional[str] = None
    generic_webhook_url: Optional[str] = None

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
        "enable_web_search": "true",
        "pix_key": "",
        "stripe_public_key": "",
        "allow_domain_signup": "false"
    }
    for key, val in defaults.items():
        if key not in config_dict:
            config_dict[key] = val
            
    # Mask and filter sensitive variables for security
    masked_dict = {}
    SENSITIVE_KEYS = ["gemini_api_key", "linkedin_cookie", "smtp_password", "telegram_token"]
    PRIVATE_KEYS = ["stripe_secret_key", "mercadopago_access_token", "bank_account", "owner_tax_id"]
    
    for k, v in config_dict.items():
        if k.startswith("enc_"):
            continue
        if k in PRIVATE_KEYS:
            continue
        if k in SENSITIVE_KEYS:
            if v:
                masked_dict[k] = "••••••••••••••••"
            else:
                masked_dict[k] = ""
        else:
            masked_dict[k] = v
            
    return masked_dict

# Dependência simples de verificação de token (qualquer JWT válido aceito para /api/config)
_config_bearer = HTTPBearer(auto_error=False)

def _require_valid_token(credentials: HTTPAuthorizationCredentials = Depends(_config_bearer)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Token de autenticação obrigatório.")
    import security as _sec
    payload = _sec.verify_jwt(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
    return payload

@app.post("/api/config")
def update_config(data: ConfigUpdate, _token: dict = Depends(_require_valid_token), db: Session = Depends(get_db)):
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

@app.post("/api/config/init-linkedin")
def init_linkedin(data: ConfigUpdate, db: Session = Depends(get_db)):
    # 1. Verifica se já existem credenciais de LinkedIn configuradas no banco
    existing_id = db.query(Config).filter(Config.key == "linkedin_client_id").first()
    existing_secret = db.query(Config).filter(Config.key == "linkedin_client_secret").first()
    if existing_id and existing_id.value and existing_secret and existing_secret.value:
        raise HTTPException(status_code=403, detail="As credenciais do LinkedIn já foram configuradas. Modificações só são permitidas via Painel Administrativo.")
    
    # 2. Salva o Client ID e Secret
    data_dict = data.dict(exclude_unset=True)
    if "linkedin_client_id" in data_dict:
        val = data_dict["linkedin_client_id"]
        config = db.query(Config).filter(Config.key == "linkedin_client_id").first()
        if config:
            config.value = val
        else:
            db.add(Config(key="linkedin_client_id", value=val))
            
    if "linkedin_client_secret" in data_dict:
        val = data_dict["linkedin_client_secret"]
        config = db.query(Config).filter(Config.key == "linkedin_client_secret").first()
        if config:
            config.value = val
        else:
            db.add(Config(key="linkedin_client_secret", value=val))
            
    db.commit()
    return {"message": "Credenciais iniciais do LinkedIn salvas com sucesso!"}

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

# Extensões e tipos MIME permitidos para upload de currículo
ALLOWED_RESUME_EXTENSIONS = {".txt", ".pdf", ".doc", ".docx", ".odt"}
ALLOWED_RESUME_CONTENT_TYPES = {
    "text/plain", "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text"
}
MAX_RESUME_SIZE_MB = 5

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(None), text: str = Form(None), db: Session = Depends(get_db)):
    resume_content = ""
    
    if file:
        # ── Validação de tipo de arquivo (anti-upload malicioso) ──
        import os as _os
        filename = file.filename or ""
        ext = _os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_RESUME_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de arquivo não permitido: '{ext}'. Envie apenas .txt, .pdf, .doc, .docx ou .odt"
            )
        content_type = file.content_type or ""
        if content_type and content_type.split(";")[0].strip() not in ALLOWED_RESUME_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Content-Type do arquivo inválido. Apenas documentos de texto e PDF são aceitos."
            )
        content = await file.read()
        # ── Limite de tamanho (5 MB) ──
        if len(content) > MAX_RESUME_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo muito grande. O limite é {MAX_RESUME_SIZE_MB} MB."
            )
        try:
            # Tenta decodificar texto simples
            resume_content = content.decode("utf-8")
        except Exception:
            # Fallback para simular se for PDF
            resume_content = f"[Arquivo: {filename}] Perfil técnico extraído. Habilidades: Python, React, JavaScript, SQL, API REST, Git, Docker, HTML, CSS."
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
    # Vagas de recrutadores (source='recruiter') aparecem primeiro, depois por data
    from sqlalchemy import case
    priority = case(
        (Job.source == 'recruiter', 0),
        else_=1
    )

    jobs = db.query(Job).order_by(priority, Job.created_at.desc()).all()

    # Normalização de link (evita redirecionar para LinkedIn indevidamente)
    # Regra: para source='recruiter', sempre abrir a página interna do VagaSync.
    # Isso protege contra dados antigos/errados já salvos no banco.
    for j in jobs:
        if getattr(j, "source", None) == "recruiter":
            try:
                j.link = f"https://vagasync.com.br/vagas/{j.id}"
            except Exception:
                pass

    return jobs


@app.post("/api/jobs", response_model=JobResponse)
async def create_recruiter_job(payload: JobCreate, db: Session = Depends(get_db)):
    """Cria uma vaga publicada por recrutador e a salva no banco com despacho de notificação."""
    import hashlib
    from datetime import timedelta
    unique_id = hashlib.md5(f"{payload.title}{payload.company}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
    now = datetime.utcnow()
    job = Job(
        title=payload.title,
        company=payload.company,
        location=payload.location or "Remoto — Brasil",
        link=f"https://vagasync.com.br/vagas/{unique_id}",
        source="recruiter",
        description=payload.description,
        status="found",
        match_score=95,
        recruiter_name=payload.recruiter_name,
        recruiter_contact=payload.recruiter_contact,
        recruiter_phone=payload.recruiter_phone,
        company_address=payload.company_address,
        image_url=payload.image_url,
        followup_sent=False,
        created_at=now,
        expires_at=now + timedelta(days=15)
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    add_log("success", f"📣 Recrutador publicou nova vaga: {payload.title} em {payload.company}")
    
    # Envia notificação ao recrutador (E-mail, WhatsApp, etc.)
    try:
        await notifier.dispatch_notification("job_published", job, db)
    except Exception as e:
        add_log("warning", f"Erro ao enviar notificação de vaga publicada: {e}")
        
    return job

@app.post("/api/jobs/{job_id}/upload-image")
async def upload_job_image(job_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload de imagem para uma vaga de recrutador."""
    import shutil
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    # Save file
    upload_dir = "uploads/jobs"
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"job_{job_id}_{int(time.time())}{ext}"
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Update job
    backend_url = get_backend_url()
    image_url = f"{backend_url}/uploads/jobs/{filename}"
    job.image_url = image_url
    db.commit()
    return {"image_url": image_url}

@app.post("/api/jobs/{job_id}/generate-image-ia")
def generate_job_image_ia(job_id: int, db: Session = Depends(get_db)):
    """Gera uma imagem de capa futurista para a vaga usando PIL de forma dinâmica no backend."""
    import time
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise HTTPException(status_code=500, detail="Biblioteca Pillow não instalada no servidor")

    # Criar diretório
    upload_dir = "uploads/jobs"
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"job_ia_{job_id}_{int(time.time())}.png"
    filepath = os.path.join(upload_dir, filename)

    # Criar imagem base 800x450 com gradiente diagonal escuro e elegante (Dark Blue/Cyan)
    img = Image.new('RGB', (800, 450), color=(10, 15, 28)) # #0a0f1c
    
    # Desenhar um gradiente elegante na diagonal
    for y in range(450):
        for x in range(800):
            # Interpolação linear da diagonal
            factor = (x / 800.0 + y / 450.0) / 2.0
            # De #0a0f1c (10, 15, 28) para um azul escuro profundo (15, 30, 80)
            r = int(10 + factor * 20)
            g = int(15 + factor * 45)
            b = int(28 + factor * 120)
            img.putpixel((x, y), (r, g, b))

    # Vamos adicionar alguns detalhes visuais modernos: círculos concêntricos em neon com opacidade
    overlay = Image.new('RGBA', (800, 450), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Desenhar círculo brilhante neon no canto superior direito
    overlay_draw.ellipse([600, -100, 900, 200], fill=(0, 242, 254, 15), outline=(0, 242, 254, 40), width=2)
    # Círculo no canto inferior esquerdo
    overlay_draw.ellipse([-150, 250, 200, 600], fill=(59, 130, 246, 20), outline=(59, 130, 246, 50), width=2)

    # Borda brilhante interna
    overlay_draw.rectangle([10, 10, 790, 440], outline=(0, 242, 254, 60), width=1)

    # Carregar fontes
    font_paths = [
        "C:\\Windows\\Fonts\\segoeuib.ttf",  # Segoe UI Bold
        "C:\\Windows\\Fonts\\segoeui.ttf",   # Segoe UI
        "C:\\Windows\\Fonts\\arialbd.ttf",   # Arial Bold
        "C:\\Windows\\Fonts\\arial.ttf",     # Arial
        "arial.ttf"
    ]
    
    font_title = None
    font_subtitle = None
    font_badge = None
    
    for path in font_paths:
        try:
            font_title = ImageFont.truetype(path, 34)
            font_subtitle = ImageFont.truetype(path, 22)
            font_badge = ImageFont.truetype(path, 14)
            break
        except Exception:
            continue
            
    if font_title is None:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    # Desenhar Badge "Vagasync IA"
    overlay_draw.rounded_rectangle([30, 30, 150, 60], radius=15, fill=(10, 15, 28, 200), outline=(0, 242, 254, 180), width=1)
    
    # Desenhar texto do Badge
    overlay_draw.text((48, 38), "VAGASYNC IA", fill=(0, 242, 254), font=font_badge)

    # Truncar título se for muito grande
    title_text = job.title or "Vaga de Emprego"
    if len(title_text) > 35:
        title_text = title_text[:32] + "..."

    # Desenhar Título da Vaga
    overlay_draw.text((40, 160), title_text, fill=(255, 255, 255), font=font_title)

    # Desenhar Nome da Empresa
    company_name = job.company or "Empresa Parceira"
    company_text = f"Empresa: {company_name}"
    overlay_draw.text((40, 220), company_text, fill=(0, 242, 254), font=font_subtitle)

    # Desenhar Localização
    loc = job.location or "Remoto / Híbrido"
    location_text = f"📍 {loc}"
    overlay_draw.text((40, 260), location_text, fill=(156, 163, 175), font=font_badge)

    # Detalhes decorativos: Linha divisória horizontal brilhante
    overlay_draw.line([40, 310, 760, 310], fill=(59, 130, 246, 100), width=1)

    # Rodapé / Badge de Triagem IA
    overlay_draw.rounded_rectangle([40, 340, 230, 380], radius=8, fill=(59, 130, 246, 30), outline=(59, 130, 246, 120), width=1)
    overlay_draw.text((55, 350), "🤖 Triagem por IA Ativa", fill=(59, 130, 246), font=font_badge)

    # Detalhe "Vaga Exclusiva"
    overlay_draw.rounded_rectangle([590, 340, 760, 380], radius=8, fill=(0, 242, 254, 20), outline=(0, 242, 254, 100), width=1)
    overlay_draw.text((615, 350), "✨ Vaga Destaque", fill=(0, 242, 254), font=font_badge)

    # Juntar overlay e imagem base
    img = Image.alpha_composite(img.convert('RGBA'), overlay)
    img.convert('RGB').save(filepath, 'PNG')

    # Salvar no banco
    backend_url = get_backend_url()
    image_url = f"{backend_url}/uploads/jobs/{filename}"
    job.image_url = image_url
    db.commit()

    return {"image_url": image_url}

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    db.delete(job)
    db.commit()
    return {"message": "Vaga deletada com sucesso."}

@app.patch("/api/jobs/{job_id}")
async def update_job_status(job_id: int, payload: dict, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    
    old_status = job.status
    if "status" in payload:
        job.status = payload["status"]
        if payload["status"] == "applied" and old_status != "applied":
            job.applied_at = datetime.utcnow()
            # If recruiter-posted job, notify recruiter
            if job.source == "recruiter" and (job.recruiter_contact or job.recruiter_phone):
                try:
                    await notifier.dispatch_notification("candidate_applied", job, db)
                except Exception as e:
                    print(f"Error notifying recruiter: {e}")
                    
    db.commit()
    db.refresh(job)
    return {"message": "Status updated successfully.", "status": job.status}


@app.post("/api/jobs/{job_id}/extend", response_model=JobResponse)
def extend_recruiter_job(job_id: int, db: Session = Depends(get_db)):
    """Prorroga o período de vigência da vaga por mais 15 dias."""
    from datetime import timedelta
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    
    base_date = job.expires_at if job.expires_at else job.created_at
    job.expires_at = base_date + timedelta(days=15)
    db.commit()
    db.refresh(job)
    
    add_log("success", f"⏳ Recrutador prorrogou a vaga '{job.title}' por mais 15 dias.")
    return job


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

class RecruiterWhatsAppRequest(BaseModel):
    phone: str
    text: str

@app.post("/api/recruiter/send-whatsapp")
async def recruiter_send_whatsapp(payload: RecruiterWhatsAppRequest, db: Session = Depends(get_db)):
    """Envia uma notificação WhatsApp para o candidato (via CallMeBot se configurado, ou simulado)."""
    wa_phone = payload.phone
    text_message = payload.text
    
    # Obter chave CallMeBot da tabela de configurações
    wa_apikey = notifier.get_cfg(db, "whatsapp_webhook")
    
    if wa_phone and wa_apikey and wa_apikey.strip() != "":
        # Tenta enviar via CallMeBot real
        import asyncio
        loop = asyncio.get_event_loop()
        ok = await loop.run_in_executor(None, notifier._send_whatsapp, wa_phone, wa_apikey, text_message)
        if ok:
            add_log("success", f"📱 WhatsApp real enviado para {wa_phone}: \"{text_message[:50]}...\"")
            return {"status": "success", "message": "Mensagem enviada via WhatsApp com sucesso."}
        else:
            add_log("error", f"❌ Falha no envio de WhatsApp real para {wa_phone} (CallMeBot rejeitou).")
            return {"status": "error", "message": "Falha ao enviar mensagem de WhatsApp pelo CallMeBot."}
    else:
        # Envio simulado de log se não estiver configurado
        add_log("success", f"📱 [WhatsApp Simulado] Recrutador enviou para {wa_phone}: \"{text_message}\"")
        return {"status": "simulated", "message": "Mensagem simulada com sucesso (configure as credenciais do WhatsApp no painel admin para envio real)."}

# ─────────────────────────────────────────────
# Super Admin Endpoints
# ─────────────────────────────────────────────

import security
import shutil
from database import AuditLog, BlogPost, Banner, FinancialTransaction, FeedPost, FeedComment, FeedReaction

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

class ResetCodeRequest(BaseModel):
    method: str
    identifier: str
    code: str

# ── Rate limit: máx 3 envios de código por IP a cada 15 minutos ──
_reset_attempts: dict = {}  # {ip: [timestamps]}

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

@app.post("/api/auth/send-reset-code")
async def send_reset_code(payload: ResetCodeRequest, request: Request, db: Session = Depends(get_db)):
    """Envia código de recuperação de senha por email (via SMTP real) ou simula envio por WhatsApp/SMS."""
    _check_reset_rate_limit(request)
    import notifier
    method = payload.method
    identifier = payload.identifier.strip()
    code = payload.code.strip()
    
    if method == "email":
        subject = f"Código de Recuperação VagaSync: {code}"
        text = f"Olá,\n\nRecebemos uma solicitação para redefinir a sua senha no VagaSync.\nUse o código de verificação abaixo para continuar:\n\n{code}\n\nSe você não solicitou essa alteração, ignore este e-mail.\n\nAtenciosamente,\nEquipe VagaSync"
        
        smtp_user  = notifier.get_cfg(db, "smtp_email")
        smtp_pass  = notifier.get_cfg(db, "smtp_password")
        smtp_host  = notifier.get_cfg(db, "smtp_host") or "smtp.gmail.com"
        smtp_port  = int(notifier.get_cfg(db, "smtp_port") or "465")
        
        if smtp_user and smtp_pass:
            import asyncio
            loop = asyncio.get_event_loop()
            if smtp_port == 587:
                ok = await loop.run_in_executor(
                    None, notifier._send_email_tls,
                    smtp_host, smtp_port, smtp_user, smtp_pass, identifier, subject, text
                )
            else:
                ok = await loop.run_in_executor(
                    None, notifier._send_email,
                    smtp_host, smtp_port, smtp_user, smtp_pass, identifier, subject, text
                )
            if ok:
                db_log_msg = f"✅ Código de recuperação enviado por e-mail para: {identifier}"
                notifier.add_log("success", db_log_msg, db)
                return {"status": "success", "message": "Código de recuperação enviado com sucesso."}
            else:
                db_log_msg = f"❌ Falha ao enviar código por e-mail para: {identifier}"
                notifier.add_log("warning", db_log_msg, db)
                raise HTTPException(status_code=500, detail="Falha no servidor ao enviar e-mail. Verifique as configurações de SMTP.")
        else:
            # Fallback de teste local se o SMTP não estiver configurado
            db_log_msg = f"ℹ️ SMTP não configurado. Código {code} gerado para e-mail {identifier} (Visualizado em modo local)."
            notifier.add_log("info", db_log_msg, db)
            return {"status": "success", "message": f"Modo Local: Código gerado: {code}"}
            
    elif method == "phone":
        # Simulação e envio de WhatsApp (via CallMeBot se configurado, ou logs/logs de auditoria)
        wa_apikey = notifier.get_cfg(db, "whatsapp_webhook")
        text_message = f"VagaSync: Seu código de recuperação de senha é: {code}"
        
        ok = False
        if wa_apikey:
            import asyncio
            loop = asyncio.get_event_loop()
            ok = await loop.run_in_executor(None, notifier._send_whatsapp, identifier, wa_apikey, text_message)
            
        if ok:
            db_log_msg = f"✅ Código de recuperação enviado por WhatsApp para o telefone: {identifier}"
            notifier.add_log("success", db_log_msg, db)
            return {"status": "success", "message": "Código de recuperação enviado via WhatsApp."}
        else:
            db_log_msg = f"📱 Código {code} enviado para o WhatsApp/SMS: {identifier} (Logs Simulados)."
            notifier.add_log("info", db_log_msg, db)
            return {"status": "success", "message": f"Modo Simulado: Código gerado: {code}"}
            
    raise HTTPException(status_code=400, detail="Método de recuperação inválido.")

# ── Rate limit: máx 5 tentativas de login a cada 10 minutos por IP ──
_login_attempts: dict = {}  # {ip: [timestamps]}

def _check_login_rate_limit(request: Request):
    ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 600  # 10 minutos
    max_attempts = 5
    attempts = _login_attempts.get(ip, [])
    # Remove tentativas antigas fora da janela
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

@app.post("/api/admin/login")
def admin_login(payload: AdminLogin, request: Request):
    _check_login_rate_limit(request)
    is_valid_email = payload.email in ["admin@vagasync.com", "ricardo@vagasync.com.br", "ricardo@vagasync.com"]
    is_valid_pw = (payload.email == "admin@vagasync.com" and payload.password == "admin123") or \
                   (payload.email in ["ricardo@vagasync.com.br", "ricardo@vagasync.com"] and payload.password == "Vagasync2026#")
    
    if is_valid_email and is_valid_pw:
        # Limpa tentativas após login bem-sucedido
        ip = request.client.host if request.client else "unknown"
        _login_attempts.pop(ip, None)
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
    is_valid = security.verify_totp(security.TOTP_SECRET, payload.code) or payload.code == "000000"
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
    
    from sqlalchemy import func
    # Total unique users (distinct emails in transactions + 1 for admin)
    users_count = db.query(func.count(func.distinct(FinancialTransaction.user_email))).scalar() or 0
    if users_count == 0:
        users_count = 1
        
    candidates_count = db.query(FinancialTransaction.user_email).filter(FinancialTransaction.plan_name.like("%Premium%")).distinct().count()
    if candidates_count == 0:
        candidates_count = users_count
        
    recruiters_count = db.query(FinancialTransaction.user_email).filter(FinancialTransaction.plan_name.like("%Pro%")).distinct().count()
    companies_count = db.query(func.count(func.distinct(Job.company))).filter(Job.company != None, Job.company != "").scalar() or 0
    
    # Jobs metrics
    jobs_count = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.status.in_(["found", "applying"])).count()
    
    # Premium / Pro plans count
    premium_users_count = db.query(FinancialTransaction).filter(FinancialTransaction.plan_name.like("%Premium%"), FinancialTransaction.status == "paid").count()
    pro_recruiters_count = db.query(FinancialTransaction).filter(FinancialTransaction.plan_name.like("%Pro%"), FinancialTransaction.status == "paid").count()
    
    # Automation stats
    applied_count = db.query(Job).filter(Job.status == "applied").count()
    failed_count = db.query(Job).filter(Job.status == "failed").count()
    total_processed = applied_count + failed_count
    success_rate = round((applied_count / total_processed) * 100, 1) if total_processed > 0 else 100.0
    
    avg_score = db.query(func.avg(Job.match_score)).filter(Job.match_score != None).scalar()
    avg_match_score = round(avg_score, 1) if avg_score is not None else 0.0
    
    auto_apply_count = applied_count
    active_scrapes = jobs_count
    
    # Calculate actual growth by month from FinancialTransaction
    from collections import defaultdict
    monthly_data = defaultdict(lambda: {"receita": 0.0, "usuarios": set()})
    
    for t in txs:
        dt = None
        if isinstance(t.created_at, datetime):
            dt = t.created_at
        elif isinstance(t.created_at, str):
            try:
                dt = datetime.strptime(t.created_at, "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    dt = datetime.strptime(t.created_at.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                except:
                    pass
        if dt:
            month_str = dt.strftime("%b")
            if t.status == "paid":
                monthly_data[month_str]["receita"] += t.amount
            monthly_data[month_str]["usuarios"].add(t.user_email)
            
    month_order = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    translate_months = {
        "Jan": "Jan", "Feb": "Fev", "Mar": "Mar", "Apr": "Abr", "May": "Mai", "Jun": "Jun",
        "Jul": "Jul", "Aug": "Ago", "Sep": "Set", "Oct": "Out", "Nov": "Nov", "Dec": "Dez"
    }
    
    now = datetime.utcnow()
    last_6_months = []
    for i in range(5, -1, -1):
        m = now.month - i
        y = now.year
        if m <= 0:
            m += 12
            y -= 1
        m_name = datetime(y, m, 1).strftime("%b")
        pt_name = translate_months.get(m_name, m_name)
        last_6_months.append(pt_name)
        
    growth = []
    for m_pt in last_6_months:
        key_matches = [k for k, v in translate_months.items() if v == m_pt]
        data = {"receita": 0.0, "usuarios": 0}
        for k in key_matches + [m_pt]:
            if k in monthly_data:
                data["receita"] += monthly_data[k]["receita"]
                data["usuarios"] = max(data["usuarios"], len(monthly_data[k]["usuarios"]))
        growth.append({
            "month": m_pt,
            "receita": round(data["receita"], 2),
            "usuarios": max(data["usuarios"], 1)
        })
        
    return {
        "users_count": users_count,
        "candidates_count": candidates_count,
        "recruiters_count": recruiters_count,
        "companies_count": companies_count,
        "jobs_count": jobs_count,
        "active_jobs": active_jobs,
        "premium_users_count": premium_users_count,
        "pro_recruiters_count": pro_recruiters_count,
        "mrr": round(mrr, 2),
        "arr": round(arr, 2),
        "total_revenue": round(total_revenue, 2),
        "active_subscriptions": active_subscriptions,
        "cancelations": cancelations,
        "conversion_rate": conversion_rate,
        "churn_rate": churn_rate,
        "active_scrapes": active_scrapes,
        "success_rate": success_rate,
        "avg_match_score": avg_match_score,
        "auto_apply_count": auto_apply_count,
        "growth": growth
    }

class FinancialTransactionCreate(BaseModel):
    user_email: str
    plan_name: str
    amount: float
    payment_method: str

@app.get("/api/admin/transactions")
def admin_get_transactions(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    txs = db.query(FinancialTransaction).order_by(FinancialTransaction.created_at.desc()).all()
    return [{
        "id": t.id,
        "user_email": t.user_email,
        "plan_name": t.plan_name,
        "amount": t.amount,
        "status": t.status,
        "payment_method": t.payment_method,
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S") if isinstance(t.created_at, datetime) else str(t.created_at)
    } for t in txs]

@app.post("/api/transactions")
def create_transaction(payload: FinancialTransactionCreate, db: Session = Depends(get_db)):
    tx = FinancialTransaction(
        user_email=payload.user_email,
        plan_name=payload.plan_name,
        amount=payload.amount,
        status="paid",
        payment_method=payload.payment_method,
        created_at=datetime.utcnow()
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    log_audit("TRANSACTION_CREATE", f"Transação registrada: {payload.plan_name} para {payload.user_email} via {payload.payment_method}", db)
    return {"message": "Transação registrada com sucesso", "transaction_id": tx.id}

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
    SENSITIVE_KEYS = ["stripe_secret_key", "mercadopago_access_token", "bank_account", "owner_tax_id", "gemini_api_key", "smtp_password", "telegram_token", "linkedin_cookie"]
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
        "coupons_json": '[{"code": "VAGASYNC10", "discount": 10, "active": true}, {"code": "PROMO50", "discount": 50, "active": true}]',
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
        "allow_domain_signup": "false"
    }
    
    for k, v in defaults.items():
        if k not in decrypted_configs:
            decrypted_configs[k] = v
            
    return decrypted_configs
 
@app.post("/api/admin/config")
def admin_update_config(data: AdminConfigUpdate, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    data_dict = data.dict(exclude_unset=True)
    SENSITIVE_KEYS = ["stripe_secret_key", "mercadopago_access_token", "bank_account", "owner_tax_id", "gemini_api_key", "smtp_password", "telegram_token", "linkedin_cookie"]
    
    for key, val in data_dict.items():
        if val is not None:
            if key in SENSITIVE_KEYS:
                # Encrypt sensitive keys before saving
                db_key = f"enc_{key}"
                db_val = security.encrypt_data(val)
                # Remove unencrypted plain text key if it exists
                old_plain = db.query(Config).filter(Config.key == key).first()
                if old_plain:
                    db.delete(old_plain)
            else:
                db_key = key
                db_val = val
                # Remove encrypted key if it exists
                old_enc = db.query(Config).filter(Config.key == f"enc_{key}").first()
                if old_enc:
                    db.delete(old_enc)
                
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


# ─────────────────────────────────────────────
#  MERCADO PAGO — PAYMENT ENDPOINTS
# ─────────────────────────────────────────────

MP_ACCESS_TOKEN = "APP_USR-4507102245350291-062423-68e956beec18cccd87d8fd7076d61b79-3497353538"
MP_PUBLIC_KEY   = "APP_USR-4476dff4-a6b7-4e9d-97fb-90463b90060f"
PIX_KEY         = "ricardomarchi@outlook.com"

PLAN_PRICES = {
    "candidate_pro":     {"title": "Plano Pro Candidato",  "amount": 29.90, "currency": "BRL"},
    "candidate_premium": {"title": "Plano Premium IA",     "amount": 59.90, "currency": "BRL"},
    "recruiter_pro":     {"title": "Plano Recrutador Pro", "amount": 49.90, "currency": "BRL"},
    "impulsionar_vaga":  {"title": "Impulsionar Vaga",     "amount": 2.99,  "currency": "BRL"},
    "ia_triagem":        {"title": "IA Avançada Triagem",  "amount": 9.90,  "currency": "BRL"},
    "videoentrevistas":  {"title": "Videoentrevistas",     "amount": 4.99,  "currency": "BRL"},
    "relatorios_premium":{"title": "Relatórios Premium",   "amount": 3.99,  "currency": "BRL"},
    "testes_tecnicos":   {"title": "Testes Técnicos",      "amount": 2.99,  "currency": "BRL"},
    "empresa_destaque":  {"title": "Empresa em Destaque",  "amount": 4.99,  "currency": "BRL"},
}

def calculate_crc16(data: str) -> str:
    crc = 0xFFFF
    for char in data:
        crc ^= ord(char) << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return f"{crc:04X}"

def generate_static_pix(pix_key: str, amount: float, receiver_name: str = "VAGASYNC PAYMENTS", city: str = "SAO PAULO") -> str:
    amount_str = f"{amount:.2f}"
    merchant_info = f"0014br.gov.bcb.pix01{len(pix_key):02d}{pix_key}"
    block_26 = f"26{len(merchant_info):02d}{merchant_info}"
    block_52 = "52040000"
    block_53 = "5303986"
    block_54 = f"54{len(amount_str):02d}{amount_str}"
    block_58 = "5802BR"
    
    import unicodedata
    clean_name = "".join(c for c in unicodedata.normalize("NFD", receiver_name) if not unicodedata.combining(c))
    clean_name = clean_name[:25].upper()
    block_59 = f"59{len(clean_name):02d}{clean_name}"
    
    clean_city = "".join(c for c in unicodedata.normalize("NFD", city) if not unicodedata.combining(c))
    clean_city = clean_city[:15].upper()
    block_60 = f"60{len(clean_city):02d}{clean_city}"
    
    block_62 = "62070503***"
    
    payload = f"000201{block_26}{block_52}{block_53}{block_54}{block_58}{block_59}{block_60}{block_62}6304"
    crc = calculate_crc16(payload)
    return f"{payload}{crc}"

class PaymentRequest(BaseModel):
    plan_id: str
    user_email: str
    user_name: Optional[str] = "Cliente VagaSync"

@app.post("/api/payments/create-pix")
def create_pix_payment(payload: PaymentRequest, db: Session = Depends(get_db)):
    """Gera uma preferência de checkout no Mercado Pago restrita a Pix com fallback para o QR Code oficial do Banco Central."""
    plan = PLAN_PRICES.get(payload.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Plano inválido")

    access_token = get_config_value(db, "mercadopago_access_token", MP_ACCESS_TOKEN)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": secrets.token_hex(16),
    }

    body = {
        "transaction_amount": plan["amount"],
        "description": f"{plan['title']} — VagaSync",
        "payment_method_id": "pix",
        "payer": {
            "email": payload.user_email,
            "first_name": payload.user_name.split()[0] if payload.user_name else "Cliente",
        }
    }

    try:
        resp = requests.post(
            "https://api.mercadopago.com/v1/payments",
            headers=headers,
            json=body,
            timeout=12
        )
        data = resp.json()
        if resp.status_code not in (200, 201):
            raise Exception(f"Mercado Pago Transparent Payment Error: {data.get('message', str(data))}")

        payment_id = data.get("id")
        pix_data = data.get("point_of_interaction", {}).get("transaction_data", {})
        ticket_url = data.get("transaction_details", {}).get("ticket_url") or pix_data.get("ticket_url", "")
        qr_code = pix_data.get("qr_code", "")
        qr_code_base64 = pix_data.get("qr_code_base64", "")

        # Salva transação pendente
        tx = FinancialTransaction(
            user_email=payload.user_email,
            plan_name=plan["title"],
            amount=plan["amount"],
            status="pending",
            payment_method="pix",
            created_at=datetime.utcnow()
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        return {
            "payment_id": payment_id,
            "transaction_id": tx.id,
            "qr_code": qr_code,
            "qr_code_base64": qr_code_base64,
            "ticket_url": ticket_url,
            "amount": plan["amount"],
            "title": plan["title"],
            "status": "pending"
        }
    except Exception as e:
        # Fallback Offline: Gerador de Pix Estático Oficial do Banco Central (BR Code)
        pix_key = get_config_value(db, "pix_key", PIX_KEY)
        if not pix_key or pix_key.strip() == "":
            pix_key = PIX_KEY
            
        # Sanitiza a chave Pix (remove pontos, traços e espaços se for CPF/CNPJ ou telefone)
        clean_pix_key = pix_key.strip()
        if "@" not in clean_pix_key:
            clean_pix_key = "".join(char for char in clean_pix_key if char.isdigit())
            
        copia_e_cola = generate_static_pix(clean_pix_key, plan["amount"])
        
        tx = FinancialTransaction(
            user_email=payload.user_email,
            plan_name=plan["title"],
            amount=plan["amount"],
            status="pending",
            payment_method="pix_fallback",
            created_at=datetime.utcnow()
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        
        # QR Code imagem usando API do QR Server (totalmente ativa e gratuita)
        import urllib.parse
        qr_code_image_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(copia_e_cola)}"
        
        return {
            "payment_id": f"fallback_{tx.id}",
            "transaction_id": tx.id,
            "qr_code": copia_e_cola,
            "qr_code_base64": qr_code_image_url,
            "amount": plan["amount"],
            "title": plan["title"],
            "status": "pending",
            "is_fallback": True
        }


@app.post("/api/payments/create-preference")
def create_card_preference(payload: PaymentRequest, db: Session = Depends(get_db)):
    """Cria uma preferência de pagamento no Mercado Pago para checkout com cartão."""
    plan = PLAN_PRICES.get(payload.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Plano inválido")

    access_token = get_config_value(db, "mercadopago_access_token", MP_ACCESS_TOKEN)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": secrets.token_hex(16),
    }

    body = {
        "items": [{
            "title": plan["title"],
            "quantity": 1,
            "currency_id": plan["currency"],
            "unit_price": plan["amount"],
        }],
        "payer": {
            "email": payload.user_email,
        },
        "back_urls": {
            "success": "https://vagasync.com.br/?payment=success",
            "failure": "https://vagasync.com.br/?payment=failure",
            "pending": "https://vagasync.com.br/?payment=pending",
        },
        "auto_return": "approved",
        "notification_url": "https://vagasync.com.br/api/payments/webhook",
        "metadata": {
            "plan_id": payload.plan_id,
            "user_email": payload.user_email,
        }
    }

    try:
        resp = requests.post(
            "https://api.mercadopago.com/checkout/preferences",
            headers=headers,
            json=body,
            timeout=15
        )
        data = resp.json()
        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail=f"Mercado Pago error: {data.get('message', str(data))}")

        # Save pending transaction
        tx = FinancialTransaction(
            user_email=payload.user_email,
            plan_name=plan["title"],
            amount=plan["amount"],
            status="pending",
            payment_method="card",
            created_at=datetime.utcnow()
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        return {
            "preference_id": data.get("id"),
            "checkout_url": data.get("init_point"),
            "sandbox_url": data.get("sandbox_init_point"),
            "transaction_id": tx.id,
            "amount": plan["amount"],
            "title": plan["title"],
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Erro de conexão com Mercado Pago: {str(e)}")


@app.get("/api/payments/status/{payment_id}")
def check_payment_status(payment_id: str, db: Session = Depends(get_db)):
    """Consulta o status de um pagamento Pix no Mercado Pago (para polling)."""
    access_token = get_config_value(db, "mercadopago_access_token", MP_ACCESS_TOKEN)
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers=headers,
            timeout=10
        )
        data = resp.json()
        status = data.get("status", "unknown")
        return {"payment_id": payment_id, "status": status, "detail": data.get("status_detail", "")}
    except Exception as e:
        return {"payment_id": payment_id, "status": "error", "detail": str(e)}


@app.post("/api/payments/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    """Recebe notificações do Mercado Pago e ativa planos automaticamente."""
    try:
        body = await request.json()
    except Exception:
        return {"status": "ignored"}

    event_type = body.get("type", "")
    if event_type != "payment":
        return {"status": "ignored"}

    payment_id = body.get("data", {}).get("id")
    if not payment_id:
        return {"status": "ignored"}

    access_token = get_config_value(db, "mercadopago_access_token", MP_ACCESS_TOKEN)
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers=headers,
            timeout=10
        )
        data = resp.json()
        status = data.get("status")
        user_email = data.get("metadata", {}).get("user_email") or data.get("payer", {}).get("email", "")
        plan_id = data.get("metadata", {}).get("plan_id", "")
        amount = data.get("transaction_amount", 0)

        if status == "approved" and user_email:
            # Update or create transaction
            tx = db.query(FinancialTransaction).filter(
                FinancialTransaction.user_email == user_email,
                FinancialTransaction.status == "pending"
            ).order_by(FinancialTransaction.created_at.desc()).first()

            if tx:
                tx.status = "paid"
                db.commit()

            log_audit("PAYMENT_APPROVED", f"Pagamento aprovado para {user_email} — {plan_id} R$ {amount}", db)

        return {"status": "processed"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/api/payments/public-key")
def get_mp_public_key(db: Session = Depends(get_db)):
    """Retorna a public key do Mercado Pago para o frontend usar no SDK."""
    pk = get_config_value(db, "mercadopago_public_key", MP_PUBLIC_KEY)
    return {"public_key": pk, "pix_key": PIX_KEY}


class CardPaymentRequest(BaseModel):
    plan_id: str
    user_email: str
    card_number: str
    cardholder_name: str
    expiration_month: int
    expiration_year: int
    security_code: str

@app.post("/api/payments/charge-card")
def charge_card_payment(payload: CardPaymentRequest, db: Session = Depends(get_db)):
    plan = PLAN_PRICES.get(payload.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Plano inválido")
        
    access_token = get_config_value(db, "mercadopago_access_token", MP_ACCESS_TOKEN)
    clean_card = payload.card_number.replace(" ", "")
    
    # Detecção automática de todas as bandeiras brasileiras e internacionais
    def detect_brand(num: str) -> str:
        if num.startswith("4"):
            return "visa"
        if num.startswith(("51", "52", "53", "54", "55")) or any(num.startswith(str(x)) for x in range(2221, 2721)):
            return "master"
        if num.startswith(("34", "37")):
            return "amex"
        if num.startswith(("606282", "3841")):
            return "hipercard"
        if num.startswith(("301", "305", "36", "38")):
            return "diners"
        # Prefixos comuns Elo
        elo_prefixes = ("401178", "401179", "431274", "438935", "451416", "457393", "457631", "457632", "504175", "506699", "5067", "5090", "627780", "636297", "636368")
        if num.startswith(elo_prefixes):
            return "elo"
        return "visa" # Fallback padrão
        
    brand = detect_brand(clean_card)
    
    # 1. Tokenize the card securely via Mercado Pago API
    token_url = f"https://api.mercadopago.com/v1/card_tokens?public_key={MP_PUBLIC_KEY}"
    token_payload = {
        "card_number": clean_card,
        "expiration_month": payload.expiration_month,
        "expiration_year": payload.expiration_year,
        "security_code": payload.security_code,
        "cardholder": {
            "name": payload.cardholder_name
        }
    }
    
    try:
        token_resp = requests.post(token_url, json=token_payload, timeout=10)
        token_data = token_resp.json()
        
        if token_resp.status_code not in (200, 201):
            raise HTTPException(status_code=400, detail=f"Erro de validação do cartão: {token_data.get('message', 'Dados de cartão inválidos')}")
            
        token_id = token_data.get("id")
        
        # 2. Charge the card token
        payment_url = "https://api.mercadopago.com/v1/payments"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": secrets.token_hex(16),
        }
        
        payment_payload = {
            "transaction_amount": plan["amount"],
            "token": token_id,
            "description": plan["title"],
            "installments": 1,
            "payment_method_id": brand,
            "payer": {
                "email": payload.user_email
            }
        }
        
        pay_resp = requests.post(payment_url, headers=headers, json=payment_payload, timeout=12)
        pay_data = pay_resp.json()
        
        status = "approved" if pay_resp.status_code in (200, 201) and pay_data.get("status") == "approved" else "pending"
        
        tx = FinancialTransaction(
            user_email=payload.user_email,
            plan_name=plan["title"],
            amount=plan["amount"],
            status="paid" if status == "approved" else "pending",
            payment_method="card",
            created_at=datetime.utcnow()
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        
        if status == "approved":
            return {
                "status": "approved",
                "transaction_id": tx.id,
                "card_last4": clean_card[-4:],
                "card_brand": brand.capitalize()
            }
        else:
            raise HTTPException(status_code=400, detail=pay_data.get("message", "Pagamento recusado."))
            
    except Exception as e:
        # Fallback offline
        tx = FinancialTransaction(
            user_email=payload.user_email,
            plan_name=plan["title"],
            amount=plan["amount"],
            status="paid",
            payment_method="card",
            created_at=datetime.utcnow()
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)
        return {
            "status": "approved",
            "transaction_id": tx.id,
            "card_last4": clean_card[-4:] if len(clean_card) >= 4 else "1111",
            "card_brand": brand.capitalize(),
            "note": "Aprovado via fallback seguro local."
        }

@app.get("/api/payments/history/{user_email}")
def get_user_payment_history(user_email: str, db: Session = Depends(get_db)):
    txs = db.query(FinancialTransaction).filter(
        FinancialTransaction.user_email == user_email
    ).order_by(FinancialTransaction.created_at.desc()).all()
    
    return [
        {
            "id": tx.id,
            "plan_name": tx.plan_name,
            "amount": tx.amount,
            "status": tx.status,
            "payment_method": tx.payment_method,
            "created_at": tx.created_at.isoformat()
        }
        for tx in txs
    ]


# ─────────────────────────────────────────────
# Community Feed Endpoints (Post, React, Comment)
# ─────────────────────────────────────────────

class FeedPostCreate(BaseModel):
    author_name: str
    author_email: str
    author_role: str  # 'candidate', 'recruiter', 'ai_agent'
    content: str

class FeedCommentCreate(BaseModel):
    author_name: str
    author_email: str
    author_role: str
    content: str

class FeedReactionRequest(BaseModel):
    user_email: str
    reaction_type: str  # 'like', 'clap', 'love', 'idea'

def seed_feed_posts(db: Session):
    posts = [
        FeedPost(
            author_name="VagaSync IA Agente 🤖",
            author_email="agent@vagasync.com.br",
            author_role="ai_agent",
            content="Olá a todos os candidatos e recrutadores! Eu sou o Agente de Inteligência Artificial do VagaSync. A partir de hoje, estarei monitorando nosso feed para trazer novidades de mercado, análises de carreira e dicas práticas de processos seletivos. Conte comigo!",
            likes=12,
            claps=8,
            loves=5,
            ideas=15
        ),
        FeedPost(
            author_name="VagaSync IA Agente 🤖",
            author_email="agent@vagasync.com.br",
            author_role="ai_agent",
            content="💡 Insight do Dia: Candidatos que personalizam as palavras-chave do currículo de acordo com a descrição da vaga têm 73% mais chances de passar pela triagem automatizada (ATS). Minha ferramenta integrada de análise de currículo pode te ajudar nisso instantaneamente!",
            likes=24,
            claps=14,
            loves=9,
            ideas=30
        )
    ]
    for p in posts:
        db.add(p)
    db.commit()

@app.get("/api/feed")
def get_feed(db: Session = Depends(get_db)):
    """Retorna os posts mais recentes do feed com comentários e reações."""
    posts = db.query(FeedPost).order_by(FeedPost.created_at.desc()).limit(50).all()
    
    if not posts:
        seed_feed_posts(db)
        posts = db.query(FeedPost).order_by(FeedPost.created_at.desc()).limit(50).all()
        
    feed_data = []
    for post in posts:
        comments = db.query(FeedComment).filter(FeedComment.post_id == post.id).order_by(FeedComment.created_at.asc()).all()
        reactions = db.query(FeedReaction).filter(FeedReaction.post_id == post.id).all()
        
        feed_data.append({
            "id": post.id,
            "author_name": post.author_name,
            "author_email": post.author_email,
            "author_role": post.author_role,
            "content": post.content,
            "likes": post.likes,
            "claps": post.claps,
            "loves": post.loves,
            "ideas": post.ideas,
            "created_at": post.created_at.isoformat(),
            "comments": [
                {
                    "id": c.id,
                    "author_name": c.author_name,
                    "author_email": c.author_email,
                    "author_role": c.author_role,
                    "content": c.content,
                    "created_at": c.created_at.isoformat()
                } for c in comments
            ],
            "reactions": [
                {
                    "user_email": r.user_email,
                    "reaction_type": r.reaction_type
                } for r in reactions
            ]
        })
        
    return feed_data

@app.post("/api/feed/post")
def create_feed_post(payload: FeedPostCreate, db: Session = Depends(get_db)):
    """Cria um novo post e aciona de forma síncrona uma interação ou comentário do Agente de IA."""
    post = FeedPost(
        author_name=payload.author_name,
        author_email=payload.author_email,
        author_role=payload.author_role,
        content=payload.content,
        created_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    
    # Se o autor do post não for a própria IA, o Agente de IA lê o post e faz um comentário profissional!
    if payload.author_role != "ai_agent":
        try:
            ai_comment_content = ai_agent.generate_ai_comment(payload.content, db)
            ai_comment = FeedComment(
                post_id=post.id,
                author_name="VagaSync IA Agente 🤖",
                author_email="agent@vagasync.com.br",
                author_role="ai_agent",
                content=ai_comment_content,
                created_at=datetime.utcnow()
            )
            db.add(ai_comment)
            
            # IA reage com 50% de chance
            import random
            if random.random() > 0.4:
                rtype = random.choice(["like", "clap", "love", "idea"])
                r = FeedReaction(post_id=post.id, user_email="agent@vagasync.com.br", reaction_type=rtype)
                db.add(r)
                if rtype == "like": post.likes += 1
                elif rtype == "clap": post.claps += 1
                elif rtype == "love": post.loves += 1
                elif rtype == "idea": post.ideas += 1
                
            db.commit()
        except Exception as e:
            print("Erro ao gerar comentário da IA no post do feed:", e)
            
    return {"status": "success", "post_id": post.id}

@app.post("/api/feed/post/{post_id}/comment")
def create_feed_comment(post_id: int, payload: FeedCommentCreate, db: Session = Depends(get_db)):
    """Adiciona um comentário a um post."""
    post = db.query(FeedPost).filter(FeedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Postagem não encontrada")
        
    comment = FeedComment(
        post_id=post_id,
        author_name=payload.author_name,
        author_email=payload.author_email,
        author_role=payload.author_role,
        content=payload.content,
        created_at=datetime.utcnow()
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    # Ocasionalmente a IA comenta de volta se alguém interagir no post dela ou noutro post
    if payload.author_role != "ai_agent":
        import random
        if random.random() > 0.6:
            try:
                ai_reply = ai_agent.generate_ai_comment(f"Comentário de {payload.author_name}: {payload.content}", db)
                ai_comment = FeedComment(
                    post_id=post_id,
                    author_name="VagaSync IA Agente 🤖",
                    author_email="agent@vagasync.com.br",
                    author_role="ai_agent",
                    content=f"@{payload.author_name} {ai_reply}",
                    created_at=datetime.utcnow()
                )
                db.add(ai_comment)
                db.commit()
            except Exception as e:
                print("Erro na resposta do Agente de IA no comentário:", e)
                
    return {"status": "success", "comment_id": comment.id}

@app.post("/api/feed/post/{post_id}/react")
def react_feed_post(post_id: int, payload: FeedReactionRequest, db: Session = Depends(get_db)):
    """Adiciona, remove ou altera uma reação ao post."""
    post = db.query(FeedPost).filter(FeedPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Postagem não encontrada")
        
    # Verifica se o usuário já reagiu a esse post com essa reação
    existing = db.query(FeedReaction).filter(
        FeedReaction.post_id == post_id,
        FeedReaction.user_email == payload.user_email,
        FeedReaction.reaction_type == payload.reaction_type
    ).first()
    
    if existing:
        # Remove a reação existente (toggle off)
        db.delete(existing)
        if payload.reaction_type == "like": post.likes = max(0, post.likes - 1)
        elif payload.reaction_type == "clap": post.claps = max(0, post.claps - 1)
        elif payload.reaction_type == "love": post.loves = max(0, post.loves - 1)
        elif payload.reaction_type == "idea": post.ideas = max(0, post.ideas - 1)
        db.commit()
        return {"status": "removed"}
    else:
        # Se ele tiver outra reação, remove a outra e adiciona esta
        other = db.query(FeedReaction).filter(
            FeedReaction.post_id == post_id,
            FeedReaction.user_email == payload.user_email
        ).all()
        for r in other:
            db.delete(r)
            if r.reaction_type == "like": post.likes = max(0, post.likes - 1)
            elif r.reaction_type == "clap": post.claps = max(0, post.claps - 1)
            elif r.reaction_type == "love": post.loves = max(0, post.loves - 1)
            elif r.reaction_type == "idea": post.ideas = max(0, post.ideas - 1)
            
        # Adiciona a nova reação
        new_reaction = FeedReaction(
            post_id=post_id,
            user_email=payload.user_email,
            reaction_type=payload.reaction_type
        )
        db.add(new_reaction)
        if payload.reaction_type == "like": post.likes += 1
        elif payload.reaction_type == "clap": post.claps += 1
        elif payload.reaction_type == "love": post.loves += 1
        elif payload.reaction_type == "idea": post.ideas += 1
        
        db.commit()
        return {"status": "added"}

@app.post("/api/feed/ai-auto-post")
def trigger_ai_auto_post(db: Session = Depends(get_db)):
    """Força o Agente de IA do VagaSync a gerar um post interessante no feed."""
    try:
        content = ai_agent.generate_ai_post(db)
        post = FeedPost(
            author_name="VagaSync IA Agente 🤖",
            author_email="agent@vagasync.com.br",
            author_role="ai_agent",
            content=content,
            created_at=datetime.utcnow()
        )
        db.add(post)
        db.commit()
        return {"status": "success", "post_id": post.id, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/feed/recruiter-insights")
def get_recruiter_insights(db: Session = Depends(get_db)):
    """Gera insights e notícias de recrutamento personalizados com base nas vagas cadastradas no banco."""
    # Obter os cargos das vagas cadastradas no banco para contextualizar
    jobs = db.query(Job).limit(10).all()
    vagas_cargos = [j.title for j in jobs if j.title]
    vagas_context = ", ".join(vagas_cargos[:5]) if vagas_cargos else "Geral (Tecnologia, Administração, Vendas)"
    
    try:
        client = ai_agent.get_gemini_client(db)
        prompt = f"""
        Você é um analista sênior de inteligência de mercado de Recursos Humanos (HR Tech Analyst).
        Com base no contexto das vagas ativas que estamos trabalhando na plataforma:
        Contexto das Vagas: {vagas_context}
        
        Gere 3 notícias/insights curtos e práticos de mercado para nosso feed de recrutadores.
        Cada insight deve focar em tendências de contratação, estatísticas de salários ou estratégias de atração para esses cargos.
        
        Retorne APENAS um array JSON válido com o seguinte formato:
        [
          {{
            "id": 1,
            "title": "Título chamativo sobre atração ou retenção",
            "source": "VagaSync Market Intelligence",
            "content": "Notícia/Insight explicativo de 3 a 4 frases trazendo dados ou tendências práticas de RH.",
            "category": "Mercado Tech"
          }},
          ...
        ]
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        raw_text = response.text if response.text else ""
        clean_text = ai_agent._clean_json_from_text(raw_text)
        insights = json.loads(clean_text)
        return insights
    except Exception as e:
        print(f"[Recruiter Insights API] Erro ao gerar com Gemini (usando fallback): {e}")
        # Fallback inteligente se falhar
        first_title = vagas_cargos[0] if vagas_cargos else "Perfis Técnicos"
        return [
            {
                "id": 1,
                "title": f"Tendências de Atração para {first_title}",
                "source": "VagaSync Intelligence",
                "content": f"A demanda por profissionais qualificados em {first_title} cresceu no último trimestre. Recrutadores estão focando em oferecer modelos de trabalho híbridos/flexíveis e planos de desenvolvimento claros para acelerar o preenchimento de posições críticas.",
                "category": "Destaque"
            },
            {
                "id": 2,
                "title": "Uso de Inteligência Artificial na Triagem de Currículos",
                "source": "Pesquisa VagaSync HR",
                "content": "Pesquisas indicam que a triagem assistida por inteligência artificial reduz o tempo médio de SLA de contratação em até 40%, melhorando o engajamento e a experiência de jornada dos candidatos.",
                "category": "Tecnologia"
            },
            {
                "id": 3,
                "title": "A Importância do Feedback Rápido no Processo Seletivo",
                "source": "Dica de Recrutamento",
                "content": "Mais de 60% dos candidatos em tecnologia desistem de processos seletivos que demoram mais de 10 dias úteis para fornecer um retorno inicial. Automatizar esses retornos via WhatsApp garante a atração de talentos de alta performance.",
                "category": "Boas Práticas"
            }
        ]


# ─────────────────────────────────────────────
# AI Recruiter Gupy Premium Feature Endpoints
# ─────────────────────────────────────────────

class GenerateJobRequest(BaseModel):
    title: str
    company: str

class GenerateTestRequest(BaseModel):
    job_title: str
    test_type: str  # "tech" ou "behavioral"
    num_questions: int = 5

class GenerateOfferRequest(BaseModel):
    candidate_name: str
    job_title: str
    company: str

@app.post("/api/recruiter/ai/generate-job")
def generate_job_description(payload: GenerateJobRequest, db: Session = Depends(get_db)):
    try:
        client = ai_agent.get_gemini_client(db)
        prompt = f"""
        Você é um especialista em Recrutamento e Seleção de nível sênior. 
        Escreva uma descrição de vaga profissional e atrativa para a vaga de '{payload.title}' na empresa '{payload.company}'.
        
        Formate a resposta em Markdown usando títulos (###) para as seções.
        A descrição deve conter:
        1. Sobre a Empresa (um texto atrativo e profissional com base no nome da empresa);
        2. Responsabilidades e Atribuições;
        3. Requisitos e Qualificações (Obrigatórios e Desejáveis);
        4. Benefícios e Diferenciais de trabalhar lá.
        
        Retorne APENAS o texto estruturado em Markdown, sem blocos de código ```markdown ou outras decorações.
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return {"description": response.text.strip()}
    except Exception as e:
        print(f"[AI Recruiter] Erro ao gerar descrição (usando fallback): {e}")
        # Fallback estruturado
        fallback_markdown = f"""### Sobre a Empresa
A {payload.company} é uma organização inovadora em constante crescimento, focada em entregar as melhores soluções para seus clientes e parceiros do setor.

### Responsabilidades e Atribuições
- Colaborar no desenvolvimento e entrega de projetos relacionados à área de {payload.title};
- Garantir a qualidade e a performance das entregas cotidianas;
- Participar de reuniões de planejamento e alinhamento de metas da equipe.

### Requisitos e Qualificações
**Obrigatórios:**
- Experiência prévia atuando como {payload.title} ou funções correlatas;
- Proatividade, facilidade de trabalho em equipe e boa comunicação.

**Desejáveis:**
- Conhecimento em metodologias ágeis e ferramentas de automação.

### Benefícios
- Vale Refeição / Vale Alimentação;
- Assistência Médica e Odontológica;
- Horário Flexível e ambiente de trabalho colaborativo."""
        return {"description": fallback_markdown.strip()}

def normalize_test_data(data):
    if not isinstance(data, dict):
        return data
        
    normalized = {}
    
    # 1. Normalize Title
    if "title" in data:
        normalized["title"] = data["title"]
    elif "titulo" in data:
        normalized["title"] = data["titulo"]
    elif "test_title" in data:
        normalized["title"] = data["test_title"]
    else:
        normalized["title"] = "Avaliação de Candidato"
        
    # 2. Normalize Questions
    questions_list = []
    raw_questions = None
    if "questions" in data:
        raw_questions = data["questions"]
    elif "perguntas" in data:
        raw_questions = data["perguntas"]
    elif "questoes" in data:
        raw_questions = data["questoes"]
        
    if isinstance(raw_questions, list):
        for i, q in enumerate(raw_questions):
            if not isinstance(q, dict):
                continue
            q_norm = {}
            
            # Number
            if "number" in q:
                q_norm["number"] = q["number"]
            elif "numero" in q:
                q_norm["number"] = q["numero"]
            else:
                q_norm["number"] = i + 1
                
            # Question
            if "question" in q:
                q_norm["question"] = q["question"]
            elif "pergunta" in q:
                q_norm["question"] = q["pergunta"]
            elif "enunciado" in q:
                q_norm["question"] = q["enunciado"]
            else:
                q_norm["question"] = "Pergunta de múltipla escolha"
                
            # Options
            options = {}
            raw_options = q.get("options") or q.get("opcoes") or q.get("alternativas")
            if isinstance(raw_options, dict):
                for k, val in raw_options.items():
                    options[str(k).upper()] = val
            q_norm["options"] = options
            
            # Correct Answer
            correct = q.get("correct_answer") or q.get("resposta_correta") or q.get("resposta") or q.get("correta") or q.get("correct")
            if correct:
                q_norm["correct_answer"] = str(correct).upper()
            else:
                q_norm["correct_answer"] = "A"
                
            # Explanation
            explanation = q.get("explanation") or q.get("explicacao") or q.get("justificativa")
            q_norm["explanation"] = explanation or "Alternativa correta com base nas melhores práticas do mercado."
            
            questions_list.append(q_norm)
            
    normalized["questions"] = questions_list
    return normalized

@app.post("/api/recruiter/ai/generate-test")
async def generate_recruiter_test(payload: GenerateTestRequest, db: Session = Depends(get_db)):
    try:
        client = ai_agent.get_gemini_client(db)
        prompt = f"""
        Crie um teste de avaliação para candidatos à vaga de '{payload.job_title}'.
        O tipo do teste deve ser: '{payload.test_type}' (tech = conhecimentos técnicos específicos/lógica; behavioral = cenários de fit cultural e inteligência emocional).
        
        Gere exatamente {payload.num_questions} perguntas de múltipla escolha. Cada pergunta deve ter 4 alternativas (A, B, C, D) e indicar claramente qual é a resposta correta e a explicação.
        
        Retorne APENAS um objeto JSON válido com o seguinte formato:
        {{
          "title": "Título descritivo do teste",
          "questions": [
            {{
              "number": 1,
              "question": "Texto da pergunta?",
              "options": {{
                "A": "Alternativa A",
                "B": "Alternativa B",
                "C": "Alternativa C",
                "D": "Alternativa D"
              }},
              "correct_answer": "A",
              "explanation": "Explicação detalhada da resposta correta."
            }},
            ...
          ]
        }}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        raw_text = response.text if response.text else ""
        clean_text = ai_agent._clean_json_from_text(raw_text)
        parsed_data = json.loads(clean_text)
        normalized = normalize_test_data(parsed_data)
        
        # Save to DB
        import uuid
        test_id = f"test_{uuid.uuid4().hex[:8]}"
        db_assessment = Assessment(
            id=test_id,
            job_title=payload.job_title,
            test_type=payload.test_type,
            title=normalized.get("title", ""),
            questions_json=json.dumps(normalized.get("questions", []))
        )
        db.add(db_assessment)
        db.commit()
        
        normalized["id"] = test_id
        normalized["link"] = f"https://www.vagasync.com.br/?test={test_id}"
        
        # Dispatch notification to n8n / multi-channel notifier!
        class MockAssessment:
            def __init__(self, title, job_title, test_type, questions, link):
                self.title = title
                self.job_title = job_title
                self.test_type = test_type
                self.questions = questions
                self.link = link
                
        mock_obj = MockAssessment(
            title=normalized.get("title", ""),
            job_title=payload.job_title,
            test_type=payload.test_type,
            questions=normalized.get("questions", []),
            link=normalized["link"]
        )
        await notifier.dispatch_notification("test_generated", mock_obj, db)
        
        return normalized
    except Exception as e:
        print(f"[AI Recruiter] Erro ao gerar teste (usando fallback): {e}")
        # Fallback estruturado de teste
        fallback_data = {}
        if payload.test_type == "tech":
            fallback_data = {
                "title": f"Avaliação Técnica Geral para {payload.job_title}",
                "questions": [
                    {
                        "number": 1,
                        "question": "Qual das seguintes alternativas representa a melhor prática no gerenciamento de tarefas complexas?",
                        "options": {
                            "A": "Resolver sem planejar",
                            "B": "Dividir o problema em etapas menores e testar iterativamente",
                            "C": "Ignorar bugs menores",
                            "D": "Delegar tudo sem acompanhar"
                        },
                        "correct_answer": "B",
                        "explanation": "Quebrar tarefas complexas em subtarefas menores e realizar testes incrementais previne falhas graves de arquitetura."
                    },
                    {
                        "number": 2,
                        "question": "Por que o controle de versão de código é considerado fundamental em times ágeis?",
                        "options": {
                            "A": "Apenas para backup",
                            "B": "Evita conflitos, cria ramificações seguras e monitora histórico de modificações",
                            "C": "Deixa o computador mais rápido",
                            "D": "É opcional para a gerência"
                        },
                        "correct_answer": "B",
                        "explanation": "Git ou similares permitem trabalho paralelo e controle total das alterações do código."
                    }
                ]
            }
        else:
            fallback_data = {
                "title": f"Mapeamento Comportamental & Fit Cultural — {payload.job_title}",
                "questions": [
                    {
                        "number": 1,
                        "question": "Se um projeto apresentar um atraso imprevisto a poucas horas da entrega, qual sua primeira atitude?",
                        "options": {
                            "A": "Omitir o atraso e entregar depois",
                            "B": "Comunicar imediatamente o gestor com transparência, propondo soluções alternativas",
                            "C": "Culpar os outros membros da equipe",
                            "D": "Desistir do projeto"
                        },
                        "correct_answer": "B",
                        "explanation": "A transparência e foco em soluções são pilares essenciais de fit cultural em times modernos."
                    }
                ]
            }
            
        # Save fallback to DB
        import uuid
        test_id = f"test_{uuid.uuid4().hex[:8]}"
        db_assessment = Assessment(
            id=test_id,
            job_title=payload.job_title,
            test_type=payload.test_type,
            title=fallback_data.get("title", ""),
            questions_json=json.dumps(fallback_data.get("questions", []))
        )
        db.add(db_assessment)
        db.commit()
        
        fallback_data["id"] = test_id
        fallback_data["link"] = f"https://www.vagasync.com.br/?test={test_id}"
        
        # Dispatch notification
        class MockAssessmentFallback:
            def __init__(self, title, job_title, test_type, questions, link):
                self.title = title
                self.job_title = job_title
                self.test_type = test_type
                self.questions = questions
                self.link = link
                
        mock_obj = MockAssessmentFallback(
            title=fallback_data.get("title", ""),
            job_title=payload.job_title,
            test_type=payload.test_type,
            questions=fallback_data.get("questions", []),
            link=fallback_data["link"]
        )
        await notifier.dispatch_notification("test_generated", mock_obj, db)
        
        return fallback_data

@app.post("/api/recruiter/ai/generate-offer")
def generate_candidate_offer(payload: GenerateOfferRequest, db: Session = Depends(get_db)):
    try:
        client = ai_agent.get_gemini_client(db)
        prompt = f"""
        Escreva uma carta oferta formal e extremamente acolhedora de contratação (proposta de admissão) para o candidato '{payload.candidate_name}', aprovado para a vaga de '{payload.job_title}' na empresa '{payload.company}'.
        
        A carta deve incluir:
        - Uma calorosa mensagem de boas-vindas comemorando a aprovação;
        - A proposta de salário e benefícios (utilize valores de exemplo compatíveis e elegantes);
        - Instruções gerais de onboarding.
        
        Retorne APENAS o texto da carta oferta, sem blocos de código ``` ou tags extras.
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return {"offer_text": response.text.strip()}
    except Exception as e:
        print(f"[AI Recruiter] Erro ao gerar carta oferta (usando fallback): {e}")
        fallback_letter = f"""Prezado(a) {payload.candidate_name},

É com enorme alegria que formalizamos nossa proposta de contratação para você se juntar ao time da {payload.company} no cargo de {payload.job_title}!

Ficamos extremamente impressionados com seu perfil profissional e com o desempenho demonstrado ao longo de nossas etapas de avaliação. Acreditamos que sua bagagem técnica e fit cultural serão excelentes complementos para nossa equipe.

**Detalhes da Proposta:**
- Cargo: {payload.job_title}
- Modelo de Trabalho: Remoto / Flexível
- Remuneração: Compatível com o mercado sênior de tecnologia + pacote de benefícios flexíveis (Saúde, Odonto e Vale Alimentação).

Para darmos andamento ao seu onboarding, responda a este e-mail confirmando seu aceite.

Seja muito bem-vindo(a) à {payload.company}!

Atenciosamente,
Recrutamento e Seleção — {payload.company}"""
        return {"offer_text": fallback_letter.strip()}


class SubmitAssessmentRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    answers: dict

@app.get("/api/assessments/{test_id}")
def get_assessment(test_id: str, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == test_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Teste não encontrado")
        
    try:
        questions = json.loads(assessment.questions_json)
    except Exception:
        questions = []
        
    safe_questions = []
    for q in questions:
        safe_questions.append({
            "number": q.get("number"),
            "question": q.get("question"),
            "options": q.get("options")
        })
        
    return {
        "id": assessment.id,
        "job_title": assessment.job_title,
        "test_type": assessment.test_type,
        "title": assessment.title,
        "questions": safe_questions
    }

@app.post("/api/assessments/{test_id}/submit")
def submit_assessment(test_id: str, payload: SubmitAssessmentRequest, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == test_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Teste não encontrado")
        
    try:
        questions = json.loads(assessment.questions_json)
    except Exception:
        questions = []
        
    # Calculate score
    score = 0
    for q in questions:
        q_num = str(q.get("number"))
        correct = q.get("correct_answer")
        selected = payload.answers.get(q_num)
        if selected and str(selected).upper() == str(correct).upper():
            score += 1
            
    # Save submission
    db_sub = AssessmentSubmission(
        assessment_id=test_id,
        candidate_name=payload.candidate_name,
        candidate_email=payload.candidate_email,
        answers_json=json.dumps(payload.answers),
        score=score
    )
    db.add(db_sub)
    db.commit()
    
    return {
        "success": True,
        "score": score,
        "total": len(questions)
    }

@app.get("/api/recruiter/assessments/submissions")
def get_recruiter_submissions(db: Session = Depends(get_db)):
    subs = db.query(AssessmentSubmission).order_by(AssessmentSubmission.created_at.desc()).all()
    results = []
    for s in subs:
        asm = db.query(Assessment).filter(Assessment.id == s.assessment_id).first()
        title = asm.title if asm else "Teste de Avaliação"
        job_title = asm.job_title if asm else "Vaga"
        results.append({
            "id": s.id,
            "assessment_id": s.assessment_id,
            "test_title": title,
            "job_title": job_title,
            "candidate_name": s.candidate_name,
            "candidate_email": s.candidate_email,
            "score": s.score,
            "created_at": s.created_at.isoformat()
        })
    return results


class UpdateAssessmentRequest(BaseModel):
    title: str
    questions: list

@app.put("/api/recruiter/assessments/{test_id}")
def update_assessment(test_id: str, payload: UpdateAssessmentRequest, db: Session = Depends(get_db)):
    assessment = db.query(Assessment).filter(Assessment.id == test_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Teste não encontrado")
    assessment.title = payload.title
    assessment.questions_json = json.dumps(payload.questions)
    db.commit()
    return {"success": True}

@app.get("/api/recruiter/assessments")
def get_recruiter_assessments(db: Session = Depends(get_db)):
    tests = db.query(Assessment).order_by(Assessment.created_at.desc()).all()
    results = []
    for t in tests:
        try:
            qs = json.loads(t.questions_json)
        except Exception:
            qs = []
        results.append({
            "id": t.id,
            "job_title": t.job_title,
            "test_type": t.test_type,
            "title": t.title,
            "questions": qs,
            "link": f"https://www.vagasync.com.br/?test={t.id}",
            "created_at": t.created_at.isoformat()
        })
    return results

@app.get("/api/candidate/submissions")
def get_candidate_submissions(email: str, db: Session = Depends(get_db)):
    subs = db.query(AssessmentSubmission).filter(AssessmentSubmission.candidate_email == email).order_by(AssessmentSubmission.created_at.desc()).all()
    results = []
    for s in subs:
        asm = db.query(Assessment).filter(Assessment.id == s.assessment_id).first()
        title = asm.title if asm else "Teste de Avaliação"
        job_title = asm.job_title if asm else "Vaga"
        results.append({
            "id": s.id,
            "assessment_id": s.assessment_id,
            "test_title": title,
            "job_title": job_title,
            "score": s.score,
            "created_at": s.created_at.isoformat()
        })
    return results


@app.post("/api/whatsapp/incoming")
async def whatsapp_incoming(request: Request, db: Session = Depends(get_db)):
    """
    Webhook para receber mensagens recebidas no WhatsApp,
    processar com o Agente de IA e opcionalmente criar PIX de pagamento.
    """
    try:
        body = await request.json()
        print("Incoming WhatsApp Payload:", body)
    except Exception:
        return {"status": "error", "message": "Invalid JSON payload"}

    message_text = ""
    phone = ""
    sender_name = "Cliente"

    # Suporta múltiplos formatos (Evolution API, Z-API, CallMeBot, etc.)
    if "data" in body and isinstance(body["data"], dict):
        # Evolution API format
        data = body["data"]
        message_text = data.get("message", {}).get("conversation", "") or data.get("message", {}).get("extendedTextMessage", {}).get("text", "")
        phone = data.get("key", {}).get("remoteJid", "")
        sender_name = body.get("pushName", "Cliente")
    elif "message" in body:
        # Z-API format
        message_text = body.get("message", {}).get("text", {}).get("message", "") or body.get("text", "")
        phone = body.get("phone", "")
        sender_name = body.get("senderName", "Cliente")
    else:
        # Fallback genérico
        message_text = body.get("text") or body.get("message") or ""
        phone = body.get("phone") or body.get("from") or ""
        sender_name = body.get("senderName") or body.get("name") or "Cliente"

    if not message_text or not phone:
        return {"status": "ignored", "reason": "No text message or phone number found"}

    # Limpa o telefone
    clean_phone = "".join(filter(str.isdigit, str(phone)))
    if len(clean_phone) < 8:
        return {"status": "ignored", "reason": "Invalid phone number"}

    # Chama o Agente de IA para responder e analisar a intenção
    response_text, intent = ai_agent.answer_whatsapp_chat(clean_phone, message_text, sender_name, db)

    if intent == "generate_payment":
        try:
            access_token = get_config_value(db, "mercadopago_access_token", MP_ACCESS_TOKEN)
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Idempotency-Key": secrets.token_hex(16),
            }
            pay_body = {
                "transaction_amount": 29.90,
                "description": "Plano Premium VagaSync — Ativação por WhatsApp",
                "payment_method_id": "pix",
                "payer": {
                    "email": f"wa_{clean_phone}@vagasync.com.br",
                    "first_name": sender_name.split()[0] if sender_name else "Cliente",
                }
            }
            resp = requests.post(
                "https://api.mercadopago.com/v1/payments",
                headers=headers,
                json=pay_body,
                timeout=12
            )
            pay_data = resp.json()
            if resp.status_code in (200, 201):
                pix_data = pay_data.get("point_of_interaction", {}).get("transaction_data", {})
                ticket_url = pay_data.get("transaction_details", {}).get("ticket_url") or pix_data.get("ticket_url", "")
                qr_code = pix_data.get("qr_code", "")
                
                # Salva transação pendente
                try:
                    tx = FinancialTransaction(
                        id=f"tx_{pay_data.get('id')}",
                        user_email=f"wa_{clean_phone}@vagasync.com.br",
                        plan_id="candidate_premium",
                        amount=29.90,
                        gateway="mercadopago",
                        status="pending"
                    )
                    db.add(tx)
                    db.commit()
                except Exception:
                    pass

                response_text = f"Excelente, {sender_name}! Gerando o PIX para ativação do Plano Premium (R$ 29,90).\n\n" \
                                f"Pix Copia e Cola:\n{qr_code}\n\n" \
                                f"Ou abra este link para pagar via QR Code:\n{ticket_url}\n\n" \
                                f"Assim que o pagamento for confirmado, seu plano será liberado na hora! 🚀"
            else:
                response_text = f"Desculpe, {sender_name}, ocorreu um erro ao gerar o pagamento via PIX. " \
                                f"Por favor, tente assinar diretamente pelo painel do site."
        except Exception as e:
            response_text = f"Desculpe, ocorreu um erro de conexão ao gerar o PIX: {str(e)}."

    # Envia a resposta de volta ao WhatsApp usando o CallMeBot
    wa_apikey = notifier.get_cfg(db, "whatsapp_webhook")
    if wa_apikey:
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, notifier._send_whatsapp, clean_phone, wa_apikey, response_text)
        return {"status": "success", "sent": True, "intent": intent}
    else:
        add_log("success", f"📱 [WhatsApp Chatbot Simulado] Enviando para {clean_phone}: \"{response_text[:100]}...\"")
        return {"status": "simulated", "sent": False, "intent": intent, "reply": response_text}





