"""
notifier.py — Sistema de Notificações Multi-Canal para o Vaga Sync
=================================================================
Fallback hierárquico:
  1. n8n Webhook (se URL configurada)
  2. Telegram Bot (se token + chat_id configurados)
  3. E-mail SMTP (Gmail/Outlook, se smtp_email + smtp_password configurados)
  4. Webhook Genérico (Slack, Discord, Zapier, Make.com, qualquer URL)
  5. Registro interno (log no banco de dados — sempre acontece)
"""

import asyncio
import smtplib
import ssl
import json
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session

from database import SessionLocal, Config, add_log


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def get_cfg(db: Session, key: str) -> str:
    """Retorna o valor de uma chave de configuração ou string vazia (suporta encriptação)."""
    row = db.query(Config).filter(Config.key == key).first()
    if row and row.value:
        return row.value.strip()
    enc_row = db.query(Config).filter(Config.key == f"enc_{key}").first()
    if enc_row and enc_row.value:
        import security
        decrypted = security.decrypt_data(enc_row.value)
        return decrypted.strip() if decrypted else ""
    return ""


def build_job_payload(event_type: str, job) -> dict:
    """Monta o payload JSON padrão enviado em todos os canais."""
    return {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "job": {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "link": job.link,
            "match_score": job.match_score,
            "status": job.status,
            "recruiter_name": job.recruiter_name,
            "recruiter_contact": job.recruiter_contact,
            "applied_at": job.applied_at.isoformat() if job.applied_at else None,
        }
    }


EVENT_LABELS = {
    "job_applied":      "✅ Candidatura Enviada",
    "recruiter_contact": "📞 Recrutador Entrou em Contato!",
    "followup_sent":    "📨 Follow-up de RH Agendado",
    "candidate_applied": "👥 Novo Candidato Inscrito!",
    "job_published":     "📣 Sua Vaga foi Publicada!"
}


def format_message(event_type: str, job) -> str:
    """Texto humanizado da notificação."""
    label = EVENT_LABELS.get(event_type, event_type)
    lines = [
        f"🔔 *Vaga Sync* — {label}",
        f"",
        f"🏢 Empresa: {job.company}",
        f"💼 Vaga:    {job.title}",
        f"📍 Local:   {job.location or 'Remoto'}",
        f"🎯 Match:   {job.match_score or 0}%",
    ]
    if job.recruiter_name:
        lines.append(f"👤 Recrutador: {job.recruiter_name}")
    if job.link:
        lines.append(f"🔗 Link: {job.link}")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Canal 1 — n8n Webhook
# ─────────────────────────────────────────────

def _send_n8n(url: str, payload: dict) -> bool:
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code in (200, 201)
    except Exception:
        return False


# ─────────────────────────────────────────────
# Canal 2 — Telegram Bot
# ─────────────────────────────────────────────

def _send_telegram(token: str, chat_id: str, text: str) -> bool:
    """
    Envia mensagem via Telegram Bot API.
    Obtenha o token em @BotFather e o chat_id mandando /start para seu bot
    e acessando: https://api.telegram.org/bot<TOKEN>/getUpdates
    """
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────
# Canal 3 — E-mail SMTP
# ─────────────────────────────────────────────

def _send_email(smtp_host: str, smtp_port: int, smtp_user: str,
                smtp_password: str, to_email: str, subject: str, body: str) -> bool:
    """
    Envia e-mail via SMTP com SSL.
    Gmail: host=smtp.gmail.com, port=465
    Outlook: host=smtp-mail.outlook.com, port=587 (use _send_email_tls)
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email

        # Corpo em texto simples
        plain_body = body.replace("*", "").replace("_", "")
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))

        # Corpo em HTML
        html_body = body.replace("\n", "<br>").replace("*", "<b>").replace("_", "<i>")
        msg.attach(MIMEText(f"<html><body>{html_body}</body></html>", "html", "utf-8"))

        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=ctx) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return True
    except Exception:
        return False


def _send_email_tls(smtp_host: str, smtp_port: int, smtp_user: str,
                    smtp_password: str, to_email: str, subject: str, body: str) -> bool:
    """Versão TLS para Outlook/Office365."""
    try:
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg.attach(MIMEText(body.replace("*", ""), "plain", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# Canal 4 — Webhook Genérico (Slack, Discord, Zapier, Make…)
# ─────────────────────────────────────────────

def _send_generic_webhook(url: str, text: str, payload: dict) -> bool:
    """
    Tenta enviar como:
    - Slack/Discord (campo "text" ou "content")
    - Zapier/Make (payload completo)
    """
    try:
        # Slack / Discord formato
        if "slack" in url or "discord" in url:
            body = {"content": text} if "discord" in url else {"text": text}
        else:
            body = {"text": text, **payload}
        r = requests.post(url, json=body, timeout=10)
        return r.status_code in (200, 201, 204)
    except Exception:
        return False


# ─────────────────────────────────────────────
# Canal 5 — WhatsApp (CallMeBot)
# ─────────────────────────────────────────────

def _send_whatsapp(phone: str, apikey: str, text: str) -> bool:
    """Envia notificação via WhatsApp usando a API gratuita do CallMeBot."""
    try:
        import urllib.parse
        encoded_text = urllib.parse.quote(text)
        # Remove caracteres indesejados do telefone (ex: + ou espaços)
        clean_phone = "".join(filter(str.isdigit, phone))
        if clean_phone and not clean_phone.startswith("+"):
            clean_phone = "+" + clean_phone
        url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={encoded_text}&apikey={apikey}"
        r = requests.get(url, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────
# Orquestrador Principal
# ─────────────────────────────────────────────

async def dispatch_notification(event_type: str, job, db: Session) -> dict:
    """
    Tenta enviar a notificação por todos os canais configurados em ordem.
    Retorna um dict com o resultado de cada canal.
    """
    results = {}
    payload = build_job_payload(event_type, job)
    text = format_message(event_type, job)
    subject = EVENT_LABELS.get(event_type, "Vaga Sync") + f" — {job.title} @ {job.company}"

    loop = asyncio.get_event_loop()

    # ── Canal 0: WhatsApp (CallMeBot) ──
    wa_phone = get_cfg(db, "whatsapp_phone")
    if event_type in ("candidate_applied", "job_published") and job.recruiter_phone:
        wa_phone = job.recruiter_phone
    wa_apikey = get_cfg(db, "whatsapp_webhook")
    if wa_phone and wa_apikey:
        ok = await loop.run_in_executor(None, _send_whatsapp, wa_phone, wa_apikey, text)
        results["whatsapp"] = "✅ enviado" if ok else "❌ falhou"
        add_log("success" if ok else "warning",
                f"[Notif WhatsApp] {results['whatsapp']} — evento: {event_type}")

    # ── Canal 1: n8n ──
    n8n_url = get_cfg(db, "n8n_webhook_url")
    if n8n_url and len(n8n_url) > 10:
        ok = await loop.run_in_executor(None, _send_n8n, n8n_url, payload)
        results["n8n"] = "✅ enviado" if ok else "❌ falhou"
        add_log("success" if ok else "warning",
                f"[Notif n8n] {results['n8n']} — evento: {event_type}")

    # ── Canal 2: Telegram ──
    tg_token = get_cfg(db, "telegram_token")
    tg_chat   = get_cfg(db, "telegram_chat_id")
    if tg_token and tg_chat:
        ok = await loop.run_in_executor(None, _send_telegram, tg_token, tg_chat, text)
        results["telegram"] = "✅ enviado" if ok else "❌ falhou"
        add_log("success" if ok else "warning",
                f"[Notif Telegram] {results['telegram']} — evento: {event_type}")

    # ── Canal 3: E-mail ──
    smtp_user  = get_cfg(db, "smtp_email")
    smtp_pass  = get_cfg(db, "smtp_password")
    smtp_to    = get_cfg(db, "notify_email") or smtp_user
    if event_type in ("candidate_applied", "job_published") and job.recruiter_contact:
        smtp_to = job.recruiter_contact
    smtp_host  = get_cfg(db, "smtp_host") or "smtp.gmail.com"
    smtp_port  = int(get_cfg(db, "smtp_port") or "465")

    if smtp_user and smtp_pass:
        if smtp_port == 587:
            ok = await loop.run_in_executor(
                None, _send_email_tls,
                smtp_host, smtp_port, smtp_user, smtp_pass, smtp_to, subject, text
            )
        else:
            ok = await loop.run_in_executor(
                None, _send_email,
                smtp_host, smtp_port, smtp_user, smtp_pass, smtp_to, subject, text
            )
        results["email"] = "✅ enviado" if ok else "❌ falhou"
        add_log("success" if ok else "warning",
                f"[Notif Email] {results['email']} — para: {smtp_to}")

    # ── Canal 4: Webhook Genérico ──
    generic_url = get_cfg(db, "generic_webhook_url")
    if generic_url and len(generic_url) > 10:
        ok = await loop.run_in_executor(None, _send_generic_webhook, generic_url, text, payload)
        results["generic_webhook"] = "✅ enviado" if ok else "❌ falhou"
        add_log("success" if ok else "warning",
                f"[Notif Webhook] {results['generic_webhook']} — url: {generic_url[:40]}...")

    # ── Sem canal configurado ──
    if not results:
        add_log("info", f"[Notif] Evento '{event_type}' registrado internamente (nenhum canal externo configurado).")
        results["interno"] = "✅ registrado no banco"

    return results


# ─────────────────────────────────────────────
# Endpoint de teste de conectividade
# ─────────────────────────────────────────────

async def test_all_channels(db: Session) -> dict:
    """Verifica quais canais estão configurados (sem enviar mensagem real)."""
    status = {}

    status["whatsapp"]        = "✅ configurado" if (get_cfg(db, "whatsapp_phone") and get_cfg(db, "whatsapp_webhook")) else "⬜ não configurado"
    status["n8n"]             = "✅ configurado" if get_cfg(db, "n8n_webhook_url") else "⬜ não configurado"
    status["telegram"]        = "✅ configurado" if (get_cfg(db, "telegram_token") and get_cfg(db, "telegram_chat_id")) else "⬜ não configurado"
    status["email"]           = "✅ configurado" if (get_cfg(db, "smtp_email") and get_cfg(db, "smtp_password")) else "⬜ não configurado"
    status["generic_webhook"] = "✅ configurado" if get_cfg(db, "generic_webhook_url") else "⬜ não configurado"

    return status
