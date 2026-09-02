import os
from pydantic import BaseModel, model_validator
from typing import List, Optional
from datetime import datetime

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


class RecruiterWhatsAppRequest(BaseModel):
    phone: str
    text: str



class ResetCodeRequest(BaseModel):
    method: str
    identifier: str
    code: str



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



class SubmitAssessmentRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    answers: dict



class UpdateAssessmentRequest(BaseModel):
    title: str
    questions: list



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

