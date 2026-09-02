import os
import asyncio
import json
import secrets
import time
import requests
from dotenv import load_dotenv

# Carrega variaveis de ambiente do diretório do backend
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
from urllib.parse import urlencode
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, model_validator
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

import security
security_scheme = HTTPBearer()

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    token = credentials.credentials
    payload = security.verify_jwt(token)
    if not payload or payload.get("role") != "admin":
        raise HTTPException(status_code=401, detail="Sessão administrativa inválida ou expirada.")
    return payload

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = security.verify_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token de sessão inválido ou expirado.")
    user_id = payload.get("user_id")
    role = payload.get("role")
    
    if role == "admin":
        return {"id": 0, "email": "admin@vagasync.com", "role": "admin", "name": "Super Admin"}
        
    from database import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário associado ao token não encontrado.")
    return user

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)), db: Session = Depends(get_db)):
    if not credentials:
        return None
    token = credentials.credentials
    payload = security.verify_jwt(token)
    if not payload:
        return None
    role = payload.get("role")
    user_id = payload.get("user_id")
    if role == "admin":
        return {"id": 0, "email": "admin@vagasync.com", "role": "admin", "name": "Super Admin"}
    from database import User
    return db.query(User).filter(User.id == user_id).first()

linkedin_oauth_states = {}
LINKEDIN_STATE_EXPIRE_SECONDS = 300

def cleanup_linkedin_oauth_states():
    now = int(time.time())
    expired = [state for state, ts in linkedin_oauth_states.items() if now - ts > LINKEDIN_STATE_EXPIRE_SECONDS]
    for state in expired:
        linkedin_oauth_states.pop(state, None)


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
    client_id = get_config_value(db, "linkedin_client_id", "") or ""
    client_secret = get_config_value(db, "linkedin_client_secret", "") or ""
    return client_id.strip(), client_secret.strip()


def get_linkedin_redirect_uri(request: Request) -> str:
    backend_url = os.getenv("BACKEND_URL", "").strip()
    if backend_url:
        return f"{backend_url.rstrip('/')}/api/linkedin/callback"

    if request is not None:
        scheme = request.url.scheme
        host = request.url.hostname
        port = request.url.port
        if host:
            port_fragment = ""
            if port and ((scheme == "http" and port != 80) or (scheme == "https" and port != 443)):
                port_fragment = f":{port}"
            return f"{scheme}://{host}{port_fragment}/api/linkedin/callback"

    return "http://localhost:8000/api/linkedin/callback"


def get_frontend_url(db: Session) -> str:
    return get_config_value(db, "frontend_url", os.getenv("FRONTEND_URL", "http://localhost:5173"))


def get_backend_url() -> str:
    return os.getenv("BACKEND_URL", "http://localhost:8000")


def get_linkedin_user_info(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_name = ""
    profile_email = ""

    try:
        resp = requests.get("https://api.linkedin.com/oidc/userinfo", headers=headers, timeout=10)
        if resp.ok:
            data = resp.json()
            profile_name = data.get("name", "") or data.get("given_name", "")
            if not profile_name:
                first_name = data.get("localizedFirstName", "")
                last_name = data.get("localizedLastName", "")
                profile_name = " ".join([part for part in [first_name, last_name] if part]).strip()
            profile_email = data.get("email", "")
    except Exception:
        profile_name = ""
        profile_email = ""

    if not profile_name:
        try:
            resp = requests.get(
                "https://api.linkedin.com/v2/me?projection=(localizedFirstName,localizedLastName)",
                headers=headers,
                timeout=10
            )
            if resp.ok:
                data = resp.json()
                profile_name = " ".join([part for part in [data.get("localizedFirstName", ""), data.get("localizedLastName", "")] if part]).strip()
        except Exception:
            pass

    if not profile_email:
        try:
            resp = requests.get(
                "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
                headers=headers,
                timeout=10
            )
            if resp.ok:
                data = resp.json()
                elements = data.get("elements", [])
                if elements and isinstance(elements, list):
                    handle = elements[0].get("handle~") if isinstance(elements[0], dict) else None
                    if handle and isinstance(handle, dict):
                        profile_email = handle.get("emailAddress", "")
        except Exception:
            pass

    return profile_name.strip(), profile_email.strip()


def create_or_get_linkedin_user(name: str, email: str, db: Session):
    from database import User
    email = email.strip().lower()
    if not email:
        return None

    user = db.query(User).filter(User.email == email).first()
    if user:
        if not user.name and name:
            user.name = name.strip()
            db.commit()
            db.refresh(user)
        if not user.password_hash:
            user.password_hash = security.hash_password(secrets.token_urlsafe(32))
            db.commit()
            db.refresh(user)
        return user

    password_hash = security.hash_password(secrets.token_urlsafe(32))
    user = User(email=email, name=name.strip() if name else email, password_hash=password_hash, role="candidate")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@asynccontextmanager
async def lifespan(app):
    """Auto-start the automation agent and marketing scheduler when the server boots."""
    import asyncio
    db = database.SessionLocal()
    try:
        resume_cfg = db.query(Config).filter(Config.key == "resume_text").first()
        if resume_cfg and resume_cfg.value and resume_cfg.value.strip():
            add_log("info", "🤖 Agente iniciado automaticamente junto com o servidor Vaga Sync.")
            asyncio.create_task(linkedin_bot.run_automation_cycle())
        else:
            add_log("info", "⏸️  Servidor iniciado. Aguardando currículo para auto-iniciar o agente.")
            
        # Task do publicador automático de marketing (5 posts por dia)
        async def run_marketing_scheduler_loop():
            await asyncio.sleep(5)  # aguarda o boot inicial
            while True:
                db_session = database.SessionLocal()
                try:
                    from marketing_publisher import schedule_5_posts
                    schedule_5_posts(db_session)
                except Exception as e:
                    print(f"[Marketing Scheduler Task] Erro ao agendar: {e}")
                finally:
                    db_session.close()
                await asyncio.sleep(12 * 3600)  # roda a cada 12 horas para reabastecer a fila
                
        asyncio.create_task(run_marketing_scheduler_loop())
    finally:
        db.close()
    yield  # server runs

app = FastAPI(title="Vaga Sync API", lifespan=lifespan)

import google_ads
app.include_router(google_ads.router)
import facebook_ads
app.include_router(facebook_ads.router)

# ─── Rate Limiter Setup ───────────────────────────────────────────────────────
if RATE_LIMIT_AVAILABLE:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── Include Routers ──────────────────────────────────────────────────────────
from routers.auth import router as auth_router
from routers.jobs import router as jobs_router
from routers.automation import router as automation_router
from routers.talent_bank import router as talent_bank_router
from routers.blog import router as blog_router
from routers.support import router as support_router

app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(automation_router)
app.include_router(talent_bank_router)
app.include_router(blog_router)
app.include_router(support_router)

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

    @model_validator(mode='after')
    def normalize_recruiter_link(self):
        if self.source == "recruiter":
            self.link = f"https://vagasync.com.br/vagas/{self.id}"
        return self

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

class UserRegister(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    role: Optional[str] = "candidate"  # 'candidate' ou 'recruiter'

class UserLogin(BaseModel):
    email: str
    password: str

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
    
    # analytics & marketing
    ga4_measurement_id: Optional[str] = None
    google_tag_manager_id: Optional[str] = None
    facebook_pixel_id: Optional[str] = None
    microsoft_clarity_id: Optional[str] = None
    google_ads_client_id: Optional[str] = None
    google_ads_client_secret: Optional[str] = None
    google_ads_developer_token: Optional[str] = None
    google_ads_customer_id: Optional[str] = None
    facebook_ads_client_id: Optional[str] = None
    facebook_ads_client_secret: Optional[str] = None
    facebook_ads_account_id: Optional[str] = None
    facebook_ads_access_token: Optional[str] = None
    
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
    power_bi_iframe_url: Optional[str] = None
    influencimax_active: Optional[bool] = None
    
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
# ─────────────────────────────────────────────
# Notificações Multi-Canal
# ─────────────────────────────────────────────

class RecruiterWhatsAppRequest(BaseModel):
    phone: str
    text: str

# ─────────────────────────────────────────────
# Super Admin Endpoints
# ─────────────────────────────────────────────

import security
import shutil
from database import AuditLog, BlogPost, Banner, FinancialTransaction, FeedPost, FeedComment, FeedReaction, FinancialExpense, SupportTicket

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
# ── Rate limit: máx 5 tentativas de login a cada 10 minutos por IP ──
# ─── Support & Bug Reporting System ───────────────────────────────────────────
class SupportTicketCreate(BaseModel):
    user_name: str
    user_email: str
    user_role: str  # 'candidate' or 'recruiter'
    type: str       # 'bug' or 'support'
    message: str
    screenshot_url: Optional[str] = None

class FinancialTransactionCreate(BaseModel):
    user_email: str
    plan_name: str
    amount: float
    payment_method: str

class FinancialExpenseCreate(BaseModel):
    category: str
    name: str
    amount: float
    description: Optional[str] = None
    date: Optional[str] = None

class ViralRequest(BaseModel):
    platform: str
    target_audience: str

# ─────────────────────────────────────────────
#  MERCADO PAGO — PAYMENT ENDPOINTS
# ─────────────────────────────────────────────

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")
MP_PUBLIC_KEY   = os.getenv("MP_PUBLIC_KEY", "")
PIX_KEY         = os.getenv("PIX_KEY", "ricardomarchi@outlook.com")

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

class CardPaymentRequest(BaseModel):
    plan_id: str
    user_email: str
    card_number: str
    cardholder_name: str
    expiration_month: int
    expiration_year: int
    security_code: str

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

class SubmitAssessmentRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    answers: dict

class UpdateAssessmentRequest(BaseModel):
    title: str
    questions: list

def update_facebook_campaign(id: str, status: str, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {"status": "success", "new_status": status}


# ──────────────────────────────────────────────────────────────────────────────
# NOVOS ENDPOINTS - MARKETING, SEO, MONETIZAÇÃO, GROWTH & INDICAÇÕES
# ──────────────────────────────────────────────────────────────────────────────
from fastapi.responses import Response, HTMLResponse
import urllib.parse
import json
from datetime import timedelta

class ReferralClaimRequest(BaseModel):
    code: str

class NotificationPrefsRequest(BaseModel):
    email: bool
    whatsapp: bool
    push: bool

class NewsletterRequest(BaseModel):
    email: str

class BulkBlogImportRequest(BaseModel):
    posts: list # Lista de dicionários de posts

