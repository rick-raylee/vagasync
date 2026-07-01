import os
import json
import re
from google import genai
from google.genai import types
from sqlalchemy.orm import Session
from database import Config

# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────

def get_api_key(db: Session = None) -> str:
    """Obtém a chave da API Gemini da variável de ambiente ou do banco de dados (suporta encriptação)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key
    if db:
        config = db.query(Config).filter(Config.key == "gemini_api_key").first()
        if config and config.value and config.value != "••••••••••••••••":
            return config.value
        enc_config = db.query(Config).filter(Config.key == "enc_gemini_api_key").first()
        if enc_config and enc_config.value:
            import security
            decrypted = security.decrypt_data(enc_config.value)
            if decrypted and decrypted != "••••••••••••••••":
                return decrypted
    return ""

def get_gemini_client(db: Session = None):
    api_key = get_api_key(db)
    if not api_key:
        raise ValueError("Gemini API Key não configurada. Configure no painel de configurações.")
    return genai.Client(api_key=api_key)


# ─────────────────────────────────────────────
# Análise de currículo
# ─────────────────────────────────────────────

def analyze_resume(resume_text: str, db: Session = None) -> dict:
    """
    Analisa o currículo do candidato e extrai informações estruturadas.
    """
    try:
        client = get_gemini_client(db)
        prompt = f"""
        Você é um agente especialista em recrutamento e seleção (Tech Recruiter).
        Analise o currículo a seguir e extraia as informações estruturadas em formato JSON.
        
        Currículo:
        {resume_text}
        
        Responda APENAS com um objeto JSON válido contendo os seguintes campos:
        - "skills": lista de strings com principais habilidades técnicas (ex: ["Python", "React", "SQL"])
        - "soft_skills": lista de strings com habilidades interpessoais
        - "suggested_roles": lista de cargos principais recomendados (ex: ["Desenvolvedor Full Stack", "Engenheiro de Software IA"])
        - "summary": resumo executivo do perfil de 3 frases
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Erro ao analisar currículo com IA: {e}")
        return {
            "skills": ["Python", "JavaScript", "HTML", "CSS"],
            "soft_skills": ["Comunicação", "Trabalho em Equipe"],
            "suggested_roles": ["Desenvolvedor Full Stack"],
            "summary": f"Erro na análise: {str(e)}. Perfil genérico criado."
        }


# ─────────────────────────────────────────────
# Match de vaga x currículo
# ─────────────────────────────────────────────

def match_job(resume_text: str, job_description: str, db: Session = None) -> dict:
    """
    Calcula a compatibilidade do currículo com a descrição da vaga.
    """
    try:
        client = get_gemini_client(db)
        prompt = f"""
        Você é um agente de IA focado em Recrutamento e Seleção.
        Analise a compatibilidade entre o Currículo do Candidato e a Descrição da Vaga.
        
        Currículo do Candidato:
        {resume_text}
        
        Descrição da Vaga:
        {job_description}
        
        Responda APENAS com um objeto JSON contendo exatamente os seguintes campos:
        - "score": número inteiro de 0 a 100 indicando a compatibilidade geral.
        - "explanation": breve explicação de por que esse score foi atribuído (máximo 4 linhas).
        - "gaps": lista de requisitos essenciais da vaga que o currículo não possui.
        - "fit_level": string: "Alto", "Médio" ou "Baixo".
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Erro ao calcular match da vaga com IA: {e}")
        return {
            "score": 50,
            "explanation": f"Falha na conexão com a IA: {str(e)}. Score genérico atribuído.",
            "gaps": ["Requisitos adicionais não avaliados devido a erro de API"],
            "fit_level": "Médio"
        }


# ─────────────────────────────────────────────
# Geração de mensagens
# ─────────────────────────────────────────────

def generate_recruiter_message(resume_text: str, job_title: str, company_name: str,
                                recruiter_name: str = None, db: Session = None) -> str:
    """
    Gera uma mensagem de follow-up profissional para o recrutador.
    """
    try:
        client = get_gemini_client(db)
        recruiter_part = f"dirigida a {recruiter_name}" if recruiter_name else "dirigida ao time de recrutamento"
        prompt = f"""
        Você é um candidato profissional buscando a vaga de "{job_title}" na empresa "{company_name}".
        Escreva uma mensagem curta de follow-up {recruiter_part}.
        
        Objetivo: Perguntar educadamente se o currículo foi analisado e se há alguma atualização.
        
        Currículo do candidato (contexto rápido):
        {resume_text}
        
        Regras:
        - Máximo 120 palavras, profissional, humana e em português do Brasil.
        - Não use placeholders como [Seu Nome].
        - Tom otimista e focado em agregar valor.
        
        Retorne APENAS o texto da mensagem.
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao gerar mensagem de follow-up: {e}")
        recruiter_str = recruiter_name if recruiter_name else "Recrutador"
        return (f"Olá, {recruiter_str}. Gostaria de acompanhar minha candidatura para a vaga de "
                f"{job_title} na {company_name}. Permaneço à disposição. Obrigado!")


def generate_recruiter_response(user_message: str, job_title: str, company_name: str,
                                 recruiter_name: str, db: Session = None) -> str:
    """
    Gera uma resposta do recrutador simulado à mensagem do candidato.
    """
    try:
        client = get_gemini_client(db)
        prompt = f"""
        Você é {recruiter_name}, recrutador(a) na empresa "{company_name}".
        Você acabou de receber esta mensagem de um candidato à vaga de "{job_title}":
        
        "{user_message}"
        
        Responda de forma profissional, simpática e realista em português do Brasil.
        Regras:
        - Máximo 70 palavras.
        - Use o nome {recruiter_name} para assinar.
        - Retorne APENAS o texto da resposta.
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Erro ao gerar resposta do recrutador: {e}")
        return (f"Olá! Agradeço o retorno. Vou avaliar com o time técnico. "
                f"Qual sua disponibilidade para conversarmos? Abraços, {recruiter_name}.")


# ─────────────────────────────────────────────
# Busca de vagas com Gemini + Google Search
# ─────────────────────────────────────────────

def _clean_json_from_text(text: str) -> str:
    """Remove blocos de markdown e extrai o JSON limpo."""
    text = text.strip()
    # Remove blocos ```json ... ``` ou ``` ... ```
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    # Encontra o array JSON na resposta
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return match.group(0)
    return text.strip()


def search_real_jobs_on_web(keywords: list, location: str, db: Session = None) -> list:
    """
    Busca vagas de emprego reais na web usando o Gemini 2.5 Flash com Google Search Grounding.
    Realiza múltiplas rodadas de busca (uma por palavra-chave) para maximizar resultados.
    Retorna lista de dicionários com dados estruturados de cada vaga.
    """
    all_jobs = []
    seen_links = set()

    try:
        client = get_gemini_client(db)
    except Exception as e:
        print(f"[Gemini Search] Sem chave de API: {e}")
        return []

    for keyword in keywords:
        try:
            print(f"[Gemini Search] Buscando vagas para: '{keyword}' em '{location}'")

            loc_lower = location.lower()
            is_international = any(term in loc_lower for term in [
                'international', 'internacional', 'worldwide', 'global', 'remote worldwide',
                'united states', 'estados unidos', 'usa', 'eua',
                'portugal', 'europe', 'europa', 'canada', 'germany', 'alemanha',
                'uk', 'united kingdom', 'reino unido', 'france', 'franca', 'spain', 'espanha',
                'italy', 'italia', 'japan', 'japao', 'australia', 'india', 'china'
            ]) and not (loc_lower.endswith('(país)') and 'brasil' in loc_lower)

            if is_international:
                location_hint = f"Localização/País: {location} — busca INTERNACIONAL (aceitar vagas em qualquer país)"
                sources_hint = """1. LinkedIn Jobs (linkedin.com/jobs) — vagas internacionais
2. Indeed (indeed.com) — vagas globais
3. Glassdoor (glassdoor.com) — internacional
4. Greenhouse, Lever, Workday, Ashby — ATS globais
5. Remote.com, WeWorkRemotely, Remote OK — vagas remotas internacionais"""
                geo_hint = f"Localização compatível: {location} — vagas presenciais, híbridas ou remotas internacionais"
                location_field = "Cidade, País ou Remote (Worldwide)"
            else:
                location_hint = f"Localização: {location}"
                sources_hint = """1. ATS oficial da empresa: Gupy, Greenhouse, Lever, Workday, Ashby, Recruitee, Kenoby, Solides, Pandapé
2. LinkedIn Jobs (linkedin.com/jobs)
3. Indeed Brasil (indeed.com.br)
4. InfoJobs, Catho, Vagas.com.br, Glassdoor"""
                geo_hint = f"Localização compatível: remoto Brasil, híbrido ou presencial em {location}"
                location_field = "Cidade, UF ou Remoto - Brasil"

            prompt = f"""
Use a ferramenta de busca Google para encontrar vagas de emprego REAIS, recentes e abertas para:
- Cargo/Área: {keyword}
- {location_hint}

Prioridade das fontes (nesta ordem):
{sources_hint}

Critérios para selecionar vagas:
- Publicadas ou atualizadas recentemente (últimas 2-4 semanas)
- Processo seletivo claramente aberto
- Link direto e válido para a vaga (não para a home da empresa)
- Descrição completa com requisitos claros
- {geo_hint}

Evite: vagas expiradas, bancos de talentos sem cargo definido, páginas de newsletter, cursos, links quebrados.

Retorne SOMENTE um array JSON válido (sem texto antes ou depois), com até 6 vagas:
[
  {{
    "title": "Título exato da vaga",
    "company": "Nome da empresa",
    "location": "{location_field}",
    "link": "https://link-direto-e-real-para-a-vaga",
    "source": "Nome do site (LinkedIn, Indeed, Gupy, etc.)",
    "description": "Resumo de 2-3 linhas com principais requisitos e tipo de contrato"
  }}
]
"""

            # ✅ Sintaxe correta para Google Search Grounding no SDK google.genai
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                )
            )

            raw_text = response.text if response.text else ""
            clean_text = _clean_json_from_text(raw_text)

            if not clean_text or clean_text == "[]":
                print(f"[Gemini Search] Nenhuma vaga retornada para '{keyword}'")
                continue

            jobs_from_keyword = json.loads(clean_text)

            if not isinstance(jobs_from_keyword, list):
                print(f"[Gemini Search] Resposta não é lista para '{keyword}'")
                continue

            # Deduplicar por link
            for job in jobs_from_keyword:
                link = job.get("link", "").strip()
                if not link or link in seen_links:
                    continue
                seen_links.add(link)
                all_jobs.append(job)

            print(f"[Gemini Search] '{keyword}': {len(jobs_from_keyword)} vagas encontradas")

        except json.JSONDecodeError as je:
            print(f"[Gemini Search] Erro ao parsear JSON para '{keyword}': {je}")
            print(f"[Gemini Search] Texto recebido: {raw_text[:300] if 'raw_text' in dir() else 'N/A'}")
        except Exception as e:
            print(f"[Gemini Search] Erro na busca para '{keyword}': {e}")

    print(f"[Gemini Search] Total de vagas únicas encontradas: {len(all_jobs)}")
    return all_jobs


def search_linkedin_jobs_with_gemini(keywords: list, location: str, db: Session = None) -> list:
    """
    Busca vagas especificamente no LinkedIn usando Gemini + Google Search Grounding.
    Complementa o Playwright bot buscando vagas que o bot não alcança.
    """
    all_jobs = []
    seen_links = set()

    try:
        client = get_gemini_client(db)
    except Exception as e:
        print(f"[Gemini LinkedIn] Sem chave de API: {e}")
        return []

    keywords_str = ", ".join(keywords)
    try:
        print(f"[Gemini LinkedIn] Buscando vagas no LinkedIn para: {keywords_str}")

        prompt = f"""
Use a busca Google para encontrar vagas de emprego reais e abertas no LinkedIn Jobs para:
- Cargos: {keywords_str}
- Localização: {location}

Busque em: site:linkedin.com/jobs OR site:linkedin.com/in (perfis de vagas)

Filtre apenas vagas:
- Com link direto linkedin.com/jobs/view/...
- Publicadas recentemente
- Easy Apply ou candidatura aberta

Retorne SOMENTE um array JSON válido com até 8 vagas do LinkedIn:
[
  {{
    "title": "Título exato da vaga",
    "company": "Nome da empresa",
    "location": "Cidade, UF ou Remoto",
    "link": "https://www.linkedin.com/jobs/view/...",
    "source": "LinkedIn",
    "description": "Principais requisitos da vaga em 2-3 linhas"
  }}
]
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            )
        )

        raw_text = response.text if response.text else ""
        clean_text = _clean_json_from_text(raw_text)

        if clean_text and clean_text != "[]":
            jobs = json.loads(clean_text)
            if isinstance(jobs, list):
                for job in jobs:
                    link = job.get("link", "").strip()
                    if link and link not in seen_links:
                        seen_links.add(link)
                        job["source"] = "LinkedIn"
                        all_jobs.append(job)

        print(f"[Gemini LinkedIn] {len(all_jobs)} vagas do LinkedIn encontradas via Gemini Search")

    except Exception as e:
        print(f"[Gemini LinkedIn] Erro: {e}")

    return all_jobs

def generate_ai_comment(post_content: str, db: Session = None) -> str:
    """Gera um comentário inteligente e profissional de IA para um post de rede social."""
    try:
        client = get_gemini_client(db)
        prompt = f"""
        Você é o "VagaSync IA Agente", um robô recrutador e consultor de carreira inteligente da plataforma VagaSync.
        Escreva um comentário profissional, curto (máximo de 2 a 3 frases) e empático para a seguinte postagem na comunidade de carreiras:
        
        Postagem do usuário:
        "{post_content}"
        
        Escreva o comentário de forma agregadora, trazendo incentivo ou dicas curtas relacionadas ao que foi postado. Não utilize hashtags e seja direto.
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip() if response.text else "Interessante! O mercado de trabalho está mudando rapidamente e estar preparado com inteligência artificial é a chave para o sucesso profissional. Continue focado!"
    except Exception as e:
        print(f"[IA Feed Comment] Falha ao chamar Gemini (usando fallback): {e}")
        content_lower = post_content.lower()
        if "entrevista" in content_lower or "seletivo" in content_lower:
            return "Dica do VagaSync Agente: Em processos seletivos, treine suas respostas com foco em resultados mensuráveis (método STAR). Boa sorte!"
        elif "curriculo" in content_lower or "currículo" in content_lower:
            return "Lembre-se: Otimizar seu currículo com palavras-chave da vaga aumenta em mais de 70% o match de recrutamento. Vale a pena revisar!"
        elif "linkedin" in content_lower:
            return "Manter o LinkedIn atualizado e com o selo 'Open to Work' (ou apenas configurado para recrutadores) ajuda muito na busca passiva por vagas."
        elif "estagio" in content_lower or "estágio" in content_lower or "junior" in content_lower or "júnior" in content_lower:
            return "Para vagas iniciais, foque em demonstrar sua capacidade de aprendizado rápido e crie projetos de portfólio práticos!"
        else:
            return "Excelente reflexão! O networking e a constante atualização profissional são as ferramentas mais poderosas no mercado corporativo atual."

def generate_ai_post(db: Session = None) -> str:
    """Gera um post de blog ou postagem de feed relevante para carreira via IA."""
    try:
        client = get_gemini_client(db)
        prompt = f"""
        Você é o "VagaSync IA Agente", um especialista em recrutamento digital e tecnologia.
        Gere um post interessante e curto (1 parágrafo com até 4 frases) para nossa comunidade profissional sobre tendências de mercado, uso de IA na carreira ou preparação para processos seletivos.
        Diga algo inspirador ou traga um dado técnico interessante do setor de tecnologia. Seja direto e profissional.
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip() if response.text else "A inteligência artificial não vai substituir os profissionais, mas os profissionais que usam IA vão substituir aqueles que não usam. Como você tem otimizado sua rotina hoje?"
    except Exception as e:
        print(f"[IA Feed Post] Falha ao chamar Gemini (usando fallback): {e}")
        import random
        posts = [
            "Você sabia que o mercado de TI deve abrir mais de 500 mil novas oportunidades na América Latina até o próximo ano? Investir em habilidades de cloud computing e engenharia de software continua sendo uma aposta extremamente segura.",
            "Dica de Carreira: A melhor forma de se destacar para recrutadores é ter um portfólio no GitHub organizado, com READMEs claros explicando o propósito e as tecnologias de cada projeto. Menos quantidade, mais qualidade!",
            "Reflexão do dia: A automação de candidaturas ajuda a expandir o alcance da sua busca, mas a preparação para a entrevista técnica continua sendo o fator decisivo para a contratação. Equilibre quantidade com preparação!",
            "Agente VagaSync: Acabei de processar mais de 200 novas vagas nas últimas horas. Percebi um aumento de 15% na busca por desenvolvedores com noções de Docker e CI/CD. Vale a pena conferir se essas habilidades constam no seu perfil!"
        ]
        return random.choice(posts)


def answer_whatsapp_chat(phone: str, message: str, sender_name: str, db: Session = None) -> tuple[str, str]:
    """
    Usa o Gemini para responder o chat do WhatsApp e detectar a intenção do usuário.
    Retorna uma tupla (resposta_texto, intencao).
    Intenções válidas: 'generate_payment', 'help', 'none'.
    """
    try:
        client = get_gemini_client(db)
        prompt = f"""
        Você é o atendente virtual inteligente do VagaSync via WhatsApp.
        Seu tom de voz deve ser prestativo, moderno e corporativo.
        O nome do usuário com quem você está falando é '{sender_name}' e o telefone é '{phone}'.
        
        Mensagem recebida do usuário:
        "{message}"
        
        Determine se a intenção do usuário é comprar, pagar, assinar o plano premium ou obter dados para pagamento/PIX.
        
        Responda APENAS com um objeto JSON contendo exatamente os seguintes campos:
        - "response_text": a resposta que você quer enviar de volta no WhatsApp para o usuário. Se for detectada intenção de pagamento, responda dizendo de forma amigável que está gerando o PIX.
        - "intent": a intenção detectada. Deve ser EXATAMENTE 'generate_payment' (se ele quer pagar/assinar/comprar o premium/pix) ou 'none' (para qualquer outro assunto de chat).
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        data = json.loads(response.text)
        return data.get("response_text", "Olá! Como posso ajudar você hoje?"), data.get("intent", "none")
    except Exception as e:
        print(f"Erro no chatbot de WhatsApp IA: {e}")
        msg_lower = message.lower()
        if "pix" in msg_lower or "pagar" in msg_lower or "premium" in msg_lower or "comprar" in msg_lower:
            return "Olá! Vou gerar o PIX para a assinatura Premium do VagaSync agora mesmo...", "generate_payment"
        return "Olá! Sou o atendente virtual do VagaSync. Como posso te ajudar hoje?", "none"

