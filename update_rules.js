const fs = require('fs');
let content = fs.readFileSync('.agents/AGENTS.md', 'utf8');

const newRule = `
3. **LGPD, Privacidade e Segurança**:
   - Sempre respeite a Lei Geral de Proteção de Dados. Exija consentimento via Banner de Cookies para rastreamento.
   - Todo dado sensível (senhas) deve ser encriptado via \`bcrypt\` ou equivalente no backend.
   - Aplique proteção Anti-DDoS e Anti-Hacking nas APIs usando middlewares como \`helmet\` e \`express-rate-limit\`.
   - Ofereça ferramentas aos usuários para Exportação ou Deleção de conta em conformidade com o direito ao esquecimento.`;

content += newRule;

fs.writeFileSync('.agents/AGENTS.md', content, 'utf8');
console.log("AGENTS.md updated with Security Rules!");
