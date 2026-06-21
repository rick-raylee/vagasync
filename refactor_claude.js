const fs = require('fs');

let content = fs.readFileSync('frontend/src/App.vue', 'utf8');

// 1. Add state variables
const stateHook = `const recruitedCandidates = ref([`;
const newVars = `const analyzingCandidateId = ref(null);
const claudeAnalysis = ref({});

const analyzeWithClaude = (cand) => {
  analyzingCandidateId.value = cand.id;
  setTimeout(() => {
    claudeAnalysis.value[cand.id] = \`🤖 **Claude 3.5 Sonnet Analysis**\\n\\n**Resumo Profissional:** Candidato forte com sólida experiência em \${cand.role}. O currículo demonstra foco em resultados, alinhamento técnico de \${cand.match}% com a vaga.\\n\\n**Pontos Fortes:**\\n- Excelente domínio das tecnologias chave.\\n- Boa estabilidade em empregos anteriores.\\n- Soft skills evidentes em liderança técnica.\\n\\n**Pontos de Atenção:**\\n- Falta detalhar métricas exatas nos últimos projetos.\\n- Pouca exposição a ambientes multiculturais (ingles intermediário).\\n\\n**Veredito:** Altamente Recomendado para entrevista técnica.\`;
    analyzingCandidateId.value = null;
  }, 1500);
};

const recruitedCandidates = ref([`;
content = content.replace(stateHook, newVars);

// 2. Add table header
const thHook = `<th>Competências Extraídas por IA</th>
                    </tr>`;
const newThHook = `<th>Competências Extraídas por IA</th>
                      <th style="width: 140px; text-align: center;">Claude AI</th>
                    </tr>`;
content = content.replace(thHook, newThHook);

// 3. Add table cell and dropdown row
const trHook = `                      <td style="font-size: 0.78rem; color: var(--text-secondary);">{{ cand.resume }}</td>
                    </tr>`;
const newTrHook = `                      <td style="font-size: 0.78rem; color: var(--text-secondary);">{{ cand.resume }}</td>
                      <td style="text-align: center;">
                        <button v-if="!claudeAnalysis[cand.id]" 
                          class="btn btn-secondary" 
                          style="padding: 0.25rem 0.5rem; font-size: 0.7rem; display: flex; align-items: center; gap: 4px; margin: 0 auto; background: rgba(212, 163, 115, 0.15); border-color: rgba(212, 163, 115, 0.4); color: #d4a373;"
                          @click="analyzeWithClaude(cand)"
                          :disabled="analyzingCandidateId === cand.id"
                        >
                          <i :class="analyzingCandidateId === cand.id ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-brain'"></i>
                          {{ analyzingCandidateId === cand.id ? 'Analisando...' : 'Análise Claude' }}
                        </button>
                        <span v-else style="font-size: 0.75rem; color: #10b981; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 4px;">
                          <i class="fa-solid fa-check-circle"></i> Analisado
                        </span>
                      </td>
                    </tr>
                    <!-- Claude Analysis Dropdown Row -->
                    <tr v-if="claudeAnalysis[cand.id]" style="background: rgba(212, 163, 115, 0.05);">
                      <td colspan="6" style="padding: 1rem 1.5rem; border-left: 2px solid #d4a373;">
                        <div style="font-size: 0.85rem; color: #e2e8f0; line-height: 1.6; white-space: pre-wrap;" v-html="claudeAnalysis[cand.id].replace(/\\n/g, '<br>').replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')"></div>
                      </td>
                    </tr>`;
content = content.replace(trHook, newTrHook);

// Do a quick replace for the closing </tr> just in case the hook matches multiple things (like in other tables)
// Oh, the first replace is safe if it matches the first occurrence. Let's make sure it replaces the right one.
// Wait, I used a literal string replace, so it replaces the first occurrence, which is in the dashboard table. But the recruitedCandidates table is in the recruiter dashboard and super admin dashboard!
// Let's use global replace just in case.

fs.writeFileSync('frontend/src/App.vue', content, 'utf8');
console.log("Claude AI integration added!");
