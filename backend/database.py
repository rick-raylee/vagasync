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
    resume_analysis = Column(Text, nullable=True)
    premium_until = Column(DateTime, nullable=True)
    recruiter_pro_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    referral_code = Column(String, nullable=True, index=True)
    referred_by = Column(String, nullable=True, index=True)
    referral_count = Column(Integer, default=0)
    notification_prefs = Column(Text, nullable=True) # JSON configuration
    linkedin_id = Column(String, nullable=True, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    language = Column(String, nullable=True)
    last_login = Column(DateTime, nullable=True)
    provider = Column(String, nullable=True)
    provider_id = Column(String, nullable=True)

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
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    gallery_images = Column(Text, nullable=True) # JSON list
    table_of_contents = Column(Text, nullable=True) # JSON list

class BlogComment(Base):
    __tablename__ = "blog_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, index=True)
    author_name = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    audio_url = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    views = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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

class TalentBank(Base):
    """Candidatos cadastrados no Banco de Talentos."""
    __tablename__ = "talent_bank"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, index=True, unique=True)  # FK users.id
    candidate_name = Column(String, nullable=False)
    candidate_email = Column(String, nullable=False, index=True)
    area = Column(String, nullable=True)       # Ex: 'TI', 'Marketing', 'Vendas'
    skills = Column(Text, nullable=True)       # Texto livre de habilidades
    city = Column(String, nullable=True)
    salary_expectation = Column(String, nullable=True)  # Ex: 'R$ 5.000'
    availability = Column(String, default="imediata")   # imediata, 15 dias, 30 dias
    linkedin_url = Column(String, nullable=True)
    resume_summary = Column(Text, nullable=True)        # Breve resumo profissional
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(Base):
    """Notificações geradas para candidatos (match de vagas, sistema, etc)."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)               # FK users.id
    user_email = Column(String, index=True)
    type = Column(String, default="job_match")           # job_match, talent_bank, system
    title = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    job_id = Column(Integer, nullable=True)             # Referência à vaga (opcional)
    job_title = Column(String, nullable=True)           # Cache do título da vaga
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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
        if "is_archived" not in columns:
            db.execute(text("ALTER TABLE jobs ADD COLUMN is_archived INTEGER DEFAULT 0"))
        
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
        if "linkedin_id" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN linkedin_id TEXT"))
        if "first_name" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN first_name TEXT"))
        if "last_name" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN last_name TEXT"))
        if "photo_url" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN photo_url TEXT"))
        if "language" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN language TEXT"))
        if "last_login" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN last_login DATETIME"))
        if "provider" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN provider TEXT"))
        if "provider_id" not in users_columns:
            db.execute(text("ALTER TABLE users ADD COLUMN provider_id TEXT"))

        # Migrações da tabela 'blog_posts'
        blog_columns = [row[1] for row in db.execute(text("PRAGMA table_info(blog_posts)")).fetchall()]
        if "category" not in blog_columns:
            db.execute(text("ALTER TABLE blog_posts ADD COLUMN category TEXT"))
        if "slug" not in blog_columns:
            db.execute(text("ALTER TABLE blog_posts ADD COLUMN slug TEXT"))
        if "views" not in blog_columns:
            db.execute(text("ALTER TABLE blog_posts ADD COLUMN views INTEGER DEFAULT 0"))
        if "likes" not in blog_columns:
            db.execute(text("ALTER TABLE blog_posts ADD COLUMN likes INTEGER DEFAULT 0"))
        if "comments_count" not in blog_columns:
            db.execute(text("ALTER TABLE blog_posts ADD COLUMN comments_count INTEGER DEFAULT 0"))
        if "gallery_images" not in blog_columns:
            db.execute(text("ALTER TABLE blog_posts ADD COLUMN gallery_images TEXT"))
        if "table_of_contents" not in blog_columns:
            db.execute(text("ALTER TABLE blog_posts ADD COLUMN table_of_contents TEXT"))
            
        db.commit()
        
        # Seeding blog posts
        cursor = db.execute(text("SELECT COUNT(*) FROM blog_posts"))
        count_blog = cursor.fetchone()[0]
        if count_blog < 15:
            # Clear old posts to ensure rich content
            db.execute(text("DELETE FROM blog_posts"))
            db.commit()
            
            import json
            posts = [
                {
                    "title": "Como Otimizar seu Currículo para Filtros de IA",
                    "category": "Dicas de Currículo",
                    "summary": "Saiba quais palavras-chave usar e como estruturar seu perfil para passar pelos sistemas de inteligência artificial.",
                    "content": "Muitas empresas hoje usam sistemas automatizados para triagem de currículos (ATS). Para garantir que o seu perfil seja selecionado, você deve incluir termos técnicos específicos listados no anúncio da vaga, evitar layouts excessivamente complexos e focar em resultados numéricos.\n\nEvite tabelas aninhadas ou caixas de texto que confundem os parsers automáticos. Use uma formatação limpa e linear. Lembre-se: as competências mais importantes devem estar no topo do seu currículo em uma seção dedicada de competências técnicas.",
                    "image_url": "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=800",
                    "slug": "como-otimizar-seu-curriculo-para-filtros-de-ia",
                    "views": 412,
                    "likes": 56,
                    "gallery": ["https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=800", "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=800"],
                    "toc": ["1. Introdução", "2. Como os ATS Funcionam", "3. Regras de Otimização", "4. Conclusão"]
                },
                {
                    "title": "O Futuro do Recrutamento com Agentes de IA",
                    "category": "IA & Tecnologia",
                    "summary": "Entenda como a IA generativa está revolucionando a forma como empresas contratam profissionais.",
                    "content": "Com o advento do ChatGPT e de outras IAs generativas, o processo de contratação tornou-se bidirecionalmente automatizado. Candidatos usam agentes para buscar vagas e enviar currículos, enquanto recrutadores usam filtros de match avançados para selecionar os melhores talentos em segundos.\n\nNo futuro próximo, as entrevistas iniciais de triagem serão conduzidas quase que inteiramente por robôs inteligentes, capazes de avaliar não apenas respostas técnicas, mas também competências comportamentais e inteligência emocional em tempo real.",
                    "image_url": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800",
                    "slug": "o-futuro-do-recrutamento-com-agentes-de-ia",
                    "views": 329,
                    "likes": 48,
                    "gallery": ["https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800", "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800"],
                    "toc": ["1. Introdução", "2. A Era das Candidaturas Automatizadas", "3. Conclusão"]
                },
                {
                    "title": "As Profissões Tech mais Procuradas em 2026",
                    "category": "Mercado de Trabalho",
                    "summary": "Veja quais são as áreas de atuação com maior potencial de crescimento e salários em alta.",
                    "content": "O mercado de tecnologia mudou drasticamente. Engenharia de IA, Engenharia de Prompt, DevOps com foco em nuvens descentralizadas e Analista de Segurança Cibernética são as quatro áreas que mais crescem globalmente em 2026.\n\nA capacitação contínua e a flexibilidade para aprender novas ferramentas rapidamente são as principais características que os gerentes de contratação buscam hoje em dia.",
                    "image_url": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800",
                    "slug": "profissoes-tech-mais-procuradas-2026",
                    "views": 598,
                    "likes": 92,
                    "gallery": ["https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800", "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800"],
                    "toc": ["1. Introdução", "2. As 4 Áreas Quentes", "3. Salários e Perspectivas"]
                },
                {
                    "title": "Guia para sua Primeira Entrevista de Emprego",
                    "category": "Entrevistas de Emprego",
                    "summary": "Aprenda a se preparar, se vestir e o que falar na sua primeira conversa com os recrutadores.",
                    "content": "A primeira entrevista pode ser intimidadora. O segredo está na preparação básica: estude o produto da empresa, revise a descrição da vaga e treine respostas para perguntas clássicas como 'fale sobre você' ou 'quais são seus pontos fortes'.\n\nManter uma postura profissional, falar pausadamente e demonstrar paixão e interesse genuíno pela oportunidade farão você se destacar de outros candidatos com o mesmo perfil técnico.",
                    "image_url": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=800",
                    "slug": "guia-primeira-entrevista-emprego",
                    "views": 245,
                    "likes": 31,
                    "gallery": ["https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=800", "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=800"],
                    "toc": ["1. Introdução", "2. Preparação Prévia", "3. Durante a Conversa", "4. Pós-Entrevista"]
                },
                {
                    "title": "Diversidade e Inclusão no Ambiente Corporativo",
                    "category": "RH & Tendências",
                    "summary": "Por que as empresas estão investindo mais em inclusão e qual o impacto real disso nos resultados.",
                    "content": "Equipes com diversidade de origens, gêneros e pensamentos são comprovadamente 30% mais inovadoras. O RH de 2026 foca em criar processos seletivos mais justos e ambientes de trabalho acolhedores.\n\nA triagem cega e a inteligência artificial sem vieses subjetivos ajudam a promover um mercado corporativo muito mais democrático e inclusivo.",
                    "image_url": "https://images.unsplash.com/photo-1531538606174-0f90ff5dce83?w=800",
                    "slug": "diversidade-inclusao-corporativa-2026",
                    "views": 189,
                    "likes": 29,
                    "gallery": ["https://images.unsplash.com/photo-1531538606174-0f90ff5dce83?w=800", "https://images.unsplash.com/photo-1515187029135-18ee286d815b?w=800"],
                    "toc": ["1. O Cenário Atual", "2. Vantagens Competitivas", "3. Como o VagaSync Ajuda"]
                },
                {
                    "title": "Como Fazer uma Transição de Carreira de Sucesso",
                    "category": "Desenvolvimento Profissional",
                    "summary": "Passos práticos para mudar de profissão sem perder o histórico profissional acumulado.",
                    "content": "Mudar de carreira exige planejamento e resiliência. Mapeie suas soft skills transferíveis, como liderança, organização e comunicação. Em seguida, estude as novas habilidades técnicas e faça pequenos projetos de portfólio para provar sua competência.\n\nO segredo é contar uma boa história aos recrutadores: explique como seu background anterior enriquece sua atuação na nova profissão.",
                    "image_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800",
                    "slug": "transicao-carreira-sucesso-dicas",
                    "views": 372,
                    "likes": 51,
                    "gallery": ["https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=800", "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800"],
                    "toc": ["1. Por Onde Começar?", "2. Mapeamento de Skills", "3. Networking e Portfólio"]
                },
                {
                    "title": "O Boom do Trabalho Híbrido nas Capitais",
                    "category": "Notícias do Mercado",
                    "summary": "Pesquisa revela que mais de 70% das vagas tech preferem regime híbrido ou remoto.",
                    "content": "Uma pesquisa recente mostra que o regime híbrido (2 a 3 vezes por semana no escritório) consolidou-se como o favorito de profissionais e gestores de tecnologia.\n\nFlexibilidade geográfica e qualidade de vida são os grandes atrativos que as empresas usam para recrutar e reter talentos altamente qualificados.",
                    "image_url": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800",
                    "slug": "boom-trabalho-hibrido-capitais-2026",
                    "views": 435,
                    "likes": 64,
                    "gallery": ["https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800", "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800"],
                    "toc": ["1. Pesquisa Recente", "2. Preferência Nacional", "3. Conclusão"]
                },
                {
                    "title": "De Estagiário a Diretor de Tecnologia",
                    "category": "Histórias de Sucesso",
                    "summary": "Conheça a trajetória inspiradora de Lucas Costa e as lições que ele aprendeu no caminho.",
                    "content": "Lucas começou no suporte técnico e hoje lidera uma equipe de 40 desenvolvedores. Seu segredo foi sempre buscar resolver problemas difíceis que ninguém queria assumir.\n\n'Habilidade técnica qualquer um aprende na internet, mas iniciativa e espírito de dono são raros', diz Lucas em sua entrevista exclusiva.",
                    "image_url": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=800",
                    "slug": "de-estagiario-a-diretor-tecnologia-trajetoria",
                    "views": 512,
                    "likes": 88,
                    "gallery": ["https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=800", "https://images.unsplash.com/photo-1552664730-d307ca884978?w=800"],
                    "toc": ["1. O Início", "2. As Promoções", "3. Dicas de Liderança"]
                },
                {
                    "title": "Resiliência: O Segredo para não Desistir da Busca",
                    "category": "Conteúdo Motivacional",
                    "summary": "Dicas de como lidar com a rejeição e se manter focado no objetivo de sua recolocação.",
                    "content": "Receber um 'não' faz parte de qualquer jornada profissional. O importante é transformar a rejeição em aprendizado. Peça feedback, ajuste seu currículo e continue aprimorando seu conhecimento.\n\nA persistência aliada a ferramentas de automação como o VagaSync economiza sua energia mental e acelera seus resultados.",
                    "image_url": "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800",
                    "slug": "resiliencia-segredo-recolocacao-profissional",
                    "views": 218,
                    "likes": 44,
                    "gallery": ["https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800", "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=1200"],
                    "toc": ["1. Lidar com o 'Não'", "2. Foco e Automação", "3. Conclusão"]
                },
                {
                    "title": "Erros no Currículo que te Eliminam da Seleção",
                    "category": "Dicas de Currículo",
                    "summary": "Descubra quais detalhes podem arruinar suas chances antes mesmo da entrevista.",
                    "content": "Erros ortográficos, falta de contatos atualizados e mentiras sobre experiências anteriores são os três maiores motivos para exclusão instantânea de candidatos.\n\nRevise seu currículo pelo menos três vezes e peça para um amigo ou IA ler e analisar a coerência das datas e atividades descritas.",
                    "image_url": "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=800",
                    "slug": "erros-curriculo-eliminam-selecao",
                    "views": 612,
                    "likes": 102,
                    "gallery": ["https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=800", "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=800"],
                    "toc": ["1. Erros Clássicos", "2. Como Revisar", "3. Checklist Final"]
                },
                {
                    "title": "Vagas em Destaque: As Maiores Empresas Contratando",
                    "category": "Vagas em Destaque",
                    "summary": "Confira a lista de corporações que estão contratando em regime híbrido e remoto nesta semana.",
                    "content": "Gigantes do setor financeiro, e-commerce e consultoria abriram novos hubs de tecnologia e têm centenas de vagas ativas no VagaSync.\n\nAproveite para atualizar seu perfil e habilitar a busca automática da IA do VagaSync para se candidatar em menos de 24 horas.",
                    "image_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800",
                    "slug": "vagas-destaque-empresas-contratando",
                    "views": 844,
                    "likes": 132,
                    "gallery": ["https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800", "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800"],
                    "toc": ["1. Principais Setores", "2. Como se Candidatar", "3. Lista de Empresas"]
                },
                {
                    "title": "Como Otimizar seu Perfil do LinkedIn",
                    "category": "Desenvolvimento Profissional",
                    "summary": "Dicas essenciais de SEO para aparecer nas buscas de recrutadores da rede social.",
                    "content": "O segredo do LinkedIn está em usar as palavras-chave certas no seu título profissional e resumo. Em vez de 'Em busca de oportunidades', coloque 'Desenvolvedor React | Node.js | TypeScript'.\n\nIsso melhora o rankeamento do seu perfil nas pesquisas internas feitas por headhunters e robôs de triagem.",
                    "image_url": "https://images.unsplash.com/photo-1616469829581-73993eb86b02?w=800",
                    "slug": "como-otimizar-perfil-linkedin-seo",
                    "views": 491,
                    "likes": 76,
                    "gallery": ["https://images.unsplash.com/photo-1616469829581-73993eb86b02?w=800", "https://images.unsplash.com/photo-1586281380349-632531db7ed4?w=800"],
                    "toc": ["1. O Segredo das Keywords", "2. O Título Ideal", "3. Resumo Atrativo"]
                },
                {
                    "title": "A Importância do Networking Genuíno",
                    "category": "Conteúdo Motivacional",
                    "summary": "Como fazer conexões reais que ajudam na sua carreira sem parecer interesseiro.",
                    "content": "Networking de verdade não é sobre pedir emprego para desconhecidos, mas sim sobre trocar conhecimento e ajudar outras pessoas do seu setor.\n\nParticipe de fóruns, interaja com posts interessantes e ofereça soluções para problemas antes de pedir favores de contratação.",
                    "image_url": "https://images.unsplash.com/photo-1515187029135-18ee286d815b?w=800",
                    "slug": "importancia-networking-genuino-carreira",
                    "views": 273,
                    "likes": 49,
                    "gallery": ["https://images.unsplash.com/photo-1515187029135-18ee286d815b?w=800", "https://images.unsplash.com/photo-1531538606174-0f90ff5dce83?w=800"],
                    "toc": ["1. Conexões Reais", "2. Como Agir online", "3. Eventos da Área"]
                },
                {
                    "title": "Modelos de Currículo Recomendados por Especialistas",
                    "category": "Dicas de Currículo",
                    "summary": "Confira opções de formatação recomendadas por nossa IA para triagem rápida.",
                    "content": "Modelos extravagantes e coloridos chamam a atenção mas costumam falhar nos filtros de recrutamento por IA.\n\nUse fontes limpas (Arial, Calibri), seções claras em ordem cronológica reversa e salve sempre em formato PDF padrão para garantir a leitura correta.",
                    "image_url": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800",
                    "slug": "modelos-curriculo-recomendados-ia",
                    "views": 488,
                    "likes": 69,
                    "gallery": ["https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=800", "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=800"],
                    "toc": ["1. Layout Ideal", "2. Fontes e Estrutura", "3. Formato do Arquivo"]
                },
                {
                    "title": "Inteligência Emocional: O Diferencial Decisivo",
                    "category": "RH & Tendências",
                    "summary": "Por que soft skills se tornaram o fator decisivo para a seleção final em grandes empresas.",
                    "content": "No mundo tech de hoje, a inteligência emocional é o diferencial competitivo. Saber ouvir, gerenciar o estresse das entregas e colaborar sob pressão é o que define a contratação de lideranças.\n\nAs empresas buscam profissionais empáticos, adaptáveis e com fortes habilidades sociais para integrar e unir equipes.",
                    "image_url": "https://images.unsplash.com/photo-1552664730-d307ca884978?w=800",
                    "slug": "inteligencia-emocional-diferencial-decisivo-rh",
                    "views": 395,
                    "likes": 58,
                    "gallery": ["https://images.unsplash.com/photo-1552664730-d307ca884978?w=800", "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=800"],
                    "toc": ["1. A Importância da IE", "2. As Habilidades mais Buscadas", "3. Como Desenvolver"]
                }
            ]
            for p in posts:
                db.execute(text("""
                    INSERT INTO blog_posts (title, category, summary, content, image_url, slug, views, likes, comments_count, gallery_images, table_of_contents, published_at)
                    VALUES (:title, :category, :summary, :content, :image_url, :slug, :views, :likes, 0, :gallery, :toc, :published_at)
                """), {
                    "title": p["title"],
                    "category": p["category"],
                    "summary": p["summary"],
                    "content": p["content"],
                    "image_url": p["image_url"],
                    "slug": p["slug"],
                    "views": p["views"],
                    "likes": p["likes"],
                    "gallery": json.dumps(p["gallery"]),
                    "toc": json.dumps(p["toc"]),
                    "published_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                })
            db.commit()
            
        # Seeding podcasts
        cursor = db.execute(text("SELECT COUNT(*) FROM podcasts"))
        count_pod = cursor.fetchone()[0]
        if count_pod == 0:
            podcasts = [
                {
                    "title": "Como conseguir emprego mais rápido em 2026",
                    "description": "Neste episódio inaugural, discutimos como as novas plataformas e a inteligência artificial mudaram a velocidade do processo seletivo e o que você deve fazer para se recolocar em tempo recorde.",
                    "thumbnail_url": "https://images.unsplash.com/photo-1590602847861-f357a9332bbc?w=600",
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                    "duration": "24 min",
                    "category": "Carreira",
                    "is_featured": True
                },
                {
                    "title": "IA procurando vagas por você: Mito ou realidade?",
                    "description": "Entenda os bastidores técnicos dos robôs de candidatura automática e como o VagaSync ajuda candidatos a automatizarem tarefas burocráticas.",
                    "thumbnail_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600",
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
                    "duration": "18 min",
                    "category": "Tecnologia",
                    "is_featured": False
                },
                {
                    "title": "Erros clássicos no currículo que você precisa evitar",
                    "description": "Mapeamos os maiores desastres em currículos e perfis do LinkedIn que fazem os recrutadores descartarem candidatos em menos de 5 segundos.",
                    "thumbnail_url": "https://images.unsplash.com/photo-1506784983877-45594efa4cbe?w=600",
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
                    "duration": "15 min",
                    "category": "Currículo",
                    "is_featured": False
                },
                {
                    "title": "Como impressionar recrutadores em entrevistas por vídeo",
                    "description": "Dicas comportamentais e técnicas para arrasar em entrevistas síncronas e assíncronas do VagaSync e outras ferramentas.",
                    "thumbnail_url": "https://images.unsplash.com/photo-1573497019940-1c28c88b4f3e?w=600",
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
                    "duration": "22 min",
                    "category": "Entrevistas",
                    "is_featured": False
                },
                {
                    "title": "LinkedIn otimizado: O segredo do algoritmo revelado",
                    "description": "Explicamos técnicas de SEO aplicadas ao seu perfil profissional do LinkedIn para que você apareça no topo das buscas dos headhunters.",
                    "thumbnail_url": "https://images.unsplash.com/photo-1616469829581-73993eb86b02?w=600",
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
                    "duration": "28 min",
                    "category": "Carreira",
                    "is_featured": False
                },
                {
                    "title": "Sua primeira entrevista de tecnologia: O que esperar",
                    "description": "Desmistificamos o teste de lógica e a primeira conversa técnica para desenvolvedores e analistas de tecnologia.",
                    "thumbnail_url": "https://images.unsplash.com/photo-1542744094-3a31f103e35f?w=600",
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
                    "duration": "31 min",
                    "category": "Entrevistas",
                    "is_featured": False
                },
                {
                    "title": "Empregabilidade e o Cenário Tech em 2026",
                    "category": "Carreira",
                    "description": "Uma análise profunda sobre o estado atual do mercado tech, layoffs, trabalho híbrido e vagas ativas no país.",
                    "thumbnail_url": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=600",
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
                    "duration": "25 min",
                    "is_featured": False
                },
                {
                    "title": "Profissões do futuro: Onde focar sua capacitação",
                    "category": "Tecnologia",
                    "description": "Debatemos sobre Engenharia de IA, Analista de Cibersegurança e as novas oportunidades que a revolução dos dados traz.",
                    "thumbnail_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600",
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
                    "duration": "20 min",
                    "is_featured": False
                },
                {
                    "title": "Salários em alta no mercado corporativo",
                    "category": "Carreira",
                    "description": "Quais setores pagam melhor hoje e como negociar sua pretensão salarial de forma profissional nas etapas finais.",
                    "thumbnail_url": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=600",
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
                    "duration": "19 min",
                    "is_featured": False
                },
                {
                    "title": "Transição de Carreira bem-sucedida aos 30 ou 40",
                    "category": "Carreira",
                    "description": "Conversamos com profissionais que mudaram de setor mais tarde na vida e alcançaram estabilidade e realização.",
                    "thumbnail_url": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600",
                    "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
                    "duration": "26 min",
                    "is_featured": False
                }
            ]
            for p in podcasts:
                db.execute(text("""
                    INSERT INTO podcasts (title, description, thumbnail_url, audio_url, duration, category, views, is_featured, created_at)
                    VALUES (:title, :description, :thumbnail_url, :audio_url, :duration, :category, 0, :is_featured, :created_at)
                """), {
                    "title": p["title"],
                    "description": p["description"],
                    "thumbnail_url": p["thumbnail_url"],
                    "audio_url": p["audio_url"],
                    "duration": p["duration"],
                    "category": p["category"],
                    "is_featured": 1 if p["is_featured"] else 0,
                    "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
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
