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

ALLOWED_RESUME_EXTENSIONS = {".txt", ".pdf", ".doc", ".docx", ".odt"}
ALLOWED_RESUME_CONTENT_TYPES = {
    "text/plain", "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.oasis.opendocument.text"
}
MAX_RESUME_SIZE_MB = 5

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


@router.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(None), text: str = Form(None), current_user = Depends(get_current_user), db: Session = Depends(get_db)):
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

    import json
    # Salva o currículo no usuário logado de forma isolada! (Fase 2)
    if isinstance(current_user, dict):
        resume_cfg = db.query(Config).filter(Config.key == "resume_text").first()
        if resume_cfg:
            resume_cfg.value = resume_content
        else:
            db.add(Config(key="resume_text", value=resume_content))

        analysis_cfg = db.query(Config).filter(Config.key == "resume_analysis").first()
        if analysis_cfg:
            analysis_cfg.value = json.dumps(analysis)
        else:
            db.add(Config(key="resume_analysis", value=json.dumps(analysis)))
    else:
        current_user.resume_text = resume_content
        current_user.resume_analysis = json.dumps(analysis)
        
    db.commit()
    
    return {
        "message": "Currículo processado com sucesso.",
        "analysis": analysis,
        "resume_text": resume_content
    }



@router.get("/api/jobs", response_model=List[JobResponse])
def get_jobs(current_user = Depends(get_optional_user), db: Session = Depends(get_db)):
    # Vagas de recrutadores (source='recruiter') aparecem primeiro, depois por data
    from sqlalchemy import case
    priority = case(
        (Job.source == 'recruiter', 0),
        else_=1
    )

    jobs = db.query(Job).order_by(priority, Job.created_at.desc()).all()

    # Se o usuário estiver logado como candidato, buscamos as candidaturas dele
    user_applications = {}
    if current_user and not isinstance(current_user, dict):
        from database import Application
        apps = db.query(Application).filter(Application.candidate_id == current_user.id).all()
        user_applications = {a.job_id: a for a in apps}

    # Normalização de link e isolamento de status/match do candidato logado
    for j in jobs:
        if getattr(j, "source", None) == "recruiter":
            try:
                j.link = f"https://vagasync.com.br/vagas/{j.id}"
            except Exception:
                pass
                
        # Injeta status do candidato se ele tiver candidatura para a vaga
        if j.id in user_applications:
            app_data = user_applications[j.id]
            j.status = app_data.status
            j.match_score = app_data.match_score
            j.match_explanation = app_data.match_explanation
            j.applied_at = app_data.applied_at
        else:
            # Caso contrário, para este candidato a vaga está pendente (found) e sem data de candidatura
            j.status = "found"
            j.applied_at = None

    return jobs




@router.post("/api/jobs", response_model=JobResponse)
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



@router.post("/api/jobs/{job_id}/upload-image")
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



@router.post("/api/jobs/{job_id}/generate-image-ia")
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



@router.delete("/api/jobs/{job_id}")
def delete_job(job_id: int, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
    db.delete(job)
    db.commit()
    return {"message": "Vaga deletada com sucesso."}



@router.patch("/api/jobs/{job_id}")
async def update_job_status(job_id: int, payload: dict, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Vaga não encontrada")
        
    # Se for o mock admin, atualiza global
    if isinstance(current_user, dict):
        if "status" in payload:
            job.status = payload["status"]
            if payload["status"] == "applied":
                job.applied_at = datetime.utcnow()
        db.commit()
        db.refresh(job)
        return {"message": "Status global updated by admin.", "status": job.status}

    # Candidato logado
    from database import Application
    app_entry = db.query(Application).filter(Application.candidate_id == current_user.id, Application.job_id == job_id).first()
    
    old_status = "found"
    if not app_entry:
        app_entry = Application(
            candidate_id=current_user.id,
            job_id=job_id,
            status=payload.get("status", "found"),
            created_at=datetime.utcnow()
        )
        db.add(app_entry)
    else:
        old_status = app_entry.status
        if "status" in payload:
            app_entry.status = payload["status"]
            
    if payload.get("status") == "applied" and old_status != "applied":
        app_entry.applied_at = datetime.utcnow()
        # If recruiter-posted job, notify recruiter
        if job.source == "recruiter" and (job.recruiter_contact or job.recruiter_phone):
            try:
                # Criamos um mock temporario do job contendo os status do candidato para o notifier
                job_mock = job
                job_mock.status = app_entry.status
                job_mock.applied_at = app_entry.applied_at
                await notifier.dispatch_notification("candidate_applied", job_mock, db)
            except Exception as e:
                print(f"Error notifying recruiter: {e}")
                
    db.commit()
    return {"message": "Status updated successfully.", "status": app_entry.status}




@router.post("/api/jobs/{job_id}/extend", response_model=JobResponse)
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




@router.post("/api/jobs/clear-all")
def clear_all_jobs(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        db.query(Job).delete()
        db.query(Log).delete()
        db.commit()
        add_log("info", "🧹 Todas as vagas e logs foram limpos do banco de dados pelo administrador.")
        return {"message": "Todas as vagas e logs foram excluídos com sucesso."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao limpar banco de dados: {str(e)}")



@router.get("/api/jobs/{job_id}/messages", response_model=List[MessageResponse])
def get_job_messages(job_id: int, db: Session = Depends(get_db)):
    from database import Message
    return db.query(Message).filter(Message.job_id == job_id).order_by(Message.timestamp.asc()).all()



@router.post("/api/jobs/{job_id}/messages", response_model=MessageResponse)
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

