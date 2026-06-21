# VagaSync IA - Project Rules & Customizations

Este documento define as regras fundamentais, hooks comportamentais e instruções do Model Context Protocol (MCP) que o agente de inteligência artificial deve seguir ao operar dentro do workspace VAGASYNC.

## 1. Project-Scoped Rules (Regras do Workspace)

1. **Stack Técnica Exclusiva**:
   - **Frontend**: Vue.js (SFC), Vanilla CSS (Sem Tailwind/Bootstrap). Cores primárias baseadas em Dark Mode (#0a0f1c), Azul (#3b82f6), Neon Cyan (#00f2fe).
   - **Backend**: Node.js com Prisma ORM e Express. Nunca alterar o código legado Python sem autorização explícita do usuário.
   - **UI/UX**: Todos os elementos devem ter aspecto premium, *glassmorphism*, bordas suaves, carrosséis de botões e *micro-animações* elegantes de hover.

2. **Segurança e Manipulação de Arquivos**:
   - Nunca utilizar comandos destrutivos.
   - Sempre documentar extensamente qualquer modificação que envolva microtransações (Stripe/Pix).

## 2. AI Hooks (Gatilhos Comportamentais)

- **`@hook:before-commit` / `before-save`**: Antes de sobrescrever o \`App.vue\`, o agente DEVE verificar se os estilos CSS inline mantêm a compatibilidade com o \`index.css\`.
- **`@hook:on-architecture-change`**: Toda vez que o banco de dados for modificado, o agente DEVE recriar as migrations usando \`npx prisma migrate dev\` ou gerar o cliente via \`npx prisma generate\`.
- **`@hook:on-user-payment-query`**: Se o usuário perguntar sobre "preços" ou "monetização", o agente deve focar na "Loja de Microtransações", recomendando valores simbólicos definidos no escopo anterior (ex: IA Avançada = R$ 9,90).

## 3. Model Context Protocol (MCP)

Este projeto prevê integrações MCP. O Agente deve estar ciente de:
- **Ferramentas de Banco de Dados**: Acesso via cliente Prisma é preferencial. Caso ativado, o agente pode invocar ferramentas MCP \`sqlite://\` para inspecionar os dados.
- **Ferramentas de Busca / ATS**: Futuras ferramentas de "Applicant Tracking" via MCP deverão cruzar os dados usando os campos \`match_score\` existentes.

3. **LGPD, Privacidade e Segurança**:
   - Sempre respeite a Lei Geral de Proteção de Dados. Exija consentimento via Banner de Cookies para rastreamento.
   - Todo dado sensível (senhas) deve ser encriptado via `bcrypt` ou equivalente no backend.
   - Aplique proteção Anti-DDoS e Anti-Hacking nas APIs usando middlewares como `helmet` e `express-rate-limit`.
   - Ofereça ferramentas aos usuários para Exportação ou Deleção de conta em conformidade com o direito ao esquecimento.
3. **LGPD, Privacidade e Segurança**:
   - Sempre respeite a Lei Geral de Proteção de Dados. Exija consentimento via Banner de Cookies para rastreamento.
   - Todo dado sensível (senhas) deve ser encriptado via `bcrypt` ou equivalente no backend.
   - Aplique proteção Anti-DDoS e Anti-Hacking nas APIs usando middlewares como `helmet` e `express-rate-limit`.
   - Ofereça ferramentas aos usuários para Exportação ou Deleção de conta em conformidade com o direito ao esquecimento.