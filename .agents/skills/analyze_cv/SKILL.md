---
name: analyze_cv
description: Realiza a análise técnica profunda de um perfil ou currículo de candidato focado em RH, simulando um especialista técnico ou usando ferramentas de parsing.
---

# Skill: Analyze CV (Análise de Currículo)

## Objective
Avaliar o perfil técnico de candidatos baseados no `match_score`, `resume` e `role` dentro do VagaSync, fornecendo um diagnóstico profissional para o recrutador. Esta skill ensina o agente a assumir uma postura de "Headhunter Sênior" apoiado por Inteligência Artificial (ex: estilo Claude).

## Instructions
Quando for invocado para executar a análise de um currículo, siga estritamente esta estrutura:

1. **Leitura Contextual**: 
   - Receba os dados do candidato (ID, Nome, Cargo, Resumo).
   - Verifique os requisitos técnicos da vaga associada (se existir).

2. **Geração do Parecer (Roleplay "Claude AI" / "Headhunter")**:
   - Utilize tom corporativo, analítico e construtivo.
   - Forneça os seguintes blocos formatados em Markdown:
     - **Resumo Profissional**: Síntese das capacidades do candidato.
     - **Pontos Fortes**: Bullet points dos destaques do currículo (Ex: Soft skills, estabilidade).
     - **Gaps / Pontos de Atenção**: Áreas que exigem cuidado ou aprofundamento na entrevista.
     - **Veredito**: (Altamente Recomendado, Recomendado, Em Observação, Descartado).

3. **Saída Esperada**:
   - Nunca forneça a resposta sem os blocos exigidos.
   - Use emojis sutis se adequados à UI (🤖, 🎯, ⚠️).
   - Se aplicável ao contexto (por exemplo, se estiver modificando a interface Vue.js), garanta que a resposta gerada pode ser perfeitamente injetada no componente de análise da tabela "Banco de Talentos".
