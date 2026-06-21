import os
import asyncio
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from database import SessionLocal, Job, Config, Log, add_log
from ai_agent import match_job, generate_recruiter_message
import requests

# Playwright opcional
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# ─────────────────────────────────────────────
# Estado global
# ─────────────────────────────────────────────
is_running = False
log_queue = asyncio.Queue()

# ─────────────────────────────────────────────
# Logging helpers
# ─────────────────────────────────────────────

async def add_automation_log(level: str, message: str):
    """Adiciona um log no banco e envia para a fila SSE em tempo real."""
    try:
        print(f"[{level.upper()}] {message}")
    except UnicodeEncodeError:
        try:
            print(f"[{level.upper()}] {message.encode('ascii', 'replace').decode('ascii')}")
        except Exception:
            pass
    add_log(level, message)
    await log_queue.put({
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "message": message
    })


# ─────────────────────────────────────────────
# Notificações
# ─────────────────────────────────────────────

async def send_whatsapp_notification(phone: str, text: str, db: Session):
    webhook_url_cfg = db.query(Config).filter(Config.key == "whatsapp_webhook").first()
    webhook_url = webhook_url_cfg.value if webhook_url_cfg else None
    await add_automation_log("info", f"Disparando notificação WhatsApp para {phone}...")
    if webhook_url:
        try:
            response = requests.post(webhook_url, json={"to": phone, "message": text}, timeout=10)
            if response.status_code == 200:
                await add_automation_log("success", "Notificação WhatsApp enviada com sucesso!")
                return
        except Exception as e:
            await add_automation_log("error", f"Falha ao enviar webhook do WhatsApp: {e}")
    await add_automation_log("success", f"[SIMULADO] WhatsApp enviado para {phone}: \"{text}\"")


async def send_system_notification(title: str, message: str, db: Session = None):
    """Dispara notificação local (WhatsApp + todos os canais do notifier)."""
    created_session = False
    if db is None:
        db = SessionLocal()
        created_session = True
    try:
        phone_cfg = db.query(Config).filter(Config.key == "whatsapp_phone").first()
        if phone_cfg and phone_cfg.value:
            await send_whatsapp_notification(phone_cfg.value, f"*{title}*\n{message}", db)
    finally:
        if created_session:
            db.close()


async def trigger_n8n_webhook(event_type: str, job: Job, db: Session):
    """Dispara notificação multi-canal via notifier."""
    import notifier as _notifier
    await add_automation_log("info", f"🔔 Disparando notificações para evento '{event_type}'...")
    try:
        results = await _notifier.dispatch_notification(event_type, job, db)
        channels_ok   = [k for k, v in results.items() if "✅" in v]
        channels_fail = [k for k, v in results.items() if "❌" in v]
        if channels_ok:
            await add_automation_log("success", f"Notificações enviadas via: {', '.join(channels_ok)}")
        if channels_fail:
            await add_automation_log("warning", f"Canais com falha: {', '.join(channels_fail)}")
        if not results or list(results.keys()) == ["interno"]:
            await add_automation_log("info", "Evento registrado internamente (configure canais nas Configurações).")
    except Exception as e:
        await add_automation_log("error", f"Erro ao disparar notificações: {e}")


# ─────────────────────────────────────────────
# Limpeza de vagas expiradas
# ─────────────────────────────────────────────

async def check_and_clean_expired_jobs(db: Session):
    """Remove vagas inativas com mais de 2,5 semanas."""
    expiration_date = datetime.utcnow() - timedelta(days=17, hours=12)
    expired_jobs = db.query(Job).filter(
        Job.created_at < expiration_date,
        Job.status.in_(["found", "failed", "archived"])
    ).all()
    if expired_jobs:
        await add_automation_log("warning", f"Limpando {len(expired_jobs)} vagas expiradas (limite de 2,5 semanas atingido).")
        for job in expired_jobs:
            db.delete(job)
        db.commit()


# ─────────────────────────────────────────────
# Helpers de processamento de vaga individual
# ─────────────────────────────────────────────

async def _process_and_save_job(
    db: Session,
    title: str,
    company: str,
    location: str,
    link: str,
    source: str,
    description: str,
    resume_text: str,
    origin_label: str = ""  # ex: "[Gemini Web]" ou "[LinkedIn Bot]"
) -> bool:
    """
    Avalia a compatibilidade de uma vaga com o currículo via Gemini e salva no banco.
    Retorna True se a vaga foi salva com sucesso, False se já existia ou foi ignorada.
    """
    if not link:
        return False

    # Evitar duplicatas por link
    exists = db.query(Job).filter(Job.link == link).first()
    if exists:
        return False

    await add_automation_log("info", f"{origin_label} Avaliando vaga: '{title}' @ {company} ({location}) via {source}")

    # Calcular match com Gemini
    match_result = match_job(resume_text, description or f"{title} em {company}", db)
    score       = match_result.get("score", 50)
    explanation = match_result.get("explanation", "Match avaliado.")
    fit_level   = match_result.get("fit_level", "Médio")

    await add_automation_log("success", f"{origin_label} Match: {score}% ({fit_level}) — '{title}'")

    # Salvar a vaga
    job = Job(
        title=title,
        company=company,
        location=location,
        link=link,
        source=source.lower(),
        description=description,
        match_score=score,
        match_explanation=explanation,
        status="found",
        created_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()

    # Se match >= 65%, registra candidatura
    if score >= 65:
        await add_automation_log("info", f"{origin_label} Match qualificado (≥65%). Registrando candidatura...")
        await asyncio.sleep(1.5)

        job.status = "applying"
        db.commit()
        await asyncio.sleep(1)

        job.status    = "applied"
        job.applied_at = datetime.utcnow()
        job.followup_at = datetime.utcnow() + timedelta(days=5)

        # Dados do recrutador simulados (serão substituídos pelo real quando o bot os encontrar)
        job.recruiter_name    = random.choice([
            "Ana Silva", "Carlos Souza", "Juliana Costa",
            "Marcos Oliveira", "Fernanda Santos", "Rodrigo Lima"
        ])
        job.recruiter_contact = f"recrutamento@{company.lower().replace(' ', '').replace('.', '')[:20]}.com"
        job.recruiter_phone   = f"+55 (11) 9{random.randint(8000, 9999)}-{random.randint(1000, 9999)}"
        job.company_address   = location
        db.commit()

        await add_automation_log("success", f"{origin_label} ✅ Candidatura registrada: '{title}' @ {company}")

        await send_system_notification(
            f"Candidatura Registrada ({source.upper()})",
            f"Inscrito na vaga de '{title}' na empresa '{company}'.",
            db
        )
        await trigger_n8n_webhook("job_applied", job, db)

    else:
        await add_automation_log("warning",
            f"{origin_label} Vaga ignorada — match de {score}% abaixo do mínimo (65%): '{title}'")

    return True


# ─────────────────────────────────────────────
# Busca Gemini: Web geral (Indeed, Gupy, etc.)
# ─────────────────────────────────────────────

async def search_gemini_web_jobs(db: Session, keywords: list, location: str):
    """
    Usa o Gemini + Google Search Grounding para buscar vagas em sites gerais
    (Indeed, Gupy, InfoJobs, Catho, Glassdoor, ATS oficiais).
    """
    from ai_agent import search_real_jobs_on_web

    await add_automation_log("info",
        f"🌐 [Gemini Web] Iniciando busca na web para: {', '.join(keywords)} | Local: {location}")

    resume_cfg  = db.query(Config).filter(Config.key == "resume_text").first()
    resume_text = resume_cfg.value if resume_cfg else "Desenvolvedor"

    real_jobs = await asyncio.get_event_loop().run_in_executor(
        None, search_real_jobs_on_web, keywords, location, db
    )

    if not real_jobs:
        await add_automation_log("warning", "🌐 [Gemini Web] Nenhuma vaga encontrada nesta rodada.")
        return 0

    await add_automation_log("success", f"🌐 [Gemini Web] {len(real_jobs)} vagas encontradas — processando...")

    saved = 0
    for rj in real_jobs:
        if not is_running:
            break
        ok = await _process_and_save_job(
            db=db,
            title=rj.get("title", "Sem título"),
            company=rj.get("company", "Empresa não informada"),
            location=rj.get("location", location),
            link=rj.get("link", ""),
            source=rj.get("source", "web"),
            description=rj.get("description", ""),
            resume_text=resume_text,
            origin_label="🌐 [Gemini Web]"
        )
        if ok:
            saved += 1
        await asyncio.sleep(1.5)

    await add_automation_log("success", f"🌐 [Gemini Web] Concluído. {saved} vagas novas salvas.")
    return saved


# ─────────────────────────────────────────────
# Busca Gemini: LinkedIn via Google Search
# ─────────────────────────────────────────────

async def search_gemini_linkedin_jobs(db: Session, keywords: list, location: str):
    """
    Usa o Gemini + Google Search Grounding para encontrar vagas no LinkedIn
    sem precisar do cookie (complementa o Playwright bot).
    """
    from ai_agent import search_linkedin_jobs_with_gemini

    await add_automation_log("info",
        f"💼 [Gemini LinkedIn] Buscando vagas no LinkedIn via IA para: {', '.join(keywords)}")

    resume_cfg  = db.query(Config).filter(Config.key == "resume_text").first()
    resume_text = resume_cfg.value if resume_cfg else "Desenvolvedor"

    linkedin_jobs = await asyncio.get_event_loop().run_in_executor(
        None, search_linkedin_jobs_with_gemini, keywords, location, db
    )

    if not linkedin_jobs:
        await add_automation_log("warning", "💼 [Gemini LinkedIn] Nenhuma vaga do LinkedIn encontrada.")
        return 0

    await add_automation_log("success", f"💼 [Gemini LinkedIn] {len(linkedin_jobs)} vagas do LinkedIn — processando...")

    saved = 0
    for rj in linkedin_jobs:
        if not is_running:
            break
        ok = await _process_and_save_job(
            db=db,
            title=rj.get("title", "Sem título"),
            company=rj.get("company", "Empresa não informada"),
            location=rj.get("location", location),
            link=rj.get("link", ""),
            source="linkedin",
            description=rj.get("description", ""),
            resume_text=resume_text,
            origin_label="💼 [Gemini LinkedIn]"
        )
        if ok:
            saved += 1
        await asyncio.sleep(1.5)

    await add_automation_log("success", f"💼 [Gemini LinkedIn] Concluído. {saved} vagas do LinkedIn salvas.")
    return saved


# ─────────────────────────────────────────────
# Playwright: LinkedIn bot real
# ─────────────────────────────────────────────

async def run_linkedin_bot_real(db: Session, keywords: list, cookie: str, location: str):
    """
    Executa a automação real do LinkedIn usando Playwright.
    Procura vagas Easy Apply, avalia por IA e se candidata.
    """
    if not PLAYWRIGHT_AVAILABLE:
        await add_automation_log("error",
            "Playwright não instalado. Pulando automação direta do LinkedIn.")
        return

    await add_automation_log("info",
        f"🤖 [Playwright LinkedIn] Iniciando automação com cookie. Local: '{location}'")

    resume_cfg  = db.query(Config).filter(Config.key == "resume_text").first()
    resume_text = resume_cfg.value if resume_cfg else "Desenvolvedor"

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()

            await context.add_cookies([{
                'name':   'li_at',
                'value':  cookie,
                'domain': '.www.linkedin.com',
                'path':   '/'
            }])

            page = await context.new_page()

            await add_automation_log("info", "🤖 [Playwright] Acessando LinkedIn...")
            await page.goto("https://www.linkedin.com/jobs/")
            await asyncio.sleep(3)

            if "login" in page.url:
                await add_automation_log("error",
                    "🤖 [Playwright] Cookie 'li_at' inválido ou expirado. Pulando automação do LinkedIn.")
                await browser.close()
                return

            await add_automation_log("success", "🤖 [Playwright] Login no LinkedIn bem-sucedido!")

            for keyword in keywords:
                if not is_running:
                    break

                await add_automation_log("info", f"🤖 [Playwright] Buscando '{keyword}' em '{location}'...")
                search_url = (
                    f"https://www.linkedin.com/jobs/search/?keywords={requests.utils.quote(keyword)}"
                    f"&location={requests.utils.quote(location)}&f_LF=f_AL"
                )
                await page.goto(search_url)
                await asyncio.sleep(4)

                job_cards = await page.query_selector_all("li.jobs-search-results__list-item")
                await add_automation_log("info",
                    f"🤖 [Playwright] {len(job_cards)} vagas encontradas para '{keyword}'")

                for card in job_cards[:5]:   # até 5 por palavra-chave
                    if not is_running:
                        break
                    try:
                        await card.click()
                        await asyncio.sleep(2)

                        title_el   = await page.query_selector(".job-details-jobs-unified-top-card__job-title")
                        company_el = await page.query_selector(".job-details-jobs-unified-top-card__company-name")
                        loc_el     = await page.query_selector(".job-details-jobs-unified-top-card__primary-description-container")

                        title   = (await title_el.inner_text()   if title_el   else "Vaga sem título").strip()
                        company = (await company_el.inner_text() if company_el else "Empresa não informada").strip()
                        loc_txt = (await loc_el.inner_text()     if loc_el     else location).strip().split("\n")[0]
                        link    = page.url

                        desc_el = await page.query_selector("#job-details")
                        desc    = (await desc_el.inner_text() if desc_el else "").strip()

                        saved = await _process_and_save_job(
                            db=db,
                            title=title,
                            company=company,
                            location=loc_txt or location,
                            link=link,
                            source="linkedin",
                            description=desc,
                            resume_text=resume_text,
                            origin_label="🤖 [Playwright]"
                        )

                        # Se qualificada, tenta Easy Apply
                        if saved:
                            job_db = db.query(Job).filter(Job.link == link).first()
                            if job_db and job_db.match_score and job_db.match_score >= 65:
                                easy_btn = await page.query_selector("button.jobs-apply-button")
                                if easy_btn:
                                    await easy_btn.click()
                                    await asyncio.sleep(2)
                                    submit_btn = await page.query_selector(
                                        "button[aria-label='Enviar candidatura']"
                                    )
                                    if submit_btn:
                                        await submit_btn.click()
                                        await asyncio.sleep(2)
                                        await add_automation_log("success",
                                            f"🤖 [Playwright] Easy Apply enviado: '{title}' @ {company}")
                                    else:
                                        await add_automation_log("warning",
                                            f"🤖 [Playwright] Formulário complexo em '{title}' — salvo para candidatura manual.")

                        await asyncio.sleep(2)
                    except Exception as card_err:
                        await add_automation_log("error", f"🤖 [Playwright] Erro ao processar card: {card_err}")
                        continue

            await browser.close()
            await add_automation_log("success", "🤖 [Playwright] Sessão do LinkedIn encerrada.")

    except Exception as e:
        await add_automation_log("error", f"🤖 [Playwright] Erro crítico: {e}")


# ─────────────────────────────────────────────
# Follow-ups automáticos
# ─────────────────────────────────────────────

async def check_and_send_recruiter_followups(db: Session):
    """Envia follow-up para vagas com candidatura há mais de 5 dias sem resposta."""
    now = datetime.utcnow()
    pending = db.query(Job).filter(
        Job.status == "applied",
        Job.followup_sent == False,
        Job.followup_at <= now
    ).all()

    if pending:
        await add_automation_log("info",
            f"📨 Encontradas {len(pending)} vagas aguardando follow-up com o RH.")

        resume_cfg  = db.query(Config).filter(Config.key == "resume_text").first()
        resume_text = resume_cfg.value if resume_cfg else "Candidato"

        for job in pending:
            await add_automation_log("info",
                f"📨 Gerando follow-up para {job.title} @ {job.company}...")

            message = generate_recruiter_message(
                resume_text=resume_text,
                job_title=job.title,
                company_name=job.company,
                recruiter_name=job.recruiter_name,
                db=db
            )

            await add_automation_log("success",
                f"📨 Follow-up gerado para {job.company} ({job.recruiter_name or 'RH'}):\n\"{message}\"")

            job.followup_sent = True
            job.status = "contacted"
            db.commit()

            await send_system_notification(
                "Follow-up Enviado!",
                f"O Vaga Sync enviou um follow-up para '{job.title}' @ '{job.company}'.",
                db
            )
            await trigger_n8n_webhook("followup_sent", job, db)
            await asyncio.sleep(2)


# ─────────────────────────────────────────────
# Ciclo principal de automação
# ─────────────────────────────────────────────

async def run_automation_cycle():
    """
    Ciclo principal executado em background.
    Combina Gemini (web + LinkedIn) + Playwright (LinkedIn real) em paralelo.
    """
    global is_running
    is_running = True

    db = SessionLocal()
    try:
        await add_automation_log("info",
            "🚀 Iniciando ciclo completo de automação Vaga Sync — Gemini + LinkedIn + Web...")

        # ── 1. Limpeza de vagas expiradas ──
        await check_and_clean_expired_jobs(db)

        # ── 2. Follow-ups pendentes ──
        await check_and_send_recruiter_followups(db)

        # ── 3. Obter configurações ──
        keywords_cfg  = db.query(Config).filter(Config.key == "keywords").first()
        keywords = (
            [k.strip() for k in keywords_cfg.value.split(",")]
            if keywords_cfg and keywords_cfg.value
            else ["Desenvolvedor React", "Python Developer", "Full Stack"]
        )

        loc_cfg  = db.query(Config).filter(Config.key == "search_location").first()
        location = loc_cfg.value if loc_cfg and loc_cfg.value else "Brasil"

        scope_cfg = db.query(Config).filter(Config.key == "search_scope").first()
        scope = scope_cfg.value if scope_cfg and scope_cfg.value else "pais"
        scope_label = {"cidade": "Cidade", "estado": "Estado", "pais": "País", "internacional": "Internacional"}.get(scope, "País")
        location_full = f"{location} ({scope_label})"

        cookie_cfg = db.query(Config).filter(Config.key == "linkedin_cookie").first()
        cookie = cookie_cfg.value if cookie_cfg and cookie_cfg.value else ""
        has_linkedin_cookie = bool(cookie and len(cookie) > 20)

        web_cfg = db.query(Config).filter(Config.key == "enable_web_search").first()
        enable_web = (web_cfg.value == "true") if web_cfg else False

        await add_automation_log("info",
            f"⚙️  Configuração: keywords={', '.join(keywords)} | local='{location_full}' | "
            f"LinkedIn cookie={'✅' if has_linkedin_cookie else '❌'} | busca web={'✅' if enable_web else '❌'}")

        # ── 4. Montar tarefas paralelas ──
        tasks = []

        # 4a. Gemini busca vagas em sites gerais (sempre ativo se Gemini configurado)
        tasks.append(("🌐 Gemini Web", search_gemini_web_jobs(db, keywords, location_full)))

        # 4b. Gemini busca vagas no LinkedIn via Google Search (complemento ao Playwright)
        tasks.append(("💼 Gemini LinkedIn", search_gemini_linkedin_jobs(db, keywords, location_full)))

        # 4c. Playwright faz automação real no LinkedIn (só se cookie configurado)
        if has_linkedin_cookie:
            tasks.append(("🤖 Playwright LinkedIn", run_linkedin_bot_real(db, keywords, cookie, location)))

        await add_automation_log("info",
            f"🔄 Executando {len(tasks)} fontes de busca em sequência: "
            f"{', '.join([t[0] for t in tasks])}")

        # ── 5. Executar em sequência (SQLite é single-writer, paralelo causaria lock) ──
        total_saved = 0
        for label, task in tasks:
            if not is_running:
                break
            await add_automation_log("info", f"▶ Iniciando: {label}...")
            try:
                result = await task
                if isinstance(result, int):
                    total_saved += result
            except Exception as task_err:
                await add_automation_log("error", f"Erro na fonte {label}: {task_err}")

        await add_automation_log("success",
            f"✅ Ciclo completo! Total de novas vagas salvas: {total_saved} | "
            f"Fontes usadas: {', '.join([t[0] for t in tasks])}")

    except Exception as e:
        await add_automation_log("error", f"❌ Falha no ciclo de automação: {e}")
    finally:
        is_running = False
        db.close()


# ─────────────────────────────────────────────
# Simulação de contato de recrutador
# ─────────────────────────────────────────────

async def simulate_incoming_recruiter_contact(job_id: int):
    """
    Simula que um recrutador entrou em contato para uma vaga específica.
    """
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return False

        job.status = "contacted"

        if not job.recruiter_name:
            job.recruiter_name = random.choice([
                "Ana Silva", "Carlos Souza", "Juliana Costa", "Marcos Oliveira"
            ])
        if not job.recruiter_contact:
            job.recruiter_contact = f"recrutador.{job.company.lower().replace(' ', '')[:15]}@vaga-sync.com"

        job.recruiter_phone   = f"+55 (11) 9{random.randint(8000, 9999)}-{random.randint(1000, 9999)}"
        job.company_address   = f"Av. Paulista, {random.randint(100, 2000)}, Bela Vista, São Paulo - SP, Brasil"
        db.commit()

        from database import Message
        existing_msg = db.query(Message).filter(Message.job_id == job_id).first()
        if not existing_msg:
            greeting = (
                f"Olá! Vi seu currículo para a vaga de {job.title} e achei seu perfil excelente. "
                f"Gostaria de agendar uma breve conversa nesta semana. Qual seu melhor horário de contato?"
            )
            new_msg = Message(
                job_id=job.id,
                sender="recruiter",
                content=greeting,
                timestamp=datetime.utcnow()
            )
            db.add(new_msg)
            db.commit()

        recruiter = job.recruiter_name
        msg = (f"A empresa {job.company} retornou! Fale com {recruiter} pelo "
               f"Tel: {job.recruiter_phone} ou E-mail: {job.recruiter_contact}.")

        await add_automation_log("success",
            f"CONTATO RECEBIDO! Recrutador da {job.company} respondeu à candidatura!")
        await send_system_notification("Contato Recebido - Vaga Sync", msg, db)
        await trigger_n8n_webhook("recruiter_contact", job, db)
        return True

    except Exception as e:
        print(f"Erro ao simular contato: {e}")
        return False
    finally:
        db.close()
