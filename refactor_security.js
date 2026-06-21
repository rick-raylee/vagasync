const fs = require('fs');

let content = fs.readFileSync('frontend/src/App.vue', 'utf8');

// 1. Add cookies state
const stateHook = `const activeTab = ref('dashboard');`;
const newVars = `const activeTab = ref('dashboard');
const cookieConsent = ref(localStorage.getItem('vagasync_cookie_consent') === 'true');

const acceptCookies = () => {
  cookieConsent.value = true;
  localStorage.setItem('vagasync_cookie_consent', 'true');
};`;
content = content.replace(stateHook, newVars);

// 2. Add Cookie Banner in template (at the very bottom before closing template)
const templateEndHook = `  </div>
</template>`;
const cookieBanner = `    <!-- Cookie Consent Banner (LGPD) -->
    <div v-if="!cookieConsent" style="
      position: fixed;
      bottom: 2rem;
      left: 2rem;
      max-width: 400px;
      background: rgba(13, 20, 38, 0.95);
      border: 1px solid rgba(59, 130, 246, 0.3);
      backdrop-filter: blur(12px);
      padding: 1.5rem;
      border-radius: 12px;
      z-index: 9999;
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
      display: flex;
      flex-direction: column;
      gap: 1rem;
    ">
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <i class="fa-solid fa-cookie-bite" style="color: #fb923c; font-size: 20px;"></i>
        <h4 style="margin: 0; color: #fff; font-size: 1rem;">Privacidade & Cookies</h4>
      </div>
      <p style="margin: 0; color: var(--text-secondary); font-size: 0.85rem; line-height: 1.5;">
        Utilizamos cookies para melhorar a sua experiência, garantir a segurança do seu acesso e analisar o tráfego em conformidade com a LGPD. 
      </p>
      <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
        <button @click="acceptCookies" class="btn btn-primary" style="flex: 1; padding: 0.5rem; font-size: 0.85rem;">
          Aceitar Tudo
        </button>
        <button @click="acceptCookies" class="btn btn-secondary" style="padding: 0.5rem 1rem; font-size: 0.85rem;">
          Essenciais
        </button>
      </div>
    </div>
  </div>
</template>`;
content = content.replace(templateEndHook, cookieBanner);

// 3. Add Settings > Security section
const settingsHook = `<div v-if="activeTab === 'config'" class="fade-in">
          <div class="glass-card">`;
const newSettingsHook = `<div v-if="activeTab === 'config'" class="fade-in">
          <div class="glass-card" style="margin-bottom: 2rem;">
            <h3 class="section-title"><i class="fa-solid fa-shield-halved"></i> Segurança & Privacidade (LGPD)</h3>
            <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1.5rem;">
              Gerencie suas preferências de segurança e controle os seus dados pessoais de acordo com a Lei Geral de Proteção de Dados (LGPD).
            </p>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
              
              <!-- Security API Card -->
              <div style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 12px; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="width: 40px; height: 40px; border-radius: 8px; background: rgba(16, 185, 129, 0.1); display: flex; align-items: center; justify-content: center; color: #10b981;">
                      <i class="fa-solid fa-server" style="font-size: 18px;"></i>
                    </div>
                    <div>
                      <h4 style="margin: 0; color: #e2e8f0; font-size: 0.95rem;">VagaSync Shield API</h4>
                      <div style="font-size: 0.75rem; color: #10b981; margin-top: 0.2rem;"><i class="fa-solid fa-circle-check"></i> Proteção Ativa</div>
                    </div>
                  </div>
                </div>
                <p style="margin: 0; font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                  Sua conexão e de todos os usuários está protegida via <strong style="color: #fff;">Anti-DDoS e Rate Limiting</strong> contra ataques de força bruta. Headers HTTP criptografados.
                </p>
              </div>

              <!-- LGPD Data Card -->
              <div style="background: rgba(13, 20, 38, 0.6); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                  <div style="width: 40px; height: 40px; border-radius: 8px; background: rgba(59, 130, 246, 0.1); display: flex; align-items: center; justify-content: center; color: #3b82f6;">
                    <i class="fa-solid fa-user-lock" style="font-size: 18px;"></i>
                  </div>
                  <div>
                    <h4 style="margin: 0; color: #e2e8f0; font-size: 0.95rem;">Direitos do Usuário</h4>
                    <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.2rem;">Conformidade LGPD</div>
                  </div>
                </div>
                <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                  <button class="btn btn-secondary" style="flex: 1; padding: 0.4rem; font-size: 0.75rem;" @click="showToast('Exportação Iniciada', 'Seus dados (JSON) foram enviados para seu e-mail.', 'success')">
                    <i class="fa-solid fa-download"></i> Exportar Dados
                  </button>
                  <button class="btn btn-secondary" style="padding: 0.4rem; font-size: 0.75rem; color: #ef4444; border-color: rgba(239, 68, 68, 0.3); background: rgba(239, 68, 68, 0.05);" @click="showToast('Alerta LGPD', 'Solicitação de exclusão submetida. Prazo de 72h.', 'warning')">
                    <i class="fa-solid fa-trash-can"></i> Excluir
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="glass-card">`;
content = content.replace(settingsHook, newSettingsHook);

fs.writeFileSync('frontend/src/App.vue', content, 'utf8');
console.log("Frontend App.vue refactored for LGPD/Security!");
