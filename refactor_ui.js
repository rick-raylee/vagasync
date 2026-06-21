const fs = require('fs');

let content = fs.readFileSync('frontend/src/App.vue', 'utf8');

const new_recruiter_billing = `<!-- ── Aba Recrutador Faturamento (Recrutador) ── -->
        <template v-if="activeTab === 'recruiter_billing'">
          <div style="max-width: 1000px; margin: 0 auto; padding-bottom: 3rem;">
            <div style="text-align: center; margin-bottom: 2rem;">
              <h2 style="font-size: 2rem; margin-bottom: 0.5rem;"><i class="fa-solid fa-store" style="color: var(--color-secondary);"></i> Loja de Recursos</h2>
              <p style="color: var(--text-secondary);">Potencialize seu recrutamento com microtransações acessíveis. Pague apenas pelo que usar.</p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem;">
              
              <!-- Impulsionar Vaga -->
              <div class="glass-card" style="display: flex; flex-direction: column;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                  <h3 style="margin: 0; font-size: 1.1rem;"><i class="fa-solid fa-rocket" style="color: #3b82f6;"></i> Impulsionar Vaga</h3>
                  <span style="font-weight: 800; color: #3b82f6;">R$ 2,99 <small style="font-weight: normal; font-size: 0.7rem;">/vaga</small></span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; flex: 1;">
                  Destaque sua vaga na página inicial e prioridade nas pesquisas.
                </p>
                <div style="margin-bottom: 0.5rem; font-size: 0.8rem; color: var(--color-secondary);">Créditos atuais: {{ userFeatures.impulsionar_vaga_credits }}</div>
                <button class="btn btn-primary" style="width: 100%;" @click="openCheckout('impulsionar_vaga', 'Impulsionar Vaga', 'R$ 2,99')">
                  Comprar Impulso
                </button>
              </div>

              <!-- Empresa em Destaque -->
              <div class="glass-card" style="display: flex; flex-direction: column;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                  <h3 style="margin: 0; font-size: 1.1rem;"><i class="fa-solid fa-building-circle-check" style="color: #10b981;"></i> Empresa Destaque</h3>
                  <span style="font-weight: 800; color: #10b981;">R$ 4,99 <small style="font-weight: normal; font-size: 0.7rem;">/mês</small></span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; flex: 1;">
                  Selo de destaque e maior credibilidade para sua marca empregadora.
                </p>
                <button v-if="userFeatures.empresa_destaque" class="btn btn-secondary" style="width: 100%;" disabled>Ativado</button>
                <button v-else class="btn btn-primary" style="width: 100%;" @click="openCheckout('empresa_destaque', 'Empresa em Destaque', 'R$ 4,99')">Assinar Recurso</button>
              </div>

              <!-- IA Avançada para Triagem -->
              <div class="glass-card" style="display: flex; flex-direction: column; border-color: rgba(0,242,254,0.3); position: relative; overflow: hidden;">
                <div style="position: absolute; top: 10px; right: -25px; background: var(--color-secondary); color: #000; font-size: 0.6rem; font-weight: 900; padding: 2px 30px; transform: rotate(45deg);">POPULAR</div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                  <h3 style="margin: 0; font-size: 1.1rem;"><i class="fa-solid fa-robot" style="color: var(--color-secondary);"></i> IA Avançada Triagem</h3>
                  <span style="font-weight: 800; color: var(--color-secondary);">R$ 9,90 <small style="font-weight: normal; font-size: 0.7rem;">/mês</small></span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; flex: 1;">
                  Compatibilidade entre currículo e vaga, ranking automático e sugestões inteligentes.
                </p>
                <button v-if="userFeatures.ia_triagem" class="btn btn-secondary" style="width: 100%;" disabled>Ativado</button>
                <button v-else class="btn btn-primary" style="width: 100%; background: linear-gradient(135deg, #00f2fe, #3b82f6); border: none;" @click="openCheckout('ia_triagem', 'IA Avançada Triagem', 'R$ 9,90')">Assinar Recurso</button>
              </div>

              <!-- Videoentrevistas -->
              <div class="glass-card" style="display: flex; flex-direction: column;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                  <h3 style="margin: 0; font-size: 1.1rem;"><i class="fa-solid fa-video" style="color: #f59e0b;"></i> Videoentrevistas</h3>
                  <span style="font-weight: 800; color: #f59e0b;">R$ 4,99 <small style="font-weight: normal; font-size: 0.7rem;">/mês</small></span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; flex: 1;">
                  Salas WebRTC ilimitadas, gravação opcional e histórico de entrevistas.
                </p>
                <button v-if="userFeatures.videoentrevistas" class="btn btn-secondary" style="width: 100%;" disabled>Ativado</button>
                <button v-else class="btn btn-primary" style="width: 100%;" @click="openCheckout('videoentrevistas', 'Videoentrevistas', 'R$ 4,99')">Assinar Recurso</button>
              </div>

              <!-- Relatórios Premium -->
              <div class="glass-card" style="display: flex; flex-direction: column;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                  <h3 style="margin: 0; font-size: 1.1rem;"><i class="fa-solid fa-file-pdf" style="color: #ef4444;"></i> Relatórios Premium</h3>
                  <span style="font-weight: 800; color: #ef4444;">R$ 3,99 <small style="font-weight: normal; font-size: 0.7rem;">/mês</small></span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; flex: 1;">
                  Exportação em PDF/Excel e estatísticas avançadas de conversão.
                </p>
                <button v-if="userFeatures.relatorios_premium" class="btn btn-secondary" style="width: 100%;" disabled>Ativado</button>
                <button v-else class="btn btn-primary" style="width: 100%;" @click="openCheckout('relatorios_premium', 'Relatórios Premium', 'R$ 3,99')">Assinar Recurso</button>
              </div>

              <!-- Testes Técnicos -->
              <div class="glass-card" style="display: flex; flex-direction: column;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                  <h3 style="margin: 0; font-size: 1.1rem;"><i class="fa-solid fa-clipboard-question" style="color: #8b5cf6;"></i> Testes Técnicos</h3>
                  <span style="font-weight: 800; color: #8b5cf6;">R$ 2,99 <small style="font-weight: normal; font-size: 0.7rem;">/mês</small></span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; flex: 1;">
                  Questionários personalizados e avaliações comportamentais automáticas.
                </p>
                <button v-if="userFeatures.testes_tecnicos" class="btn btn-secondary" style="width: 100%;" disabled>Ativado</button>
                <button v-else class="btn btn-primary" style="width: 100%;" @click="openCheckout('testes_tecnicos', 'Testes Técnicos', 'R$ 2,99')">Assinar Recurso</button>
              </div>

            </div>
          </div>
        </template>`;

const new_candidate_config = `<!-- ── Aba Configurações do Candidato (Monetização) ── -->
        <template v-if="activeTab === 'config'">
          <div style="max-width: 1000px; margin: 0 auto; padding-bottom: 3rem;">
            <div style="text-align: center; margin-bottom: 2rem;">
              <h2 style="font-size: 2rem; margin-bottom: 0.5rem;"><i class="fa-solid fa-store" style="color: var(--color-secondary);"></i> Loja de Recursos</h2>
              <p style="color: var(--text-secondary);">Assine apenas as ferramentas que você precisa para alavancar sua carreira.</p>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem;">
              
              <!-- Currículo em Destaque -->
              <div class="glass-card" style="display: flex; flex-direction: column;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                  <h3 style="margin: 0; font-size: 1.1rem;"><i class="fa-solid fa-star" style="color: #f59e0b;"></i> Currículo Destaque</h3>
                  <span style="font-weight: 800; color: #f59e0b;">R$ 2,99 <small style="font-weight: normal; font-size: 0.7rem;">/mês</small></span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; flex: 1;">
                  Selo de destaque e maior exposição para os recrutadores na plataforma.
                </p>
                <button v-if="userFeatures.curriculo_destaque" class="btn btn-secondary" style="width: 100%;" disabled>Ativado</button>
                <button v-else class="btn btn-primary" style="width: 100%;" @click="openCheckout('curriculo_destaque', 'Currículo em Destaque', 'R$ 2,99')">Assinar Recurso</button>
              </div>

              <!-- IA Ilimitada -->
              <div class="glass-card" style="display: flex; flex-direction: column; border-color: rgba(0,242,254,0.3); position: relative; overflow: hidden;">
                <div style="position: absolute; top: 10px; right: -25px; background: var(--color-secondary); color: #000; font-size: 0.6rem; font-weight: 900; padding: 2px 30px; transform: rotate(45deg);">POPULAR</div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                  <h3 style="margin: 0; font-size: 1.1rem;"><i class="fa-solid fa-robot" style="color: var(--color-secondary);"></i> IA Ilimitada</h3>
                  <span style="font-weight: 800; color: var(--color-secondary);">R$ 7,90 <small style="font-weight: normal; font-size: 0.7rem;">/mês</small></span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; flex: 1;">
                  Melhore seu CV, simule entrevistas, gere cartas de apresentação e obtenha dicas.
                </p>
                <button v-if="userFeatures.ia_ilimitada" class="btn btn-secondary" style="width: 100%;" disabled>Ativado</button>
                <button v-else class="btn btn-primary" style="width: 100%; background: linear-gradient(135deg, #00f2fe, #3b82f6); border: none;" @click="openCheckout('ia_ilimitada', 'IA Ilimitada', 'R$ 7,90')">Assinar Recurso</button>
              </div>

              <!-- Score de Empregabilidade -->
              <div class="glass-card" style="display: flex; flex-direction: column;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                  <h3 style="margin: 0; font-size: 1.1rem;"><i class="fa-solid fa-chart-pie" style="color: #10b981;"></i> Score Empregabilidade</h3>
                  <span style="font-weight: 800; color: #10b981;">R$ 2,99 <small style="font-weight: normal; font-size: 0.7rem;">/mês</small></span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; flex: 1;">
                  Avaliação contínua do perfil, recomendações personalizadas e evolução profissional.
                </p>
                <button v-if="userFeatures.score_empregabilidade" class="btn btn-secondary" style="width: 100%;" disabled>Ativado</button>
                <button v-else class="btn btn-primary" style="width: 100%;" @click="openCheckout('score_empregabilidade', 'Score de Empregabilidade', 'R$ 2,99')">Assinar Recurso</button>
              </div>

              <!-- Perfil Premium -->
              <div class="glass-card" style="display: flex; flex-direction: column;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                  <h3 style="margin: 0; font-size: 1.1rem;"><i class="fa-solid fa-id-badge" style="color: #8b5cf6;"></i> Perfil Premium</h3>
                  <span style="font-weight: 800; color: #8b5cf6;">R$ 4,99 <small style="font-weight: normal; font-size: 0.7rem;">/mês</small></span>
                </div>
                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem; flex: 1;">
                  Destaque nas pesquisas dos recrutadores, estatísticas de visualização do perfil e selo VIP.
                </p>
                <button v-if="userFeatures.perfil_premium" class="btn btn-secondary" style="width: 100%;" disabled>Ativado</button>
                <button v-else class="btn btn-primary" style="width: 100%;" @click="openCheckout('perfil_premium', 'Perfil Premium', 'R$ 4,99')">Assinar Recurso</button>
              </div>

            </div>
          </div>
        </template>`;

content = content.replace(/<!-- ── Aba Recrutador Faturamento \(Recrutador\) ── -->[\s\S]*?<template v-if="activeTab === 'recruiter_billing'">[\s\S]*?<\/template>/g, new_recruiter_billing);
content = content.replace(/<!-- ── Aba Configurações do Candidato ── -->[\s\S]*?<template v-if="activeTab === 'config'">[\s\S]*?<\/template>/g, new_candidate_config);

fs.writeFileSync('frontend/src/App.vue', content, 'utf8');
console.log("UI templates refactored!");
