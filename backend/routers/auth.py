import requests
from pydantic import BaseModel
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
import secrets
from urllib.parse import urlencode

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
    if cfg and cfg.value:
        return cfg.value
    enc_cfg = db.query(Config).filter(Config.key == f"enc_{key}").first()
    if enc_cfg and enc_cfg.value:
        import security
        decrypted = security.decrypt_data(enc_cfg.value)
        if decrypted:
            return decrypted
    return os.getenv(key.upper(), default)

linkedin_oauth_states = {}
LINKEDIN_STATE_EXPIRE_SECONDS = 300

def cleanup_linkedin_oauth_states():
    now = int(time.time())
    expired = [state for state, ts in linkedin_oauth_states.items() if now - ts > LINKEDIN_STATE_EXPIRE_SECONDS]
    for state in expired:
        linkedin_oauth_states.pop(state, None)

def get_linkedin_credentials(db: Session):
    client_id = get_config_value(db, "linkedin_client_id", "") or ""
    client_secret = get_config_value(db, "linkedin_client_secret", "") or ""
    return client_id.strip(), client_secret.strip()

def get_linkedin_redirect_uri(request: Request) -> str:
    if request is not None:
        host = request.url.hostname or ""
        if "localhost" in host or "127.0.0.1" in host:
            port = request.url.port
            port_fragment = f":{port}" if port and port != 80 else ""
            return f"http://{host}{port_fragment}/api/linkedin/callback"
    # O redirect URI oficial cadastrado e homologado no Console do LinkedIn
    return "https://www.vagasync.com.br/api/linkedin/callback"

def get_linkedin_user_info(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    profile_name = ""
    profile_email = ""
    
    print(f"[LinkedIn Auth] Iniciando consulta ao endpoint OIDC Userinfo...")
    try:
        resp = requests.get("https://api.linkedin.com/oidc/userinfo", headers=headers, timeout=10)
        print(f"[LinkedIn Auth] OIDC Userinfo HTTP Status: {resp.status_code}")
        print(f"[LinkedIn Auth] OIDC Userinfo Response: {resp.text}")
        if resp.ok:
            data = resp.json()
            profile_name = data.get("name", "") or data.get("given_name", "")
            if not profile_name:
                first_name = data.get("localizedFirstName", "")
                last_name = data.get("localizedLastName", "")
                profile_name = " ".join([part for part in [first_name, last_name] if part]).strip()
            profile_email = data.get("email", "")
            print(f"[LinkedIn Auth] OIDC obtido com sucesso: Nome={profile_name}, E-mail={profile_email}")
    except Exception as e:
        print(f"[LinkedIn Auth] Erro ao consultar endpoint OIDC: {e}")
        profile_name = ""
        profile_email = ""

    # Fallbacks legado caso o novo endpoint OIDC não retorne as chaves necessárias
    if not profile_name:
        print(f"[LinkedIn Auth] Nome vazio. Tentando endpoint legado /v2/me...")
        try:
            resp = requests.get(
                "https://api.linkedin.com/v2/me?projection=(localizedFirstName,localizedLastName)",
                headers=headers,
                timeout=10
            )
            print(f"[LinkedIn Auth] Legado /v2/me Status: {resp.status_code}, Resposta: {resp.text}")
            if resp.ok:
                data = resp.json()
                profile_name = " ".join([part for part in [data.get("localizedFirstName", ""), data.get("localizedLastName", "")] if part]).strip()
                print(f"[LinkedIn Auth] Nome obtido via endpoint legado: {profile_name}")
        except Exception as e:
            print(f"[LinkedIn Auth] Erro no endpoint legado /v2/me: {e}")

    if not profile_email:
        print(f"[LinkedIn Auth] Email vazio. Tentando endpoint legado /v2/emailAddress...")
        try:
            resp = requests.get(
                "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
                headers=headers,
                timeout=10
            )
            print(f"[LinkedIn Auth] Legado emailAddress Status: {resp.status_code}, Resposta: {resp.text}")
            if resp.ok:
                data = resp.json()
                elements = data.get("elements", [])
                if elements and isinstance(elements, list):
                    handle = elements[0].get("handle~") if isinstance(elements[0], dict) else None
                    if handle and isinstance(handle, dict):
                        profile_email = handle.get("emailAddress", "")
                        print(f"[LinkedIn Auth] Email obtido via endpoint legado: {profile_email}")
        except Exception as e:
            print(f"[LinkedIn Auth] Erro no endpoint legado /v2/emailAddress: {e}")

    return profile_name.strip(), profile_email.strip()

def create_or_get_linkedin_user(name: str, email: str, db: Session):
    from database import User
    email = email.strip().lower()
    if not email:
        print("[LinkedIn Auth] Erro: E-mail do usuário do LinkedIn está vazio.")
        return None

    print(f"[LinkedIn Auth] Buscando usuário pelo e-mail no DB: {email}")
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"[LinkedIn Auth] Usuário existente encontrado: ID={user.id}, Role={user.role}")
        if not user.name and name:
            user.name = name.strip()
            db.commit()
            db.refresh(user)
            print("[LinkedIn Auth] Nome do usuário atualizado no DB.")
        if not user.password_hash:
            user.password_hash = security.hash_password(secrets.token_urlsafe(32))
            db.commit()
            db.refresh(user)
            print("[LinkedIn Auth] Password hash gerado e salvo para usuário do LinkedIn.")
        return user

    print(f"[LinkedIn Auth] Usuário inexistente. Criando nova conta de candidato...")
    password_hash = security.hash_password(secrets.token_urlsafe(32))
    user = User(
        email=email,
        name=name.strip() if name else email,
        password_hash=password_hash,
        role="candidate"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"[LinkedIn Auth] Nova conta criada com sucesso: ID={user.id}")
    return user

def get_frontend_url(db: Session) -> str:
    return get_config_value(db, "frontend_url", os.getenv("FRONTEND_URL", "http://localhost:5173"))

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


@router.get("/api/linkedin/login")
def linkedin_login(request: Request, db: Session = Depends(get_db)):
    print("[LinkedIn Auth] Iniciando fluxo de autorização...")
    client_id, client_secret = get_linkedin_credentials(db)
    if not client_id or not client_secret:
        msg = "Chaves do LinkedIn (Client ID / Secret) não configuradas no sistema."
        print(f"[LinkedIn Auth] Erro: {msg}")
        add_log("error", f"LinkedIn Auth falhou: {msg}")
        return HTMLResponse(
            f"<h1>LinkedIn OAuth não configurado</h1><p>{msg}</p><p>Verifique o painel administrativo ou as configurações do banco.</p>",
            status_code=500
        )

    cleanup_linkedin_oauth_states()
    state = secrets.token_urlsafe(16)
    linkedin_oauth_states[state] = int(time.time())

    redirect_uri = get_linkedin_redirect_uri(request)
    print(f"[LinkedIn Auth] Gerado State: {state}")
    print(f"[LinkedIn Auth] Redirect URI utilizado: {redirect_uri}")

    # Escopos OIDC oficiais atualizados (openid, profile, email)
    # Escopos legados de 2023 (r_liteprofile, r_emailaddress) geram erro imediato de permissão/página de erro no console LinkedIn.
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": "openid profile email"
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    print(f"[LinkedIn Auth] Redirecionando usuário para: {auth_url}")
    return RedirectResponse(auth_url)


@router.get("/api/linkedin/callback")
def linkedin_callback(request: Request, db: Session = Depends(get_db)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")
    error_description = request.query_params.get("error_description")

    print(f"[LinkedIn Auth Callback] Recebido callback do LinkedIn.")
    print(f"[LinkedIn Auth Callback] Code: {code[:10] if code else None}...")
    print(f"[LinkedIn Auth Callback] State: {state}")
    print(f"[LinkedIn Auth Callback] Error: {error}, Description: {error_description}")

    frontend_url = get_frontend_url(db)

    # Caso o usuário cancele ou ocorra erro de consentimento no LinkedIn
    if error:
        detail = error_description or "Autorização do LinkedIn foi negada pelo usuário."
        print(f"[LinkedIn Auth Callback] Erro retornado pelo LinkedIn: {detail}")
        add_log("warning", f"Login LinkedIn cancelado/erro: {detail}")
        redirect_to = f"{frontend_url}/?{urlencode({'linkedin_auth': 'error', 'error_message': detail})}"
        return RedirectResponse(redirect_to)

    # Validar state gerado contra CSRF
    if not code or not state or state not in linkedin_oauth_states:
        msg = "Estado OAuth inválido ou código de autorização ausente (CSRF ou timeout de sessão)."
        print(f"[LinkedIn Auth Callback] Falha de validação de estado. States válidos: {list(linkedin_oauth_states.keys())}")
        add_log("error", f"Falha de validação de estado CSRF no login LinkedIn.")
        cleanup_linkedin_oauth_states()
        redirect_to = f"{frontend_url}/?{urlencode({'linkedin_auth': 'error', 'error_message': msg})}"
        return RedirectResponse(redirect_to)

    # Consumir o state
    linkedin_oauth_states.pop(state, None)
    cleanup_linkedin_oauth_states()

    try:
        client_id, client_secret = get_linkedin_credentials(db)
        redirect_uri = get_linkedin_redirect_uri(request)

        print(f"[LinkedIn Auth Callback] Efetuando POST para accessToken...")
        print(f"[LinkedIn Auth Callback] URL: https://www.linkedin.com/oauth/v2/accessToken")
        print(f"[LinkedIn Auth Callback] Redirect URI: {redirect_uri}")
        print(f"[LinkedIn Auth Callback] Client ID: {client_id}")

        # Requisição POST de troca do token
        token_resp = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )

        print(f"[LinkedIn Auth Callback] AccessToken Response HTTP Status: {token_resp.status_code}")
        if not token_resp.ok:
            detail = token_resp.text or "Falha ao trocar código por token de acesso do LinkedIn."
            print(f"[LinkedIn Auth Callback] Erro na requisição do token: {detail}")
            add_log("error", f"Troca de token do LinkedIn falhou: {detail}")
            redirect_to = f"{frontend_url}/?{urlencode({'linkedin_auth': 'error', 'error_message': detail})}"
            return RedirectResponse(redirect_to)

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            msg = "Token de acesso do LinkedIn ausente no retorno da API."
            print(f"[LinkedIn Auth Callback] Erro: {msg}")
            add_log("error", f"LinkedIn Auth: {msg}")
            redirect_to = f"{frontend_url}/?{urlencode({'linkedin_auth': 'error', 'error_message': msg})}"
            return RedirectResponse(redirect_to)

        print("[LinkedIn Auth Callback] Token de acesso obtido com sucesso.")

        # Buscar dados cadastrais do perfil
        profile_name, profile_email = get_linkedin_user_info(access_token)
        if not profile_email:
            msg = "Não foi possível recuperar o e-mail da conta do LinkedIn. Por favor, verifique as permissões de acesso do seu aplicativo."
            print(f"[LinkedIn Auth Callback] Erro: {msg}")
            add_log("error", f"LinkedIn Auth: {msg}")
            redirect_to = f"{frontend_url}/?{urlencode({'linkedin_auth': 'error', 'error_message': msg})}"
            return RedirectResponse(redirect_to)

        # Autenticar/Registrar no DB
        user = create_or_get_linkedin_user(profile_name, profile_email, db)
        if not user:
            msg = "Falha ao registrar ou buscar usuário correspondente ao LinkedIn no banco de dados."
            print(f"[LinkedIn Auth Callback] Erro: {msg}")
            add_log("error", f"LinkedIn Auth: {msg}")
            redirect_to = f"{frontend_url}/?{urlencode({'linkedin_auth': 'error', 'error_message': msg})}"
            return RedirectResponse(redirect_to)

        # Criar JWT do VagaSync
        access_jwt = security.create_jwt({"user_id": user.id, "role": user.role}, expires_in=3600)
        log_audit("USER_LOGIN", f"Usuário {profile_email} logado com sucesso via LinkedIn.", db)
        print(f"[LinkedIn Auth Callback] Login concluído. Gerado JWT para usuário ID={user.id}")

        query = {
            "linkedin_auth": "success",
            "linkedin_token": access_jwt,
            "linkedin_email": profile_email,
            "linkedin_role": user.role
        }
        if profile_name:
            query["linkedin_name"] = profile_name

        redirect_to = f"{frontend_url}/?{urlencode(query)}"
        print(f"[LinkedIn Auth Callback] Redirecionando usuário logado para o frontend: {redirect_to}")
        return RedirectResponse(redirect_to)

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[LinkedIn Auth Callback] Exceção crítica disparada no fluxo: {e}\nTraceback:\n{tb}")
        add_log("error", f"Erro interno crítico no callback do LinkedIn: {str(e)}")
        # Tratamento amigável - nunca envia tela em branco
        friendly_error = f"Erro crítico interno no processo de login: {str(e)}"
        redirect_to = f"{frontend_url}/?{urlencode({'linkedin_auth': 'error', 'error_message': friendly_error})}"
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



@router.post("/api/auth/send-reset-code")
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



@router.get("/api/auth/me")
def get_current_user_profile(current_user = Depends(get_current_user)):
    import json
    analysis_data = None
    if getattr(current_user, "resume_analysis", None):
        try:
            analysis_data = json.loads(current_user.resume_analysis)
        except Exception:
            pass
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "resume_text": current_user.resume_text or "",
        "resume_analysis": analysis_data
    }


@router.post("/api/auth/register")
def auth_register(payload: UserRegister, db: Session = Depends(get_db)):
    from database import User
    # Verifica se usuario ja existe
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado.")
    
    password_hash = security.hash_password(payload.password)
    
    new_user = User(
        email=payload.email,
        password_hash=password_hash,
        name=payload.name,
        role=payload.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_audit("USER_REGISTER", f"Novo usuário registrado: {payload.email} (papel: {payload.role})", db)
    return {"message": "Usuário registrado com sucesso.", "user_id": new_user.id}



@router.post("/api/auth/login")
def auth_login(payload: UserLogin, request: Request, db: Session = Depends(get_db)):
    _check_login_rate_limit(request)
    from database import User
    
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
        
    if not security.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
        
    ip = request.client.host if request.client else "unknown"
    _login_attempts.pop(ip, None)
    
    access_token = security.create_jwt({"user_id": user.id, "role": user.role}, expires_in=3600)
    refresh_token = security.create_jwt({"user_id": user.id, "role": user.role, "type": "refresh"}, expires_in=86400 * 7)
    
    log_audit("USER_LOGIN", f"Usuário {user.email} efetuou login com sucesso.", db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": user.role,
        "user_id": user.id,
        "name": user.name
    }



@router.post("/api/admin/login")
def admin_login(payload: AdminLogin, request: Request):
    _check_login_rate_limit(request)
    import hmac

    # Carrega credenciais do .env com fallbacks
    admin_email = os.getenv("ADMIN_EMAIL", "admin@vagasync.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "admin123")

    ricardo_email_1 = os.getenv("ADMIN_RICARDO_EMAIL_1", "ricardo@vagasync.com.br")
    ricardo_email_2 = os.getenv("ADMIN_RICARDO_EMAIL_2", "ricardo@vagasync.com")
    ricardo_password = os.getenv("ADMIN_RICARDO_PASSWORD", "Vagasync2026#")

    is_valid_email = payload.email in [admin_email, ricardo_email_1, ricardo_email_2]
    
    is_valid_pw = False
    if payload.email == admin_email:
        is_valid_pw = hmac.compare_digest(payload.password.encode(), admin_password.encode())
    elif payload.email in [ricardo_email_1, ricardo_email_2]:
        is_valid_pw = hmac.compare_digest(payload.password.encode(), ricardo_password.encode())
    
    if is_valid_email and is_valid_pw:
        # Limpa tentativas após login bem-sucedido
        ip = request.client.host if request.client else "unknown"
        _login_attempts.pop(ip, None)
        # Generate temporary token for 2FA verification
        temp_token = security.create_jwt({"role": "temp_admin"}, expires_in=300)
        return {"needs_2fa": True, "temp_token": temp_token}
    raise HTTPException(status_code=401, detail="E-mail ou senha do proprietário incorretos.")



@router.post("/api/admin/verify-2fa")
def admin_verify_2fa(payload: Verify2FA, db: Session = Depends(get_db)):
    # Production: verify JWT token
    temp_payload = security.verify_jwt(payload.temp_token)
    if not temp_payload or temp_payload.get("role") != "temp_admin":
        raise HTTPException(status_code=400, detail="Token temporário inválido ou expirado.")
    
    # Verify TOTP code (backdoor "000000" allowed in DEV_MODE for local testing)
    dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
    is_valid = security.verify_totp(security.TOTP_SECRET, payload.code) or (dev_mode and payload.code == "000000")
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



@router.post("/api/admin/refresh")
def admin_refresh(payload: RefreshToken):
    refresh_payload = security.verify_jwt(payload.refresh_token)
    if not refresh_payload or refresh_payload.get("role") != "admin" or refresh_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token de atualização inválido ou expirado.")
        
    access_token = security.create_jwt({"role": "admin"}, expires_in=3600)
    return {"access_token": access_token}


@router.post("/api/auth/refresh")
def auth_refresh(payload: RefreshToken, db: Session = Depends(get_db)):
    refresh_payload = security.verify_jwt(payload.refresh_token)
    if not refresh_payload or refresh_payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token de atualização inválido ou expirado.")
        
    user_id = refresh_payload.get("user_id")
    role = refresh_payload.get("role")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token de atualização inválido.")
        
    # Generate new access token and fresh refresh token
    access_token = security.create_jwt({"user_id": user_id, "role": role}, expires_in=3600)
    new_refresh_token = security.create_jwt({"user_id": user_id, "role": role, "type": "refresh"}, expires_in=86400 * 7)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token
    }



@router.get("/api/google-ads/status")
def google_ads_status(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    connected = db.query(Config).filter(Config.key == "google_ads_connected").first()
    is_connected = connected.value == "true" if connected else False
    return {"connected": is_connected, "mode": "sandbox", "customer_id": "DEMO-123-4567" if is_connected else None}



@router.get("/api/google-ads/auth-url")
def google_ads_auth_url(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {"auth_url": "https://accounts.google.com/o/oauth2/v2/auth?demo=1", "is_demo": True}



@router.post("/api/google-ads/callback")
def google_ads_callback(code: str = "demo_code", admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    cfg = db.query(Config).filter(Config.key == "google_ads_connected").first()
    if cfg:
        cfg.value = "true"
    else:
        db.add(Config(key="google_ads_connected", value="true"))
    db.commit()
    return {"status": "success"}



@router.post("/api/google-ads/disconnect")
def google_ads_disconnect(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    cfg = db.query(Config).filter(Config.key == "google_ads_connected").first()
    if cfg:
        cfg.value = "false"
        db.commit()
    return {"status": "success"}



@router.get("/api/google-ads/metrics")
def google_ads_metrics(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return {
        "totals": {"impressions": 340050, "clicks": 45100, "cost": 1500.50, "conversions": 3400},
        "timeline": [{"date": "2026-07-01", "impressions": 5000, "clicks": 400}, {"date": "2026-07-02", "impressions": 6000, "clicks": 450}],
        "spend_by_campaign": [{"name": "Campanha Pesquisa", "spend": 1000}, {"name": "Campanha Display", "spend": 500}]
    }



@router.get("/api/google-ads/campaigns")
def google_ads_campaigns(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    return [
        {"id": "g_101", "name": "Pesquisa - Vagas Tech", "status": "ACTIVE", "budget": 50.0, "spend": 45.2, "impressions": 15000, "clicks": 2500, "conversions": 120}
    ]

# --- FACEBOOK ADS INTEGRATION (DEMO/SANDBOX) ---



class GoogleLoginPayload(BaseModel):
    credential: str

@router.post("/api/auth/google/callback")
def google_callback(payload: GoogleLoginPayload, db: Session = Depends(get_db)):
    token = payload.credential
    try:
        res = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={token}", timeout=10)
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail="Token do Google inválido ou expirado.")
        
        info = res.json()
        expected_aud = "223926647816-72gp4pekojfk2q3p9ro4o67i8058csi0.apps.googleusercontent.com"
        if info.get("aud") != expected_aud:
            raise HTTPException(status_code=400, detail="Audiência do token do Google inválida.")
            
        email = info.get("email")
        name = info.get("name", "")
        
        if not email:
            raise HTTPException(status_code=400, detail="O token do Google não fornece e-mail.")
            
        user = db.query(User).filter(User.email == email).first()
        if not user:
            import secrets
            password_hash = security.hash_password(secrets.token_urlsafe(32))
            user = User(
                email=email,
                name=name if name else email,
                password_hash=password_hash,
                role="candidate"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            log_audit("AUTH_GOOGLE_REGISTER", f"Usuário registrado automaticamente via Google: {email}", db)
        else:
            log_audit("AUTH_GOOGLE_LOGIN", f"Usuário logado via Google: {email}", db)
            
        access_token = security.create_jwt({"user_id": user.id, "role": user.role}, expires_in=3600)
        refresh_token = security.create_jwt({"user_id": user.id, "role": user.role, "type": "refresh"}, expires_in=86400 * 7)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "role": user.role,
            "user_id": user.id,
            "name": user.name,
            "email": user.email
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Erro interno de autenticação Google: {str(e)}")
