<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { 
  Briefcase, 
  UploadCloud, 
  Square, 
  Settings, 
  Terminal, 
  CheckCircle, 
  Clock, 
  MessageSquare, 
  AlertCircle, 
  Trash2, 
  Bell, 
  User, 
  Smartphone, 
  Sparkles, 
  Globe,
  Loader,
  Map,
  PhoneCall
} from '@lucide/vue';
import JobMap from './JobMap.vue';
import ContatoRH from './ContatoRH.vue';
import Messenger from './Messenger.vue';

const API_BASE = 'http://localhost:8000/api';

// Config state
const config = ref({
  gemini_api_key: '',
  linkedin_cookie: '',
  whatsapp_phone: '',
  whatsapp_webhook: '',
  n8n_webhook_url: '',
  telegram_token: '',
  telegram_chat_id: '',
  smtp_email: '',
  smtp_password: '',
  smtp_host: 'smtp.gmail.com',
  smtp_port: '465',
  notify_email: '',
  generic_webhook_url: '',
  google_maps_api_key: '',
  keywords: 'Desenvolvedor React, Python Developer, Full Stack',
  resume_text: '',
  search_location: 'Brasil',
  search_scope: 'pais',
  enable_web_search: 'true'
});

const notifyChannels = ref(null);
const testingNotify = ref(false);

const loadNotifyChannels = async () => {
  try {
    const res = await fetch(`${API_BASE}/notify/channels`);
    if (res.ok) notifyChannels.value = await res.json();
  } catch {}
};

const testNotification = async () => {
  testingNotify.value = true;
  try {
    const res = await fetch(`${API_BASE}/notify/test`, { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      const ok = Object.entries(data.channels).filter(([,v]) => v.includes('✅')).map(([k]) => k);
      const fail = Object.entries(data.channels).filter(([,v]) => v.includes('❌')).map(([k]) => k);
      showToast('Teste Enviado!', `✅ ${ok.join(', ') || 'nenhum canal'} ${fail.length ? '| ❌ ' + fail.join(', ') : ''}`, 'success');
      loadNotifyChannels();
    }
  } catch { showToast('Erro', 'Falha ao testar notificações.', 'error'); }
  testingNotify.value = false;
};

// UI States
const jobs = ref([]);
const logs = ref([]);
const isAutomationRunning = ref(false);
const liveStatus = ref(null);
const activeSources = ref([]); // fontes de busca ativas
const uploadProgress = ref(null);
const resumeAnalysis = ref(null);
const toast = ref(null);
const activeTab = ref('dashboard');
const cookieConsent = ref(localStorage.getItem('vagasync_cookie_consent') === 'true');

const acceptCookies = () => {
  cookieConsent.value = true;
  localStorage.setItem('vagasync_cookie_consent', 'true');
};
const saveSuccess = ref(false);
const isDragActive = ref(false);
const showNotifications = ref(false);
const activeJobIdFromNotification = ref(null);

const fileInputRef = ref(null);
const terminalEndRef = ref(null);

const searchScopeText = {
  cidade: {
    label: 'cidade',
    placeholder: 'Ex: São Paulo, SP',
    help: 'A busca fica concentrada na cidade informada.'
  },
  estado: {
    label: 'estado',
    placeholder: 'Ex: São Paulo, Rio de Janeiro ou Paraná',
    help: 'A busca considera vagas em todo o estado informado.'
  },
  pais: {
    label: 'país',
    placeholder: 'Ex: Brasil, Portugal ou Estados Unidos',
    help: 'A busca considera vagas no país informado.'
  },
  internacional: {
    label: 'internacional',
    placeholder: 'Ex: Remoto mundial, Europa ou América Latina',
    help: 'A busca considera vagas fora do Brasil ou remotas internacionais.'
  }
};

const activeSearchScope = computed(() => {
  return searchScopeText[config.value.search_scope] || searchScopeText.pais;
});

// Auth states
const isLoggedIn = ref(localStorage.getItem('vagasync_logged') === 'true');
const authMode = ref('login'); // 'login' or 'signup'
const authForm = ref({ name: '', email: '', password: '', linkLinkedIn: true });

const handleLogin = (e) => {
  e.preventDefault();
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(authForm.value.email)) {
    showToast('E-mail Inválido', 'Por favor, insira um e-mail no formato correto (exemplo@dominio.com).', 'error');
    return;
  }
  localStorage.setItem('vagasync_logged', 'true');
  isLoggedIn.value = true;
  showToast('Acesso Autorizado', 'Bem-vindo de volta ao Vaga Sync!', 'success');
};

const handleSignup = (e) => {
  e.preventDefault();
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(authForm.value.email)) {
    showToast('E-mail Inválido', 'Por favor, insira um e-mail no formato correto (exemplo@dominio.com).', 'error');
    return;
  }
  localStorage.setItem('vagasync_logged', 'true');
  isLoggedIn.value = true;
  showToast('Conta Criada!', 'Seu perfil foi sincronizado com sucesso.', 'success');
};

const handleLogout = () => {
  localStorage.removeItem('vagasync_logged');
  isLoggedIn.value = false;
  showToast('Sessão Encerrada', 'Até breve!', 'info');
};

// SSE real-time logs
let eventSource = null;
let pollInterval = null;

onMounted(() => {
  fetchConfig();
  fetchJobs();
  checkAutomationStatus();

  // Setup Server-Sent Events for real-time logs
  eventSource = new EventSource('http://localhost:8000/api/automation/events');
  eventSource.onmessage = (event) => {
    try {
      const logData = JSON.parse(event.data);
      const exists = logs.value.some(l => l.message === logData.message && l.timestamp === logData.timestamp);
      if (!exists) {
        logs.value.push(logData);
        if (logs.value.length > 100) logs.value.shift();
      }

      // Update live status with latest meaningful message
      liveStatus.value = { message: logData.message, level: logData.level, timestamp: logData.timestamp };
      
      // Auto scroll terminal
      if (terminalEndRef.value) {
        terminalEndRef.value.scrollIntoView({ behavior: 'smooth' });
      }

      // Trigger toast/sound por eventos importantes
      if (logData.message.includes('Candidatura registrada') || logData.message.includes('Easy Apply enviado') || logData.message.includes('candidatado')) {
        showToast('✅ Candidatura Registrada!', logData.message, 'success');
      } else if (logData.message.includes('CONTATO RECEBIDO') || logData.message.includes('respondeu')) {
        showToast('📞 Contato de Recrutador!', logData.message, 'success');
        playNotificationSound();
      } else if (logData.message.includes('Gemini Web') && logData.message.includes('vagas encontradas')) {
        showToast('🌐 Gemini Web', logData.message, 'info');
      } else if (logData.message.includes('Gemini LinkedIn') && logData.message.includes('vagas')) {
        showToast('💼 Gemini LinkedIn', logData.message, 'info');
      }
    } catch (err) {
      console.error("SSE parse error", err);
    }
  };

  // Request browser notification permission
  if (Notification.permission === 'default') {
    Notification.requestPermission();
  }

  // Poll automation status periodically
  pollInterval = setInterval(() => {
    checkAutomationStatus();
    fetchJobs();
  }, 5000);
});

onBeforeUnmount(() => {
  if (eventSource) {
    eventSource.close();
  }
  if (pollInterval) {
    clearInterval(pollInterval);
  }
});

const fetchConfig = async () => {
  try {
    const res = await fetch(`${API_BASE}/config`);
    if (res.ok) {
      const data = await res.json();
      config.value = data;
    }
  } catch (e) {
    console.error("Error loading config", e);
  }
};

const fetchJobs = async () => {
  try {
    const res = await fetch(`${API_BASE}/jobs`);
    if (res.ok) {
      const data = await res.json();
      jobs.value = data;
    }
  } catch (e) {
    console.error("Error loading jobs", e);
  }
};

const checkAutomationStatus = async () => {
  try {
    const res = await fetch(`${API_BASE}/automation/status`);
    if (res.ok) {
      const data = await res.json();
      if (isAutomationRunning.value && !data.is_running) {
        liveStatus.value = null;
      }
      isAutomationRunning.value = data.is_running;
      // Atualiza fontes de busca ativas
      if (data.active_sources) activeSources.value = data.active_sources;
    }
  } catch (e) {
    console.error("Error loading status", e);
  }
};

const saveConfig = async (e) => {
  if (e) e.preventDefault();
  saveSuccess.value = false;
  try {
    const res = await fetch(`${API_BASE}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config.value)
    });
    if (res.ok) {
      saveSuccess.value = true;
      setTimeout(() => saveSuccess.value = false, 3000);
      showToast('Configurações salvas', 'As novas credenciais e chaves foram atualizadas.', 'success');
    }
  } catch (e) {
    showToast('Erro ao salvar', 'Não foi possível salvar as configurações.', 'error');
  }
};

const runAutomation = async () => {
  if (isAutomationRunning.value) return;
  try {
    const res = await fetch(`${API_BASE}/automation/run`, { method: 'POST' });
    if (res.ok) {
      isAutomationRunning.value = true;
      liveStatus.value = { message: '🤖 Agente iniciado — Gemini buscando vagas na web e LinkedIn...', level: 'info', timestamp: new Date().toISOString() };
      showToast('Automação Iniciada', 'O agente Gemini está buscando vagas nos principais portais e ATS.', 'success');
    } else {
      const err = await res.json();
      showToast('Não foi possível iniciar', err.detail || 'Verifique se seu currículo está cadastrado.', 'error');
    }
  } catch (e) {
    showToast('Erro', 'Falha ao conectar ao servidor.', 'error');
  }
};

const stopAutomation = async () => {
  try {
    await fetch(`${API_BASE}/automation/stop`, { method: 'POST' });
    isAutomationRunning.value = false;
    liveStatus.value = null;
    showToast('Agente Parado', 'A automação foi interrompida manualmente.', 'info');
  } catch (e) {
    // Optimistically stop UI even if request fails
    isAutomationRunning.value = false;
    liveStatus.value = null;
  }
};

const handleResumeUpload = async (file) => {
  if (!file) return;
  uploadProgress.value = 'uploading';
  
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    uploadProgress.value = 'parsing';
    const res = await fetch(`${API_BASE}/resume/upload`, {
      method: 'POST',
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      uploadProgress.value = 'done';
      resumeAnalysis.value = data.analysis;
      config.value.resume_text = data.resume_text;
      showToast('Currículo Importado!', 'A IA analisou suas competências e atualizou seu perfil.', 'success');
    } else {
      uploadProgress.value = null;
      showToast('Erro de processamento', 'Falha ao analisar o currículo.', 'error');
    }
  } catch (e) {
    uploadProgress.value = null;
    showToast('Erro', 'Falha ao conectar para upload.', 'error');
  }
};

const deleteJob = async (jobId) => {
  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`, { method: 'DELETE' });
    if (res.ok) {
      jobs.value = jobs.value.filter(j => j.id !== jobId);
      showToast('Vaga Removida', 'Vaga excluída com sucesso.', 'info');
    }
  } catch (e) {
    console.error(e);
  }
};

const showToast = (title, message, type = 'info') => {
  toast.value = { title, message, type };
  setTimeout(() => toast.value = null, 5000);

  // Send push notification if browser supports it
  if (Notification.permission === 'granted') {
    new Notification(title, { body: message });
  }
};

const playNotificationSound = () => {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const now = ctx.currentTime;
    const osc1 = ctx.createOscillator();
    const osc2 = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(587.33, now); // D5
    osc1.frequency.exponentialRampToValueAtTime(880, now + 0.15); // A5
    
    osc2.type = 'triangle';
    osc2.frequency.setValueAtTime(440, now); // A4
    osc2.frequency.exponentialRampToValueAtTime(1174.66, now + 0.15); // D6

    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + 0.6);
    
    osc1.connect(gain);
    osc2.connect(gain);
    gain.connect(ctx.destination);
    
    osc1.start(now);
    osc2.start(now);
    osc1.stop(now + 0.6);
    osc2.stop(now + 0.6);
  } catch (e) {
    console.error("Audio synth error", e);
  }
};

// Drag and drop handlers
const handleDrag = (e) => {
  e.preventDefault();
  e.stopPropagation();
  if (e.type === "dragenter" || e.type === "dragover") {
    isDragActive.value = true;
  } else if (e.type === "dragleave") {
    isDragActive.value = false;
  }
};

const handleDrop = (e) => {
  e.preventDefault();
  e.stopPropagation();
  isDragActive.value = false;
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    handleResumeUpload(e.dataTransfer.files[0]);
  }
};

// Stats helper
const stats = computed(() => {
  const safeList = Array.isArray(jobs.value) ? jobs.value : [];
  return {
    total: safeList.length,
    applied: safeList.filter(j => j.status === 'applied' || j.status === 'contacted').length,
    averageMatch: safeList.length > 0 
      ? Math.round(safeList.reduce((acc, curr) => acc + (curr.match_score || 0), 0) / safeList.length) 
      : 0,
    contacted: safeList.filter(j => j.status === 'contacted').length
  };
});

const contactedJobs = computed(() => {
  const safeList = Array.isArray(jobs.value) ? jobs.value : [];
  return safeList.filter(j => j.status === 'contacted');
});

const triggerNotificationChat = (jobId) => {
  activeJobIdFromNotification.value = jobId;
  activeTab.value = 'messenger';
  showNotifications.value = false;
};

const saveResumeText = async () => {
  uploadProgress.value = 'parsing';
  try {
    const res = await fetch(`${API_BASE}/resume/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ text: config.value.resume_text })
    });
    if (res.ok) {
      const data = await res.json();
      uploadProgress.value = 'done';
      resumeAnalysis.value = data.analysis;
      showToast('Currículo Atualizado', 'Seu currículo em texto foi salvo com sucesso.', 'success');
    }
  } catch (e) {
    uploadProgress.value = null;
  }
};

</script>

<template>
  <div class="app-container" :class="{ 'auth-wrapper': !isLoggedIn }">
    <!-- Toast popup -->
    <div v-if="toast" :class="['toast-notification', { success: toast.type === 'success' }]">
      <div class="toast-content">
        <h4>{{ toast.title }}</h4>
        <p>{{ toast.message }}</p>
      </div>
    </div>

    <!-- Login/Signup Screen -->
    <template v-if="!isLoggedIn">
      <div class="auth-grid">
        <!-- Left panel: Presentation -->
        <div class="auth-left glass-card">
          <div class="logo-container" style="margin-bottom: 1.5rem;">
            <img src="/vagasync_logo.png" alt="Vaga Sync Logo" class="logo-icon-img" style="width: 56px; height: 56px;" />
            <span class="logo-text" style="font-size: 2.5rem;">Vaga Sync</span>
          </div>
          <p style="color: var(--text-secondary); font-size: 1.05rem; margin-bottom: 1.5rem; line-height: 1.6;">
            Seu copiloto inteligente de carreira. Sincronize perfis, analise compatibilidade de vagas por IA e automatize candidaturas em lote.
          </p>
          
          <img 
            src="/vagasync_banner.png"
            alt="Vaga Sync AI Banner" 
            class="banner-img" 
          />

          <div class="features-intro">
            <h3 style="margin: 1.5rem 0 1rem 0; color: var(--color-secondary);">Como Funciona:</h3>
            <div class="step-item">
              <span class="step-number">1</span>
              <div>
                <h4>Vincule seu LinkedIn</h4>
                <p>Conecte seu perfil para puxar e analisar vagas compatíveis diretamente com suas preferências.</p>
              </div>
            </div>
            <div class="step-item">
              <span class="step-number">2</span>
              <div>
                <h4>Importação e Mapeamento IA</h4>
                <p>Envie seu currículo. A IA do Gemini mapeia suas competências técnicas e alinha seu perfil.</p>
              </div>
            </div>
            <div class="step-item">
              <span class="step-number">3</span>
              <div>
                <h4>Agente de Candidatura</h4>
                <p>O robô Playwright realiza candidaturas simplificadas automáticas em segundo plano.</p>
              </div>
            </div>
            <div class="step-item">
              <span class="step-number">4</span>
              <div>
                <h4>Follow-up de RH & WhatsApp</h4>
                <p>Acompanhamento inteligente de análise do RH e alertas instantâneos no seu celular.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right panel: Login/Signup Card -->
        <div class="auth-right">
          <div class="glass-card auth-form-card">
            <form v-if="authMode === 'login'" @submit="handleLogin">
              <h2 style="margin-bottom: 0.5rem; font-size: 1.75rem;">Acesse sua Conta</h2>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1.5rem;">
                Faça login para gerenciar suas candidaturas automatizadas.
              </p>

              <button 
                type="button" 
                class="btn social-btn-linkedin"
                @click="
                  localStorage.setItem('vagasync_logged', 'true');
                  isLoggedIn = true;
                  showToast('Login LinkedIn', 'Sessão iniciada via LinkedIn com sucesso!', 'success');
                "
              >
                <Globe :size="18" /> Entrar com LinkedIn
              </button>

              <div class="divider-or">Ou use e-mail</div>

              <div class="form-group">
                <label>E-mail Corporativo ou Pessoal</label>
                <input 
                  type="email" 
                  required
                  class="form-input" 
                  placeholder="exemplo@vaga-sync.com" 
                  v-model="authForm.email"
                />
              </div>

              <div class="form-group">
                <label>Senha de Acesso</label>
                <input 
                  type="password" 
                  required
                  class="form-input" 
                  placeholder="••••••••" 
                  v-model="authForm.password"
                />
              </div>

              <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 1.25rem;">
                Entrar no Dashboard
              </button>

              <p style="text-align: center; font-size: 0.85rem; margin-top: 1.5rem; color: var(--text-secondary);">
                Não tem conta? 
                <span 
                  style="color: var(--color-secondary); cursor: pointer; font-weight: 600;"
                  @click="authMode = 'signup'"
                >
                  Criar uma conta e vincular LinkedIn
                </span>
              </p>
            </form>

            <form v-else @submit="handleSignup">
              <h2 style="margin-bottom: 0.5rem; font-size: 1.75rem;">Criar Conta</h2>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1.5rem;">
                Comece a impulsionar sua carreira com inteligência artificial.
              </p>

              <div class="form-group">
                <label>Nome Completo</label>
                <input 
                  type="text" 
                  required
                  class="form-input" 
                  placeholder="Ricardo Santos" 
                  v-model="authForm.name"
                />
              </div>

              <div class="form-group">
                <label>E-mail</label>
                <input 
                  type="email" 
                  required
                  class="form-input" 
                  placeholder="seu.email@provedor.com" 
                  v-model="authForm.email"
                />
              </div>

              <div class="form-group">
                <label>Senha</label>
                <input 
                  type="password" 
                  required
                  class="form-input" 
                  placeholder="Mínimo 6 caracteres" 
                  v-model="authForm.password"
                />
              </div>

              <div class="form-group" style="display: flex; align-items: center; gap: 0.5rem; margin-top: 1rem; margin-bottom: 1.5rem;">
                <input 
                  type="checkbox" 
                  id="linkedin_chk" 
                  v-model="authForm.linkLinkedIn"
                  style="cursor: pointer; width: 16px; height: 16px;"
                />
                <label htmlFor="linkedin_chk" style="margin: 0; cursor: pointer; font-size: 0.85rem; color: var(--text-secondary);">
                  Vincular conta do LinkedIn para puxar melhor as vagas (Recomendado)
                </label>
              </div>

              <button type="submit" class="btn btn-primary" style="width: 100%;">
                Criar Conta & Sincronizar
              </button>

              <p style="text-align: center; font-size: 0.85rem; margin-top: 1.5rem; color: var(--text-secondary);">
                Já possui conta? 
                <span 
                  style="color: var(--color-secondary); cursor: pointer; font-weight: 600;"
                  @click="authMode = 'login'"
                >
                  Acessar conta
                </span>
              </p>
            </form>
          </div>
        </div>
      </div>
      <footer class="footer-bar">
        <p>© 2026 Vaga Sync. Todos os direitos reservados. • Conexão Segura SSL • Gemini Core Engine • n8n Connected</p>
      </footer>
    </template>

    <!-- Main Logged In Application Dashboard -->
    <template v-else>
      <!-- Unified Navigation Bar -->
      <header class="header">
        <div class="logo-container">
          <img src="/vagasync_logo.png" alt="Vaga Sync Logo" class="logo-icon-img" />
          <span class="logo-text">Vaga Sync</span>
        </div>

        <nav class="nav-menu">
          <button 
            :class="['nav-link-btn', { active: activeTab === 'dashboard' }]"
            @click="activeTab = 'dashboard'"
          >
            <Briefcase :size="15" /> Painel Principal
          </button>
          
          <button 
            :class="['nav-link-btn', { active: activeTab === 'map' }]"
            @click="activeTab = 'map'"
            style="position: relative;"
          >
            <Map :size="15" /> Mapa de Vagas
            <span v-if="jobs.length > 0" style="
              position: absolute; top: -4px; right: -4px;
              min-width: 16px; height: 16px; border-radius: 8px;
              background: linear-gradient(135deg, #3b82f6, #00f2fe);
              color: white; font-size: 0.62rem; font-weight: 700;
              display: flex; align-items: center; justify-content: center;
              padding: 0 3px; line-height: 1;
            ">{{ jobs.length }}</span>
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'contato' }]"
            @click="activeTab = 'contato'"
            style="position: relative;"
          >
            <PhoneCall :size="15" /> Contato com RH
            <span v-if="stats.applied > 0" style="
              position: absolute; top: -4px; right: -4px;
              min-width: 16px; height: 16px; border-radius: 8px;
              background: linear-gradient(135deg, #10b981, #00f2fe);
              color: white; font-size: 0.62rem; font-weight: 700;
              display: flex; align-items: center; justify-content: center;
              padding: 0 3px; line-height: 1;
            ">{{ stats.applied }}</span>
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'messenger' }]"
            @click="activeTab = 'messenger'"
            style="position: relative;"
          >
            <MessageSquare :size="15" /> Mensagens
            <span v-if="contactedJobs.length > 0" style="
              position: absolute; top: -4px; right: -4px;
              min-width: 16px; height: 16px; border-radius: 8px;
              background: linear-gradient(135deg, #00f2fe, #3b82f6);
              color: white; font-size: 0.62rem; font-weight: 700;
              display: flex; align-items: center; justify-content: center;
              padding: 0 3px; line-height: 1;
            ">{{ contactedJobs.length }}</span>
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'resume' }]"
            @click="activeTab = 'resume'"
          >
            <User :size="15" /> Currículo & Perfil IA
          </button>
          
          <button 
            :class="['nav-link-btn', { active: activeTab === 'config' }]"
            @click="activeTab = 'config'"
          >
            <Settings :size="15" /> Configurações
          </button>
        </nav>
        
        <div class="header-actions" style="display: flex; gap: 0.75rem; align-items: center; position: relative;">
          <!-- Notification Bell Dropdown -->
          <div style="position: relative;">
            <button
              @click="showNotifications = !showNotifications"
              class="btn btn-secondary"
              style="
                padding: 0.5rem;
                border-radius: 50%;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
              "
              :style="{
                borderColor: contactedJobs.length > 0 ? 'rgba(0, 242, 254, 0.4)' : undefined,
                background: contactedJobs.length > 0 ? 'rgba(0, 242, 254, 0.05)' : undefined
              }"
              title="Notificações de Retorno de RH"
            >
              <Bell :size="16" />
              <span v-if="contactedJobs.length > 0" style="
                position: absolute; top: -2px; right: -2px;
                width: 15px; height: 15px; border-radius: 50%;
                background: linear-gradient(135deg, #ef4444, #f59e0b);
                color: white; font-size: 0.6rem; font-weight: 800;
                display: flex; align-items: center; justify-content: center;
                box-shadow: 0 0 5px rgba(239, 68, 68, 0.5);
              ">
                {{ contactedJobs.length }}
              </span>
            </button>
            
            <template v-if="showNotifications">
              <div 
                style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 998;"
                @click="showNotifications = false"
              />
              <div class="glass-card" style="
                position: absolute;
                top: 120%;
                right: 0;
                width: 360px;
                max-height: 400px;
                overflow-y: auto;
                z-index: 999;
                padding: 1rem;
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
                box-shadow: 0 10px 25px rgba(0,0,0,0.5);
                border: 1px solid var(--border-color);
                background: rgba(13, 20, 38, 0.98);
                backdrop-filter: blur(12px);
                border-radius: 10px;
              ">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.5rem; margin-bottom: 0.25rem;">
                  <span style="font-weight: 800; font-size: 0.85rem; color: #00f2fe; display: flex; align-items: center; gap: 4px;">
                    <Bell :size="13" /> Retornos de RH ({{ contactedJobs.length }})
                  </span>
                  <button 
                    style="background: transparent; border: none; color: var(--text-muted); font-size: 0.72rem; cursor: pointer;"
                    @click="showNotifications = false"
                  >
                    Fechar
                  </button>
                </div>
                
                <div v-if="contactedJobs.length === 0" style="text-align: center; padding: 1.5rem 0; color: var(--text-secondary); font-size: 0.8rem;">
                  Nenhum retorno de RH no momento.
                </div>
                
                <div v-else style="display: flex; flex-direction: column; gap: 0.6rem;">
                  <div v-for="job in contactedJobs" :key="job.id" style="
                    padding: 0.75rem;
                    background: rgba(255,255,255,0.02);
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    display: flex;
                    flex-direction: column;
                    gap: 0.3rem;
                  ">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                      <strong style="font-size: 0.8rem; color: #ffffff;">{{ job.company }}</strong>
                      <span style="font-size: 0.68rem; color: var(--color-success); font-weight: 600;">RH Retornou</span>
                    </div>
                    <span style="font-size: 0.75rem; color: var(--text-secondary);">{{ job.title }}</span>
                    
                    <div style="
                      font-size: 0.7rem;
                      color: var(--text-secondary);
                      background: rgba(0,0,0,0.25);
                      padding: 0.4rem 0.5rem;
                      border-radius: 4px;
                      margin-top: 2px;
                      display: flex;
                      flex-direction: column;
                      gap: 3px;
                    ">
                      <div v-if="job.recruiter_name">👤 <strong>Recrutador:</strong> {{ job.recruiter_name }}</div>
                      <div v-if="job.recruiter_phone">📞 <strong>Telefone:</strong> {{ job.recruiter_phone }}</div>
                      <div v-if="job.recruiter_contact">✉️ <strong>Email:</strong> {{ job.recruiter_contact }}</div>
                      <div v-if="job.company_address">📍 <strong>Endereço:</strong> {{ job.company_address }}</div>
                    </div>
                    
                    <div style="display: flex; gap: 0.4rem; margin-top: 0.3rem;">
                      <button
                        class="btn btn-primary"
                        style="padding: 0.3rem 0.5rem; font-size: 0.7rem; flex: 1;"
                        @click="triggerNotificationChat(job.id)"
                      >
                        Conversar no Chat
                      </button>
                      <a
                        v-if="job.company_address"
                        :href="`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(job.company_address)}`"
                        target="_blank"
                        rel="noopener noreferrer"
                        class="btn btn-secondary"
                        style="padding: 0.3rem 0.5rem; font-size: 0.7rem; text-decoration: none; display: flex; align-items: center; justify-content: center;"
                      >
                        Maps
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <button 
            v-if="isAutomationRunning"
            class="agent-badge btn-secondary running"
            @click="stopAutomation"
            title="Clique para parar o agente"
          >
            <span class="pulse-dot"></span>
            Agente Executando — Parar
          </button>
          
          <button 
            v-else
            class="agent-badge btn-secondary"
            @click="runAutomation"
          >
            <span class="pulse-dot" style="animation-play-state: paused; opacity: 0.4;"></span>
            Iniciar Agente
          </button>
          
          <button 
            class="btn btn-secondary" 
            style="padding: 0.5rem 1rem; font-size: 0.8rem; border: 1px solid rgba(239, 68, 68, 0.2); color: var(--color-error);"
            @click="handleLogout"
          >
            Sair
          </button>
        </div>
      </header>

      <!-- Main Content Tabs -->
      <main style="padding-bottom: 2rem;">
        <template v-if="activeTab === 'dashboard'">
          <!-- Agent Live Status Banner -->
          <div v-if="isAutomationRunning" class="agent-status-bar">
            <div class="agent-status-left">
              <div class="agent-spinner">
                <span class="spinner-ring"></span>
                <span class="spinner-ring spinner-ring-2"></span>
              </div>
              <div class="agent-status-info">
                <div class="agent-status-title">
                  <span class="agent-status-dot"></span>
                  🤖 Agente Vaga Sync — Varredura em andamento
                  <!-- Badges das fontes ativas -->
                  <span v-if="activeSources.length > 0" style="display: flex; gap: 0.35rem; margin-left: 0.75rem; flex-wrap: wrap;">
                    <span 
                      v-for="(src, i) in activeSources" 
                      :key="i" 
                      :style="{
                        fontSize: '0.65rem', padding: '2px 7px', borderRadius: '20px',
                        background: src.includes('🌐') ? 'rgba(16,185,129,0.15)' : src.includes('💼') ? 'rgba(59,130,246,0.15)' : 'rgba(168,85,247,0.15)',
                        border: src.includes('🌐') ? '1px solid rgba(16,185,129,0.3)' : src.includes('💼') ? '1px solid rgba(59,130,246,0.3)' : '1px solid rgba(168,85,247,0.3)',
                        color: src.includes('🌐') ? '#34d399' : src.includes('💼') ? '#60a5fa' : '#c084fc',
                        fontWeight: 700, lineHeight: 1, display: 'inline-flex', alignItems: 'center'
                      }"
                    >
                      {{ src }}
                    </span>
                  </span>
                </div>
                <div class="agent-status-message">
                  {{ liveStatus ? liveStatus.message : 'Iniciando varredura de vagas...' }}
                </div>
              </div>
            </div>
            <div class="agent-status-right">
              <span class="agent-status-time">
                {{ liveStatus ? new Date(liveStatus.timestamp).toLocaleTimeString() : '' }}
              </span>
              <button 
                class="agent-stop-btn"
                @click="stopAutomation"
                title="Parar agente"
              >
                <Square :size="12" />
                Parar
              </button>
            </div>
          </div>

          <!-- Stats Metrics Row -->
          <div class="stats-row">
            <div class="glass-card stat-card">
              <div class="stat-icon"><Briefcase :size="22" /></div>
              <div>
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">Vagas Encontradas</div>
              </div>
            </div>
            <div class="glass-card stat-card">
              <div class="stat-icon"><CheckCircle :size="22" style="color: #a855f7;" /></div>
              <div>
                <div class="stat-value">{{ stats.applied }}</div>
                <div class="stat-label">Candidaturas</div>
              </div>
            </div>
            <div class="glass-card stat-card">
              <div class="stat-icon"><Sparkles :size="22" style="color: #00f2fe;" /></div>
              <div>
                <div class="stat-value">{{ stats.averageMatch }}%</div>
                <div class="stat-label">Match Médio IA</div>
              </div>
            </div>
            <div class="glass-card stat-card">
              <div class="stat-icon"><MessageSquare :size="22" style="color: #10b981;" /></div>
              <div>
                <div class="stat-value">{{ stats.contacted }}</div>
                <div class="stat-label">Retornos de RH</div>
              </div>
            </div>
          </div>

          <!-- Main Dashboard Panel -->
          <div class="dashboard-grid">
            <!-- Left Col: Jobs Table -->
            <div class="glass-card">
              <h2 class="section-title">
                <Briefcase :size="20" /> Vagas e Candidaturas Ativas
              </h2>
              
              <div v-if="jobs.length === 0" style="text-align: center; padding: 3rem 0; color: var(--text-secondary);">
                <Briefcase :size="40" style="opacity: 0.2; margin-bottom: 1rem;" />
                <p>Nenhuma vaga processada ainda pelo Vaga Sync.</p>
                <p style="font-size: 0.8rem; margin-top: 0.5rem;">Clique em "Iniciar Agente" acima ou configure seu currículo para iniciar.</p>
              </div>
              
              <div v-else class="jobs-table-wrapper">
                <table class="jobs-table">
                  <thead>
                    <tr>
                      <th>Vaga / Empresa</th>
                      <th>Match</th>
                      <th>Status</th>
                      <th>Follow-up</th>
                      <th>Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="job in jobs" :key="job.id">
                      <td>
                        <div class="job-name-cell">
                          <a 
                            :href="job.link" 
                            target="_blank" 
                            rel="noopener noreferrer"
                            style="color: var(--text-primary); font-weight: 600; text-decoration: none;"
                          >
                            {{ job.title }}
                          </a>
                          <span class="job-company">
                            {{ job.company }} • {{ job.location || 'Sem local' }} • 
                            <span :class="['source-badge', job.source === 'linkedin' ? 'linkedin' : 'web']">
                              {{ job.source === 'linkedin' ? 'LinkedIn' : `Gemini ${job.source || 'Web'}` }}
                            </span>
                          </span>
                        </div>
                      </td>
                      <td>
                        <span :class="['match-badge', job.match_score >= 80 ? 'match-high' : job.match_score >= 65 ? 'match-med' : 'match-low']">
                          {{ job.match_score }}%
                        </span>
                      </td>
                      <td>
                        <span :class="['status-tag', `status-${job.status}`]">
                          {{ job.status === 'found' ? 'Encontrada' : '' }}
                          {{ job.status === 'applying' ? 'Candidatando' : '' }}
                          {{ job.status === 'applied' ? 'Inscrita' : '' }}
                          {{ job.status === 'contacted' ? 'Retorno/Contatada' : '' }}
                          {{ job.status === 'failed' ? 'Falhou' : '' }}
                        </span>
                      </td>
                      <td>
                        <span style="font-size: 0.8rem; color: var(--text-secondary); display: flex; align-items: center; gap: 0.25rem;">
                          <Clock :size="12" />
                          <span v-if="job.status === 'contacted'" style="color: var(--color-success); font-weight: 600;">RH Retornou ✓</span>
                          <span v-else-if="job.followup_sent" style="color: var(--color-warning);">Follow-up Enviado</span>
                          <span v-else>Aguardando RH</span>
                        </span>
                      </td>
                      <td>
                        <div style="display: flex; gap: 0.5rem;">
                          <button 
                            class="btn btn-secondary" 
                            style="padding: 0.25rem; min-width: 30px; color: var(--color-error);"
                            @click="deleteJob(job.id)"
                          >
                            <Trash2 :size="14" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Right Col: Terminal Logs -->
            <div class="glass-card terminal-panel" style="display: flex; flex-direction: column;">
              <div class="terminal-header">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                  <Terminal :size="16" style="color: var(--color-secondary);" />
                  <span style="font-size: 0.85rem; font-weight: 600; color: var(--text-secondary);">Console do Agente Sync</span>
                </div>
                <div class="terminal-dot-group">
                  <span class="terminal-dot" style="background-color: #ef4444;"></span>
                  <span class="terminal-dot" style="background-color: #f59e0b;"></span>
                  <span class="terminal-dot" style="background-color: #10b981;"></span>
                </div>
              </div>

              <div class="terminal-logs-container">
                <div v-if="logs.length === 0" style="color: var(--text-muted); font-size: 0.8rem; padding: 1rem 0;">
                  Aguardando logs de atividade do backend...
                </div>
                
                <div v-else v-for="(log, i) in logs" :key="i" class="log-line">
                  <span class="log-timestamp">[{{ new Date(log.timestamp).toLocaleTimeString() }}]</span>
                  <span :class="`log-level-${log.level}`">{{ log.message }}</span>
                </div>
                <div ref="terminalEndRef" />
              </div>
              
              <div style="margin-top: auto; padding-top: 1rem; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #142036;">
                <span style="font-size: 0.75rem; color: var(--text-muted);">Frequência de Limpeza: 2.5 semanas</span>
                <button 
                  class="btn btn-secondary" 
                  style="padding: 0.2rem 0.5rem; font-size: 0.7rem;"
                  @click="logs = []"
                >
                  Limpar Console
                </button>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Aba Mapa de Vagas ── -->
        <template v-if="activeTab === 'map'">
          <div class="glass-card" style="padding: 1.5rem;">
            <JobMap :jobs="jobs" :mapsApiKey="config.google_maps_api_key" />
          </div>
        </template>

        <!-- ── Aba Contato com RH ── -->
        <template v-if="activeTab === 'contato'">
          <ContatoRH :jobs="jobs" :showToast="showToast" :config="config" />
        </template>

        <!-- ── Aba Mensagens ── -->
        <template v-if="activeTab === 'messenger'">
          <Messenger 
            :jobs="jobs" 
            :showToast="showToast" 
            :activeJobIdFromNotification="activeJobIdFromNotification" 
            :clearNotificationSelection="() => activeJobIdFromNotification = null" 
          />
        </template>

        <!-- ── Aba Currículo & Perfil IA ── -->
        <template v-if="activeTab === 'resume'">
          <div class="glass-card" style="max-width: 800px; margin: 0 auto;">
            <h2 class="section-title">
              <User :size="20" /> Análise de Currículo por IA
            </h2>
            <p style="color: var(--text-secondary); margin-bottom: 1.5rem; font-size: 0.9rem;">
              Faça upload do seu currículo em texto simples ou cole as informações no formulário. Nosso agente inteligente do Gemini classificará suas competências e avaliará a compatibilidade de cada vaga com seu perfil.
            </p>

            <!-- Upload Area -->
            <div 
              class="upload-zone"
              :class="{ 'drag-active': isDragActive }"
              @dragenter="handleDrag"
              @dragover="handleDrag"
              @dragleave="handleDrag"
              @drop="handleDrop"
              @click="fileInputRef?.click()"
            >
              <input 
                type="file" 
                ref="fileInputRef" 
                style="display: none;" 
                accept=".txt"
                @change="(e) => handleResumeUpload(e.target.files[0])"
              />
              <UploadCloud :size="40" class="upload-icon" />
              <div>
                <p style="font-weight: 600;">Arraste seu currículo ou clique para importar</p>
                <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">Suporta arquivos .txt</p>
              </div>
              
              <span v-if="uploadProgress === 'uploading'" style="font-size: 0.85rem;">Enviando arquivo...</span>
              <span v-if="uploadProgress === 'parsing'" style="font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem; color: var(--color-primary);">
                <Loader :size="14" class="spin-animation" /> Analisando currículo com Gemini AI...
              </span>
              <span v-if="uploadProgress === 'done'" style="font-size: 0.85rem; color: var(--color-success);">Currículo importado com sucesso!</span>
            </div>

            <div style="margin: 2rem 0; border-top: 1px solid var(--border-color);"></div>

            <!-- Resume Text Box -->
            <div class="form-group">
              <label>Texto do Currículo (para matching de IA)</label>
              <textarea 
                class="form-input" 
                rows="6"
                v-model="config.resume_text"
                placeholder="Cole seu currículo completo aqui..."
                style="resize: vertical;"
              />
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 1rem;">
              <button 
                class="btn btn-primary"
                @click="saveResumeText"
              >
                Salvar Texto do Currículo
              </button>
            </div>

            <!-- Extracted Details Profile -->
            <div v-if="resumeAnalysis" style="margin-top: 2rem; padding: 1.5rem; background: rgba(255,255,255,0.02); border-radius: 10px; border: 1px solid var(--border-color);">
              <h3 style="display: flex; align-items: center; gap: 0.5rem; font-size: 1.1rem; margin-bottom: 1rem; color: var(--color-secondary);">
                <Sparkles :size="16" /> Perfil Técnico Mapeado por IA
              </h3>
              
              <div style="margin-bottom: 1rem;">
                <strong style="font-size: 0.85rem; color: var(--text-secondary);">Resumo de Perfil:</strong>
                <p style="font-size: 0.9rem; margin-top: 0.25rem; color: var(--text-primary);">{{ resumeAnalysis.summary }}</p>
              </div>

              <div style="margin-bottom: 1.25rem;">
                <strong style="font-size: 0.85rem; color: var(--text-secondary);">Habilidades Técnicas:</strong>
                <div class="skills-container">
                  <span v-for="(skill, i) in resumeAnalysis.skills" :key="i" class="skill-tag suggested">{{ skill }}</span>
                </div>
              </div>

              <div>
                <strong style="font-size: 0.85rem; color: var(--text-secondary);">Cargos Recomendados:</strong>
                <div class="skills-container">
                  <span v-for="(role, i) in resumeAnalysis.suggested_roles" :key="i" class="skill-tag">{{ role }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Aba Configurações ── -->
        <template v-if="activeTab === 'config'">
          <div style="max-width: 680px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem;">
            <!-- Busca e LinkedIn -->
            <div class="glass-card">
              <h2 class="section-title">
                <Settings :size="20" /> Configurações Gerais
              </h2>
              
              <form @submit="saveConfig">
                <!-- Gemini API Key -->
                <div style="
                  display: flex; align-items: center; gap: 0.75rem;
                  padding: 0.75rem 1rem; border-radius: 10px;
                  background: rgba(16,185,129,0.07);
                  border: 1px solid rgba(16,185,129,0.2);
                  margin-bottom: 1.25rem;
                ">
                  <Sparkles :size="16" style="color: var(--color-success); flex-shrink: 0;" />
                  <div>
                    <span style="font-size: 0.85rem; font-weight: 600; color: var(--color-success);">
                      Gemini AI — Ativo e Configurado
                    </span>
                    <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.1rem;">
                      Chave da API armazenada com segurança no servidor. Não é exibida por razões de segurança.
                    </p>
                  </div>
                  <span style="
                    margin-left: auto; font-size: 0.7rem; padding: 0.2rem 0.6rem;
                    border-radius: 20px; background: rgba(16,185,129,0.15);
                    border: 1px solid rgba(16,185,129,0.3); color: var(--color-success);
                    font-weight: 700; letter-spacing: 0.05em;
                  ">🔒 OCULTA</span>
                </div>

                <div class="form-group">
                  <label>Palavras-Chave de Busca (Gemini + LinkedIn, separadas por vírgula)</label>
                  <input 
                    type="text" 
                    class="form-input" 
                    v-model="config.keywords" 
                    placeholder="Ex: Desenvolvedor React, Python, Node.js"
                  />
                </div>

                <!-- Filtros de Localização e Fontes -->
                <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 1rem;">
                  <div class="form-group">
                    <label>Localização da Busca ({{ activeSearchScope.label }})</label>
                    <input 
                      type="text" 
                      class="form-input" 
                      v-model="config.search_location" 
                      :placeholder="activeSearchScope.placeholder"
                    />
                    <span style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.35rem; display: block;">
                      {{ activeSearchScope.help }}
                    </span>
                  </div>

                  <div class="form-group">
                    <label>Buscar por</label>
                    <select 
                      class="form-input" 
                      v-model="config.search_scope" 
                      style="background: #0d1426; color: var(--text-primary); border: 1px solid var(--border-color);"
                    >
                      <option value="cidade">Cidade</option>
                      <option value="estado">Estado</option>
                      <option value="pais">País</option>
                      <option value="internacional">Internacional</option>
                    </select>
                  </div>
                </div>

                <div class="form-group" style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem;">
                  <input 
                    type="checkbox" 
                    id="web_search_chk"
                    :checked="config.enable_web_search === 'true'"
                    @change="(e) => config.enable_web_search = e.target.checked ? 'true' : 'false'"
                    style="cursor: pointer; width: 16px; height: 16px;"
                  />
                  <label htmlFor="web_search_chk" style="margin: 0; cursor: pointer; font-size: 0.85rem; color: var(--text-secondary);">
                    Gemini busca vagas na internet junto com o agente (ATS oficiais, Gupy, Greenhouse, Lever, LinkedIn, Indeed, InfoJobs)
                  </label>
                </div>

                <div class="form-group" style="background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.22); border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                  <label style="display: flex; align-items: center; gap: 0.4rem; color: var(--color-success); font-weight: 700;">
                    <Map :size="15" /> Mapa Interativo & Geocodificação (Leaflet Ativo)
                  </label>
                  <div style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.5rem; line-height: 1.4;">
                    🚀 <strong>Mapa Gratuito Ativado!</strong> O buscador de vagas agora utiliza **Leaflet & OpenStreetMap** por padrão. Não é necessária nenhuma chave de API ou configuração para visualizar o mapa interativo.
                  </div>
                  <input
                    type="password"
                    class="form-input"
                    v-model="config.google_maps_api_key"
                    placeholder="Google Maps API Key (opcional para geocodificação externa)..."
                    style="margin-top: 0.7rem;"
                  />
                  <span style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.45rem; display: block; line-height: 1.5;">
                    Nota: A chave acima é opcional. O mapa na aba de Radar de Vagas funciona 100% de graça com Leaflet.
                  </span>
                </div>

                <div class="form-group" style="background: rgba(10,102,194,0.06); border: 1px solid rgba(10,102,194,0.25); border-radius: 12px; padding: 1.25rem; margin-bottom: 0.5rem;">
                  <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                    <label style="margin: 0; font-size: 0.9rem; font-weight: 700; color: #60a5fa; display: flex; align-items: center; gap: 0.4rem;">
                      <Globe :size="15" /> LinkedIn &mdash; Sessão para Candidatura Real
                    </label>
                    <button
                      type="button"
                      @click="window.open('https://www.linkedin.com/login', '_blank', 'width=900,height=650')"
                      style="
                        display: flex; align-items: center; gap: 0.5rem;
                        padding: 0.45rem 1rem; border: none;
                        background: linear-gradient(135deg, #0a66c2, #0077b5);
                        color: #fff; font-weight: 700; font-size: 0.82rem;
                        cursor: pointer; box-shadow: 0 2px 12px rgba(10,102,194,0.4);
                        transition: all 0.2s; white-space: nowrap;
                      "
                      class="linkedin-login-btn"
                    >
                      <Globe :size="14" />
                      Abrir Login LinkedIn
                    </button>
                  </div>
                  <div style="font-size: 0.75rem; color: var(--text-secondary); background: rgba(0,0,0,0.2); border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.9rem; line-height: 1.7;">
                    <strong style="color: var(--text-primary); display: block; margin-bottom: 0.4rem;">Como obter o Cookie de sessão (li_at):</strong>
                    <ol style="margin: 0; padding-left: 1.1rem;">
                      <li>Clique em <strong>"Abrir Login LinkedIn"</strong> acima e faça login normalmente.</li>
                      <li>Com o LinkedIn aberto, pressione <kbd style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; padding: 0 4px; font-family: monospace;">F12</kbd> para abrir o DevTools.</li>
                      <li>Vá em <strong>Application &rarr; Cookies &rarr; linkedin.com</strong>.</li>
                      <li>Copie o valor do cookie chamado <code style="color: #60a5fa; background: rgba(96,165,250,0.1); padding: 0 4px; border-radius: 3px;">li_at</code>.</li>
                      <li>Cole no campo abaixo e salve.</li>
                    </ol>
                  </div>
                  <input
                    type="password"
                    class="form-input"
                    v-model="config.linkedin_cookie"
                    placeholder="Cole aqui o valor do cookie 'li_at'..."
                    :style="{ borderColor: config.linkedin_cookie ? 'rgba(10,102,194,0.5)' : undefined }"
                  />
                  <span style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.4rem; display: flex; align-items: center; gap: 0.3rem;">
                    <AlertCircle :size="11" />
                    {{ config.linkedin_cookie
                      ? 'Cookie configurado — o agente fará candidaturas reais no LinkedIn.'
                      : 'Sem cookie → O agente não fará candidaturas no LinkedIn. Configure o cookie acima para ativar.' }}
                  </span>
                </div>

                <!-- Notificações Simples -->
                <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.25rem;">
                  <label style="font-weight: 700; font-size: 0.9rem; display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.5rem;">
                    <Bell :size="15" style="color: var(--color-secondary);" /> Como você quer receber alertas das vagas?
                  </label>
                  <p style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 1rem;">
                    Escolha <strong>uma</strong> das opções abaixo — configure só o que precisar.
                  </p>

                  <!-- Opção A — WhatsApp CallMeBot -->
                  <details open style="margin-bottom: 0.9rem;">
                    <summary style="cursor: pointer; padding: 0.6rem 0.75rem; border-radius: 8px; background: rgba(37,211,102,0.07); border: 1px solid rgba(37,211,102,0.2); index-size: 0.85rem; font-weight: 600; color: #4ade80; list-style: none; display: flex; align-items: center; gap: 0.5rem;">
                      <span style="font-size: 1.1rem;">💬</span> WhatsApp (grátis, sem aplicativo extra)
                      <span style="margin-left: auto; font-size: 0.72rem; opacity: 0.7;">clique para recolher/expandir</span>
                    </summary>
                    <div style="padding: 0.9rem; background: rgba(0,0,0,0.2); border-radius: 0 0 8px 8px; font-size: 0.78rem; color: var(--text-secondary); line-height: 1.8;">
                      <strong style="color: var(--text-primary); display: block; margin-bottom: 0.4rem;">Configurar em 3 passos (serviço CallMeBot — 100% gratuito):</strong>
                      <ol style="padding-left: 1.1rem; margin: 0 0 0.75rem;">
                        <li>Adicione o contato <strong>+34 644 53 40 20</strong> no seu WhatsApp.</li>
                        <li>Envie a mensagem: <code style="background: rgba(255,255,255,0.08); padding: 1px 5px; border-radius: 3px; color: #4ade80;">I allow callmebot to send me messages</code></li>
                        <li>Você receberá a sua <strong>API Key</strong>. Depois preencha abaixo:</li>
                      </ol>
                      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem;">
                        <div class="form-group" style="margin: 0;">
                          <label>Seu número (+55...)</label>
                          <input type="text" class="form-input" v-model="config.whatsapp_phone" placeholder="+5511999999999" />
                        </div>
                        <div class="form-group" style="margin: 0;">
                          <label>API Key recebida</label>
                          <input type="text" class="form-input" v-model="config.whatsapp_webhook" placeholder="Cole aqui a API Key..." />
                        </div>
                      </div>
                    </div>
                  </details>

                  <!-- Opção B — n8n -->
                  <details>
                    <summary style="cursor: pointer; padding: 0.6rem 0.75rem; border-radius: 8px; background: rgba(234,88,12,0.07); border: 1px solid rgba(234,88,12,0.2); font-size: 0.85rem; font-weight: 600; color: #fb923c; list-style: none; display: flex; align-items: center; gap: 0.5rem;">
                      <span style="font-size: 1.1rem;">⚙️</span> n8n / Webhook avançado (para quem já usa automação)
                      <span style="margin-left: auto; font-size: 0.72rem; opacity: 0.7;">clique para expandir</span>
                    </summary>
                    <div style="padding: 0.9rem; background: rgba(0,0,0,0.2); border-radius: 0 0 8px 8px; font-size: 0.78rem; color: var(--text-secondary); line-height: 1.8;">
                      <p style="margin: 0 0 0.6rem;">Se você tem um workflow no n8n ou outra plataforma (Zapier, Make…), cole a URL abaixo. O Vaga Sync enviará um JSON automaticamente a cada candidatura ou retorno de RH.</p>
                      <div class="form-group" style="margin: 0;">
                        <label>URL do Webhook</label>
                        <input type="text" class="form-input" v-model="config.n8n_webhook_url" placeholder="https://n8n.seu-dominio.com/webhook/..." />
                      </div>
                    </div>
                  </details>
                </div>

                <div style="display: flex; justify-content: flex-end; margin-top: 2rem;">
                  <button type="submit" class="btn btn-primary">
                    Salvar Configurações
                  </button>
                </div>
              </form>

              <div v-if="saveSuccess" style="margin-top: 1rem; color: var(--color-success); font-size: 0.9rem; text-align: center;">
                Alterações salvas com sucesso!
              </div>
            </div>

            <!-- Notificações Multi-Canal -->
            <div class="glass-card">
              <h2 class="section-title" style="margin-bottom: 0.5rem;">
                <Bell :size="20" /> Notificações Multi-Canal
              </h2>
              <p style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.5;">
                Configure um ou mais canais abaixo. O Vaga Sync tentará cada canal em ordem (n8n → Telegram → E-mail → Webhook Genérico) com fallback automático.
              </p>

              <!-- Status dos canais -->
              <div style="display: flex; flex-wrap: wrap; gap: 0.6rem; margin-bottom: 1.5rem;">
                <span 
                  v-if="notifyChannels" 
                  v-for="[canal, status] in Object.entries(notifyChannels)" 
                  :key="canal" 
                  style="
                    font-size: 0.75rem; padding: 0.25rem 0.6rem;
                    border-radius: 20px; font-weight: 600;
                  "
                  :style="{
                    background: status.includes('✅') ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.04)',
                    border: `1px solid ${status.includes('✅') ? 'rgba(16,185,129,0.3)' : 'var(--border-color)'}`,
                    color: status.includes('✅') ? 'var(--color-success)' : 'var(--text-muted)'
                  }"
                >
                  {{ status }} {{ canal }}
                </span>
                <button 
                  v-else 
                  class="btn btn-secondary" 
                  style="font-size: 0.78rem; padding: 0.3rem 0.8rem;"
                  @click="loadNotifyChannels"
                >
                  Verificar canais configurados
                </button>
              </div>

              <!-- Telegram -->
              <div style="margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border-color);">
                <h4 style="font-size: 0.9rem; margin-bottom: 0.75rem; color: var(--color-secondary); display: flex; gap: 0.4rem; align-items: center;">
                  <Smartphone :size="14" /> Telegram Bot
                </h4>
                <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                  Gratuito, instantâneo no celular. Crie um bot em @BotFather e copie o Token. Para o Chat ID, mande /start ao bot e acesse
                  <code style="margin-left: 4px; color: var(--color-secondary);">api.telegram.org/bot&lt;TOKEN&gt;/getUpdates</code>.
                </p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                  <div class="form-group">
                    <label>Token do Bot Telegram</label>
                    <input type="password" class="form-input" v-model="config.telegram_token" placeholder="1234567890:ABCDef..." />
                  </div>
                  <div class="form-group">
                    <label>Chat ID</label>
                    <input type="text" class="form-input" v-model="config.telegram_chat_id" placeholder="Ex: 123456789" />
                  </div>
                </div>
              </div>

              <!-- E-mail SMTP -->
              <div style="margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border-color);">
                <h4 style="font-size: 0.9rem; margin-bottom: 0.75rem; color: var(--color-secondary); display: flex; gap: 0.4rem; align-items: center;">
                  <MessageSquare :size="14" /> E-mail (SMTP)
                </h4>
                <p style="font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.75rem;">
                  Gmail: host <code style="color: var(--color-secondary);">smtp.gmail.com</code> porta <code style="color: var(--color-secondary);">465</code> (use uma Senha de App).
                  Outlook: host <code style="color: var(--color-secondary);">smtp-mail.outlook.com</code> porta <code style="color: var(--color-secondary);">587</code>.
                </p>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                  <div class="form-group">
                    <label>E-mail Remetente (Login SMTP)</label>
                    <input type="email" class="form-input" v-model="config.smtp_email" placeholder="seu@gmail.com" />
                  </div>
                  <div class="form-group">
                    <label>Senha de App / Senha SMTP</label>
                    <input type="password" class="form-input" v-model="config.smtp_password" placeholder="Senha de App do Gmail..." />
                  </div>
                  <div class="form-group">
                    <label>Host SMTP</label>
                    <input type="text" class="form-input" v-model="config.smtp_host" placeholder="smtp.gmail.com" />
                  </div>
                  <div class="form-group">
                    <label>Porta SMTP</label>
                    <input type="number" class="form-input" v-model="config.smtp_port" placeholder="465" />
                  </div>
                  <div class="form-group" style="grid-column: 1 / -1;">
                    <label>Enviar Notificações Para (E-mail Destino)</label>
                    <input type="email" class="form-input" v-model="config.notify_email" placeholder="Deixe em branco para usar o mesmo do remetente" />
                  </div>
                </div>
              </div>

              <!-- Webhook Genérico -->
              <div style="margin-bottom: 1.5rem;">
                <h4 style="font-size: 0.9rem; margin-bottom: 0.75rem; color: var(--color-secondary); display: flex; gap: 0.4rem; align-items: center;">
                  <Globe :size="14" /> Webhook Genérico (Slack, Discord, Zapier, Make…)
                </h4>
                <div class="form-group">
                  <label>URL do Webhook</label>
                  <input type="text" class="form-input" v-model="config.generic_webhook_url" placeholder="https://hooks.slack.com/... ou https://discord.com/api/webhooks/..." />
                  <span style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.25rem; display: block;">
                    Funciona com Slack, Discord, Zapier, Make.com ou qualquer serviço que aceita POST JSON.
                  </span>
                </div>
              </div>

              <!-- Botões de ação -->
              <div style="display: flex; gap: 0.75rem; justify-content: flex-end;">
                <button type="button" class="btn btn-secondary" @click="loadNotifyChannels" style="font-size: 0.85rem;">
                  <CheckCircle :size="14" style="margin-right: 0.3rem;" />
                  Verificar Canais
                </button>
                <button 
                  type="button" 
                  class="btn btn-primary"
                  @click="testNotification" 
                  :disabled="testingNotify"
                  style="font-size: 0.85rem;"
                  :style="{ background: testingNotify ? 'rgba(59,130,246,0.4)' : undefined }"
                >
                  <template v-if="testingNotify">
                    <Loader :size="14" class="spin-animation" style="margin-right: 0.3rem;" />Testando...
                  </template>
                  <template v-else>
                    <Bell :size="14" style="margin-right: 0.3rem;" />Testar Todos os Canais
                  </template>
                </button>
                <button 
                  type="button" 
                  class="btn btn-primary"
                  @click="async (e) => { await saveConfig(e); loadNotifyChannels(); }"
                  style="font-size: 0.85rem;"
                >
                  Salvar Notificações
                </button>
              </div>
            </div>
          </div>
        </template>
      </main>

      <footer class="footer-bar" style="margin-top: 3rem;">
        <p>© 2026 Vaga Sync. Todos os direitos reservados. • Conexão Segura SSL • Gemini Core Engine • n8n Connected</p>
      </footer>
    </template>
  </div>
</template>

<style scoped>
.spin-animation {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.linkedin-login-btn:hover {
  transform: translateY(-1px);
}
</style>
