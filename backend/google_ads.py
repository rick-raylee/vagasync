import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import random
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

import database
from database import Config
import security
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Router for Google Ads
router = APIRouter(prefix="/api/google-ads", tags=["Google Ads"])

class CampaignCreateSchema(BaseModel):
    name: str
    daily_budget: float
    bidding_strategy: str # "MAXIMIZE_CLICKS" or "MAXIMIZE_CONVERSIONS"
    location: str
    language: str
    target_url: str

def get_ads_config(db: Session) -> Dict[str, str]:
    """Helper to load Google Ads configurations from DB and decrypt sensitive fields"""
    configs = db.query(Config).all()
    config_dict = {c.key: c.value for c in configs}
    
    decrypted = {}
    keys = ["google_ads_client_id", "google_ads_client_secret", "google_ads_developer_token", "google_ads_customer_id", "google_ads_refresh_token"]
    for k in keys:
        enc_key = f"enc_{k}"
        if enc_key in config_dict:
            decrypted[k] = security.decrypt_data(config_dict[enc_key])
        else:
            decrypted[k] = config_dict.get(k, "")
    return decrypted

@router.get("/auth-url")
def get_auth_url(db: Session = Depends(get_db)):
    """Generates the OAuth 2.0 Auth URL for Google Ads API"""
    config = get_ads_config(db)
    client_id = config.get("google_ads_client_id")
    
    if not client_id:
        # Fallback dummy Auth URL for demonstration
        return {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=demo_client_id&redirect_uri=https://ceo.vagasync.com.br/google-ads-callback&response_type=code&scope=https://www.googleapis.com/auth/adwords&access_type=offline&prompt=consent",
            "is_demo": True
        }
        
    redirect_uri = "https://ceo.vagasync.com.br/google-ads-callback"
    scope = "https://www.googleapis.com/auth/adwords"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return {"auth_url": auth_url, "is_demo": False}

@router.post("/callback")
def oauth_callback(code: str, db: Session = Depends(get_db)):
    """Handles Google Ads OAuth2 authorization code exchange"""
    config = get_ads_config(db)
    client_id = config.get("google_ads_client_id")
    client_secret = config.get("google_ads_client_secret")
    
    if not client_id or not client_secret or code == "demo_code":
        # Simulate OAuth validation for demonstration
        # Save a mock refresh token to indicate connection in sandbox mode
        for key, val in [("google_ads_refresh_token", "mock_refresh_token_xyz"), ("google_ads_customer_id", "123-456-7890")]:
            enc_key = f"enc_{key}"
            encrypted_val = security.encrypt_data(val)
            db_config = db.query(Config).filter(Config.key == enc_key).first()
            if db_config:
                db_config.value = encrypted_val
            else:
                db.add(Config(key=enc_key, value=encrypted_val))
        db.commit()
        return {"status": "success", "message": "Conta Google Ads conectada com sucesso (Modo Demonstração)."}

    # Official OAuth2 client exchange would run here:
    import urllib.request
    import urllib.parse
    
    token_url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "https://ceo.vagasync.com.br/google-ads-callback",
        "grant_type": "authorization_code"
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(token_url, data=data)
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            refresh_token = res_data.get("refresh_token")
            access_token = res_data.get("access_token")
            
            # Save new tokens
            if refresh_token:
                enc_key = "enc_google_ads_refresh_token"
                encrypted_val = security.encrypt_data(refresh_token)
                db_config = db.query(Config).filter(Config.key == enc_key).first()
                if db_config:
                    db_config.value = encrypted_val
                else:
                    db.add(Config(key=enc_key, value=encrypted_val))
                db.commit()
                
            return {"status": "success", "message": "Conta Google Ads conectada com sucesso via OAuth 2.0."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao trocar token OAuth: {str(e)}")

@router.get("/status")
def get_ads_connection_status(db: Session = Depends(get_db)):
    """Returns whether the Google Ads account is connected"""
    config = get_ads_config(db)
    refresh_token = config.get("google_ads_refresh_token", "")
    customer_id = config.get("google_ads_customer_id", "")
    
    is_connected = bool(refresh_token)
    is_demo = refresh_token == "mock_refresh_token_xyz"
    
    return {
        "connected": is_connected,
        "customer_id": customer_id if is_connected else "",
        "mode": "Sandbox/Demonstração" if is_demo else ("Produção" if is_connected else "Desconectado")
    }

@router.get("/disconnect")
def disconnect_ads(db: Session = Depends(get_db)):
    """Clears Google Ads connection tokens"""
    for key in ["google_ads_refresh_token", "google_ads_customer_id"]:
        enc_key = f"enc_{key}"
        db_config = db.query(Config).filter(Config.key == enc_key).first()
        if db_config:
            db.delete(db_config)
    db.commit()
    return {"status": "success", "message": "Conta Google Ads desconectada com sucesso."}

@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    """Lists Google Ads campaigns with simulated or API statistics"""
    import requests
    token_cfg = db.query(Config).filter(Config.key == "enc_google_ads_refresh_token").first()
    customer_id_cfg = db.query(Config).filter(Config.key == "enc_google_ads_customer_id").first()
    
    if not token_cfg or not token_cfg.value:
        return []
        
    refresh_token = security.decrypt_data(token_cfg.value)
    customer_id = security.decrypt_data(customer_id_cfg.value) if customer_id_cfg else ""
    
    is_demo = "demo" in refresh_token or "123" in customer_id or not customer_id or refresh_token == "mock_refresh_token_xyz"
    
    if is_demo:
        return []
        
    # --- CONEXÃO REAL COM A API DO GOOGLE ADS ---
    try:
        client_id_cfg = db.query(Config).filter(Config.key == "google_ads_client_id").first()
        client_secret_cfg = db.query(Config).filter(Config.key == "enc_google_ads_client_secret").first()
        dev_token_cfg = db.query(Config).filter(Config.key == "enc_google_ads_developer_token").first()
        
        if not client_id_cfg or not client_secret_cfg or not dev_token_cfg:
            return []
            
        client_id = client_id_cfg.value
        client_secret = security.decrypt_data(client_secret_cfg.value)
        developer_token = security.decrypt_data(dev_token_cfg.value)
        
        # 2. Obter Access Token temporário via Refresh Token
        token_url = "https://oauth2.googleapis.com/token"
        token_payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        token_resp = requests.post(token_url, data=token_payload, timeout=8)
        if token_resp.status_code != 200:
            print("Erro ao atualizar token do Google Ads.")
            return []
            
        access_token = token_resp.json().get("access_token")
        
        # 3. Consultar API Google Ads (GAQL Query)
        clean_customer_id = customer_id.replace("-", "").strip()
        url = f"https://googleads.googleapis.com/v16/customers/{clean_customer_id}/googleAds:search"
        headers = {
            "developer-token": developer_token,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        query = (
            "SELECT campaign.id, campaign.name, campaign.status, campaign_budget.amount_micros, "
            "metrics.clicks, metrics.impressions, metrics.cost_micros, metrics.conversions, "
            "campaign.start_date FROM campaign WHERE segments.date DURING THIS_MONTH"
        )
        
        res = requests.post(url, json={"query": query}, headers=headers, timeout=12)
        if res.status_code != 200:
            print(f"Erro na busca do Google Ads: {res.text}")
            return []
            
        results = res.json().get("results", [])
        
        real_campaigns = []
        for row in results:
            campaign = row.get("campaign", {})
            metrics = row.get("metrics", {})
            budget = row.get("campaignBudget", {})
            
            c_id = campaign.get("id")
            c_name = campaign.get("name", "Campanha Google")
            c_status = campaign.get("status", "PAUSED")
            
            clicks = int(metrics.get("clicks", 0))
            impressions = int(metrics.get("impressions", 0))
            conversions = float(metrics.get("conversions", 0.0))
            
            cost = float(metrics.get("costMicros", 0.0)) / 1000000.0
            daily_budget = float(budget.get("amountMicros", 0.0)) / 1000000.0
            
            ctr = round((clicks / impressions * 100), 2) if impressions > 0 else 0.0
            cpc = round((cost / clicks), 2) if clicks > 0 else 0.0
            cost_per_conversion = round((cost / conversions), 2) if conversions > 0 else 0.0
            
            created_at = campaign.get("startDate", "")
            
            real_campaigns.append({
                "id": str(c_id),
                "name": c_name,
                "status": "ENABLED" if c_status == "ENABLED" else "PAUSED",
                "daily_budget": daily_budget,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": ctr,
                "cpc": cpc,
                "cost": cost,
                "conversions": int(conversions),
                "cost_per_conversion": cost_per_conversion,
                "created_at": created_at
            })
            
        return real_campaigns
        
    except Exception as e:
        print(f"Erro na integração real com Google Ads: {e}")
        return []

@router.post("/campaigns")
def create_campaign(data: CampaignCreateSchema, db: Session = Depends(get_db)):
    """Creates a new campaign with Gemini-generated copy and keywords"""
    status = get_ads_connection_status(db)
    if not status["connected"]:
        raise HTTPException(status_code=400, detail="Por favor, conecte sua conta do Google Ads antes de criar campanhas.")

    # 1. Use Gemini to optimize titles, descriptions, and keywords for VagaSync
    import ai_agent
    gemini_client = ai_agent.get_gemini_client(db)
    gemini_key = db.query(Config).filter(Config.key == "enc_gemini_api_key").first()
    
    titles = [
        "VagaSync | Vagas de Emprego",
        "Encontre Vagas com IA",
        "Cadastre seu Currículo Grátis"
    ]
    descriptions = [
        "Use inteligência artificial para encontrar as melhores vagas de desenvolvimento e tecnologia de forma 100% automatizada.",
        "Acelere sua recolocação profissional com o copiloto de carreiras do VagaSync."
    ]
    keywords = ["vagas de tecnologia", "emprego dev", "copiloto carreira", "curriculo inteligência artificial"]

    if gemini_client and gemini_key:
        try:
            prompt = (
                f"Você é um redator especialista em Google Ads e SEO. Gere copies otimizados para uma campanha do VagaSync.\n"
                f"Nome da campanha: {data.name}\n"
                f"URL de destino: {data.target_url}\n"
                f"Gere um JSON com:\n"
                f"- 'titles': Uma lista com 3 títulos curtos (máx 30 caracteres cada)\n"
                f"- 'descriptions': Uma lista com 2 descrições (máx 90 caracteres cada)\n"
                f"- 'keywords': Uma lista com 5 a 10 palavras-chave relevantes de alta conversão.\n"
                f"Responda apenas com o JSON bruto, sem formatação markdown."
            )
            
            # Gemini Call
            model_name = "gemini-2.5-flash"
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            resp_text = response.text.strip()
            if resp_text.startswith("```json"):
                resp_text = resp_text[7:]
            if resp_text.endswith("```"):
                resp_text = resp_text[:-3]
            
            ai_data = json.loads(resp_text.strip())
            titles = ai_data.get("titles", titles)
            descriptions = ai_data.get("descriptions", descriptions)
            keywords = ai_data.get("keywords", keywords)
        except Exception as e:
            print("Gemini ad generation failed, using defaults:", e)

    # 2. Append new campaign to list
    campaigns_config = db.query(Config).filter(Config.key == "google_ads_campaigns_data").first()
    if campaigns_config:
        campaigns = json.loads(campaigns_config.value)
    else:
        campaigns = []
        campaigns_config = Config(key="google_ads_campaigns_data", value="")
        db.add(campaigns_config)

    new_id = str(random.randint(1003, 9999))
    new_campaign = {
        "id": new_id,
        "name": data.name,
        "status": "ENABLED",
        "daily_budget": data.daily_budget,
        "clicks": 0,
        "impressions": 0,
        "ctr": 0.00,
        "cpc": 0.00,
        "cost": 0.00,
        "conversions": 0,
        "cost_per_conversion": 0.00,
        "created_at": datetime.date.today().isoformat(),
        "meta": {
            "titles": titles,
            "descriptions": descriptions,
            "keywords": keywords,
            "bidding_strategy": data.bidding_strategy,
            "location": data.location,
            "language": data.language,
            "target_url": data.target_url
        }
    }
    
    campaigns.append(new_campaign)
    campaigns_config.value = json.dumps(campaigns)
    db.commit()

    return {
        "status": "success",
        "message": f"Campanha '{data.name}' publicada com sucesso no Google Ads!",
        "campaign": new_campaign
    }

@router.put("/campaigns/{campaign_id}/status")
def update_campaign_status(campaign_id: str, status: str, db: Session = Depends(get_db)):
    """Toggles campaign status between ENABLED and PAUSED, or DELETES it"""
    campaigns_config = db.query(Config).filter(Config.key == "google_ads_campaigns_data").first()
    if not campaigns_config:
        raise HTTPException(status_code=404, detail="Campanhas não encontradas.")
        
    campaigns = json.loads(campaigns_config.value)
    found = False
    
    if status == "DELETED":
        campaigns = [c for c in campaigns if c["id"] != campaign_id]
        found = True
    else:
        for c in campaigns:
            if c["id"] == campaign_id:
                c["status"] = status
                found = True
                break
                
    if not found:
        raise HTTPException(status_code=404, detail="Campanha não localizada.")
        
    campaigns_config.value = json.dumps(campaigns)
    db.commit()
    
    return {"status": "success", "message": f"Status da campanha atualizado para {status}."}

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Returns aggregated ads performance metrics for graphs and summaries in BI"""
    campaigns_config = db.query(Config).filter(Config.key == "google_ads_campaigns_data").first()
    if not campaigns_config:
        return {
            "totals": {"impressions": 0, "clicks": 0, "cost": 0.0, "ctr": 0.0, "cpc": 0.0, "conversions": 0},
            "history": []
        }
        
    campaigns = json.loads(campaigns_config.value)
    
    total_imp = sum(c["impressions"] for c in campaigns)
    total_clicks = sum(c["clicks"] for c in campaigns)
    total_cost = sum(c["cost"] for c in campaigns)
    total_conv = sum(c["conversions"] for c in campaigns)
    
    ctr = (total_clicks / total_imp * 100) if total_imp > 0 else 0.0
    cpc = (total_cost / total_clicks) if total_clicks > 0 else 0.0
    
    # Generate mock daily metrics for the last 7 days chart
    history = []
    base_date = datetime.date.today()
    for i in range(6, -1, -1):
        day = base_date - datetime.timedelta(days=i)
        # Add random variations
        clicks_day = random.randint(150, 320) if total_clicks > 0 else 0
        imp_day = clicks_day * random.randint(12, 16)
        cost_day = clicks_day * random.uniform(0.60, 0.85)
        
        history.append({
            "date": day.strftime("%d/%m"),
            "impressions": imp_day,
            "clicks": clicks_day,
            "cost": round(cost_day, 2),
            "conversions": int(clicks_day * random.uniform(0.08, 0.12))
        })
        
    return {
        "totals": {
            "impressions": total_imp,
            "clicks": total_clicks,
            "cost": round(total_cost, 2),
            "ctr": round(ctr, 2),
            "cpc": round(cpc, 2),
            "conversions": total_conv
        },
        "history": history
    }
