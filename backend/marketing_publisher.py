import sqlite3
import re
from datetime import datetime, timedelta
import random

# Tópicos de Growth e Marketing Digital para o VagaSync
TOPICS = [
    {
        "id": "ats_mapping",
        "topic": "Mapeamento ATS em 2026: Guia Completo para Candidatos",
        "category": "Currículo",
        "default_summary": "Como estruturar seu currículo para passar nas leituras de sistemas automáticos de grandes empresas.",
        "default_content": "Os sistemas ATS (Applicant Tracking Systems) tornaram-se o primeiro filtro em processos seletivos. Para garantir que seu currículo chegue aos olhos do recrutador, é essencial utilizar palavras-chave presentes na descrição da vaga. Evite colunas, tabelas e gráficos complexos no documento. Prefira fontes limpas e salvação em formato PDF legível por máquina."
    },
    {
        "id": "linkedin_net",
        "topic": "Networking no LinkedIn: Como Chamar Atenção de Headhunters",
        "category": "Carreira",
        "default_summary": "Dicas práticas de posicionamento e conexões estratégicas na maior rede profissional do mundo.",
        "default_content": "Fazer networking no LinkedIn vai muito além de enviar solicitações de conexão. Produza conteúdos curtos sobre suas experiências de aprendizado, comente de forma construtiva nos posts de líderes da sua área e otimize seu título profissional com palavras-chave claras da sua especialidade, em vez de termos genéricos."
    },
    {
        "id": "portfolio_tech",
        "topic": "Otimizando seu Portfólio de Tecnologia para Triagens por IA",
        "category": "IA & Tecnologia",
        "default_summary": "Como apresentar seus projetos no GitHub e portfólios de forma atrativa para algoritmos de recrutamento.",
        "default_content": "Recrutadores modernos e robôs de triagem analisam seus repositórios públicos. Mantenha seus READMEs claros com explicações de como rodar o projeto, as tecnologias utilizadas e os desafios de arquitetura resolvidos. Isso demonstra organização e proficiência técnica real."
    },
    {
        "id": "behavior_sim",
        "topic": "Simulando Perguntas de Comportamento com Oratória por IA",
        "category": "Entrevistas",
        "default_summary": "Use treinadores virtuais para vencer o nervosismo e aperfeiçoar seu método de fala.",
        "default_content": "A simulação de oratória baseada em inteligência artificial ajuda a identificar preenchimentos de fala excessivos, como 'tipo' ou 'né', além de analisar o tempo de pausa nas respostas. Use o método STAR (Situação, Tarefa, Ação, Resultado) para estruturar suas respostas."
    },
    {
        "id": "ats_costs",
        "topic": "Como Recrutadores Usam Triagem Inteligente para Reduzir Custos",
        "category": "IA & Tecnologia",
        "default_summary": "O impacto financeiro e operacional da triagem automática na contratação corporativa.",
        "default_content": "O custo de uma contratação errada ou de uma vaga aberta por meses prejudica diretamente as margens de qualquer startup. A triagem automática reduz o tempo de triagem manual em 90%, garantindo que apenas profissionais alinhados cheguem à fase de entrevistas."
    },
    {
        "id": "global_salary",
        "topic": "O Impacto da Inteligência Artificial nos Salários Globais de TI",
        "category": "IA & Tecnologia",
        "default_summary": "Análise das tendências de remuneração para profissionais que utilizam copilotos de código.",
        "default_content": "Profissionais de tecnologia que dominam ferramentas de IA e engenharia de prompt têm alcançado salários mais altos em contratações internacionais. A eficiência na entrega de valor supera a mera velocidade de digitação de código."
    },
    {
        "id": "prompt_eng",
        "topic": "Engenharia de Prompt: Como Usar IA para Escrever Cartas de Apresentação",
        "category": "Currículo",
        "default_summary": "Aprenda a criar cartas de apresentação personalizadas e assertivas usando Inteligência Artificial.",
        "default_content": "Ao criar cartas de apresentação com IA, evite comandos genéricos. Forneça o contexto da vaga, seu currículo atual e peça uma carta focada em demonstrar compatibilidade de competências e soluções de problemas reais que você resolveu no passado."
    },
    {
        "id": "career_prod",
        "topic": "Produtividade de Carreira: Ferramentas de IA para o Dia a Dia",
        "category": "Carreira",
        "default_summary": "Melhore sua eficiência no trabalho com o auxílio de assistentes de produtividade.",
        "default_content": "Incorporar ferramentas de IA no seu cotidiano ajuda a organizar tarefas, gerar atas de reuniões automaticamente e rascunhar e-mails corporativos, liberando tempo para focar na solução de problemas complexos de engenharia."
    },
    {
        "id": "remote_global",
        "topic": "Como se Destacar em Vagas de Trabalho Remoto Internacional",
        "category": "Carreira",
        "default_summary": "O que empresas da Europa e EUA procuram ao contratar talentos na América Latina.",
        "default_content": "O trabalho remoto internacional exige alto nível de auto-gerenciamento, excelente comunicação escrita (assíncrona) e proficiência em inglês. Mostre em seu currículo suas experiências anteriores trabalhando com equipes distribuídas."
    },
    {
        "id": "rh_comms",
        "topic": "Falar com o RH: Dicas de Comunicação Pós-Candidatura",
        "category": "Entrevistas",
        "default_summary": "Como realizar o follow-up da sua candidatura de maneira educada e profissional.",
        "default_content": "Depois de se candidatar, envie uma mensagem curta e educada ao recrutador no LinkedIn expressando seu entusiasmo pela oportunidade e resumindo brevemente como suas competências agregam valor à equipe. Evite cobranças excessivas."
    },
    {
        "id": "blind_screening",
        "topic": "Triagem às Cegas: Como a IA Promove a Diversidade no Recrutamento",
        "category": "IA & Tecnologia",
        "default_summary": "Entenda como filtros algorítmicos ajudam a mitigar vieses subjetivos de seleção.",
        "default_content": "A triagem às cegadas utiliza filtros que analisam unicamente competências e qualificações técnicas, omitindo dados pessoais como idade, gênero ou universidade de origem nas etapas iniciais, estimulando um processo seletivo muito mais inclusivo."
    },
    {
        "id": "eq_interviews",
        "topic": "Inteligência Emocional em Entrevistas de Emprego Tecnológicas",
        "category": "Entrevistas",
        "default_summary": "Equilíbrio emocional e soft skills continuam sendo o grande divisor na contratação.",
        "default_content": "Dominar competências de inteligência emocional, empatia, escuta ativa e facilidade de adaptação é o que convence o painel técnico de que você é a escolha certa para a cultura interna da corporação."
    },
    {
        "id": "career_trans",
        "topic": "Guia de Transição de Carreira: Do Tradicional para o Digital com IA",
        "category": "Carreira",
        "default_summary": "Passos essenciais para migrar de área profissional usando Inteligência Artificial como mentora.",
        "default_content": "Utilize copilotos de IA para mapear quais de suas habilidades atuais são transferíveis para a nova área e receber roteiros de estudo personalizados contendo os principais conceitos a serem aprendidos."
    },
    {
        "id": "soft_skills",
        "topic": "A Importância dos Soft Skills no Mercado Dominado por Automação",
        "category": "Carreira",
        "default_summary": "Enquanto a IA codifica, os humanos se destacam pelo alinhamento e comunicação clara.",
        "default_content": "Habilidades interpessoais, liderança, resolução de conflitos e negociação não podem ser emuladas por máquinas. Invista no desenvolvimento dos seus soft skills para manter-se indispensável no mercado profissional moderno."
    },
    {
        "id": "cv_storytelling",
        "topic": "Como Criar um Currículo com Storytelling de Sucesso",
        "category": "Currículo",
        "default_summary": "Transforme sua lista de tarefas profissionais em uma narrativa envolvente de conquistas.",
        "default_content": "Seu currículo deve contar sua trajetória profissional de forma coerente. Em vez de apenas listar o que você fazia, descreva o contexto inicial, as ações tomadas e os resultados numéricos que você trouxe para os negócios anteriores."
    }
]

def slugify(text):
    text = text.lower()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'ç', 'c', text)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def get_current_slugs(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT slug FROM blog_posts")
    return {row[0] for row in cursor.fetchall() if row[0]}

def generate_post_content(db_session, topic_data):
    """
    Tenta gerar conteúdo via Gemini AI. Caso indisponível, usa fallback local
    com variações de parágrafo para garantir não-repetição.
    """
    title = topic_data["topic"]
    category = topic_data["category"]
    
    try:
        from ai_agent import get_gemini_client
        client = get_gemini_client(db_session)
        
        prompt = f"""
        Escreva um artigo de blog profissional e engajador em português do Brasil sobre o tema: "{title}".
        O foco deste artigo é Marketing de Conteúdo, Growth Hacking e SEO da nossa plataforma SaaS "VagaSync".
        A categoria do post é "{category}".
        O conteúdo deve ser rico, estruturado em markdown, com subtítulos (H2/H3), listas de dicas práticas e uma CTA (Call to Action) chamativa no final direcionando os usuários para se cadastrarem e assinarem o VagaSync Premium (para candidatos) ou VagaSync Pro (para recrutadores).
        Formate a saída exatamente em JSON com as chaves:
        "title": "título do artigo otimizado para SEO",
        "summary": "resumo chamativo de 1 linha",
        "content": "conteúdo completo do artigo em Markdown"
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text = response.text
        # Extrai JSON de blocos de código markdown se houver
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
            
        import json
        data = json.loads(text)
        return data["title"], data["summary"], data["content"]
    except Exception as e:
        print(f"Usando fallback para o tópico '{title}' devido a: {e}")
        # Fallback local enriquecido e aleatorizado
        random_intro = random.choice([
            "No cenário atual altamente dinâmico, dominar as melhores práticas profissionais faz toda a diferença.",
            "Com as constantes inovações no mercado de recrutamento, manter-se atualizado é um requisito de sobrevivência.",
            "Entender a mecânica por trás das novas tecnologias ajuda você a se posicionar no topo das escolhas dos headhunters."
        ])
        
        random_cta = random.choice([
            f"\n\n### 🚀 Dica de Growth do VagaSync\nInscreva-se no **VagaSync** hoje mesmo. Nossa Inteligência Artificial ajuda você a calibrar suas competências, melhora seu currículo e automatiza todo o processo de busca e candidatura. Conquiste sua vaga perfeita agora!",
            f"\n\n### ⚡ Comece a usar o VagaSync Pro\nSe você é recrutador, otimize seu fluxo de contratação com a nossa IA de triagem e Kanban integrado. Mude o patamar de atração de talentos da sua corporação agora!"
        ])
        
        content = f"{random_intro}\n\n{topic_data['default_content']}{random_cta}"
        return title, topic_data["default_summary"], content

def schedule_5_posts(db_session=None):
    """
    Programa 5 publicações no banco de dados para o dia atual ou subsequente,
    garantindo que não haja repetições de tópicos já existentes.
    """
    conn = sqlite3.connect("vagasync.db")
    
    try:
        existing_slugs = get_current_slugs(conn)
        available_topics = [t for t in TOPICS if slugify(t["topic"]) not in existing_slugs]
        
        if len(available_topics) < 5:
            # Se faltar tópicos novos, re-permite tópicos antigos com slugs alterados
            available_topics = list(TOPICS)
            random.shuffle(available_topics)
            
        # Seleciona 5 tópicos aleatórios sem duplicar nesta rodada
        selected_topics = random.sample(available_topics, min(5, len(available_topics)))
        
        # Horários de publicação ao longo do dia (horário atual + intervalos)
        now = datetime.now()
        intervals = [8, 11, 14, 17, 20] # horas do dia
        
        cursor = conn.cursor()
        scheduled_count = 0
        
        for i, t in enumerate(selected_topics):
            # Gera data/hora de publicação fictícia programada para o dia atual
            target_hour = intervals[i % len(intervals)]
            publish_time = datetime(now.year, now.month, now.day, target_hour, 0, 0)
            
            # Se o horário já passou hoje, agenda para amanhã
            if publish_time < now:
                publish_time += timedelta(days=1)
                
            title, summary, content = generate_post_content(db_session, t)
            slug = slugify(title)
            
            # Garante slug único adicionando sufixo numérico se colidir
            final_slug = slug
            counter = 1
            while final_slug in existing_slugs:
                final_slug = f"{slug}-{counter}"
                counter += 1
            existing_slugs.add(final_slug)
            
            # Imagem aleatória do nosso acervo do blog
            images = ["/cv_ats_optimization.png", "/gemini_interview_sim.png", "/ai_recruitment_future.png"]
            image_url = random.choice(images)
            
            cursor.execute(
                "INSERT INTO blog_posts (title, summary, content, image_url, category, slug, published_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (title, summary, content, image_url, t["category"], final_slug, publish_time.strftime("%Y-%m-%d %H:%M:%S"))
            )
            scheduled_count += 1
            print(f"[-] Programado: '{title}' para {publish_time.strftime('%Y-%m-%d %H:%M:%S')} com slug '{final_slug}'")
            
        conn.commit()
        print(f"[*] Sucesso: {scheduled_count} publicações automáticas agendadas no banco!")
        return scheduled_count
    except Exception as e:
        print("Erro ao programar posts:", e)
        return 0
    finally:
        conn.close()

if __name__ == "__main__":
    schedule_5_posts()
