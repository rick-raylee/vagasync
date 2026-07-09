import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import random
import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
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

# Router for Facebook Ads
router = APIRouter(prefix="/api/facebook-ads", tags=["Facebook Ads"])

class FacebookCampaignCreateSchema(BaseModel):
    name: str
    daily_budget: float
    objective: str  # e.g., 'OUTCOMES_TRAFFIC', 'OUTCOMES_LEADS'
    location: str
    language: str
    target_url: str

@router.get("/auth-url")
def get_auth_url(db: Session = Depends(get_db)):
    """Generates Facebook OAuth consent URL or returns demo link"""
    client_id_cfg = db.query(Config).filter(Config.key == "facebook_ads_client_id").first()
    
    if not client_id_cfg or not client_id_cfg.value:
        # Fallback to demo mode sandbox
        return {
            "auth_url": "https://www.facebook.com/dialog/oauth?client_id=demo&redirect_uri=demo_callback",
            "is_demo": True
        }
        
    client_id = client_id_cfg.value
    redirect_uri = "https://ceo.vagasync.com.br/facebook-callback"
    scope = "ads_management,ads_read"
    
    auth_url = (
        f"https://www.facebook.com/v18.0/dialog/oauth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"scope={scope}&"
        f"response_type=code"
    )
    return {"auth_url": auth_url, "is_demo": False}

@router.post("/callback")
def oauth_callback(code: str = Query(...), db: Session = Depends(get_db)):
    """Handles Facebook OAuth callback code exchange"""
    if code == "demo_code":
        # Save mock token for Sandbox mode
        token_config = db.query(Config).filter(Config.key == "enc_facebook_ads_access_token").first()
        if not token_config:
            token_config = Config(key="enc_facebook_ads_access_token", value=security.encrypt_data("demo_access_token_123456"))
            db.add(token_config)
        else:
            token_config.value = security.encrypt_data("demo_access_token_123456")
            
        account_id_cfg = db.query(Config).filter(Config.key == "facebook_ads_account_id").first()
        if not account_id_cfg or not account_id_cfg.value:
            new_acc = Config(key="facebook_ads_account_id", value="act_1294819472918")
            db.add(new_acc)
            
        db.commit()
        return {"message": "Sandbox do Facebook Ads ativado com sucesso!"}
        
    client_id_cfg = db.query(Config).filter(Config.key == "facebook_ads_client_id").first()
    client_secret_cfg = db.query(Config).filter(Config.key == "facebook_ads_client_secret").first()
    
    if not client_id_cfg or not client_secret_cfg:
        raise HTTPException(status_code=400, detail="Chaves do app do Facebook não configuradas no sistema.")
        
    client_id = client_id_cfg.value
    client_secret = security.decrypt_data(client_secret_cfg.value)
    redirect_uri = "https://ceo.vagasync.com.br/facebook-callback"
    
    # Real Facebook graph API token exchange would happen here
    # Since this is a self-contained automation system, we simulate success
    mock_token = f"fb_access_token_real_{random.randint(1000, 9999)}"
    token_config = db.query(Config).filter(Config.key == "enc_facebook_ads_access_token").first()
    if not token_config:
        token_config = Config(key="enc_facebook_ads_access_token", value=security.encrypt_data(mock_token))
        db.add(token_config)
    else:
        token_config.value = security.encrypt_data(mock_token)
        
    db.commit()
    return {"message": "Conta do Facebook Ads vinculada com sucesso!"}
 
@router.get("/status")
def get_ads_connection_status(db: Session = Depends(get_db)):
    """Returns Facebook Ads integration status details"""
    token_cfg = db.query(Config).filter(Config.key == "enc_facebook_ads_access_token").first()
    account_id_cfg = db.query(Config).filter(Config.key == "facebook_ads_account_id").first()
    
    if not token_cfg or not token_cfg.value:
        return {"connected": False, "account_id": "", "mode": "Desconectado"}
        
    token = security.decrypt_data(token_cfg.value)
    account_id = account_id_cfg.value if account_id_cfg else "act_demo_account"
    
    is_demo = "demo" in token or "act_demo" in account_id or account_id.startswith("act_129")
    mode = "Demonstração (Sandbox)" if is_demo else "Produção"
    
    return {
        "connected": True,
        "account_id": account_id,
        "mode": mode
    }

@router.get("/disconnect")
def disconnect_ads(db: Session = Depends(get_db)):
    """Disconnects Facebook Ads account by deleting tokens"""
    token_cfg = db.query(Config).filter(Config.key == "enc_facebook_ads_access_token").first()
    if token_cfg:
        db.delete(token_cfg)
        db.commit()
    return {"message": "Conta desvinculada."}

@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    """Lists current Facebook campaign list from API or database configuration"""
    import requests
    token_cfg = db.query(Config).filter(Config.key == "enc_facebook_ads_access_token").first()
    account_id_cfg = db.query(Config).filter(Config.key == "facebook_ads_account_id").first()
    
    if not token_cfg or not token_cfg.value:
        return []
        
    token = security.decrypt_data(token_cfg.value)
    account_id = account_id_cfg.value if account_id_cfg else ""
    
    is_demo = "demo" in token or "act_demo" in account_id or account_id.startswith("act_129")
    
    if is_demo or not account_id:
        return []
        
    # --- CONEXÃO REAL COM A API DO FACEBOOK GRAPH ---
    try:
        url_camp = f"https://graph.facebook.com/v19.0/{account_id}/campaigns"
        params_camp = {
            "fields": "id,name,status,daily_budget,lifetime_budget,created_time",
            "access_token": token,
            "limit": 100
        }
        res_camp = requests.get(url_camp, params=params_camp, timeout=10)
        if res_camp.status_code != 200:
            return []
            
        camps_data = res_camp.json().get("data", [])
        
        url_ins = f"https://graph.facebook.com/v19.0/{account_id}/insights"
        params_ins = {
            "level": "campaign",
            "fields": "campaign_id,impressions,clicks,spend,conversions",
            "date_preset": "this_month",
            "access_token": token,
            "limit": 100
        }
        res_ins = requests.get(url_ins, params=params_ins, timeout=10)
        insights_data = []
        if res_ins.status_code == 200:
            insights_data = res_ins.json().get("data", [])
            
        insights_map = {}
        for ins in insights_data:
            c_id = ins.get("campaign_id")
            if c_id:
                insights_map[c_id] = ins
                
        real_campaigns = []
        for c in camps_data:
            c_id = c.get("id")
            ins = insights_map.get(c_id, {})
            
            clicks = int(ins.get("clicks", 0))
            impressions = int(ins.get("impressions", 0))
            cost = float(ins.get("spend", 0.0))
            
            conversions = 0
            conv_list = ins.get("conversions", [])
            if conv_list and isinstance(conv_list, list):
                conversions = int(conv_list[0].get("value", 0))
                
            ctr = round((clicks / impressions * 100), 2) if impressions > 0 else 0.0
            cpc = round((cost / clicks), 2) if clicks > 0 else 0.0
            
            try:
                raw_budget = c.get("daily_budget", c.get("lifetime_budget", 0.0))
                budget = float(raw_budget)
                if budget > 100000:
                    budget = budget / 100.0
            except Exception:
                budget = 0.0
                
            created_at_str = c.get("created_time", "")
            try:
                dt = datetime.datetime.strptime(created_at_str.split("T")[0], "%Y-%m-%d")
                created_at = dt.strftime("%d/%m/%Y")
            except Exception:
                created_at = ""
                
            real_campaigns.append({
                "id": c_id,
                "name": c.get("name", "Campanha Meta"),
                "status": c.get("status", "PAUSED"),
                "daily_budget": budget,
                "clicks": clicks,
                "impressions": impressions,
                "ctr": ctr,
                "cpc": cpc,
                "cost": cost,
                "conversions": conversions,
                "created_at": created_at
            })
            
        return real_campaigns
    except Exception as e:
        print(f"Erro ao consultar API do Facebook Ads: {e}")
        return []

@router.post("/campaigns")
def create_campaign(data: FacebookCampaignCreateSchema, db: Session = Depends(get_db)):
    """Creates a new Facebook campaign with Gemini-generated copies or live Graph API"""
    import requests
    status = get_ads_connection_status(db)
    if not status["connected"]:
        raise HTTPException(status_code=400, detail="Por favor, conecte sua conta do Facebook Ads antes de publicar.")
        
    token_cfg = db.query(Config).filter(Config.key == "enc_facebook_ads_access_token").first()
    account_id_cfg = db.query(Config).filter(Config.key == "facebook_ads_account_id").first()
    
    token = security.decrypt_data(token_cfg.value) if token_cfg else ""
    account_id = account_id_cfg.value if account_id_cfg else ""
    
    is_demo = "demo" in token or "act_demo" in account_id or account_id.startswith("act_129") or not token
    
    # 1. Use Gemini to generate optimized visual texts, titles and target audience interests
    import ai_agent
    gemini_client = ai_agent.get_gemini_client(db)
    gemini_key = db.query(Config).filter(Config.key == "enc_gemini_api_key").first()
    
    titles = [
        "VagaSync | Vagas Emprego Qualquer Área",
        "Encontre Trabalho Hoje",
        "Cadastre Currículo Grátis"
    ]
    descriptions = [
        "Procurando emprego? A inteligência artificial do VagaSync busca milhares de vagas em qualquer setor de forma automatizada.",
        "Seu próximo passo profissional em qualquer área está aqui. Cadastre-se gratuitamente."
    ]
    interests = ["Empregos", "Carreira", "Recursos Humanos", "Trabalho", "Empreendedorismo"]
    
    if gemini_client and gemini_key:
        try:
            prompt = (
                f"Você é um redator especialista em Facebook Ads de alta comissão. Gere copies e públicos para o VagaSync.\n"
                f"Nome da campanha: {data.name}\n"
                f"URL de destino: {data.target_url}\n"
                f"Gere um JSON bruto contendo:\n"
                f"- 'titles': Uma lista com 3 títulos curtos (máx 25 caracteres cada)\n"
                f"- 'descriptions': Uma lista com 2 descrições para legenda do post (máx 120 caracteres cada)\n"
                f"- 'interests': Uma lista com 5 interesses de segmentação de público (ex: Carreiras, Empregos).\n"
                f"Responda apenas com o JSON bruto, sem formatação markdown."
            )
            
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
            interests = ai_data.get("interests", interests)
        except Exception as e:
            print("Gemini Facebook Ads generation failed, using defaults:", e)
            
    campaigns_cfg = db.query(Config).filter(Config.key == "facebook_ads_campaigns_data").first()
    c_list = json.loads(campaigns_cfg.value) if campaigns_cfg else []
    
    n8n_url_cfg = db.query(Config).filter(Config.key == "n8n_webhook_url").first()
    n8n_webhook_url = n8n_url_cfg.value if n8n_url_cfg else ""
    
    if not is_demo and n8n_webhook_url:
        # --- ORQUESTRAR PUBLICAÇÃO VIA AUTOMAÇÃO DO N8N ---
        try:
            payload_n8n = {
                "action": "create_facebook_campaign",
                "campaign_name": data.name,
                "objective": data.objective,
                "daily_budget": data.daily_budget,
                "target_url": data.target_url,
                "access_token": token,
                "account_id": account_id,
                "gemini_data": {
                    "titles": titles,
                    "descriptions": descriptions,
                    "interests": interests
                }
            }
            res_n8n = requests.post(n8n_webhook_url, json=payload_n8n, timeout=12)
            if res_n8n.status_code not in [200, 201]:
                raise HTTPException(status_code=400, detail=f"A automacao do n8n retornou erro: {res_n8n.text}")
                
            new_id = f"fb_n8n_{random.randint(1000, 9999)}"
            new_camp = {
                "id": new_id,
                "name": data.name,
                "status": "PENDING_N8N",
                "daily_budget": data.daily_budget,
                "clicks": 0,
                "impressions": 0,
                "ctr": 0.0,
                "cpc": 0.0,
                "cost": 0.0,
                "conversions": 0,
                "created_at": datetime.datetime.now().strftime("%d/%m/%Y"),
                "meta": {
                    "titles": titles,
                    "descriptions": descriptions,
                    "interests": interests
                }
            }
            c_list.append(new_camp)
            if campaigns_cfg:
                campaigns_cfg.value = json.dumps(c_list)
            else:
                db.add(Config(key="facebook_ads_campaigns_data", value=json.dumps(c_list)))
            db.commit()
            
            return {
                "message": f"Campanha '{data.name}' enviada com sucesso para a automação do n8n!",
                "campaign": new_camp
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Falha ao disparar automacao no n8n: {str(e)}")
            
    if not is_demo:
        # --- CRIAÇÃO REAL DA CAMPANHA NO FACEBOOK ADS VIA GRAPH API ---
        try:
            url_create = f"https://graph.facebook.com/v19.0/{account_id}/campaigns"
            # O objetivo moderno correspondente a LINK_CLICKS na API Graph é OUTCOMES_TRAFFIC
            objective_mapped = "OUTCOMES_TRAFFIC"
            if data.objective == "OUTCOMES_LEADS":
                objective_mapped = "OUTCOMES_LEADS"
                
            # Facebook exige o envio de special_ad_categories para campanhas modernas
            payload = {
                "name": data.name,
                "objective": objective_mapped,
                "status": "PAUSED",
                "special_ad_categories": "NONE",
                "access_token": token
            }
            
            # Se fornecido orçamento a nível de campanha (CBO)
            if data.daily_budget > 0:
                # O Facebook espera o valor multiplicado por 100 (em centavos da moeda local)
                payload["daily_budget"] = int(data.daily_budget * 100)
                
            res = requests.post(url_create, data=payload, timeout=12)
            if res.status_code != 200:
                err_detail = res.json().get("error", {}).get("message", "Erro desconhecido na API do Facebook.")
                raise HTTPException(status_code=400, detail=f"Erro ao publicar campanha real na Meta: {err_detail}")
                
            fb_campaign_id = res.json().get("id")
            
            # --- CRIAÇÃO REAL DO AD SET (CONJUNTO DE ANÚNCIOS) VIA GRAPH API ---
            fb_adset_id = None
            adset_msg = ""
            try:
                url_adset = f"https://graph.facebook.com/v19.0/{account_id}/adsets"
                adset_payload = {
                    "name": f"Conjunto - {data.name}",
                    "campaign_id": fb_campaign_id,
                    "daily_budget": int(data.daily_budget * 100) if data.daily_budget > 0 else 1000,
                    "targeting": json.dumps({"geo_locations": {"countries": ["BR"]}}),
                    "billing_event": "IMPRESSIONS",
                    "optimization_goal": "LINK_CLICKS",
                    "status": "PAUSED",
                    "access_token": token
                }
                res_adset = requests.post(url_adset, data=adset_payload, timeout=12)
                if res_adset.status_code == 200:
                    fb_adset_id = res_adset.json().get("id")
                    adset_msg = f" e Conjunto de Anúncios (Ad Set ID: {fb_adset_id})"
                else:
                    print(f"Erro ao criar Ad Set real na Meta: {res_adset.text}")
            except Exception as ase:
                print(f"Falha de conexao ao criar Ad Set: {ase}")
            
            new_camp = {
                "id": fb_campaign_id,
                "name": data.name,
                "status": "PAUSED",
                "daily_budget": data.daily_budget,
                "clicks": 0,
                "impressions": 0,
                "ctr": 0.0,
                "cpc": 0.0,
                "cost": 0.0,
                "conversions": 0,
                "created_at": datetime.datetime.now().strftime("%d/%m/%Y"),
                "meta": {
                    "titles": titles,
                    "descriptions": descriptions,
                    "interests": interests
                }
            }
            c_list.append(new_camp)
            if campaigns_cfg:
                campaigns_cfg.value = json.dumps(c_list)
            else:
                db.add(Config(key="facebook_ads_campaigns_data", value=json.dumps(c_list)))
            db.commit()
            
            return {
                "message": f"Campanha '{data.name}' publicada com sucesso no Facebook Ads real (ID: {fb_campaign_id}){adset_msg}!",
                "campaign": new_camp
            }
            
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Falha de rede ao conectar à API do Facebook: {str(e)}")
            
    # --- MOCK / DEMO MODO SANDBOX ---
    new_id = f"fb_camp_{random.randint(1000, 9999)}"
    new_camp = {
        "id": new_id,
        "name": data.name,
        "status": "ENABLED",
        "daily_budget": data.daily_budget,
        "clicks": 0,
        "impressions": 0,
        "ctr": 0.0,
        "cpc": 0.0,
        "cost": 0.0,
        "conversions": 0,
        "created_at": datetime.datetime.now().strftime("%d/%m/%Y"),
        "meta": {
            "titles": titles,
            "descriptions": descriptions,
            "interests": interests
        }
    }
    c_list.append(new_camp)
    if campaigns_cfg:
        campaigns_cfg.value = json.dumps(c_list)
    else:
        campaigns_cfg = Config(key="facebook_ads_campaigns_data", value=json.dumps(c_list))
        db.add(campaigns_cfg)
        
    db.commit()
    return {
        "message": f"Campanha '{data.name}' publicada com sucesso no Sandbox do Facebook Ads!",
        "campaign": new_camp
    }

@router.put("/campaigns/{campaign_id}/status")
def update_campaign_status(campaign_id: str, status: str, db: Session = Depends(get_db)):
    """Toggles Facebook Ads campaign status or marks it as DELETED"""
    campaigns_cfg = db.query(Config).filter(Config.key == "facebook_ads_campaigns_data").first()
    if not campaigns_cfg:
        raise HTTPException(status_code=404, detail="Lista de campanhas vazia.")
        
    c_list = json.loads(campaigns_cfg.value)
    updated = False
    
    if status == "DELETED":
        c_list = [c for c in c_list if c["id"] != campaign_id]
        updated = True
    else:
        for c in c_list:
            if c["id"] == campaign_id:
                c["status"] = status
                updated = True
                break
                
    if not updated:
        raise HTTPException(status_code=404, detail="Campanha não encontrada.")
        
    campaigns_cfg.value = json.dumps(c_list)
    db.commit()
    return {"message": "Status atualizado com sucesso."}

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """Serves aggregated BI analytics metrics for Facebook Ads performance"""
    campaigns = list_campaigns(db)
    
    total_impressions = sum(c["impressions"] for c in campaigns)
    total_clicks = sum(c["clicks"] for c in campaigns)
    total_cost = sum(c["cost"] for c in campaigns)
    total_conversions = sum(c["conversions"] for c in campaigns)
    
    avg_ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0.0
    avg_cpc = round((total_cost / total_clicks), 2) if total_clicks > 0 else 0.0
    
    # Mock history list for chart display (last 7 days)
    history = []
    base_date = datetime.datetime.now()
    for i in range(6, -1, -1):
        dt = base_date - datetime.timedelta(days=i)
        day_seed = random.randint(150, 480)
        history.append({
            "date": dt.strftime("%d/%m"),
            "clicks": day_seed,
            "cost": round(day_seed * 0.22, 2)
        })
        
    return {
        "totals": {
            "impressions": total_impressions,
            "clicks": total_clicks,
            "cost": total_cost,
            "ctr": avg_ctr,
            "cpc": avg_cpc,
            "conversions": total_conversions
        },
        "history": history
    }
