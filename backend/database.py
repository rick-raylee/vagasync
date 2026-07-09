import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, Float, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./vagasync.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String, index=True)
    location = Column(String, nullable=True)
    link = Column(String, unique=True, index=True)
    source = Column(String, default="linkedin") # linkedin, web
    description = Column(Text, nullable=True)
    match_score = Column(Integer, nullable=True)
    match_explanation = Column(Text, nullable=True)
    status = Column(String, default="found")  # found, applying, applied, failed, contacted, archived
    applied_at = Column(DateTime, nullable=True)
    recruiter_name = Column(String, nullable=True)
    recruiter_contact = Column(String, nullable=True)
    recruiter_phone = Column(String, nullable=True)
    company_address = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    followup_sent = Column(Boolean, default=False)
    followup_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    recruiter_id = Column(Integer, nullable=True)  # Adicionado na Fase 2

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    name = Column(String, nullable=True)
    role = Column(String, default="candidate")  # 'candidate', 'recruiter', 'admin'
    resume_text = Column(Text, nullable=True)
    premium_until = Column(DateTime, nullable=True)
    recruiter_pro_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    referral_code = Column(String, nullable=True, index=True)
    referred_by = Column(String, nullable=True, index=True)
    referral_count = Column(Integer, default=0)
    notification_prefs = Column(Text, nullable=True) # JSON configuration

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    status = Column(String, default="found")  # found, applying, applied, failed...
    match_score = Column(Integer, nullable=True)
    match_explanation = Column(Text, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Config(Base):
    __tablename__ = "configs"

    key = Column(String, primary_key=True, index=True)
    value = Column(Text, nullable=True)

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String, default="info")  # info, warning, success, error
    message = Column(Text)

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True)
    sender = Column(String) # 'user' or 'recruiter'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String, index=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)

class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    summary = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    category = Column(String, nullable=True, index=True)
    slug = Column(String, nullable=True, index=True)

class Banner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    image_url = Column(String, nullable=True)
    link_url = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    position = Column(String, default="home")

class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, index=True)
    plan_name = Column(String)
    amount = Column(Float)
    status = Column(String, default="paid") # paid, pending, cancelled
    payment_method = Column(String) # stripe, mercadopago, pix
    created_at = Column(DateTime, default=datetime.utcnow)

class FinancialExpense(Base):
    __tablename__ = "financial_expenses"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)  # 'fornecedor', 'trafego_pago', 'outros'
    name = Column(String)      # e.g., 'Gemini API', 'Locaweb VPS', 'Google Ads'
    amount = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class FeedPost(Base):
    __tablename__ = "feed_posts"

    id = Column(Integer, primary_key=True, index=True)
    author_name = Column(String, nullable=False)
    author_email = Column(String, nullable=False)
    author_role = Column(String, nullable=False) # 'candidate', 'recruiter', 'ai_agent'
    content = Column(Text, nullable=False)
    likes = Column(Integer, default=0)
    claps = Column(Integer, default=0)
    loves = Column(Integer, default=0)
    ideas = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class FeedComment(Base):
    __tablename__ = "feed_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, index=True)
    author_name = Column(String, nullable=False)
    author_email = Column(String, nullable=False)
    author_role = Column(String, nullable=False) # 'candidate', 'recruiter', 'ai_agent'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class FeedReaction(Base):
    __tablename__ = "feed_reactions"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, index=True)
    user_email = Column(String, index=True)
    reaction_type = Column(String) # 'like', 'clap', 'love', 'idea'

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, index=True)
    job_title = Column(String, index=True)
    test_type = Column(String) # tech, behavioral
    title = Column(String)
    questions_json = Column(Text) # JSON string of questions
    created_at = Column(DateTime, default=datetime.utcnow)

class AssessmentSubmission(Base):
    __tablename__ = "assessment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(String, index=True)
    candidate_name = Column(String)
    candidate_email = Column(String)
    answers_json = Column(Text) # Selected alternatives
    score = Column(Integer) # correct answers
    created_at = Column(DateTime, default=datetime.utcnow)

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String, nullable=False)
    user_email = Column(String, nullable=False)
    user_role = Column(String, nullable=False)  # 'candidate' or 'recruiter'
    type = Column(String, nullable=False)       # 'bug' or 'support'
    message = Column(Text, nullable=False)
    screenshot_url = Column(String, nullable=True)
    status = Column(String, default="Pendente")  # 'Pendente', 'Resolvido'
    created_at = Column(DateTime, default=datetime.utcnow)

class AdsSpendCache(Base):
    __tablename__ = "ads_spend_cache"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True)  # 'facebook' ou 'google'
    date = Column(String, index=True)  # 'YYYY-MM-DD'
    spend = Column(Float, default=0.0)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Simple migration for SQLite to add missing columns in 'jobs' table
    db = SessionLocal()
    try:
        columns = [row[1] for row in db.execute(text("PRAGMA table_info(jobs)")).fetchall()]
        if "recruiter_phone" not in columns:
            db.execute(text("ALTER TABLE jobs ADD COLUMN recruiter_phone TEXT"))
        if "company_address" not in columns:
            db.execute(text("ALTER TABLE jobs ADD COLUMN company_address TEXT"))
        if "image_url" not in columns:
            db.execute(text("ALTER TABLE jobs ADD COLUMN image_url TEXT"))
        if "expires_at" not in columns:
            db.execute(text("ALTER TABLE jobs ADD COLUMN expires_at DATETIME"))
        if "recruiter_id" not in columns:
            db.execute(text("ALTER TABLE jobs ADD COLUMN recruiter_id INTEGER"))
        
        # Migrações da tabela 'users'
        users_columns = [row[1] for row in db.execute(text("PRAGMA table_info(users)")).fetchall()]
        if "referral_code" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN referral_code TEXT"))
        if "referred_by" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN referred_by TEXT"))
        if "referral_count" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0"))
        if "notification_prefs" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN notification_prefs TEXT"))

        # Migrações da tabela 'blog_posts'
        blog_columns = [row[1] for row in db.execute(text("PRAGMA table_info(blog_posts)")).fetchall()]
        if "category" not in blog_columns:
            db.execute(text("ALTER TABLE blog_posts ADD COLUMN category TEXT"))
        if "slug" not in blog_columns:
            db.execute(text("ALTER TABLE blog_posts ADD COLUMN slug TEXT"))
            
        db.commit()
        
        # Check if transaction table is empty
        # Mock transaction seeding disabled for production live site
            
        cursor = db.execute(text("SELECT COUNT(*) FROM blog_posts"))
        count_blog = cursor.fetchone()[0]
        if count_blog == 0:
            posts = [
                ("Como Otimizar seu Currículo para Filtros de IA", 
                 "Saiba quais palavras-chave usar e como estruturar seu perfil para passar pelos sistemas de inteligência artificial.",
                 "Muitas empresas hoje usam sistemas automatizados para triagem de currículos. Para garantir que o seu perfil seja selecionado, você deve incluir termos técnicos específicos listados no anúncio da vaga, evitar layouts excessivamente complexos e focar em resultados numéricos.",
                 "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=800"),
                ("O Futuro do Recrutamento com Agentes de IA",
                 "Entenda como a IA generativa está revolucionando a forma como empresas contratam profissionais.",
                 "Com o advento do ChatGPT e de outras IAs generativas, o processo de contratação tornou-se bidirecionalmente automatizado. Candidatos usam agentes para buscar vagas e enviar currículos, enquanto recrutadores usam filtros de match avançados para selecionar os melhores talentos em segundos.",
                 "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800")
            ]
            for title, summary, content, img in posts:
                db.execute(text("""
                    INSERT INTO blog_posts (title, summary, content, image_url, published_at)
                    VALUES (:title, :summary, :content, :image_url, :published_at)
                """), {
                    "title": title,
                    "summary": summary,
                    "content": content,
                    "image_url": img,
                    "published_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                })
            db.commit()
            
        cursor = db.execute(text("SELECT COUNT(*) FROM banners"))
        count_banners = cursor.fetchone()[0]
        if count_banners == 0:
            banners = [
                ("VagaSync Premium — IA Ilimitada", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200", "#checkout", True, "home"),
                ("Novo Treinamento de Entrevista por Vídeo", "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=1200", "#interview", True, "interview")
            ]
            for title, img, link, active, pos in banners:
                db.execute(text("""
                    INSERT INTO banners (title, image_url, link_url, active, position)
                    VALUES (:title, :image_url, :link_url, :active, :position)
                """), {
                    "title": title,
                    "image_url": img,
                    "link_url": link,
                    "active": 1 if active else 0,
                    "position": pos
                })
            db.commit()
            
        cursor = db.execute(text("SELECT COUNT(*) FROM audit_logs"))
        count_audit = cursor.fetchone()[0]
        if count_audit == 0:
            audit_logs = [
                ("SYSTEM_INIT", "Banco de dados inicializado com sucesso.", "127.0.0.1"),
                ("CONFIG_LOAD", "Configurações globais carregadas.", "127.0.0.1")
            ]
            for action, details, ip in audit_logs:
                db.execute(text("""
                    INSERT INTO audit_logs (action, details, ip_address, timestamp)
                    VALUES (:action, :details, :ip_address, :timestamp)
                """), {
                    "action": action,
                    "details": details,
                    "ip_address": ip,
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                })
            db.commit()
            
    except Exception as e:
        print(f"Error performing SQLite migration or seeding: {e}")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def add_log(level: str, message: str):
    db = SessionLocal()
    try:
        log = Log(level=level, message=message)
        db.add(log)
        db.commit()
    except Exception as e:
        print(f"Error saving log: {e}")
    finally:
        db.close()
