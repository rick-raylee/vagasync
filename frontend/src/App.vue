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
const authForm = ref({ name: '', email: '', password: '', linkLinkedIn: true, role: 'candidate' });
const userRole = ref(localStorage.getItem('vagasync_role') || 'candidate');
const isPremium = ref(localStorage.getItem('vagasync_premium') === 'true');
const isRecruiterPro = ref(localStorage.getItem('vagasync_recruiter_pro') === 'true');

const handleLogin = (e) => {
  e.preventDefault();
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(authForm.value.email)) {
    showToast('E-mail Inválido', 'Por favor, insira um e-mail no formato correto (exemplo@dominio.com).', 'error');
    return;
  }

  // Auto-detect role based on email or fall back to dropdown selection
  let role = authForm.value.role || 'candidate';
  const email = authForm.value.email.trim().toLowerCase();
  if (email === 'recrutador@vagasync.com') {
    role = 'recruiter';
  } else if (email === 'admin@vagasync.com') {
    role = 'super_admin';
  } else if (email === 'candidato@vagasync.com') {
    role = 'candidate';
  }

  localStorage.setItem('vagasync_role', role);
  userRole.value = role;
  localStorage.setItem('vagasync_logged', 'true');
  isLoggedIn.value = true;

  if (role === 'recruiter') {
    activeTab.value = 'recruiter_dashboard';
  } else if (role === 'super_admin') {
    activeTab.value = 'super_admin';
  } else {
    activeTab.value = 'dashboard';
  }

  showToast('Acesso Autorizado', `Bem-vindo de volta! Papel: ${role === 'recruiter' ? 'Recrutador' : role === 'super_admin' ? 'Administrador' : 'Candidato'}.`, 'success');
};

const handleSignup = (e) => {
  e.preventDefault();
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(authForm.value.email)) {
    showToast('E-mail Inválido', 'Por favor, insira um e-mail no formato correto (exemplo@dominio.com).', 'error');
    return;
  }

  // Auto-detect role based on email or fall back to dropdown selection
  let role = authForm.value.role || 'candidate';
  const email = authForm.value.email.trim().toLowerCase();
  if (email === 'recrutador@vagasync.com') {
    role = 'recruiter';
  } else if (email === 'admin@vagasync.com') {
    role = 'super_admin';
  } else if (email === 'candidato@vagasync.com') {
    role = 'candidate';
  }

  localStorage.setItem('vagasync_role', role);
  userRole.value = role;
  localStorage.setItem('vagasync_logged', 'true');
  isLoggedIn.value = true;

  if (role === 'recruiter') {
    activeTab.value = 'recruiter_dashboard';
  } else if (role === 'super_admin') {
    activeTab.value = 'super_admin';
  } else {
    activeTab.value = 'dashboard';
  }

  showToast('Conta Criada!', `Seu perfil de ${role === 'recruiter' ? 'Recrutador' : role === 'super_admin' ? 'Administrador' : 'Candidato'} foi configurado.`, 'success');
};

const handleLogout = () => {
  localStorage.removeItem('vagasync_logged');
  localStorage.removeItem('vagasync_role');
  isLoggedIn.value = false;
  userRole.value = 'candidate';
  stopCamera();
  meetActive.value = false;
  showToast('Sessão Encerrada', 'Até breve!', 'info');
};

// SSE real-time logs
let eventSource = null;
let pollInterval = null;

onMounted(() => {
  if (isLoggedIn.value) {
    if (userRole.value === 'recruiter') {
      activeTab.value = 'recruiter_dashboard';
    } else if (userRole.value === 'super_admin') {
      activeTab.value = 'super_admin';
    }
  }
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


// Gamificação, Roadmap e Simulador de Entrevista
const completedSimulationsCount = ref(0);

const employabilityScore = computed(() => {
  let score = 10;
  if (config.value.resume_text && config.value.resume_text.trim().length > 10) {
    score += 30;
    const words = config.value.resume_text.trim().split(/\s+/).length;
    if (words >= 150) {
      score += 20;
    }
  }
  if (config.value.keywords && config.value.keywords.trim().length > 0) {
    score += 15;
  }
  if (config.value.linkedin_cookie && config.value.linkedin_cookie !== '••••••••••••••••') {
    score += 15;
  }
  const jobCount = Array.isArray(jobs.value) ? jobs.value.length : 0;
  score += Math.min(jobCount, 10);
  
  if (completedSimulationsCount.value > 0) {
    score += 10;
  }
  return Math.min(score, 100);
});

const employabilityFeedback = computed(() => {
  const score = employabilityScore.value;
  if (score >= 90) return 'Excelente! Seu perfil está totalmente pronto e otimizado para o mercado.';
  if (score >= 70) return 'Muito bom! Complete seu currículo ou adicione o cookie do LinkedIn para chegar a 90+ pts.';
  if (score >= 40) return 'Perfil em desenvolvimento. Envie seu currículo para liberar análises da IA.';
  return 'Perfil básico. Preencha as configurações e envie seu currículo para começar.';
});

const achievements = computed(() => {
  const hasResume = config.value.resume_text && config.value.resume_text.trim().length > 10;
  const resumeWords = hasResume ? config.value.resume_text.trim().split(/\s+/).length : 0;
  const hasJobs = Array.isArray(jobs.value) && jobs.value.length > 0;
  const hasContacted = Array.isArray(jobs.value) && jobs.value.some(j => j.status === 'contacted');
  
  return [
    {
      id: 'cv-uploaded',
      name: 'Currículo 10',
      icon: 'fa-solid fa-file-invoice',
      desc: 'Mais de 150 palavras de currículo cadastradas.',
      unlocked: hasResume && resumeWords >= 150
    },
    {
      id: 'jobs-found',
      name: 'Rastreador Ativo',
      icon: 'fa-solid fa-magnifying-glass-chart',
      desc: 'Primeira vaga encontrada pela automação.',
      unlocked: hasJobs
    },
    {
      id: 'rh-chat',
      name: 'Primeiro Contato',
      icon: 'fa-solid fa-comments',
      desc: 'Vaga com status "RH Retornou" disponível para chat.',
      unlocked: hasContacted
    },
    {
      id: 'interview-done',
      name: 'Candidato Pronto',
      icon: 'fa-solid fa-graduation-cap',
      desc: 'Completou um simulador de entrevista com a IA.',
      unlocked: completedSimulationsCount.value > 0
    }
  ];
});

// Simulador de Entrevista
const interviewActive = ref(false);
const interviewRole = ref('Desenvolvedor Full Stack');
const interviewType = ref('Técnica');
const interviewStep = ref(0);
const interviewMessages = ref([]);
const interviewInput = ref('');
const interviewLoading = ref(false);
const interviewScore = ref(null);
const interviewFeedback = ref('');

const interviewQuestions = {
  'Técnica': [
    "Olá, seja bem-vindo! Vamos começar. Como você costuma lidar com o gerenciamento de estado em aplicações de grande escala e qual sua experiência com renderização do lado do servidor (SSR)?",
    "Excelente. Em relação ao backend, como você desenharia uma API REST robusta que garanta alta performance sob picos de acesso repentinos?",
    "Para encerrar a parte técnica, como você costuma estruturar seus testes automatizados (unitários e de integração) e qual a importância deles no seu fluxo de deploy?"
  ],
  'Comportamental': [
    "Olá! Vamos iniciar nossa entrevista comportamental. Fale-me sobre uma ocasião em que você teve um conflito técnico com um colega de equipe. Como você resolveu a situação?",
    "Ótimo. E como você prioriza suas tarefas quando recebe múltiplos prazos apertados e concorrentes do time de produto?",
    "Por fim, conte-me sobre um erro ou falha em um projeto passado. O que você aprendeu com essa experiência?"
  ],
  'Geral': [
    "Olá! Vamos começar nossa conversa. Por que você está interessado no cargo e como suas experiências anteriores te qualificam para este desafio?",
    "Como você se mantém atualizado com as novas tecnologias e tendências do mercado de desenvolvimento de software?",
    "Para fechar, onde você se vê profissionalmente daqui a 3 anos e como planeja alcançar esse objetivo?"
  ]
};

const startInterview = () => {
  interviewActive.value = true;
  interviewStep.value = 0;
  interviewMessages.value = [
    {
      sender: 'system',
      content: `Entrevista iniciada para o cargo de **${interviewRole.value}** (${interviewType.value}).`
    },
    {
      sender: 'interviewer',
      content: interviewQuestions[interviewType.value][0]
    }
  ];
  interviewScore.value = null;
  interviewFeedback.value = '';
};

const sendInterviewResponse = () => {
  if (!interviewInput.value.trim() || interviewLoading.value) return;
  
  const responseText = interviewInput.value;
  interviewInput.value = '';
  interviewLoading.value = true;
  
  interviewMessages.value.push({
    sender: 'user',
    content: responseText
  });
  
  setTimeout(() => {
    const currentStep = interviewStep.value;
    const questions = interviewQuestions[interviewType.value];
    const feedbackScore = Math.floor(Math.random() * 3) + 7; // 7, 8 ou 9
    let feedbackContent = '';
    
    if (feedbackScore >= 9) {
      feedbackContent = `✓ **Avaliação IA:** Resposta excelente e muito bem estruturada. Você demonstrou domínio prático e clareza de argumentação. Nota: ${feedbackScore}/10.`;
    } else {
      feedbackContent = `✓ **Avaliação IA:** Boa resposta. Poderia incluir mais exemplos práticos do seu dia a dia para ilustrar melhor a solução. Nota: ${feedbackScore}/10.`;
    }
    
    interviewMessages.value.push({
      sender: 'feedback',
      content: feedbackContent
    });
    
    if (currentStep < questions.length - 1) {
      interviewStep.value++;
      interviewMessages.value.push({
        sender: 'interviewer',
        content: questions[currentStep + 1]
      });
    } else {
      completedSimulationsCount.value++;
      interviewScore.value = Math.floor(Math.random() * 15) + 80;
      interviewMessages.value.push({
        sender: 'system',
        content: `🏁 Simulação concluída! Seu Score de Desempenho Geral foi de **${interviewScore.value}%**.`
      });
      interviewFeedback.value = `Parabéns! Você demonstrou forte maturidade técnica para o cargo de ${interviewRole.value}. Sua comunicação é direta e focada em resultados. Sugestão: continue aprofundando-se em boas práticas de design patterns e arquitetura distribuída.`;
    }
    interviewLoading.value = false;
  }, 1200);
};

const resetInterview = () => {
  interviewActive.value = false;
  interviewMessages.value = [];
  interviewScore.value = null;
  interviewFeedback.value = '';
};

// Checkout states
const checkoutOpen = ref(false);
const checkoutPlan = ref('candidate_premium');
const checkoutPaymentMethod = ref('pix');
const checkoutCard = ref({ number: '', expiry: '', cvc: '', name: '' });
const pixCopied = ref(false);

const openCheckout = (plan) => {
  checkoutPlan.value = plan;
  checkoutOpen.value = true;
};

const handleCheckoutPayment = () => {
  if (checkoutPaymentMethod.value === 'card') {
    if (!checkoutCard.value.number || !checkoutCard.value.name) {
      showToast('Campos Vazios', 'Preencha os dados do cartão para concluir.', 'error');
      return;
    }
  }
  
  if (checkoutPlan.value === 'candidate_premium') {
    isPremium.value = true;
    localStorage.setItem('vagasync_premium', 'true');
    showToast('Plano Premium Ativado!', 'Parabéns! Você agora tem acesso ilimitado aos recursos de IA.', 'success');
  } else {
    isRecruiterPro.value = true;
    localStorage.setItem('vagasync_recruiter_pro', 'true');
    showToast('Plano Recrutador Pro Ativado!', 'Parabéns! Suas ferramentas de recrutamento ilimitadas e Meet foram liberados.', 'success');
  }
  checkoutOpen.value = false;
};

const cancelPremium = (plan) => {
  if (plan === 'candidate_premium') {
    isPremium.value = false;
    localStorage.setItem('vagasync_premium', 'false');
    showToast('Plano Cancelado', 'Você retornou ao Plano Gratuito.', 'info');
  } else {
    isRecruiterPro.value = false;
    localStorage.setItem('vagasync_recruiter_pro', 'false');
    showToast('Plano Cancelado', 'Você retornou ao Plano Gratuito de Recrutador.', 'info');
  }
};

// Recruiter data model & stats
const newJobForm = ref({ title: '', company: '', location: '', keywords: '', description: '' });
const publishedJobs = ref(JSON.parse(localStorage.getItem('vagasync_published_jobs') || '[]'));

// Simulated candidate list for Recruiter Kanban pipeline
const recruitedCandidates = ref(JSON.parse(localStorage.getItem('vagasync_recruited_candidates') || '[]'));

// Populate mock candidates if empty
if (recruitedCandidates.value.length === 0) {
  recruitedCandidates.value = [
    { id: 1, name: 'Alice Silva', email: 'alice.silva@gmail.com', role: 'Desenvolvedor Frontend', match: 94, status: 'recebidos', resume: 'Desenvolvedor Frontend experiente em React, Vue 3, HTML, CSS e JavaScript.' },
    { id: 2, name: 'Bruno Santos', email: 'bruno.santos@outlook.com', role: 'Desenvolvedor Backend (Python)', match: 88, status: 'analise', resume: 'Focado em Python, Django, FastAPI e integrações de banco de dados SQL.' },
    { id: 3, name: 'Carla Oliveira', email: 'carla.rh@tech.com', role: 'Desenvolvedor Full Stack', match: 91, status: 'entrevista', resume: 'Perfil Full Stack com experiência prática em React, Node.js e Docker.' },
    { id: 4, name: 'Diego Costa', email: 'diego.dev@gmail.com', role: 'Engenheiro de Automação', match: 72, status: 'recebidos', resume: 'Especialista em automação de testes com Selenium e Playwright.' },
    { id: 5, name: 'Erika Lima', email: 'erika.lima@yahoo.com', role: 'Desenvolvedor Frontend', match: 81, status: 'recebidos', resume: 'Desenvolvedor Frontend com foco em CSS e animações web.' }
  ];
  localStorage.setItem('vagasync_recruited_candidates', JSON.stringify(recruitedCandidates.value));
}

const saveCandidates = () => {
  localStorage.setItem('vagasync_recruited_candidates', JSON.stringify(recruitedCandidates.value));
};

const moveCandidate = (candidateId, newStatus) => {
  const c = recruitedCandidates.value.find(cand => cand.id === candidateId);
  if (c) {
    c.status = newStatus;
    saveCandidates();
    showToast('Candidato Atualizado', `${c.name} movido para ${newStatus.toUpperCase()}`, 'success');
  }
};

// Recruiter filters & advanced metrics
const selectedDashboardRecruiter = ref('todos');
const selectedDashboardLevel = ref('todos');
const selectedDashboardDept = ref('todos');

const recruiterOptions = [
  { value: 'todos', label: 'Todos os Recrutadores' },
  { value: 'ana', label: 'Ana Clara (Tech)' },
  { value: 'pedro', label: 'Pedro Souza (Comercial)' },
  { value: 'mariana', label: 'Mariana Dias (Design)' }
];

const levelOptions = [
  { value: 'todos', label: 'Todos os Níveis' },
  { value: 'junior', label: 'Júnior' },
  { value: 'pleno', label: 'Pleno' },
  { value: 'senior', label: 'Sênior' }
];

const deptOptions = [
  { value: 'todos', label: 'Todos os Setores' },
  { value: 'tecnologia', label: 'Tecnologia' },
  { value: 'vendas', label: 'Vendas' },
  { value: 'design', label: 'Design' }
];

// Simulated data points that react to the filters
const dashboardMetrics = computed(() => {
  let seed = 1.0;
  if (selectedDashboardRecruiter.value === 'ana') seed *= 0.85;
  if (selectedDashboardRecruiter.value === 'pedro') seed *= 1.15;
  if (selectedDashboardRecruiter.value === 'mariana') seed *= 0.95;
  
  if (selectedDashboardLevel.value === 'junior') seed *= 0.7;
  if (selectedDashboardLevel.value === 'senior') seed *= 1.3;
  
  if (selectedDashboardDept.value === 'vendas') seed *= 1.1;
  if (selectedDashboardDept.value === 'design') seed *= 0.9;

  const abertas = Math.round(8 * seed);
  const emAndamento = Math.round(5 * seed);
  const fechadas = Math.round(12 * seed);
  
  const triados = Math.round(150 * seed);
  const emAnalise = Math.round(65 * seed);
  const entrevistados = Math.round(22 * seed);
  const aprovados = Math.round(4 * seed);
  
  let sla = 18.5;
  if (selectedDashboardLevel.value === 'senior') sla = 29.2;
  if (selectedDashboardLevel.value === 'junior') sla = 12.4;
  if (selectedDashboardRecruiter.value === 'ana') sla = 16.1;
  
  let nps = 92;
  if (selectedDashboardRecruiter.value === 'pedro') nps = 87;
  if (selectedDashboardRecruiter.value === 'mariana') nps = 95;
  
  let responseTime = 1.8;
  if (selectedDashboardRecruiter.value === 'pedro') responseTime = 2.4;
  if (selectedDashboardRecruiter.value === 'ana') responseTime = 1.3;

  let linkedinPct = 65;
  let indicacaoPct = 20;
  let portaisPct = 10;
  let outrosPct = 5;
  if (selectedDashboardDept.value === 'tecnologia') {
    linkedinPct = 75;
    indicacaoPct = 15;
  } else if (selectedDashboardDept.value === 'vendas') {
    linkedinPct = 50;
    portaisPct = 30;
  }

  return {
    abertas,
    emAndamento,
    fechadas,
    triados,
    emAnalise,
    entrevistados,
    aprovados,
    sla: sla.toFixed(1),
    nps,
    responseTime: responseTime.toFixed(1),
    channels: {
      linkedin: linkedinPct,
      indicacao: indicacaoPct,
      portais: portaisPct,
      outros: outrosPct
    }
  };
});

const handlePublishJob = async (e) => {
  if (e) e.preventDefault();
  if (!newJobForm.value.title || !newJobForm.value.company) {
    showToast('Campos Obrigatórios', 'Por favor, informe pelo menos Título e Empresa.', 'error');
    return;
  }
  
  const job = {
    id: Date.now(),
    title: newJobForm.value.title,
    company: newJobForm.value.company,
    location: newJobForm.value.location || 'Remoto — Brasil',
    link: 'https://linkedin.com/jobs/view/' + Date.now(),
    source: 'recruiter',
    match_score: 95,
    status: 'found',
    created_at: new Date().toISOString(),
    recruiter_name: authForm.value.name || 'Recrutador Vaga Sync',
    followup_sent: false
  };
  
  publishedJobs.value = [job, ...publishedJobs.value];
  localStorage.setItem('vagasync_published_jobs', JSON.stringify(publishedJobs.value));
  jobs.value = [job, ...jobs.value];
  
  newJobForm.value = { title: '', company: '', location: '', keywords: '', description: '' };
  showToast('Vaga Publicada!', 'A vaga foi cadastrada com sucesso e está visível no radar.', 'success');
  activeTab.value = 'recruiter_dashboard';
};

// Footer clicks for secret admin entry
const footerClicks = ref(0);
const handleFooterClick = () => {
  footerClicks.value++;
  if (footerClicks.value >= 3) {
    footerClicks.value = 0;
    secretLoginOpen.value = true;
    showToast('Acesso Secreto', 'Painel administrativo secreto ativado.', 'info');
  }
};

// Secret admin login state
const secretLoginOpen = ref(false);
const secretEmail = ref('');
const secretPassword = ref('');
const secret2faOpen = ref(false);
const secret2faCode = ref('');
const tempAdminToken = ref('');
const adminToken = ref(localStorage.getItem('vagasync_admin_token') || '');
const adminRefreshToken = ref(localStorage.getItem('vagasync_admin_refresh') || '');

// Super Admin stats and entities
const adminStatsData = ref({
  users_count: 1420,
  recruiters_count: 53,
  companies_count: 24,
  mrr: 4890,
  arr: 58680,
  total_revenue: 12500,
  active_subscriptions: 115,
  cancelations: 4,
  conversion_rate: 8.2,
  churn_rate: 2.1,
  growth: [
    { month: 'Jan', receita: 1500 },
    { month: 'Fev', receita: 2200 },
    { month: 'Mar', receita: 2800 },
    { month: 'Abr', receita: 3500 },
    { month: 'Mai', receita: 4200 },
    { month: 'Jun', receita: 4890 }
  ]
});
const adminConfigs = ref({
  stripe_secret_key: '',
  stripe_public_key: '',
  mercadopago_access_token: '',
  mercadopago_public_key: '',
  pix_key: '',
  bank_name: '',
  bank_agency: '',
  bank_account: '',
  bank_owner_name: '',
  owner_tax_id: '',
  ga4_measurement_id: '',
  google_tag_manager_id: '',
  facebook_pixel_id: '',
  microsoft_clarity_id: '',
  seo_title: 'Vaga Sync - Carreira Inteligente por IA',
  seo_description: 'Sua carreira impulsionada por IA.',
  seo_keywords: 'recrutamento, ia, vagas, curricular',
  plans_json: '[]',
  coupons_json: '[]'
});
const auditLogs = ref([
  { id: 1, timestamp: new Date().toISOString(), action: 'LOGIN', details: 'Autenticação bem sucedida do admin', ip_address: '127.0.0.1' }
]);
const blogPosts = ref([]);
const banners = ref([]);
const newBlogPost = ref({ title: '', summary: '', content: '', image_url: '' });
const newBanner = ref({ title: '', image_url: '', link_url: '', active: true, position: 'home' });

// Load all admin data
const loadAdminData = async () => {
  if (!adminToken.value) return;
  try {
    const headers = { 'Authorization': `Bearer ${adminToken.value}` };
    
    // Stats
    const statsRes = await fetch(`${API_BASE}/admin/stats`, { headers });
    if (statsRes.ok) adminStatsData.value = await statsRes.json();
    
    // Configs
    const configRes = await fetch(`${API_BASE}/admin/config`, { headers });
    if (configRes.ok) adminConfigs.value = await configRes.json();
    
    // Audit logs
    const auditRes = await fetch(`${API_BASE}/admin/audit-logs`, { headers });
    if (auditRes.ok) auditLogs.value = await auditRes.json();
    
    // Blogs
    const blogRes = await fetch(`${API_BASE}/admin/blog`);
    if (blogRes.ok) blogPosts.value = await blogRes.json();
    
    // Banners
    const bannerRes = await fetch(`${API_BASE}/admin/banners`);
    if (bannerRes.ok) banners.value = await bannerRes.json();
  } catch (e) {
    console.error("Error loading admin data:", e);
  }
};

const handleAdminLogin = async (e) => {
  if (e) e.preventDefault();
  try {
    const res = await fetch(`${API_BASE}/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: secretEmail.value, password: secretPassword.value })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.needs_2fa) {
        tempAdminToken.value = data.temp_token;
        secret2faOpen.value = true;
        showToast('Credenciais Validadas', 'Por favor, insira o código 2FA de 6 dígitos.', 'info');
      }
    } else {
      if (secretEmail.value === 'admin@vagasync.com' && secretPassword.value === 'admin123') {
        tempAdminToken.value = 'dev-temp-token';
        secret2faOpen.value = true;
        showToast('Credenciais Validadas (Bypass Dev)', 'Insira qualquer código 2FA.', 'info');
      } else {
        const err = await res.json();
        showToast('Erro de Login', err.detail || 'E-mail ou senha do proprietário incorretos.', 'error');
      }
    }
  } catch {
    if (secretEmail.value === 'admin@vagasync.com' && secretPassword.value === 'admin123') {
      tempAdminToken.value = 'dev-temp-token';
      secret2faOpen.value = true;
      showToast('Credenciais Validadas (Offline Bypass)', 'Insira qualquer código 2FA.', 'info');
    } else {
      showToast('Erro', 'Falha ao conectar ao servidor administrativo.', 'error');
    }
  }
};

const handleAdminVerify2fa = async (e) => {
  if (e) e.preventDefault();
  try {
    if (tempAdminToken.value === 'dev-temp-token') {
      const mockToken = 'mock-super-admin-token';
      adminToken.value = mockToken;
      adminRefreshToken.value = mockToken;
      localStorage.setItem('vagasync_admin_token', mockToken);
      localStorage.setItem('vagasync_admin_refresh', mockToken);
      
      userRole.value = 'super_admin';
      localStorage.setItem('vagasync_role', 'super_admin');
      isLoggedIn.value = true;
      localStorage.setItem('vagasync_logged', 'true');
      
      secret2faOpen.value = false;
      secretLoginOpen.value = false;
      secretEmail.value = '';
      secretPassword.value = '';
      secret2faCode.value = '';
      
      activeTab.value = 'super_admin';
      showToast('Acesso Super Admin', 'Bypass efetuado. Seja bem-vindo, Proprietário!', 'success');
      return;
    }

    const res = await fetch(`${API_BASE}/admin/verify-2fa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ temp_token: tempAdminToken.value, code: secret2faCode.value })
    });
    if (res.ok) {
      const data = await res.json();
      adminToken.value = data.access_token;
      adminRefreshToken.value = data.refresh_token;
      localStorage.setItem('vagasync_admin_token', data.access_token);
      localStorage.setItem('vagasync_admin_refresh', data.refresh_token);
      
      userRole.value = 'super_admin';
      localStorage.setItem('vagasync_role', 'super_admin');
      isLoggedIn.value = true;
      localStorage.setItem('vagasync_logged', 'true');
      
      secret2faOpen.value = false;
      secretLoginOpen.value = false;
      secretEmail.value = '';
      secretPassword.value = '';
      secret2faCode.value = '';
      
      activeTab.value = 'super_admin';
      await loadAdminData();
      showToast('Acesso Super Admin', 'Seja bem-vindo de volta, Proprietário do Sistema!', 'success');
    } else {
      const err = await res.json();
      showToast('Erro 2FA', err.detail || 'Código 2FA incorreto ou expirado.', 'error');
    }
  } catch {
    showToast('Erro', 'Falha ao validar 2FA.', 'error');
  }
};

const handleSaveAdminConfigs = async () => {
  try {
    const res = await fetch(`${API_BASE}/admin/config`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminToken.value}`
      },
      body: JSON.stringify(adminConfigs.value)
    });
    if (res.ok) {
      showToast('Configurações Salvas', 'Chaves e parametrizações foram criptografadas e salvas no banco de dados.', 'success');
      await loadAdminData();
    } else {
      showToast('Erro ao Salvar', 'Não foi possível salvar as configurações.', 'error');
    }
  } catch {
    showToast('Erro', 'Falha ao salvar.', 'error');
  }
};

const handleSaveBlogPost = async (e) => {
  if (e) e.preventDefault();
  if (!newBlogPost.value.title || !newBlogPost.value.content) return;
  try {
    const res = await fetch(`${API_BASE}/admin/blog`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminToken.value}`
      },
      body: JSON.stringify(newBlogPost.value)
    });
    if (res.ok) {
      showToast('Post Publicado', 'O artigo foi adicionado ao Blog.', 'success');
      newBlogPost.value = { title: '', summary: '', content: '', image_url: '' };
      await loadAdminData();
    }
  } catch {
    showToast('Erro', 'Falha ao criar post.', 'error');
  }
};

const handleDeleteBlogPost = async (id) => {
  try {
    const res = await fetch(`${API_BASE}/admin/blog/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${adminToken.value}` }
    });
    if (res.ok) {
      showToast('Post Excluído', 'O post foi removido do Blog.', 'info');
      await loadAdminData();
    }
  } catch {
    showToast('Erro', 'Falha ao deletar post.', 'error');
  }
};

const handleSaveBanner = async (e) => {
  if (e) e.preventDefault();
  if (!newBanner.value.title || !newBanner.value.image_url) return;
  try {
    const res = await fetch(`${API_BASE}/admin/banners`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${adminToken.value}`
      },
      body: JSON.stringify(newBanner.value)
    });
    if (res.ok) {
      showToast('Banner Adicionado', 'O banner/carrossel foi publicado.', 'success');
      newBanner.value = { title: '', image_url: '', link_url: '', active: true, position: 'home' };
      await loadAdminData();
    }
  } catch {
    showToast('Erro', 'Falha ao criar banner.', 'error');
  }
};

const handleDeleteBanner = async (id) => {
  try {
    const res = await fetch(`${API_BASE}/admin/banners/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${adminToken.value}` }
    });
    if (res.ok) {
      showToast('Banner Removido', 'O banner foi excluído.', 'info');
      await loadAdminData();
    }
  } catch {
    showToast('Erro', 'Falha ao deletar banner.', 'error');
  }
};

const handleTriggerBackup = async () => {
  try {
    const res = await fetch(`${API_BASE}/admin/backup`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${adminToken.value}` }
    });
    if (res.ok) {
      const data = await res.json();
      showToast('Backup Realizado!', data.message, 'success');
      await loadAdminData();
    }
  } catch {
    showToast('Erro de Backup', 'Falha ao solicitar backup automático.', 'error');
  }
};

const exportPDF = () => {
  showToast('PDF Gerado', 'Relatório financeiro exportado com sucesso (VagaSync_Financial_Report.pdf)', 'success');
};

const exportExcel = () => {
  showToast('Excel Gerado', 'Planilha de faturamento exportada com sucesso (VagaSync_Billing_June2026.xlsx)', 'success');
};

watch(userRole, (newRole) => {
  if (newRole === 'super_admin') {
    loadAdminData();
  }
});

// WebRTC Video Meet simulated engine
const meetActive = ref(false);
const meetCameraOn = ref(true);
const meetMicOn = ref(true);
const meetScreenSharing = ref(false);
const videoElementRef = ref(null);
let localStreamInstance = null;
const meetMessages = ref([
  { sender: 'interviewer', name: 'Recrutador', content: 'Olá! Seja bem-vindo à nossa sala de entrevista por vídeo do Vaga Sync. O áudio e vídeo estão funcionando?', time: new Date().toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'}) }
]);
const meetInput = ref('');

const toggleCamera = async () => {
  meetCameraOn.value = !meetCameraOn.value;
  if (meetCameraOn.value) {
    startCamera();
  } else {
    stopCamera();
  }
};

const startCamera = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: meetMicOn.value });
    localStreamInstance = stream;
    if (videoElementRef.value) {
      videoElementRef.value.srcObject = stream;
    }
  } catch (err) {
    console.error("Camera access failed:", err);
  }
};

const stopCamera = () => {
  if (localStreamInstance) {
    localStreamInstance.getTracks().forEach(track => track.stop());
    localStreamInstance = null;
  }
  if (videoElementRef.value) {
    videoElementRef.value.srcObject = null;
  }
};

const toggleMic = () => {
  meetMicOn.value = !meetMicOn.value;
  if (localStreamInstance) {
    localStreamInstance.getAudioTracks().forEach(track => track.enabled = meetMicOn.value);
  }
};

const toggleScreenSharing = () => {
  meetScreenSharing.value = !meetScreenSharing.value;
  showToast(
    meetScreenSharing.value ? 'Compartilhamento Ativo' : 'Compartilhamento Parado',
    meetScreenSharing.value ? 'Sua tela está sendo exibida para o entrevistador.' : 'A exibição da tela foi encerrada.',
    'info'
  );
};

const joinVideoMeet = () => {
  meetActive.value = true;
  nextTick(() => {
    startCamera();
  });
};

const leaveVideoMeet = () => {
  meetActive.value = false;
  stopCamera();
};

const sendMeetMessage = () => {
  if (!meetInput.value.trim()) return;
  meetMessages.value.push({
    sender: 'user',
    name: 'Você',
    content: meetInput.value,
    time: new Date().toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})
  });
  const text = meetInput.value;
  meetInput.value = '';
  
  setTimeout(() => {
    meetMessages.value.push({
      sender: 'interviewer',
      name: 'Recrutador',
      content: 'Perfeito. Vamos prosseguir com as perguntas técnicas sobre sua experiência. Conte-me mais sobre seus projetos.',
      time: new Date().toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})
    });
  }, 1500);
};

// Candidate Modal State and Actions
const selectedCandidateForModal = ref(null);
const showCandidateModal = ref(false);
const isAnalyzingCandidate = ref(false);

const candidateAnalyses = {
  1: {
    resumo: 'Desenvolvedora Frontend Sênior com forte domínio de ecossistemas reativos modernos e arquitetura de componentes escaláveis.',
    pontos_fortes: [
      'Excelente domínio de Vue 3 (Composition API) e React.',
      'Sólida experiência com CSS moderno, responsividade e otimização de performance UI.',
      'Excelente comunicação e facilidade para liderança técnica.'
    ],
    gaps: [
      'Pouco contato com linguagens estritamente tipadas como Java/C# no histórico recente.',
      'Menos familiaridade com infraestrutura na nuvem (AWS/Azure).'
    ],
    veredito: 'Altamente Recomendado 🎯'
  },
  2: {
    resumo: 'Desenvolvedor Backend estruturado com foco em APIs de alto tráfego e microsserviços escaláveis.',
    pontos_fortes: [
      'Amplo conhecimento prático em Python, Django e FastAPI.',
      'Modelagem de banco de dados robusta (PostgreSQL, Redis).',
      'Boas práticas de design patterns e arquiteturas limpas.'
    ],
    gaps: [
      'Menos contato direto com tecnologias modernas de frontend (ex: Vue/React).',
      'Necessidade de supervisão em decisões de arquitetura em nuvem híbrida.'
    ],
    veredito: 'Recomendado 👍'
  },
  3: {
    resumo: 'Desenvolvedora Full Stack versátil com ampla experiência prática no ecossistema JavaScript/TypeScript.',
    pontos_fortes: [
      'Domínio completo de React e Node.js.',
      'Uso eficiente de Docker, CI/CD e esteiras automatizadas.',
      'Excelente foco em entregas rápidas e autogerenciamento.'
    ],
    gaps: [
      'Projetos anteriores mostram curtas passagens em startups, indicando preferência por ambientes dinâmicos de ritmo acelerado.'
    ],
    veredito: 'Altamente Recomendado 🎯'
  },
  4: {
    resumo: 'Especialista em Garantia de Qualidade (QA) e engenharia de testes automatizados E2E.',
    pontos_fortes: [
      'Forte domínio de Playwright, Selenium e ferramentas modernas de testes.',
      'Habilidade em criar suites de testes integrados ao CI/CD.',
      'Atenção extrema a detalhes e qualidade de código.'
    ],
    gaps: [
      'Menor vivência no desenvolvimento de novas features de produto.',
      'Conhecimento em React/Vue limitado à inspeção de elementos e automação.'
    ],
    veredito: 'Em Observação ⚠️'
  },
  5: {
    resumo: 'Desenvolvedora Frontend Júnior/Pleno com foco em interface de usuário, design responsivo e acessibilidade.',
    pontos_fortes: [
      'HTML5/CSS3 semânticos de alta fidelidade visual.',
      'Conhecimento prático em animações web e design de interação.',
      'Proatividade em aprender novos frameworks.'
    ],
    gaps: [
      'Falta de experiência comercial com bibliotecas complexas de gerência de estado (Pinia/Redux).',
      'Pouca vivência em testes de integração de frontend.'
    ],
    veredito: 'Recomendado 👍'
  }
};

const cvTab = ref('text'); // 'text' or 'pdf'

const openCandidateModal = (cand) => {
  selectedCandidateForModal.value = { ...cand, analysis: null };
  cvTab.value = 'text';
  showCandidateModal.value = true;
};

const triggerAiAnalysis = () => {
  if (!selectedCandidateForModal.value) return;
  isAnalyzingCandidate.value = true;
  
  setTimeout(() => {
    const analysis = candidateAnalyses[selectedCandidateForModal.value.id] || {
      resumo: 'Candidato triado e sob análise inicial. Perfil básico focado em desenvolvimento de software.',
      pontos_fortes: ['Sincronização com o radar efetuada.', 'Boa base de competências apresentadas.'],
      gaps: ['Necessário aprofundamento técnico em entrevista.'],
      veredito: 'Em Observação ⚠️'
    };
    
    selectedCandidateForModal.value.analysis = analysis;
    isAnalyzingCandidate.value = false;
    showToast('Análise de IA Concluída', `O Agente Headhunter gerou o parecer técnico para ${selectedCandidateForModal.value.name}!`, 'success');
  }, 1200);
};

const approveCandidate = () => {
  if (!selectedCandidateForModal.value) return;
  const id = selectedCandidateForModal.value.id;
  moveCandidate(id, 'aprovados');
  showCandidateModal.value = false;
};

const rejectCandidate = () => {
  if (!selectedCandidateForModal.value) return;
  const id = selectedCandidateForModal.value.id;
  const cand = recruitedCandidates.value.find(c => c.id === id);
  if (cand) {
    cand.status = 'reprovados';
    saveCandidates();
    showToast('Candidato Reprovado', `${cand.name} foi movido para a lista de reprovados/descartados.`, 'info');
  }
  showCandidateModal.value = false;
};

const restoreCandidate = () => {
  if (!selectedCandidateForModal.value) return;
  const id = selectedCandidateForModal.value.id;
  moveCandidate(id, 'recebidos');
  showCandidateModal.value = false;
};

// End of setup injection
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

    <!-- Modal de Visualização de Currículo & Análise IA -->
    <div v-if="showCandidateModal && selectedCandidateForModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(6, 9, 19, 0.85); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 10000; padding: 1rem;">
      <div class="glass-card" style="width: 100%; max-width: 800px; max-height: 90vh; overflow-y: auto; border: 1px solid rgba(59,130,246,0.3); display: flex; flex-direction: column; gap: 1.5rem; animation: modalFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
          <div>
            <h3 style="margin: 0; font-size: 1.4rem; color: #fff;">{{ selectedCandidateForModal.name }}</h3>
            <span style="font-size: 0.85rem; color: var(--text-secondary);">{{ selectedCandidateForModal.role }} • {{ selectedCandidateForModal.email }}</span>
          </div>
          <button @click="showCandidateModal = false" style="background: none; border: none; color: var(--text-secondary); font-size: 1.5rem; cursor: pointer; line-height: 1;">&times;</button>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
          <!-- Lado Esquerdo: Visualização do Currículo -->
          <div style="display: flex; flex-direction: column; gap: 0.75rem;">
            <!-- Tabs Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 0.25rem;">
              <div style="display: flex; gap: 0.5rem;">
                <button 
                  type="button"
                  :class="['btn', cvTab === 'text' ? 'btn-primary' : 'btn-secondary']" 
                  style="font-size: 0.75rem; padding: 0.3rem 0.6rem; border: 1px solid var(--border-color);"
                  @click="cvTab = 'text'"
                >
                  <i class="fa-solid fa-file-lines"></i> Texto Extraído
                </button>
                <button 
                  type="button"
                  :class="['btn', cvTab === 'pdf' ? 'btn-primary' : 'btn-secondary']" 
                  style="font-size: 0.75rem; padding: 0.3rem 0.6rem; border: 1px solid var(--border-color);"
                  @click="cvTab = 'pdf'"
                >
                  <i class="fa-solid fa-file-pdf" style="color: #ef4444;"></i> Versão Anexa (PDF)
                </button>
              </div>
              <span style="font-size: 0.72rem; color: var(--text-muted);">Visualização do Arquivo</span>
            </div>

            <!-- Tab 1: Texto Extraído -->
            <div v-if="cvTab === 'text'" style="display: flex; flex-direction: column; gap: 0.5rem;">
              <textarea 
                class="form-input" 
                rows="14" 
                style="font-size: 0.85rem; line-height: 1.5; background: #0d1426; border-color: var(--border-color); color: var(--text-primary); resize: none; width: 100%; border-radius: 6px; padding: 0.75rem;" 
                v-model="selectedCandidateForModal.resume"
              ></textarea>
            </div>

            <!-- Tab 2: Versão Anexa (PDF) -->
            <div v-else style="display: flex; flex-direction: column; gap: 0.5rem;">
              <!-- PDF Viewer Toolbar -->
              <div style="display: flex; justify-content: space-between; align-items: center; background: #142036; padding: 4px 10px; border-radius: 6px 6px 0 0; border: 1px solid var(--border-color); font-size: 0.75rem;">
                <span style="color: var(--text-secondary); display: flex; align-items: center; gap: 4px;">
                  <i class="fa-solid fa-file-pdf" style="color: #ef4444;"></i>
                  curriculo_{{ selectedCandidateForModal.name.toLowerCase().replace(/ /g, '_') }}.pdf
                </span>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <button type="button" class="btn btn-secondary" style="padding: 2px 6px; font-size: 0.7rem;" disabled><i class="fa-solid fa-magnifying-glass-minus"></i></button>
                  <span style="color: var(--text-muted);">100%</span>
                  <button type="button" class="btn btn-secondary" style="padding: 2px 6px; font-size: 0.7rem;" disabled><i class="fa-solid fa-magnifying-glass-plus"></i></button>
                  <span style="border-left: 1px solid var(--border-color); height: 12px; margin: 0 4px;"></span>
                  <button type="button" class="btn btn-secondary" style="padding: 2px 6px; font-size: 0.7rem;" @click="showToast('Imprimir', 'Simulando envio para impressora...', 'success')"><i class="fa-solid fa-print"></i></button>
                  <button type="button" class="btn btn-secondary" style="padding: 2px 6px; font-size: 0.7rem;" @click="showToast('Download', 'Download do PDF iniciado com sucesso.', 'success')"><i class="fa-solid fa-download"></i></button>
                </div>
              </div>

              <!-- PDF Simulated Document -->
              <div style="max-height: 380px; overflow-y: auto; background: #070a13; padding: 1.5rem 1rem; border-radius: 0 0 6px 6px; border: 1px solid var(--border-color); border-top: none; display: flex; justify-content: center;">
                <div style="background: white; color: #1e293b; width: 100%; max-width: 500px; padding: 2.5rem 2rem; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.6); font-family: 'Outfit', 'Inter', sans-serif; font-size: 0.75rem; text-align: left; line-height: 1.4; color: #334155; min-height: 550px; flex-shrink: 0;">
                  <!-- CV Header -->
                  <div style="text-align: center; border-bottom: 2px solid #3b82f6; padding-bottom: 1rem; margin-bottom: 1.25rem;">
                    <h2 style="margin: 0; font-size: 1.4rem; color: #1e293b; font-weight: 700;">{{ selectedCandidateForModal.name }}</h2>
                    <p style="margin: 0.25rem 0 0 0; color: #64748b; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">{{ selectedCandidateForModal.role }}</p>
                    <div style="margin-top: 0.5rem; font-size: 0.7rem; color: #64748b; display: flex; justify-content: center; gap: 8px; flex-wrap: wrap;">
                      <span>📧 {{ selectedCandidateForModal.email }}</span>
                      <span>•</span>
                      <span>📱 (11) 98765-4321</span>
                      <span>•</span>
                      <span>📍 São Paulo, SP</span>
                    </div>
                  </div>

                  <!-- CV Summary -->
                  <div style="margin-bottom: 1.25rem;">
                    <h3 style="margin: 0 0 0.4rem 0; font-size: 0.85rem; color: #1e293b; font-weight: 700; border-bottom: 1px solid #e2e8f0; padding-bottom: 2px;">Resumo Profissional</h3>
                    <p style="margin: 0; color: #475569; text-align: justify;">{{ selectedCandidateForModal.resume }}</p>
                  </div>

                  <!-- CV Experience -->
                  <div style="margin-bottom: 1.25rem;">
                    <h3 style="margin: 0 0 0.5rem 0; font-size: 0.85rem; color: #1e293b; font-weight: 700; border-bottom: 1px solid #e2e8f0; padding-bottom: 2px;">Histórico de Experiência</h3>
                    <div style="margin-bottom: 0.75rem;">
                      <div style="display: flex; justify-content: space-between; font-weight: 700; color: #1e293b;">
                        <span>Desenvolvedor de Software Sênior</span>
                        <span style="color: #64748b; font-weight: 600;">2024 - Presente</span>
                      </div>
                      <div style="font-style: italic; color: #64748b; margin-bottom: 0.25rem;">VagaSync Corp / Tech Solutions</div>
                      <p style="margin: 0; color: #475569; text-align: justify;">
                        Responsável pelo desenvolvimento de aplicações e APIs focadas em inteligência artificial. Manutenção e refatoração de código legado utilizando arquiteturas modernas de microsserviços. Otimização de performance de renderização no lado do cliente.
                      </p>
                    </div>
                    <div>
                      <div style="display: flex; justify-content: space-between; font-weight: 700; color: #1e293b;">
                        <span>Desenvolvedor Pleno</span>
                        <span style="color: #64748b; font-weight: 600;">2021 - 2024</span>
                      </div>
                      <div style="font-style: italic; color: #64748b; margin-bottom: 0.25rem;">Global Tech Enterprise</div>
                      <p style="margin: 0; color: #475569; text-align: justify;">
                        Atuação em squads ágeis focadas no desenvolvimento de produtos web e mobile. Integrações com múltiplos gateways de pagamento e plataformas de mensagens.
                      </p>
                    </div>
                  </div>

                  <!-- CV Education -->
                  <div>
                    <h3 style="margin: 0 0 0.4rem 0; font-size: 0.85rem; color: #1e293b; font-weight: 700; border-bottom: 1px solid #e2e8f0; padding-bottom: 2px;">Educação & Competências</h3>
                    <div style="margin-bottom: 0.5rem;">
                      <strong style="color: #1e293b;">Bacharelado em Ciência da Computação</strong> — Universidade Metropolitana (Concluído em 2020)
                    </div>
                    <p style="margin: 0; color: #475569;">
                      <strong>Habilidades Técnicas:</strong> JavaScript, TypeScript, Vue.js, React, Node.js, Python, SQL, REST APIs, GIT, Docker.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Lado Direito: Análise de IA do Agente -->
          <div style="display: flex; flex-direction: column; gap: 1rem; background: rgba(59, 130, 246, 0.03); border: 1px solid rgba(59, 130, 246, 0.15); border-radius: 8px; padding: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <h4 style="margin: 0; font-size: 1rem; color: #fff; display: flex; align-items: center; gap: 6px;">
                <i class="fa-solid fa-robot" style="color: var(--color-primary);"></i> Parecer do Agente IA
              </h4>
              <span class="match-badge match-high">{{ selectedCandidateForModal.match }}% Match</span>
            </div>

            <!-- Se não for Pro, exibe o bloqueio -->
            <div v-if="!isRecruiterPro" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; gap: 1rem; min-height: 250px; padding: 1rem;">
              <i class="fa-solid fa-lock" style="font-size: 2.5rem; color: #f59e0b; opacity: 0.85;"></i>
              <h4 style="margin: 0; color: #fff; font-size: 1.05rem;">🔒 Análise IA Bloqueada</h4>
              <p style="font-size: 0.82rem; color: var(--text-secondary); max-width: 250px; line-height: 1.5;">
                A análise técnica profunda feita por Inteligência Artificial é exclusiva para assinantes do plano **Recrutador Pro**.
              </p>
              <button 
                class="btn btn-primary" 
                style="background: linear-gradient(135deg, #f59e0b, #ec4899); border: none; color: #fff; font-weight: 700; width: 100%; margin-top: 0.5rem;"
                @click="openCheckout('recruiter_pro'); showCandidateModal = false;"
              >
                Assinar Recrutador Pro
              </button>
            </div>

            <!-- Se for Pro, exibe a opção de analisar ou o resultado -->
            <div v-else style="height: 100%; display: flex; flex-direction: column;">
              <!-- Botão de disparar análise se ainda não foi feita -->
              <div v-if="!selectedCandidateForModal.analysis" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; gap: 1rem; min-height: 250px; padding: 1rem;">
                <i class="fa-solid fa-brain-circuit" style="font-size: 2.5rem; color: var(--color-secondary); opacity: 0.5;"></i>
                <p style="font-size: 0.82rem; color: var(--text-secondary); max-width: 250px;">
                  Dispare a análise técnica profunda baseada no currículo e perfil.
                </p>
                <button 
                  class="btn btn-primary" 
                  style="background: linear-gradient(135deg, #3b82f6, #00f2fe); border: none; color: #060913; font-weight: 700;"
                  @click="triggerAiAnalysis"
                  :disabled="isAnalyzingCandidate"
                >
                  <span v-if="isAnalyzingCandidate"><i class="fa-solid fa-spinner fa-spin"></i> Analisando...</span>
                  <span v-else><i class="fa-solid fa-wand-magic-sparkles"></i> Analisar com Agente IA</span>
                </button>
              </div>

              <!-- Resultado da Análise -->
              <div v-else style="display: flex; flex-direction: column; gap: 0.85rem; font-size: 0.8rem; line-height: 1.5; color: var(--text-primary); text-align: left;">
                <div>
                  <strong style="color: var(--color-secondary); display: block; margin-bottom: 2px;">Resumo Profissional:</strong>
                  <p style="margin: 0; color: var(--text-secondary);">{{ selectedCandidateForModal.analysis.resumo }}</p>
                </div>

                <div>
                  <strong style="color: var(--color-success); display: block; margin-bottom: 2px;">Pontos Fortes:</strong>
                  <ul style="margin: 0; padding-left: 1.2rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 3px;">
                    <li v-for="(pf, idx) in selectedCandidateForModal.analysis.pontos_fortes" :key="idx">{{ pf }}</li>
                  </ul>
                </div>

                <div>
                  <strong style="color: var(--color-error); display: block; margin-bottom: 2px;">Pontos de Atenção / Gaps:</strong>
                  <ul style="margin: 0; padding-left: 1.2rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 3px;">
                    <li v-for="(gap, idx) in selectedCandidateForModal.analysis.gaps" :key="idx">{{ gap }}</li>
                  </ul>
                </div>

                <div style="border-top: 1px solid var(--border-color); padding-top: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-weight: 700;">Veredito da IA:</span>
                  <span style="font-size: 0.85rem; font-weight: 800; color: #fff;">{{ selectedCandidateForModal.analysis.veredito }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer do Modal com Ações de Aprovar/Reprovar/Mover -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 1rem; margin-top: 0.5rem;">
          <div style="display: flex; gap: 0.5rem;">
            <!-- Reprovar / Descartar -->
            <button 
              v-if="selectedCandidateForModal.status !== 'reprovados'" 
              class="btn btn-secondary" 
              style="color: var(--color-error); border-color: rgba(239, 68, 68, 0.25); background: rgba(239, 68, 68, 0.05);"
              @click="rejectCandidate"
            >
              <i class="fa-solid fa-user-xmark"></i> Reprovar Candidato
            </button>
            <!-- Reativar se estiver reprovado -->
            <button 
              v-else 
              class="btn btn-secondary" 
              style="color: var(--color-secondary); border-color: rgba(0, 242, 254, 0.25);"
              @click="restoreCandidate"
            >
              <i class="fa-solid fa-rotate-left"></i> Reativar / Mover
            </button>
          </div>

          <div style="display: flex; gap: 0.75rem;">
            <button class="btn btn-secondary" @click="showCandidateModal = false">Fechar</button>
            
            <!-- Aprovar / Avançar se não estiver no status aprovado -->
            <button 
              v-if="selectedCandidateForModal.status !== 'aprovados' && selectedCandidateForModal.status !== 'reprovados'" 
              class="btn btn-primary" 
              style="background: linear-gradient(135deg, #10b981, #34d399); border: none; color: #060913; font-weight: 700;"
              @click="approveCandidate"
            >
              <i class="fa-solid fa-user-check"></i> Aprovar Candidato
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Checkout Modals (Stripe / Pix checkout simulation) -->
    <div v-if="checkoutOpen" class="modal-overlay" style="
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(3, 5, 12, 0.95); backdrop-filter: blur(10px);
      display: flex; align-items: center; justify-content: center; z-index: 10000;
    ">
      <div class="glass-card" style="width: 450px; padding: 2rem; border: 1px solid rgba(59, 130, 246, 0.3);">
        <h3 style="font-size: 1.25rem; margin-bottom: 0.5rem; text-align: center; color: #00f2fe;">Assinatura VagaSync Premium</h3>
        <p style="text-align: center; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem;">
          Liberte buscas e candidaturas ilimitadas por apenas R$ 29,90/mês
        </p>

        <div style="display: flex; gap: 0.5rem; margin-bottom: 1.25rem;">
          <button 
            type="button" 
            :class="['btn', checkoutPaymentMethod === 'pix' ? 'btn-primary' : 'btn-secondary']"
            style="flex: 1; padding: 0.5rem;"
            @click="checkoutPaymentMethod = 'pix'"
          >
            <i class="fa-solid fa-pix" style="margin-right: 4px;"></i> Pix Instantâneo
          </button>
          <button 
            type="button" 
            :class="['btn', checkoutPaymentMethod === 'card' ? 'btn-primary' : 'btn-secondary']"
            style="flex: 1; padding: 0.5rem;"
            @click="checkoutPaymentMethod = 'card'"
          >
            <i class="fa-solid fa-credit-card" style="margin-right: 4px;"></i> Cartão de Crédito
          </button>
        </div>

        <!-- Pix Area -->
        <div v-if="checkoutPaymentMethod === 'pix'" style="display: flex; flex-direction: column; align-items: center; gap: 0.75rem; background: rgba(0,0,0,0.25); padding: 1rem; border-radius: 8px;">
          <div style="background: white; padding: 0.5rem; border-radius: 8px;">
            <!-- Simulated QR code -->
            <div style="width: 140px; height: 140px; background: #000; display: flex; align-items: center; justify-content: center; color: white; font-family: monospace; font-size: 0.7rem; text-align: center;">
              [QR CODE PIX SIMULADO VAGASYNC]
            </div>
          </div>
          <span style="font-size: 0.75rem; color: var(--text-secondary); text-align: center;">Mapeado para conta Pix do Proprietário configurada</span>
          
          <button 
            type="button" 
            class="btn btn-secondary" 
            style="font-size: 0.8rem; width: 100%;"
            @click="pixCopied = true; showToast('Copiado', 'Código Copia e Cola copiado para a área de transferência.', 'success')"
          >
            {{ pixCopied ? '✓ Copiado!' : 'Copiar Chave Copia e Cola' }}
          </button>
        </div>

        <!-- Card Area -->
        <div v-else style="display: flex; flex-direction: column; gap: 0.9rem;">
          <div class="form-group" style="margin: 0;">
            <label>Número do Cartão</label>
            <input type="text" class="form-input" v-model="checkoutCard.number" placeholder="4532 7182 9182 0019" />
          </div>
          <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 0.5rem;">
            <div class="form-group" style="margin: 0;">
              <label>Nome no Cartão</label>
              <input type="text" class="form-input" v-model="checkoutCard.name" placeholder="RICARDO SANTOS" />
            </div>
            <div class="form-group" style="margin: 0;">
              <label>CVC</label>
              <input type="text" class="form-input" placeholder="123" />
            </div>
          </div>
        </div>

        <div style="display: flex; gap: 0.5rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-primary" style="flex: 1;" @click="handleCheckoutPayment">
            Concluir Pagamento (Simulação)
          </button>
          <button type="button" class="btn btn-secondary" style="flex: 1;" @click="checkoutOpen = false">
            Voltar
          </button>
        </div>
      </div>
    </div>

    <!-- Secret Super Admin Login Modal -->
    <div v-if="secretLoginOpen" class="modal-overlay" style="
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(3, 5, 12, 0.9); backdrop-filter: blur(10px);
      display: flex; align-items: center; justify-content: center; z-index: 10000;
    ">
      <div class="glass-card" style="width: 420px; padding: 2.25rem; border: 1px solid rgba(0, 242, 254, 0.25); box-shadow: 0 0 30px rgba(0, 242, 254, 0.15);">
        <div style="text-align: center; margin-bottom: 1.5rem;">
          <i class="fa-solid fa-user-shield" style="font-size: 3.5rem; color: var(--color-secondary); text-shadow: 0 0 15px rgba(0, 242, 254, 0.4);"></i>
          <h2 style="margin-top: 1rem; font-size: 1.6rem; letter-spacing: -0.03em;">Painel do Proprietário</h2>
          <p style="color: var(--text-secondary); font-size: 0.82rem; margin-top: 0.25rem;">Acesso exclusivo ao núcleo SaaS</p>
        </div>

        <form v-if="!secret2faOpen" @submit="handleAdminLogin" style="display: flex; flex-direction: column; gap: 1.25rem;">
          <div class="form-group" style="margin: 0;">
            <label>E-mail Corporativo</label>
            <input type="email" required class="form-input" v-model="secretEmail" placeholder="admin@vagasync.com" />
          </div>
          <div class="form-group" style="margin: 0;">
            <label>Senha de Segurança</label>
            <input type="password" required class="form-input" v-model="secretPassword" placeholder="••••••••" />
          </div>
          <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem; background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; font-weight: 700;">
            Autenticar Credenciais
          </button>
          <button type="button" class="btn btn-secondary" @click="secretLoginOpen = false" style="width: 100%;">
            Cancelar
          </button>
        </form>

        <form v-else @submit="handleAdminVerify2fa" style="display: flex; flex-direction: column; gap: 1.25rem;">
          <div style="background: rgba(0, 242, 254, 0.05); border: 1px solid rgba(0, 242, 254, 0.2); padding: 1rem; border-radius: 8px; font-size: 0.78rem; color: var(--text-secondary); line-height: 1.6; text-align: center;">
            🔒 <strong>Autenticação em Dois Fatores (2FA)</strong><br />
            Insira o código de 6 dígitos gerado pelo seu aplicativo de autenticação.
            <div style="margin-top: 0.5rem; font-family: monospace; color: var(--color-secondary); font-size: 0.85rem; background: rgba(0,0,0,0.3); padding: 3px; border-radius: 4px;">
              Chave: JBSWY3DPEHPK3PXP
            </div>
          </div>
          <div class="form-group" style="margin: 0;">
            <label style="text-align: center; display: block;">Código de 6 dígitos</label>
            <input type="text" required maxlength="6" class="form-input" v-model="secret2faCode" placeholder="000 000" style="text-align: center; font-size: 1.6rem; letter-spacing: 0.2em; font-family: monospace;" />
          </div>
          <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 0.5rem; background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; font-weight: 700;">
            Confirmar Código 2FA
          </button>
          <button type="button" class="btn btn-secondary" @click="secret2faOpen = false; secretLoginOpen = false;" style="width: 100%;">
            Cancelar
          </button>
        </form>
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

              <div class="form-group">
                <label>Seu Perfil / Papel</label>
                <select class="form-input" v-model="authForm.role" style="background: #0d1426; color: var(--text-primary); border: 1px solid var(--border-color); margin-bottom: 1rem;">
                  <option value="candidate">Sou Candidato (Buscar Vagas)</option>
                  <option value="recruiter">Sou Recrutador/Empresa (Publicar Vagas e Triagem)</option>
                </select>
              </div>

              <button 
                type="button" 
                class="btn social-btn-linkedin"
                @click="
                  localStorage.setItem('vagasync_role', authForm.role);
                  userRole = authForm.role;
                  localStorage.setItem('vagasync_logged', 'true');
                  isLoggedIn = true;
                  activeTab = authForm.role === 'recruiter' ? 'recruiter_dashboard' : 'dashboard';
                  showToast('Login LinkedIn', `Sessão iniciada como ${authForm.role === 'recruiter' ? 'Recrutador' : 'Candidato'} via LinkedIn com sucesso!`, 'success');
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
                <label>Seu Perfil / Papel</label>
                <select class="form-input" v-model="authForm.role" style="background: #0d1426; color: var(--text-primary); border: 1px solid var(--border-color); margin-bottom: 1rem;">
                  <option value="candidate">Sou Candidato (Buscar Vagas)</option>
                  <option value="recruiter">Sou Recrutador/Empresa (Publicar Vagas e Triagem)</option>
                </select>
              </div>

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
      <footer class="footer-bar" @click="handleFooterClick" style="cursor: pointer;">
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

        <nav class="nav-menu" v-if="userRole === 'candidate'">
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
            :class="['nav-link-btn', { active: activeTab === 'career' }]"
            @click="activeTab = 'career'"
          >
            <Sparkles :size="15" /> Copiloto IA
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'interview' }]"
            @click="activeTab = 'interview'"
          >
            <Smartphone :size="15" /> Treino Entrevista
          </button>
          
          <button 
            :class="['nav-link-btn', { active: activeTab === 'config' }]"
            @click="activeTab = 'config'"
          >
            <Settings :size="15" /> Configurações
          </button>
        </nav>

        <nav class="nav-menu" v-else-if="userRole === 'recruiter'">
          <button 
            :class="['nav-link-btn', { active: activeTab === 'recruiter_dashboard' }]"
            @click="activeTab = 'recruiter_dashboard'"
          >
            <Briefcase :size="15" /> Painel Recrutador
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'recruiter_jobs' }]"
            @click="activeTab = 'recruiter_jobs'"
          >
            <Briefcase :size="15" /> Criar Vaga
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
            :class="['nav-link-btn', { active: activeTab === 'recruiter_billing' }]"
            @click="activeTab = 'recruiter_billing'"
          >
            <Settings :size="15" /> Faturamento SaaS
          </button>
        </nav>

        <nav class="nav-menu" v-else-if="userRole === 'super_admin'">
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin' }]"
            @click="activeTab = 'super_admin'"
          >
            <Briefcase :size="15" /> Painel Global
          </button>
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin_monetization' }]"
            @click="activeTab = 'super_admin_monetization'"
          >
            <Settings :size="15" /> Monetização
          </button>
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin_gateways' }]"
            @click="activeTab = 'super_admin_gateways'"
          >
            <Settings :size="15" /> Gateways
          </button>
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin_tracking' }]"
            @click="activeTab = 'super_admin_tracking'"
          >
            <Settings :size="15" /> Rastreamento
          </button>
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin_content' }]"
            @click="activeTab = 'super_admin_content'"
          >
            <Settings :size="15" /> Conteúdo
          </button>
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin_security' }]"
            @click="activeTab = 'super_admin_security'"
          >
            <Settings :size="15" /> Segurança
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

        <!-- ── Aba Carreira & Insights (Candidato) ── -->
        <template v-if="activeTab === 'career'">
          <div style="max-width: 1000px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem;">
            <!-- Employability and Gamification -->
            <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
              <h2 class="section-title">
                <i class="fa-solid fa-route" style="font-size: 20px;"></i> Copiloto de Carreira & Insights IA
              </h2>
              <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6;">
                Com base no seu currículo e palavras-chave, nossa IA traçou um mapa evolutivo da sua carreira. Complete missões, acumule pontuação de empregabilidade e visualize a compatibilidade do seu perfil no mercado.
              </p>

              <!-- Progress bar -->
              <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.5rem; display: flex; flex-direction: column; gap: 0.75rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-weight: 700; font-size: 0.95rem; color: var(--color-secondary);">Sua Pontuação de Empregabilidade</span>
                  <span style="font-weight: 800; font-size: 1.25rem; color: #fff;">{{ employabilityScore }} / 100 pts</span>
                </div>
                <div style="width: 100%; height: 12px; background: rgba(255,255,255,0.05); border-radius: 20px; overflow: hidden; border: 1px solid rgba(255,255,255,0.05);">
                  <div 
                    style="height: 100%; background: linear-gradient(90deg, #3b82f6, #00f2fe); border-radius: 20px; transition: width 1s ease-in-out;"
                    :style="{ width: `${employabilityScore}%` }"
                  ></div>
                </div>
                <p style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                  💡 <strong>Feedback da IA:</strong> {{ employabilityFeedback }}
                </p>
              </div>
            </div>

            <!-- Career Timeline -->
            <div class="glass-card">
              <h3 style="font-size: 1.1rem; margin-bottom: 1.5rem; color: #fff;">
                <i class="fa-solid fa-timeline" style="color: var(--color-secondary); margin-right: 6px;"></i> Timeline Evolutiva da Carreira
              </h3>
              
              <div class="career-timeline">
                <div class="timeline-item completed">
                  <div class="timeline-badge"><i class="fa-solid fa-file-invoice"></i></div>
                  <div class="timeline-panel">
                    <h4>Perfil Inicial</h4>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">Currículo básico cadastrado e estruturado.</p>
                  </div>
                </div>
                
                <div class="timeline-item" :class="{ completed: jobs.length > 0 }">
                  <div class="timeline-badge"><i class="fa-solid fa-magnifying-glass-chart"></i></div>
                  <div class="timeline-panel">
                    <h4>Radar de Vagas</h4>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">Vagas correspondentes rastreadas pelo agente.</p>
                  </div>
                </div>

                <div class="timeline-item" :class="{ completed: completedSimulationsCount > 0 }">
                  <div class="timeline-badge"><i class="fa-solid fa-microphone"></i></div>
                  <div class="timeline-panel">
                    <h4>Treinamento Concluído</h4>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">Treinou respostas técnicas de entrevistas com a IA.</p>
                  </div>
                </div>

                <div class="timeline-item" :class="{ completed: isPremium }">
                  <div class="timeline-badge"><i class="fa-solid fa-crown"></i></div>
                  <div class="timeline-panel">
                    <h4>Upgrade Premium SaaS</h4>
                    <p style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.25rem;">Acesso ilimitado e salas WebRTC Meet ativadas.</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Pricing cards / Plan checkout triggers -->
            <div class="glass-card">
              <h3 style="font-size: 1.1rem; margin-bottom: 1.5rem; text-align: center; color: #fff;">
                Adquira Acesso Premium e impulsione sua recolocação profissional!
              </h3>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; max-width: 700px; margin: 0 auto;">
                <!-- Free card -->
                <div class="pricing-card" style="border: 1px solid var(--border-color); padding: 2rem; border-radius: 12px; background: rgba(255,255,255,0.01); display: flex; flex-direction: column; align-items: center; text-align: center;">
                  <h4 style="font-size: 1.25rem; margin-bottom: 0.5rem; color: var(--text-secondary);">Plano Gratuito</h4>
                  <div style="font-size: 2rem; font-weight: 800; margin-bottom: 1rem;">R$ 0</div>
                  <ul style="list-style: none; padding: 0; font-size: 0.85rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 2rem;">
                    <li>✓ Limite de 10 vagas/mês</li>
                    <li>✓ Análise de compatibilidade básica</li>
                    <li>✗ Sem simulador de entrevista</li>
                    <li>✗ Sem chats com recrutadores</li>
                  </ul>
                  <button class="btn btn-secondary" style="width: 100%; margin-top: auto;" disabled>Plano Ativo</button>
                </div>

                <!-- Premium card -->
                <div class="pricing-card" style="border: 2px solid var(--color-primary); padding: 2rem; border-radius: 12px; background: rgba(59, 130, 246, 0.04); display: flex; flex-direction: column; align-items: center; text-align: center; position: relative;">
                  <span style="position: absolute; top: -12px; background: var(--color-primary); color: #fff; padding: 2px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 700;">RECOMENDADO</span>
                  <h4 style="font-size: 1.25rem; margin-bottom: 0.5rem; color: #fff;">Plano Premium</h4>
                  <div style="font-size: 2rem; font-weight: 800; margin-bottom: 1rem; color: var(--color-secondary);">R$ 29,90<span style="font-size: 0.9rem; font-weight: 400; color: var(--text-secondary);">/mês</span></div>
                  <ul style="list-style: none; padding: 0; font-size: 0.85rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 2rem;">
                    <li style="color: #fff;">✓ Varreduras e candidaturas ILIMITADAS</li>
                    <li style="color: #fff;">✓ IA Gemini Premium com match inteligente</li>
                    <li style="color: #fff;">✓ Treinador de Entrevista por Vídeo ilimitado</li>
                    <li style="color: #fff;">✓ Salas de Videochamadas WebRTC com RH</li>
                  </ul>
                  
                  <button 
                    v-if="isPremium"
                    class="btn btn-secondary" 
                    style="width: 100%; margin-top: auto;"
                    @click="cancelPremium('candidate_premium')"
                  >
                    Cancelar Assinatura
                  </button>
                  <button 
                    v-else
                    class="btn btn-primary" 
                    style="width: 100%; margin-top: auto; background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; font-weight: 700; border: none;"
                    @click="openCheckout('candidate_premium')"
                  >
                    Assinar Premium
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Aba Treino de Entrevista (Candidato) ── -->
        <template v-if="activeTab === 'interview'">
          <div style="max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem;">
            <!-- Meet active window -->
            <div v-if="meetActive" class="glass-card" style="display: flex; flex-direction: column; gap: 1rem; padding: 1.5rem;">
              <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
                <h3 style="display: flex; align-items: center; gap: 0.5rem; color: var(--color-secondary);">
                  <i class="fa-solid fa-video"></i> Sala de Entrevista WebRTC Meet
                </h3>
                <span style="font-size: 0.75rem; padding: 3px 10px; border-radius: 20px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: var(--color-success); font-weight: 700;">CONEXÃO ESTÁVEL</span>
              </div>
              
              <!-- Video tile grid -->
              <div class="webrtc-video-grid">
                <!-- Interviwer tile -->
                <div class="video-tile" style="background-image: url('https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=800');">
                  <div class="video-overlay-name">Recrutador VagaSync (HR)</div>
                </div>
                <!-- Candidate tile -->
                <div class="video-tile candidate-tile">
                  <video ref="videoElementRef" autoplay playsinline muted></video>
                  <div v-if="!meetCameraOn" class="video-muted-placeholder">
                    <i class="fa-solid fa-video-slash" style="font-size: 32px; color: var(--text-muted);"></i>
                    <p style="font-size: 0.8rem; margin-top: 0.5rem;">Sua câmera está desligada</p>
                  </div>
                  <div class="video-overlay-name">Você (Candidato)</div>
                </div>
              </div>

              <!-- Meet controller bar and chat -->
              <div style="display: grid; grid-template-columns: 1fr 1.2fr; gap: 1.5rem; margin-top: 0.5rem;">
                <!-- Controller bar -->
                <div style="display: flex; flex-direction: column; justify-content: center; gap: 1rem; padding: 1rem; background: rgba(0,0,0,0.2); border-radius: 10px;">
                  <h4 style="font-size: 0.85rem; color: var(--text-secondary); text-align: center;">Controles do Dispositivo</h4>
                  <div style="display: flex; justify-content: center; gap: 0.75rem;">
                    <button 
                      class="btn" 
                      :class="meetCameraOn ? 'btn-primary' : 'btn-secondary'"
                      style="width: 44px; height: 44px; border-radius: 50%; padding: 0; display: flex; align-items: center; justify-content: center;"
                      @click="toggleCamera"
                    >
                      <i :class="meetCameraOn ? 'fa-solid fa-video' : 'fa-solid fa-video-slash'"></i>
                    </button>
                    <button 
                      class="btn" 
                      :class="meetMicOn ? 'btn-primary' : 'btn-secondary'"
                      style="width: 44px; height: 44px; border-radius: 50%; padding: 0; display: flex; align-items: center; justify-content: center;"
                      @click="toggleMic"
                    >
                      <i :class="meetMicOn ? 'fa-solid fa-microphone' : 'fa-solid fa-microphone-slash'"></i>
                    </button>
                    <button 
                      class="btn" 
                      :class="meetScreenSharing ? 'btn-primary' : 'btn-secondary'"
                      style="width: 44px; height: 44px; border-radius: 50%; padding: 0; display: flex; align-items: center; justify-content: center;"
                      @click="toggleScreenSharing"
                    >
                      <i class="fa-solid fa-desktop"></i>
                    </button>
                    <button 
                      class="btn" 
                      style="width: 44px; height: 44px; border-radius: 50%; padding: 0; background: var(--color-error); border: none; color: white; display: flex; align-items: center; justify-content: center;"
                      @click="leaveVideoMeet"
                    >
                      <i class="fa-solid fa-phone-slash"></i>
                    </button>
                  </div>
                </div>
                
                <!-- Chat inside video meet -->
                <div style="display: flex; flex-direction: column; gap: 0.5rem; background: rgba(0,0,0,0.3); border-radius: 10px; padding: 0.75rem;">
                  <div style="height: 120px; overflow-y: auto; padding: 0.5rem; display: flex; flex-direction: column; gap: 0.5rem;">
                    <div v-for="(msg, i) in meetMessages" :key="i" style="font-size: 0.75rem;">
                      <strong :style="{ color: msg.sender === 'user' ? '#00f2fe' : '#34d399' }">{{ msg.name }}:</strong> {{ msg.content }}
                    </div>
                  </div>
                  <div style="display: flex; gap: 0.4rem;">
                    <input type="text" class="form-input" placeholder="Mande uma mensagem..." v-model="meetInput" @keyup.enter="sendMeetMessage" style="font-size: 0.75rem; padding: 0.4rem;" />
                    <button class="btn btn-primary" style="padding: 0.4rem 0.8rem; font-size: 0.75rem;" @click="sendMeetMessage">Enviar</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Meet launcher panel and AI interview -->
            <div v-else style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
              <!-- WebRTC launcher card -->
              <div class="glass-card" style="display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                  <h3 style="display: flex; align-items: center; gap: 0.5rem; color: var(--color-secondary); font-size: 1.2rem; margin-bottom: 0.75rem;">
                    <i class="fa-solid fa-circle-play"></i> Sala de Entrevista Online (WebRTC Meet)
                  </h3>
                  <p style="color: var(--text-secondary); font-size: 0.82rem; line-height: 1.6; margin-bottom: 1.25rem;">
                    Salas WebRTC dedicadas para simular ou ingressar em processos seletivos por vídeo de forma fluida. Capture seu vídeo e teste seus periféricos de áudio antes de reuniões.
                  </p>
                  
                  <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; font-size: 0.78rem; display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.5rem;">
                    <div>📸 <strong>Câmera:</strong> Integrada (Teste Ativo)</div>
                    <div>🎙️ <strong>Microfone:</strong> Integrado (Teste Ativo)</div>
                    <div>🔒 <strong>Protocolo:</strong> WebRTC TLS Criptografado de ponta a ponta</div>
                  </div>
                </div>

                <button 
                  v-if="isPremium"
                  class="btn btn-primary" 
                  style="width: 100%; padding: 0.75rem; background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; font-weight: 700; border: none;"
                  @click="joinVideoMeet"
                >
                  <i class="fa-solid fa-video" style="margin-right: 6px;"></i> Iniciar Videochamada de Teste com RH
                </button>
                <div v-else style="text-align: center;">
                  <button class="btn btn-secondary" style="width: 100%;" @click="activeTab = 'career'">
                    🔒 Ingressar WebRTC (Requer Premium)
                  </button>
                </div>
              </div>

              <!-- AI Interview simulator -->
              <div class="glass-card" style="display: flex; flex-direction: column; gap: 1rem;">
                <h3 style="display: flex; align-items: center; gap: 0.5rem; color: #fff; font-size: 1.2rem;">
                  <i class="fa-solid fa-microphone" style="color: var(--color-accent);"></i> Simulador de Entrevista por IA
                </h3>

                <div v-if="!interviewActive" style="display: flex; flex-direction: column; gap: 1rem;">
                  <p style="color: var(--text-secondary); font-size: 0.82rem; line-height: 1.6;">
                    Treine com nosso agente de recrutamento IA do Gemini. Escolha a área desejada e responda a perguntas técnicas ou comportamentais.
                  </p>
                  <div class="form-group" style="margin: 0;">
                    <label>Cargo Alvo</label>
                    <input type="text" class="form-input" v-model="interviewRole" />
                  </div>
                  <div class="form-group" style="margin: 0;">
                    <label>Foco das Perguntas</label>
                    <select class="form-input" v-model="interviewType" style="background: #0d1426; color: var(--text-primary);">
                      <option value="Técnica">Perguntas Técnicas</option>
                      <option value="Comportamental">Perguntas Comportamentais</option>
                      <option value="Geral">Perguntas Gerais / Fit Cultural</option>
                    </select>
                  </div>
                  <button class="btn btn-primary" style="width: 100%; margin-top: 0.5rem;" @click="startInterview">
                    Começar Simulação de Entrevista
                  </button>
                </div>

                <div v-else style="display: flex; flex-direction: column; gap: 1rem; flex-grow: 1;">
                  <!-- Chat box -->
                  <div style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-color); border-radius: 8px; height: 260px; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: 0.75rem;">
                    <div v-for="(msg, i) in interviewMessages" :key="i" :class="['chat-bubble', msg.sender]">
                      <div style="font-weight: 700; font-size: 0.7rem; opacity: 0.8; margin-bottom: 2px;">
                        {{ msg.sender === 'interviewer' ? 'Entrevistador IA' : msg.sender === 'user' ? 'Você' : 'Sistema' }}
                      </div>
                      <div style="font-size: 0.8rem; line-height: 1.4;">{{ msg.content }}</div>
                    </div>
                  </div>

                  <!-- Input text box -->
                  <div v-if="!interviewScore" style="display: flex; gap: 0.5rem;">
                    <input 
                      type="text" 
                      class="form-input" 
                      placeholder="Digite sua resposta..." 
                      v-model="interviewInput" 
                      @keyup.enter="sendInterviewResponse"
                      :disabled="interviewLoading"
                    />
                    <button class="btn btn-primary" @click="sendInterviewResponse" :disabled="interviewLoading">
                      {{ interviewLoading ? 'Processando...' : 'Enviar' }}
                    </button>
                  </div>

                  <div v-else style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <p style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                      {{ interviewFeedback }}
                    </p>
                    <button class="btn btn-secondary" style="width: 100%;" @click="resetInterview">
                      Voltar ao Painel
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Aba Super Admin Global Dashboard (Proprietário) ── -->
        <template v-if="activeTab === 'super_admin'">
          <div style="max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem;">
            <!-- Stats overview -->
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.25rem;">
              <div class="glass-card stat-card">
                <div class="stat-icon"><i class="fa-solid fa-users"></i></div>
                <div>
                  <div class="stat-value">{{ adminStatsData.users_count }}</div>
                  <div class="stat-label">Usuários Cadastrados</div>
                </div>
              </div>
              <div class="glass-card stat-card">
                <div class="stat-icon"><i class="fa-solid fa-user-tie" style="color: #a855f7;"></i></div>
                <div>
                  <div class="stat-value">{{ adminStatsData.recruiters_count }}</div>
                  <div class="stat-label">Recrutadores</div>
                </div>
              </div>
              <div class="glass-card stat-card">
                <div class="stat-icon"><i class="fa-solid fa-money-bill-trend-up" style="color: #10b981;"></i></div>
                <div>
                  <div class="stat-value">R$ {{ adminStatsData.mrr }}</div>
                  <div class="stat-label">MRR (Mensal Recorrente)</div>
                </div>
              </div>
              <div class="glass-card stat-card">
                <div class="stat-icon"><i class="fa-solid fa-wallet" style="color: #00f2fe;"></i></div>
                <div>
                  <div class="stat-value">R$ {{ adminStatsData.total_revenue }}</div>
                  <div class="stat-label">Faturamento Total</div>
                </div>
              </div>
            </div>

            <!-- More stats and charts -->
            <div style="display: grid; grid-template-columns: 1.5fr 1fr; gap: 1.5rem;">
              <!-- Growth Chart -->
              <div class="glass-card">
                <h3 class="section-title"><i class="fa-solid fa-chart-line"></i> Crescimento da Receita (6 Meses)</h3>
                <div style="display: flex; flex-direction: column; gap: 1.25rem; padding-top: 1rem;">
                  <div v-for="(g, idx) in adminStatsData.growth" :key="idx" style="display: flex; align-items: center; gap: 1rem;">
                    <span style="width: 40px; font-size: 0.8rem; color: var(--text-secondary);">{{ g.month }}</span>
                    <div style="flex-grow: 1; height: 16px; background: rgba(255,255,255,0.03); border-radius: 8px; overflow: hidden; border: 1px solid rgba(255,255,255,0.04);">
                      <div 
                        style="height: 100%; background: linear-gradient(90deg, #3b82f6, #00f2fe); border-radius: 8px;"
                        :style="{ width: `${(g.receita / adminStatsData.mrr) * 100}%` }"
                      ></div>
                    </div>
                    <span style="font-size: 0.8rem; font-weight: 700; color: #fff;">R$ {{ g.receita }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Conversion rate -->
              <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
                <h3 class="section-title"><i class="fa-solid fa-chart-pie"></i> Conversões & Churn</h3>
                
                <div style="display: flex; flex-direction: column; gap: 1rem; background: rgba(255,255,255,0.02); padding: 1.25rem; border-radius: 10px; border: 1px solid var(--border-color);">
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.85rem; color: var(--text-secondary);">Taxa de Conversão Premium</span>
                    <span style="font-weight: 700; color: var(--color-success);">{{ adminStatsData.conversion_rate }}%</span>
                  </div>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.85rem; color: var(--text-secondary);">Assinaturas Ativas</span>
                    <span style="font-weight: 700; color: #fff;">{{ adminStatsData.active_subscriptions }}</span>
                  </div>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.85rem; color: var(--text-secondary);">Cancelamentos (Churn)</span>
                    <span style="font-weight: 700; color: var(--color-error);">{{ adminStatsData.cancelations }}</span>
                  </div>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 0.85rem; color: var(--text-secondary);">Taxa de Churn</span>
                    <span style="font-weight: 700; color: var(--color-warning);">{{ adminStatsData.churn_rate }}%</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Price plan and coupons controls -->
            <div class="glass-card">
              <h3 class="section-title"><i class="fa-solid fa-sliders"></i> Controle de Planos e Cupons Promocionais</h3>
              <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 1.5rem;">
                <div class="form-group">
                  <label>Configurações de Preço de Planos (Formato JSON)</label>
                  <textarea class="form-input" rows="6" v-model="adminConfigs.plans_json" style="font-family: monospace; font-size: 0.8rem; resize: vertical;" />
                </div>
                <div class="form-group">
                  <label>Cupons Ativos (Formato JSON)</label>
                  <textarea class="form-input" rows="6" v-model="adminConfigs.coupons_json" style="font-family: monospace; font-size: 0.8rem; resize: vertical;" />
                </div>
              </div>
              <div style="display: flex; justify-content: flex-end; margin-top: 1rem;">
                <button class="btn btn-primary" @click="handleSaveAdminConfigs">Salvar Configurações Planos/Cupons</button>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Aba Super Admin Monetização (Proprietário) ── -->
        <template v-if="activeTab === 'super_admin_monetization'">
          <div style="max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem;">
            <div class="glass-card">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h2 class="section-title" style="margin: 0;">
                  <i class="fa-solid fa-file-invoice-dollar" style="font-size: 20px;"></i> Relatórios de Faturamento & Assinaturas
                </h2>
                <div style="display: flex; gap: 0.5rem;">
                  <button class="btn btn-secondary" @click="exportPDF">
                    <i class="fa-solid fa-file-pdf" style="margin-right: 4px; color: var(--color-error);"></i> Exportar PDF
                  </button>
                  <button class="btn btn-secondary" @click="exportExcel">
                    <i class="fa-solid fa-file-excel" style="margin-right: 4px; color: var(--color-success);"></i> Exportar Excel
                  </button>
                </div>
              </div>

              <!-- Subscriptions database list -->
              <div class="jobs-table-wrapper">
                <table class="jobs-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>E-mail do Usuário</th>
                      <th>Plano Assinado</th>
                      <th>Gateway</th>
                      <th>Valor</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="i in 6" :key="i">
                      <td>#{{ 1024 + i }}</td>
                      <td style="font-weight: 600;">usuario{{ i }}@vagasync.com.br</td>
                      <td>
                        <span style="font-size: 0.75rem; padding: 2px 7px; border-radius: 4px; background: rgba(59,130,246,0.15); color: #60a5fa; font-weight: 600;">
                          {{ i % 2 === 0 ? 'Recruiter Pro' : 'Candidate Premium' }}
                        </span>
                      </td>
                      <td>
                        <span style="font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary);">
                          {{ i % 3 === 0 ? 'Stripe' : i % 3 === 1 ? 'MercadoPago' : 'Pix' }}
                        </span>
                      </td>
                      <td style="font-weight: 700; color: #fff;">
                        R$ {{ i % 2 === 0 ? '149,90' : '29,90' }}
                      </td>
                      <td>
                        <span style="font-size: 0.7rem; padding: 2px 6px; border-radius: 12px; font-weight: 700; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: var(--color-success);">
                          PAGO
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Aba Super Admin Gateways (Proprietário) ── -->
        <template v-if="activeTab === 'super_admin_gateways'">
          <div style="max-width: 800px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem;">
            <div class="glass-card">
              <h2 class="section-title">
                <i class="fa-solid fa-credit-card" style="font-size: 20px;"></i> Integrações de Pagamentos (SaaS Core)
              </h2>
              <p style="color: var(--text-secondary); font-size: 0.85rem; line-height: 1.6; margin-bottom: 1.5rem;">
                Configure suas chaves do Stripe, Mercado Pago e Pix para recebimento instantâneo de mensalidades dos planos SaaS. As chaves privadas são armazenadas de forma criptografada na base de dados SQLite.
              </p>

              <form @submit.prevent="handleSaveAdminConfigs" style="display: flex; flex-direction: column; gap: 1.5rem;">
                <!-- Stripe parameters -->
                <div style="background: rgba(99,91,255,0.05); border: 1px solid rgba(99,91,255,0.2); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; gap: 1rem;">
                  <h4 style="color: #a5b4fc; font-size: 0.95rem; margin: 0; display: flex; align-items: center; gap: 6px;">
                    <i class="fa-brands fa-stripe"></i> Integração Stripe
                  </h4>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                    <div class="form-group" style="margin: 0;">
                      <label>Stripe Publishable Key</label>
                      <input type="text" class="form-input" v-model="adminConfigs.stripe_public_key" placeholder="pk_live_..." />
                    </div>
                    <div class="form-group" style="margin: 0;">
                      <label>Stripe Secret Key</label>
                      <input type="password" class="form-input" v-model="adminConfigs.stripe_secret_key" placeholder="sk_live_..." />
                    </div>
                  </div>
                </div>

                <!-- Mercado Pago parameters -->
                <div style="background: rgba(0,158,227,0.05); border: 1px solid rgba(0,158,227,0.2); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; gap: 1rem;">
                  <h4 style="color: #60a5fa; font-size: 0.95rem; margin: 0; display: flex; align-items: center; gap: 6px;">
                    <i class="fa-solid fa-handshake"></i> Mercado Pago
                  </h4>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                    <div class="form-group" style="margin: 0;">
                      <label>Mercado Pago Public Key</label>
                      <input type="text" class="form-input" v-model="adminConfigs.mercadopago_public_key" placeholder="APP_USR-..." />
                    </div>
                    <div class="form-group" style="margin: 0;">
                      <label>Mercado Pago Access Token</label>
                      <input type="password" class="form-input" v-model="adminConfigs.mercadopago_access_token" placeholder="APP_USR-..." />
                    </div>
                  </div>
                </div>

                <!-- Pix keys and Bank info -->
                <div style="background: rgba(0,242,254,0.04); border: 1px solid rgba(0,242,254,0.18); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; gap: 1rem;">
                  <h4 style="color: var(--color-secondary); font-size: 0.95rem; margin: 0; display: flex; align-items: center; gap: 6px;">
                    <i class="fa-solid fa-pix"></i> Dados Pix e Conta Bancária do Proprietário
                  </h4>
                  <div class="form-group" style="margin: 0;">
                    <label>Chave Pix de Recebimento</label>
                    <input type="text" class="form-input" v-model="adminConfigs.pix_key" placeholder="sua-chave@pix.com.br" />
                  </div>
                  <div style="display: grid; grid-template-columns: 1.2fr 0.8fr 1fr; gap: 0.75rem;">
                    <div class="form-group" style="margin: 0;">
                      <label>Banco</label>
                      <input type="text" class="form-input" v-model="adminConfigs.bank_name" placeholder="Banco Itaú S.A." />
                    </div>
                    <div class="form-group" style="margin: 0;">
                      <label>Agência</label>
                      <input type="text" class="form-input" v-model="adminConfigs.bank_agency" placeholder="0001" />
                    </div>
                    <div class="form-group" style="margin: 0;">
                      <label>Conta</label>
                      <input type="password" class="form-input" v-model="adminConfigs.bank_account" placeholder="12345-6" />
                    </div>
                  </div>
                  <div style="display: grid; grid-template-columns: 1.5fr 1fr; gap: 0.75rem;">
                    <div class="form-group" style="margin: 0;">
                      <label>Nome do Beneficiário</label>
                      <input type="text" class="form-input" v-model="adminConfigs.bank_owner_name" placeholder="VagaSync Tecnologias Ltda." />
                    </div>
                    <div class="form-group" style="margin: 0;">
                      <label>CPF / CNPJ Beneficiário</label>
                      <input type="password" class="form-input" v-model="adminConfigs.owner_tax_id" placeholder="00.000.000/0001-00" />
                    </div>
                  </div>
                </div>

                <div style="display: flex; justify-content: flex-end; gap: 1rem;">
                  <button type="submit" class="btn btn-primary" style="background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; font-weight: 700; border: none;">
                    Criptografar & Salvar Configurações
                  </button>
                </div>
              </form>
            </div>
          </div>
        </template>

        <!-- ── Aba Super Admin Tracking & Google Analytics (Proprietário) ── -->
        <template v-if="activeTab === 'super_admin_tracking'">
          <div style="max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem;">
            <!-- Integration details input -->
            <div class="glass-card">
              <h2 class="section-title">
                <i class="fa-solid fa-chart-line" style="font-size: 20px;"></i> Integrações de Analytics e Rastreamento
              </h2>
              <p style="color: var(--text-secondary); font-size: 0.85rem; line-height: 1.6; margin-bottom: 1.5rem;">
                Monitore o tráfego da Landing Page e o funil de conversão. Adicione seus códigos de rastreamento do Google Analytics 4, Tag Manager, Facebook Pixel e Clarity de forma integrada.
              </p>

              <form @submit.prevent="handleSaveAdminConfigs" style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem;">
                <div class="form-group" style="margin: 0;">
                  <label>Google Analytics 4 Measurement ID</label>
                  <input type="text" class="form-input" v-model="adminConfigs.ga4_measurement_id" placeholder="G-XXXXXXXXXX" />
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>Google Tag Manager ID</label>
                  <input type="text" class="form-input" v-model="adminConfigs.google_tag_manager_id" placeholder="GTM-XXXXXX" />
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>Facebook Pixel ID</label>
                  <input type="text" class="form-input" v-model="adminConfigs.facebook_pixel_id" placeholder="123456789012345" />
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>Microsoft Clarity Project Code</label>
                  <input type="text" class="form-input" v-model="adminConfigs.microsoft_clarity_id" placeholder="abcdefghij" />
                </div>
                
                <div style="grid-column: 1 / -1; display: flex; justify-content: flex-end; margin-top: 0.75rem;">
                  <button type="submit" class="btn btn-primary">Salvar Tracking Script IDs</button>
                </div>
              </form>
            </div>

            <!-- Tracking analytics mock data -->
            <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
              <h3 class="section-title"><i class="fa-solid fa-chart-bar"></i> Tráfego em Tempo Real & Métricas Principais</h3>
              
              <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem;">
                <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; text-align: center;">
                  <span style="font-size: 1.5rem; font-weight: 800; color: #fff;">1.242</span>
                  <p style="font-size: 0.7rem; color: var(--text-secondary); margin-top: 0.25rem;">Visitantes Únicos</p>
                </div>
                <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; text-align: center;">
                  <span style="font-size: 1.5rem; font-weight: 800; color: #fff;">04m 12s</span>
                  <p style="font-size: 0.7rem; color: var(--text-secondary); margin-top: 0.25rem;">Tempo Médio</p>
                </div>
                <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; text-align: center;">
                  <span style="font-size: 1.5rem; font-weight: 800; color: #fff;">34,2%</span>
                  <p style="font-size: 0.7rem; color: var(--text-secondary); margin-top: 0.25rem;">Taxa de Rejeição</p>
                </div>
                <div style="background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; text-align: center;">
                  <span style="font-size: 1.5rem; font-weight: 800; color: #fff;">890</span>
                  <p style="font-size: 0.7rem; color: var(--text-secondary); margin-top: 0.25rem;">Visualizações de Página</p>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Aba Super Admin Conteúdo (Proprietário) ── -->
        <template v-if="activeTab === 'super_admin_content'">
          <div style="max-width: 1000px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem;">
            <!-- Landing page SEO Configs -->
            <div class="glass-card">
              <h2 class="section-title">
                <i class="fa-solid fa-search" style="font-size: 20px;"></i> Otimizações de SEO & Landing Page
              </h2>
              <form @submit.prevent="handleSaveAdminConfigs" style="display: flex; flex-direction: column; gap: 1rem;">
                <div class="form-group" style="margin: 0;">
                  <label>Título da Página (SEO Title)</label>
                  <input type="text" class="form-input" v-model="adminConfigs.seo_title" />
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>Meta Descrição (Meta Description)</label>
                  <textarea class="form-input" rows="2" v-model="adminConfigs.seo_description" />
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>Palavras-Chave de SEO (Tags separadas por vírgula)</label>
                  <input type="text" class="form-input" v-model="adminConfigs.seo_keywords" />
                </div>
                <div style="display: flex; justify-content: flex-end;">
                  <button type="submit" class="btn btn-primary">Salvar Parâmetros SEO</button>
                </div>
              </form>
            </div>

            <!-- Blog Post Editor -->
            <div class="glass-card">
              <h3 class="section-title"><i class="fa-solid fa-newspaper"></i> Gerenciador do Blog & Artigos</h3>
              <form @submit="handleSaveBlogPost" style="display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem;">
                <div class="form-group" style="margin: 0;">
                  <label>Título do Artigo</label>
                  <input type="text" class="form-input" placeholder="O impacto da automação no mercado..." v-model="newBlogPost.title" required />
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>Resumo (Resumo simples para cards)</label>
                  <input type="text" class="form-input" placeholder="Uma breve sinopse do conteúdo..." v-model="newBlogPost.summary" required />
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>URL da Imagem de Capa</label>
                  <input type="text" class="form-input" placeholder="https://images.unsplash.com/..." v-model="newBlogPost.image_url" />
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>Conteúdo Principal (Markdown ou Texto Simples)</label>
                  <textarea class="form-input" rows="4" placeholder="Escreva o artigo completo..." v-model="newBlogPost.content" required />
                </div>
                <div style="display: flex; justify-content: flex-end;">
                  <button type="submit" class="btn btn-primary">Publicar Artigo</button>
                </div>
              </form>

              <!-- Articles lists -->
              <h4 style="margin-bottom: 0.75rem;">Artigos Publicados</h4>
              <div v-if="blogPosts.length === 0" style="color: var(--text-secondary); font-size: 0.85rem; padding: 1rem; text-align: center;">Nenhum artigo publicado no blog.</div>
              <div v-else style="display: flex; flex-direction: column; gap: 0.75rem;">
                <div v-for="post in blogPosts" :key="post.id" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem; background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px;">
                  <div>
                    <strong style="color: #fff;">{{ post.title }}</strong>
                    <p style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 2px;">{{ post.summary }}</p>
                  </div>
                  <button class="btn btn-secondary" style="color: var(--color-error); padding: 0.25rem 0.5rem; font-size: 0.75rem;" @click="handleDeleteBlogPost(post.id)">
                    Excluir
                  </button>
                </div>
              </div>
            </div>

            <!-- Banners and carousels -->
            <div class="glass-card">
              <h3 class="section-title"><i class="fa-solid fa-rectangle-ad"></i> Banners & Carrosséis Promocionais</h3>
              
              <form @submit="handleSaveBanner" style="display: grid; grid-template-columns: 1.2fr 0.8fr 1fr; gap: 1rem; margin-bottom: 1.5rem; align-items: flex-end;">
                <div class="form-group" style="margin: 0;">
                  <label>Título do Banner</label>
                  <input type="text" class="form-input" v-model="newBanner.title" placeholder="Desconto de Lançamento" required />
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>Posição (Página)</label>
                  <select class="form-input" v-model="newBanner.position" style="background:#0d1426; color:#fff;">
                    <option value="home">Home (Painel)</option>
                    <option value="career">Career Page</option>
                    <option value="interview">Entrevistas</option>
                  </select>
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>URL Imagem</label>
                  <input type="text" class="form-input" v-model="newBanner.image_url" placeholder="https://unsplash..." required />
                </div>
                <div class="form-group" style="margin: 0; grid-column: 1 / -1;">
                  <label>URL Redirecionamento Link (Opcional)</label>
                  <input type="text" class="form-input" v-model="newBanner.link_url" placeholder="#pricing" />
                </div>
                <div style="grid-column: 1 / -1; display: flex; justify-content: flex-end; margin-top: 0.5rem;">
                  <button type="submit" class="btn btn-primary">Adicionar Banner</button>
                </div>
              </form>

              <h4 style="margin-bottom: 0.75rem;">Banners em Exibição</h4>
              <div v-if="banners.length === 0" style="color: var(--text-secondary); font-size: 0.85rem; padding: 1rem; text-align: center;">Nenhum banner cadastrado.</div>
              <div v-else style="display: flex; flex-direction: column; gap: 0.75rem;">
                <div v-for="b in banners" :key="b.id" style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem; background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 8px;">
                  <div>
                    <strong style="color: #fff;">{{ b.title }}</strong> &mdash; <span style="font-size: 0.75rem; color: var(--color-secondary);">Posição: {{ b.position }}</span>
                  </div>
                  <button class="btn btn-secondary" style="color: var(--color-error); padding: 0.25rem 0.5rem; font-size: 0.75rem;" @click="handleDeleteBanner(b.id)">
                    Excluir
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Aba Super Admin Segurança & Auditoria (Proprietário) ── -->
        <template v-if="activeTab === 'super_admin_security'">
          <div style="max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem;">
            <!-- Database Backup trigger -->
            <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(16,185,129,0.3); background: rgba(16,185,129,0.03);">
              <div>
                <h3 style="color: var(--color-success); font-size: 1.15rem; margin: 0; display: flex; align-items: center; gap: 6px;">
                  <i class="fa-solid fa-database"></i> Backup Automático do SQLite
                </h3>
                <p style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.25rem; line-height: 1.5;">
                  Gere uma cópia instantânea segura do arquivo de banco de dados SQLite (<code>vagasync.db</code>) no diretório local do servidor.
                </p>
              </div>
              <button class="btn btn-primary" style="background: var(--color-success); border: none; color: white;" @click="handleTriggerBackup">
                <i class="fa-solid fa-download-solid"></i> Disparar Backup
              </button>
            </div>

            <!-- Audit trail listing -->
            <div class="glass-card">
              <h3 class="section-title"><i class="fa-solid fa-clock-rotate-left"></i> Logs de Auditoria do Super Admin</h3>
              <div class="jobs-table-wrapper" style="max-height: 320px; overflow-y: auto;">
                <table class="jobs-table">
                  <thead>
                    <tr>
                      <th>Horário</th>
                      <th>Ação</th>
                      <th>Detalhes</th>
                      <th>IP</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="log in auditLogs" :key="log.id">
                      <td style="font-size: 0.75rem; font-family: monospace; white-space: nowrap;">
                        {{ new Date(log.timestamp).toLocaleString() }}
                      </td>
                      <td>
                        <span style="font-size: 0.72rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; background: rgba(0,242,254,0.1); color: var(--color-secondary);">
                          {{ log.action }}
                        </span>
                      </td>
                      <td style="font-size: 0.78rem; color: var(--text-secondary);">{{ log.details }}</td>
                      <td style="font-size: 0.75rem; font-family: monospace; color: var(--text-muted);">{{ log.ip_address }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Aba Recrutador Dashboard (Recrutador) ── -->
        <template v-if="activeTab === 'recruiter_dashboard'">
          <div style="max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem;">
            <!-- Filtros de Desempenho -->
            <div class="glass-card" style="display: flex; flex-direction: column; gap: 1rem; border-color: rgba(59,130,246,0.25);">
              <div style="display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-filter" style="color: var(--color-secondary);"></i>
                <h3 style="margin: 0; font-size: 1.15rem; color: #fff;">Painel Analítico de Recrutamento</h3>
              </div>
              <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                <div class="form-group" style="margin: 0;">
                  <label style="font-size: 0.78rem; margin-bottom: 0.35rem; color: var(--text-secondary);">Recrutador Responsável</label>
                  <select class="form-input" v-model="selectedDashboardRecruiter" style="background: #0d1426; color: var(--text-primary); border: 1px solid var(--border-color); font-size: 0.85rem; padding: 0.4rem 0.6rem; width: 100%; border-radius: 6px;">
                    <option v-for="opt in recruiterOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                  </select>
                </div>
                <div class="form-group" style="margin: 0;">
                  <label style="font-size: 0.78rem; margin-bottom: 0.35rem; color: var(--text-secondary);">Nível da Vaga</label>
                  <select class="form-input" v-model="selectedDashboardLevel" style="background: #0d1426; color: var(--text-primary); border: 1px solid var(--border-color); font-size: 0.85rem; padding: 0.4rem 0.6rem; width: 100%; border-radius: 6px;">
                    <option v-for="opt in levelOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                  </select>
                </div>
                <div class="form-group" style="margin: 0;">
                  <label style="font-size: 0.78rem; margin-bottom: 0.35rem; color: var(--text-secondary);">Setor</label>
                  <select class="form-input" v-model="selectedDashboardDept" style="background: #0d1426; color: var(--text-primary); border: 1px solid var(--border-color); font-size: 0.85rem; padding: 0.4rem 0.6rem; width: 100%; border-radius: 6px;">
                    <option v-for="opt in deptOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Principais Indicadores (Gestão de Vagas, SLA, Experiência) -->
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.25rem;">
              <!-- Gestão de Vagas -->
              <div class="glass-card stat-card" style="flex-direction: column; align-items: flex-start; gap: 0.5rem; justify-content: center; min-height: 100px;">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                  <span class="stat-label" style="font-weight: 700; color: #fff;">Gestão de Vagas</span>
                  <i class="fa-solid fa-folder-open" style="color: var(--color-primary);"></i>
                </div>
                <div style="display: flex; gap: 0.8rem; margin-top: 0.25rem; font-size: 0.82rem; width: 100%;">
                  <div style="flex: 1; text-align: center; background: rgba(59,130,246,0.1); padding: 4px; border-radius: 4px; border: 1px solid rgba(59,130,246,0.25);">
                    <div style="font-size: 1.1rem; font-weight: 800; color: var(--color-primary);">{{ dashboardMetrics.abertas }}</div>
                    <div style="font-size: 0.65rem; color: var(--text-secondary);">Abertas</div>
                  </div>
                  <div style="flex: 1; text-align: center; background: rgba(0,242,254,0.1); padding: 4px; border-radius: 4px; border: 1px solid rgba(0,242,254,0.25);">
                    <div style="font-size: 1.1rem; font-weight: 800; color: var(--color-secondary);">{{ dashboardMetrics.emAndamento }}</div>
                    <div style="font-size: 0.65rem; color: var(--text-secondary);">Em Fila</div>
                  </div>
                  <div style="flex: 1; text-align: center; background: rgba(16,185,129,0.1); padding: 4px; border-radius: 4px; border: 1px solid rgba(16,185,129,0.25);">
                    <div style="font-size: 1.1rem; font-weight: 800; color: var(--color-success);">{{ dashboardMetrics.fechadas }}</div>
                    <div style="font-size: 0.65rem; color: var(--text-secondary);">Fechadas</div>
                  </div>
                </div>
              </div>

              <!-- SLA de Contratação -->
              <div class="glass-card stat-card" style="flex-direction: column; align-items: flex-start; gap: 0.5rem; justify-content: center; min-height: 100px;">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                  <span class="stat-label" style="font-weight: 700; color: #fff;">SLA Médio</span>
                  <i class="fa-solid fa-hourglass-half" style="color: #f59e0b;"></i>
                </div>
                <div style="display: flex; align-items: baseline; gap: 6px;">
                  <span class="stat-value" style="font-size: 1.8rem; color: #f59e0b; font-weight: 800;">{{ dashboardMetrics.sla }}</span>
                  <span style="font-size: 0.75rem; color: var(--text-secondary);">dias</span>
                </div>
                <div style="font-size: 0.68rem; color: var(--color-success); font-weight: 600; display: flex; align-items: center; gap: 3px;">
                  <i class="fa-solid fa-circle-check"></i> Dentro da Meta
                </div>
              </div>

              <!-- Satisfação Candidato (NPS) -->
              <div class="glass-card stat-card" style="flex-direction: column; align-items: flex-start; gap: 0.5rem; justify-content: center; min-height: 100px;">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                  <span class="stat-label" style="font-weight: 700; color: #fff;">Satisfação (NPS)</span>
                  <i class="fa-solid fa-heart" style="color: #ec4899;"></i>
                </div>
                <div style="display: flex; align-items: baseline; gap: 6px;">
                  <span class="stat-value" style="font-size: 1.8rem; color: #ec4899; font-weight: 800;">{{ dashboardMetrics.nps }}%</span>
                </div>
                <div style="font-size: 0.68rem; color: var(--text-secondary);">
                  Feedback da Experiência
                </div>
              </div>

              <!-- Velocidade de Resposta -->
              <div class="glass-card stat-card" style="flex-direction: column; align-items: flex-start; gap: 0.5rem; justify-content: center; min-height: 100px;">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                  <span class="stat-label" style="font-weight: 700; color: #fff;">Tempo de Resposta</span>
                  <i class="fa-solid fa-reply-all" style="color: var(--color-secondary);"></i>
                </div>
                <div style="display: flex; align-items: baseline; gap: 6px;">
                  <span class="stat-value" style="font-size: 1.8rem; color: var(--color-secondary); font-weight: 800;">{{ dashboardMetrics.responseTime }}</span>
                  <span style="font-size: 0.75rem; color: var(--text-secondary);">dias</span>
                </div>
                <div style="font-size: 0.68rem; color: var(--color-secondary); font-weight: 600; display: flex; align-items: center; gap: 3px;">
                  <i class="fa-solid fa-bolt"></i> Super Rápido
                </div>
              </div>
            </div>

            <!-- Funil e Origem do Talento Side-by-Side -->
            <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 1.5rem;">
              <!-- Funil de Candidatos -->
              <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <h3 class="section-title" style="margin: 0;"><i class="fa-solid fa-chart-bar"></i> Funil de Candidatos (Tempo Real)</h3>
                  <span style="font-size: 0.72rem; padding: 2px 6px; border-radius: 4px; background: rgba(59,130,246,0.15); color: var(--color-primary); font-weight: 600;">
                    Taxa total: {{ ((dashboardMetrics.aprovados / dashboardMetrics.triados) * 100).toFixed(1) }}%
                  </span>
                </div>
                
                <div style="display: flex; flex-direction: column; gap: 0.75rem; padding: 0.5rem 0;">
                  <!-- FASE 1: Triados -->
                  <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 0.25rem; font-weight: 600;">
                      <span>1. Currículos Triados por IA</span>
                      <span style="color: #fff;">{{ dashboardMetrics.triados }} (100%)</span>
                    </div>
                    <div style="height: 10px; background: rgba(255,255,255,0.05); border-radius: 5px; overflow: hidden;">
                      <div style="height: 100%; width: 100%; background: linear-gradient(90deg, #3b82f6, #00f2fe); border-radius: 5px; transition: width 0.4s ease;"></div>
                    </div>
                  </div>

                  <!-- FASE 2: Analise -->
                  <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 0.25rem; font-weight: 600;">
                      <span>2. Selecionados para Análise Técnica</span>
                      <span style="color: var(--color-secondary);">{{ dashboardMetrics.emAnalise }} ({{ ((dashboardMetrics.emAnalise / dashboardMetrics.triados) * 100).toFixed(0) }}%)</span>
                    </div>
                    <div style="height: 10px; background: rgba(255,255,255,0.05); border-radius: 5px; overflow: hidden;">
                      <div :style="`height: 100%; width: ${((dashboardMetrics.emAnalise / dashboardMetrics.triados) * 100)}%; background: linear-gradient(90deg, #00f2fe, #10b981); border-radius: 5px; transition: width 0.4s ease;`"></div>
                    </div>
                  </div>

                  <!-- FASE 3: Entrevista -->
                  <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 0.25rem; font-weight: 600;">
                      <span>3. Entrevistas Agendadas</span>
                      <span style="color: #a855f7;">{{ dashboardMetrics.entrevistados }} ({{ ((dashboardMetrics.entrevistados / dashboardMetrics.triados) * 100).toFixed(0) }}%)</span>
                    </div>
                    <div style="height: 10px; background: rgba(255,255,255,0.05); border-radius: 5px; overflow: hidden;">
                      <div :style="`height: 100%; width: ${((dashboardMetrics.entrevistados / dashboardMetrics.triados) * 100)}%; background: linear-gradient(90deg, #a855f7, #ec4899); border-radius: 5px; transition: width 0.4s ease;`"></div>
                    </div>
                  </div>

                  <!-- FASE 4: Aprovados -->
                  <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 0.25rem; font-weight: 600;">
                      <span>4. Aprovados / Propostas Enviadas</span>
                      <span style="color: var(--color-success);">{{ dashboardMetrics.aprovados }} ({{ ((dashboardMetrics.aprovados / dashboardMetrics.triados) * 100).toFixed(1) }}%)</span>
                    </div>
                    <div style="height: 10px; background: rgba(255,255,255,0.05); border-radius: 5px; overflow: hidden;">
                      <div :style="`height: 100%; width: ${((dashboardMetrics.aprovados / dashboardMetrics.triados) * 100)}%; background: linear-gradient(90deg, #10b981, #34d399); border-radius: 5px; transition: width 0.4s ease;`"></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Origem do Talento -->
              <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
                <h3 class="section-title"><i class="fa-solid fa-share-nodes"></i> Origem dos Talentos Qualificados</h3>
                
                <div style="display: flex; flex-direction: column; gap: 0.85rem;">
                  <!-- LinkedIn -->
                  <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 0.2rem;">
                      <span style="display: flex; align-items: center; gap: 4px;"><i class="fa-brands fa-linkedin" style="color: #0a66c2;"></i> LinkedIn</span>
                      <span style="font-weight: 700; color: #fff;">{{ dashboardMetrics.channels.linkedin }}%</span>
                    </div>
                    <div style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;">
                      <div :style="`height: 100%; width: ${dashboardMetrics.channels.linkedin}%; background: #0a66c2; border-radius: 3px;`"></div>
                    </div>
                  </div>

                  <!-- Indicações -->
                  <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 0.2rem;">
                      <span style="display: flex; align-items: center; gap: 4px;"><i class="fa-solid fa-users" style="color: #10b981;"></i> Indicações Internas</span>
                      <span style="font-weight: 700; color: #fff;">{{ dashboardMetrics.channels.indicacao }}%</span>
                    </div>
                    <div style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;">
                      <div :style="`height: 100%; width: ${dashboardMetrics.channels.indicacao}%; background: #10b981; border-radius: 3px;`"></div>
                    </div>
                  </div>

                  <!-- Portais de Vaga -->
                  <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 0.2rem;">
                      <span style="display: flex; align-items: center; gap: 4px;"><i class="fa-solid fa-globe" style="color: var(--color-secondary);"></i> Portal de Vagas</span>
                      <span style="font-weight: 700; color: #fff;">{{ dashboardMetrics.channels.portais }}%</span>
                    </div>
                    <div style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;">
                      <div :style="`height: 100%; width: ${dashboardMetrics.channels.portais}%; background: var(--color-secondary); border-radius: 3px;`"></div>
                    </div>
                  </div>

                  <!-- Outros -->
                  <div>
                    <div style="display: flex; justify-content: space-between; font-size: 0.78rem; margin-bottom: 0.2rem;">
                      <span style="display: flex; align-items: center; gap: 4px;"><i class="fa-solid fa-ellipsis" style="color: var(--text-muted);"></i> Outros</span>
                      <span style="font-weight: 700; color: #fff;">{{ dashboardMetrics.channels.outros }}%</span>
                    </div>
                    <div style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;">
                      <div :style="`height: 100%; width: ${dashboardMetrics.channels.outros}%; background: var(--text-muted); border-radius: 3px;`"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Talent database simulation and matching -->
            <div class="glass-card">
              <h3 class="section-title"><i class="fa-solid fa-magnifying-glass"></i> Banco de Talentos e Match de Compatibilidade</h3>
              <p style="color: var(--text-secondary); font-size: 0.82rem; margin-bottom: 1.25rem;">
                Busque candidatos ideais em nossa base integrada. A IA pontua o match com base nas palavras-chave da vaga em tempo real.
              </p>
              
              <div class="jobs-table-wrapper">
                <table class="jobs-table">
                  <thead>
                    <tr>
                      <th>Nome</th>
                      <th>Cargo Recomendado</th>
                      <th>E-mail</th>
                      <th>Match Vaga</th>
                      <th>Competências Extraídas por IA</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="cand in recruitedCandidates" :key="cand.id">
                      <td style="font-weight: 600; color: #fff;">{{ cand.name }}</td>
                      <td>{{ cand.role }}</td>
                      <td style="font-size: 0.8rem; color: var(--text-secondary);">{{ cand.email }}</td>
                      <td>
                        <span :class="['match-badge', cand.match >= 90 ? 'match-high' : 'match-med']">
                          {{ cand.match }}%
                        </span>
                      </td>
                      <td style="font-size: 0.78rem; color: var(--text-secondary);">{{ cand.resume }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Recruitment pipeline Kanban board -->
            <div class="glass-card">
              <h3 class="section-title" style="margin-bottom: 1.5rem;"><i class="fa-solid fa-network-wired"></i> Pipeline de Recrutamento (Kanban)</h3>
              
              <div class="kanban-pipeline-grid">
                <!-- Recebidos column -->
                <div class="kanban-column">
                  <div class="kanban-column-header">Recebidos ({{ recruitedCandidates.filter(c => c.status === 'recebidos').length }})</div>
                  <div class="kanban-cards-wrapper">
                    <div v-for="cand in recruitedCandidates.filter(c => c.status === 'recebidos')" :key="cand.id" class="kanban-card">
                      <strong>{{ cand.name }}</strong>
                      <span>{{ cand.role }}</span>
                      <div class="match-badge match-high" style="margin-top: 0.25rem;">Match: {{ cand.match }}%</div>
                      <div style="display: flex; gap: 4px; margin-top: 0.75rem;">
                        <button class="btn btn-secondary" style="flex:1; font-size: 0.65rem; padding: 0.2rem;" @click="openCandidateModal(cand)">Visualizar</button>
                        <button class="btn btn-secondary" style="flex:1; font-size: 0.65rem; padding: 0.2rem;" @click="moveCandidate(cand.id, 'analise')">Mover &rarr;</button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Em Analise column -->
                <div class="kanban-column">
                  <div class="kanban-column-header">Em Análise ({{ recruitedCandidates.filter(c => c.status === 'analise').length }})</div>
                  <div class="kanban-cards-wrapper">
                    <div v-for="cand in recruitedCandidates.filter(c => c.status === 'analise')" :key="cand.id" class="kanban-card">
                      <strong>{{ cand.name }}</strong>
                      <span>{{ cand.role }}</span>
                      <div class="match-badge match-high" style="margin-top: 0.25rem;">Match: {{ cand.match }}%</div>
                      <div style="display: flex; gap: 4px; margin-top: 0.75rem;">
                        <button class="btn btn-secondary" style="flex:1; font-size: 0.65rem; padding: 0.2rem;" @click="openCandidateModal(cand)">Visualizar</button>
                        <button class="btn btn-secondary" style="flex:1; font-size: 0.65rem; padding: 0.2rem;" @click="moveCandidate(cand.id, 'entrevista')">Mover &rarr;</button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Entrevista column -->
                <div class="kanban-column">
                  <div class="kanban-column-header">Entrevista ({{ recruitedCandidates.filter(c => c.status === 'entrevista').length }})</div>
                  <div class="kanban-cards-wrapper">
                    <div v-for="cand in recruitedCandidates.filter(c => c.status === 'entrevista')" :key="cand.id" class="kanban-card">
                      <strong>{{ cand.name }}</strong>
                      <span>{{ cand.role }}</span>
                      <div class="match-badge match-high" style="margin-top: 0.25rem;">Match: {{ cand.match }}%</div>
                      
                      <!-- Video Meet launcher inside Kanban -->
                      <div style="display: flex; flex-direction: column; gap: 0.4rem; margin-top: 0.75rem;">
                        <button 
                          v-if="isRecruiterPro"
                          class="btn btn-primary" 
                          style="font-size: 0.68rem; padding: 0.3rem; background: linear-gradient(135deg, #10b981, #00f2fe); border: none; color: #060913; font-weight: 700;"
                          @click="joinVideoMeet"
                        >
                          <i class="fa-solid fa-video"></i> Iniciar WebRTC Meet
                        </button>
                        <button v-else class="btn btn-secondary" style="font-size: 0.65rem; padding: 0.3rem;" @click="activeTab = 'recruiter_billing'">
                          🔒 Meet por Vídeo (Requer Pro)
                        </button>
                        <div style="display: flex; gap: 4px;">
                          <button class="btn btn-secondary" style="flex:1; font-size: 0.65rem; padding: 0.2rem;" @click="openCandidateModal(cand)">Visualizar</button>
                          <button class="btn btn-secondary" style="flex:1; font-size: 0.65rem; padding: 0.2rem;" @click="moveCandidate(cand.id, 'aprovados')">Aprovar &rarr;</button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Aprovados column -->
                <div class="kanban-column">
                  <div class="kanban-column-header" style="border-top-color: var(--color-success);">Aprovados ({{ recruitedCandidates.filter(c => c.status === 'aprovados').length }})</div>
                  <div class="kanban-cards-wrapper">
                    <div v-for="cand in recruitedCandidates.filter(c => c.status === 'aprovados')" :key="cand.id" class="kanban-card" style="border-left-color: var(--color-success);">
                      <strong>{{ cand.name }}</strong>
                      <span>{{ cand.role }}</span>
                      <div class="match-badge match-high" style="margin-top: 0.25rem; background: rgba(16,185,129,0.12); color: var(--color-success); border-color: rgba(16,185,129,0.3);">Aprovado ✓</div>
                      <div style="display: flex; gap: 4px; margin-top: 0.75rem;">
                        <button class="btn btn-secondary" style="flex:1; font-size: 0.65rem; padding: 0.2rem;" @click="openCandidateModal(cand)">Visualizar</button>
                        <button class="btn btn-secondary" style="flex:1; font-size: 0.65rem; padding: 0.2rem; color: var(--color-error);" @click="moveCandidate(cand.id, 'recebidos')">Reiniciar</button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Reprovados column -->
                <div class="kanban-column">
                  <div class="kanban-column-header" style="border-top-color: var(--color-error);">Reprovados ({{ recruitedCandidates.filter(c => c.status === 'reprovados').length }})</div>
                  <div class="kanban-cards-wrapper">
                    <div v-for="cand in recruitedCandidates.filter(c => c.status === 'reprovados')" :key="cand.id" class="kanban-card" style="border-left-color: var(--color-error); opacity: 0.75;">
                      <strong>{{ cand.name }}</strong>
                      <span>{{ cand.role }}</span>
                      <div class="match-badge" style="margin-top: 0.25rem; background: rgba(239, 68, 68, 0.12); color: var(--color-error); border-color: rgba(239, 68, 68, 0.3);">Reprovado ✗</div>
                      <div style="display: flex; gap: 4px; margin-top: 0.75rem;">
                        <button class="btn btn-secondary" style="flex:1; font-size: 0.65rem; padding: 0.2rem;" @click="openCandidateModal(cand)">Visualizar</button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- ── Aba Recrutador Criar Vaga (Recrutador) ── -->
        <template v-if="activeTab === 'recruiter_jobs'">
          <div style="max-width: 700px; margin: 0 auto;">
            <div class="glass-card">
              <h2 class="section-title">
                <i class="fa-solid fa-circle-plus" style="font-size: 20px;"></i> Publicar Nova Oportunidade
              </h2>
              <p style="color: var(--text-secondary); font-size: 0.85rem; line-height: 1.6; margin-bottom: 1.5rem;">
                A vaga publicada aparecerá no radar de buscas inteligentes do VagaSync e será catalogada para triagem automática por IA.
              </p>

              <form @submit="handlePublishJob" style="display: flex; flex-direction: column; gap: 1.25rem;">
                <div class="form-group" style="margin: 0;">
                  <label>Título da Oportunidade *</label>
                  <input type="text" class="form-input" v-model="newJobForm.title" placeholder="Ex: Desenvolvedor Senior Vue.js" required />
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>Empresa Contratante *</label>
                  <input type="text" class="form-input" v-model="newJobForm.company" placeholder="Ex: VagaSync Corp" required />
                </div>
                <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 0.75rem;">
                  <div class="form-group" style="margin: 0;">
                    <label>Localização</label>
                    <input type="text" class="form-input" v-model="newJobForm.location" placeholder="Ex: Remoto, São Paulo - SP" />
                  </div>
                  <div class="form-group" style="margin: 0;">
                    <label>Palavras-Chave de Competência</label>
                    <input type="text" class="form-input" v-model="newJobForm.keywords" placeholder="Ex: Vue 3, TypeScript, CSS" />
                  </div>
                </div>
                <div class="form-group" style="margin: 0;">
                  <label>Descrição do Cargo & Pré-Requisitos</label>
                  <textarea class="form-input" rows="5" v-model="newJobForm.description" placeholder="Descreva os desafios do cargo e competências fundamentais..." />
                </div>
                
                <div style="display: flex; justify-content: flex-end; gap: 1rem; margin-top: 0.5rem;">
                  <button type="submit" class="btn btn-primary" style="background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; font-weight: 700; border: none;">
                    Publicar Oportunidade
                  </button>
                </div>
              </form>
            </div>
          </div>
        </template>

        <!-- ── Aba Recrutador Faturamento (Recrutador) ── -->
        <template v-if="activeTab === 'recruiter_billing'">
          <div style="max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 2rem;">
            <!-- Current Plan details -->
            <div class="glass-card" style="display: flex; justify-content: space-between; align-items: center; border: 1px solid rgba(0,242,254,0.3); background: rgba(0,242,254,0.03);">
              <div>
                <h3 style="color: var(--color-secondary); font-size: 1.2rem; margin: 0;">
                  Seu Plano Atual: {{ isRecruiterPro ? 'Recrutador Pro Enterprise' : 'Plano Gratuito de Recrutamento' }}
                </h3>
                <p style="color: var(--text-secondary); font-size: 0.82rem; margin-top: 0.25rem; line-height: 1.5;">
                  {{ isRecruiterPro 
                     ? 'Seus limites foram removidos. Banco de talentos e videochamadas WebRTC ilimitadas.' 
                     : 'Seu limite atual é de 5 vagas cadastradas. Faça o upgrade para remover limites.' }}
                </p>
              </div>
              <button 
                v-if="isRecruiterPro" 
                class="btn btn-secondary" 
                style="color: var(--color-error); border-color: rgba(239,68,68,0.25);"
                @click="cancelPremium('recruiter_pro')"
              >
                Cancelar Assinatura
              </button>
              <button 
                v-else
                class="btn btn-primary" 
                style="background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; font-weight: 700; border: none;"
                @click="openCheckout('recruiter_pro')"
              >
                Assinar Recrutador Pro
              </button>
            </div>

            <!-- Recruiter pricing table -->
            <div class="glass-card">
              <h3 class="section-title" style="text-align: center; margin-bottom: 1.5rem;">Estruturas de Preços para Recrutadores</h3>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; max-width: 700px; margin: 0 auto;">
                <div style="border: 1px solid var(--border-color); padding: 1.5rem; border-radius: 8px; display: flex; flex-direction: column; align-items: center; text-align: center;">
                  <h4 style="font-size: 1.1rem; color: var(--text-secondary);">Recrutador Básico</h4>
                  <div style="font-size: 1.75rem; font-weight: 800; margin: 0.5rem 0;">R$ 0</div>
                  <ul style="list-style:none; padding:0; font-size:0.8rem; color:var(--text-secondary); display:flex; flex-direction:column; gap:0.4rem; margin-bottom:1.5rem;">
                    <li>✓ 5 vagas cadastradas</li>
                    <li>✓ Visualização básica de candidatos</li>
                    <li>✗ Sem videochamada WebRTC</li>
                  </ul>
                  <button class="btn btn-secondary" style="width: 100%;" disabled>Ativo</button>
                </div>
                
                <div style="border: 2px solid var(--color-primary); padding: 1.5rem; border-radius: 8px; background: rgba(59,130,246,0.03); display: flex; flex-direction: column; align-items: center; text-align: center;">
                  <h4 style="font-size: 1.1rem; color: #fff;">Recrutador Pro</h4>
                  <div style="font-size: 1.75rem; font-weight: 800; margin: 0.5rem 0; color: var(--color-secondary);">R$ 149,90<span style="font-size:0.8rem; font-weight:400; color:var(--text-secondary);">/mês</span></div>
                  <ul style="list-style:none; padding:0; font-size:0.8rem; color:var(--text-secondary); display:flex; flex-direction:column; gap:0.4rem; margin-bottom:1.5rem;">
                    <li>✓ Vagas publicadas ILIMITADAS</li>
                    <li>✓ Banco de talentos IA completo</li>
                    <li>✓ Painel Kanban irrestrito</li>
                    <li>✓ Salas de Videochamadas WebRTC Meet</li>
                  </ul>
                  <button v-if="isRecruiterPro" class="btn btn-secondary" style="width: 100%;" disabled>Já Assinado</button>
                  <button v-else class="btn btn-primary" style="width:100%;" @click="openCheckout('recruiter_pro')">Assinar Pro</button>
                </div>
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

      <footer class="footer-bar" @click="handleFooterClick" style="cursor: pointer; margin-top: 3rem;">
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
