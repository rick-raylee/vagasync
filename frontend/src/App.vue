<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
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
  PhoneCall,
  Lock
} from '@lucide/vue';
import JobMap from './JobMap.vue';
import ContatoRH from './ContatoRH.vue';
import Messenger from './Messenger.vue';

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000/api'
  : '/api';

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

// ── Community Feed States ──
const feedPosts = ref([]);
const newPostContent = ref('');
const commentInputs = ref({});
const isSubmittingPost = ref(false);
const activeCommentsPostId = ref(null);

const activeConfigSubTab = ref('profile');

// ── Dynamic Settings States (Netflix-style) ──
const activeSettingsTab = ref('billing');
const cardBrand = ref(localStorage.getItem('vagasync_card_brand') || 'Visa');
const cardLast4 = ref(localStorage.getItem('vagasync_card_last4') || '8899');
const cardExpiry = ref(localStorage.getItem('vagasync_card_expiry') || '12/28');
const showChangeCardModal = ref(false);

const changeCardForm = ref({
  number: '',
  name: '',
  expiry: '',
  cvv: ''
});

const securityData = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
  twoFactorEnabled: localStorage.getItem('vagasync_2fa_enabled') === 'true'
});

const privacyData = ref({
  profileVisibleToRecruiters: localStorage.getItem('vagasync_privacy_visible') !== 'false',
  allowTargetedAds: localStorage.getItem('vagasync_privacy_ads') === 'true',
  cookieConsent: localStorage.getItem('vagasync_cookie_consent') === 'true'
});



// Mock login history for Access & Security tab
const loginHistory = ref([
  { device: 'Windows 11 PC - Google Chrome', location: 'São Paulo, SP - Brasil', ip: '200.234.212.34', date: 'Hoje às 22:30' },
  { device: 'iPhone 15 - Safari', location: 'São Paulo, SP - Brasil', ip: '189.120.45.10', date: 'Ontem às 14:15' }
]);

const saveCardData = () => {
  if (!changeCardForm.value.number || !changeCardForm.value.expiry) {
    showToast('Erro', 'Por favor, preencha os dados do cartão.', 'error');
    return;
  }
  const last4 = changeCardForm.value.number.slice(-4);
  cardLast4.value = last4;
  cardExpiry.value = changeCardForm.value.expiry;
  
  if (changeCardForm.value.number.startsWith('5')) cardBrand.value = 'Mastercard';
  else if (changeCardForm.value.number.startsWith('4')) cardBrand.value = 'Visa';
  else cardBrand.value = 'Elo';

  localStorage.setItem('vagasync_card_brand', cardBrand.value);
  localStorage.setItem('vagasync_card_last4', cardLast4.value);
  localStorage.setItem('vagasync_card_expiry', cardExpiry.value);
  
  showToast('Cartão Atualizado!', 'Os dados do seu cartão de pagamento foram salvos.', 'success');
  showChangeCardModal.value = false;
};

const updateSecuritySettings = () => {
  if (securityData.value.newPassword) {
    if (securityData.value.newPassword !== securityData.value.confirmPassword) {
      showToast('Erro', 'A nova senha e a confirmação não conferem.', 'error');
      return;
    }
    showToast('Senha Alterada!', 'Sua senha foi atualizada.', 'success');
    securityData.value.currentPassword = '';
    securityData.value.newPassword = '';
    securityData.value.confirmPassword = '';
  }
  localStorage.setItem('vagasync_2fa_enabled', securityData.value.twoFactorEnabled ? 'true' : 'false');
  showToast('Segurança Salva!', 'As configurações foram salvas.', 'success');
};

const updatePrivacySettings = () => {
  localStorage.setItem('vagasync_privacy_visible', privacyData.value.profileVisibleToRecruiters ? 'true' : 'false');
  localStorage.setItem('vagasync_privacy_ads', privacyData.value.allowTargetedAds ? 'true' : 'false');
  localStorage.setItem('vagasync_cookie_consent', privacyData.value.cookieConsent ? 'true' : 'false');
  showToast('Privacidade Salva!', 'Suas preferências de privacidade foram atualizadas.', 'success');
};

const updateNotificationSettings = () => {
  localStorage.setItem('vagasync_notify_email', notificationSettings.value.notifyEmail ? 'true' : 'false');
  localStorage.setItem('vagasync_notify_whatsapp', notificationSettings.value.notifyWhatsApp ? 'true' : 'false');
  localStorage.setItem('vagasync_notify_telegram', notificationSettings.value.notifyTelegram ? 'true' : 'false');
  localStorage.setItem('vagasync_notify_newsletter', notificationSettings.value.newsletterEnabled ? 'true' : 'false');
  showToast('Notificações Salvas!', 'Preferências de alertas salvas.', 'success');
};

// Profile Photo Upload
const handleProfilePhotoUpload = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  if (file.size > 2 * 1024 * 1024) {
    showToast('Erro', 'O tamanho máximo da foto é 2MB.', 'error');
    return;
  }
  const reader = new FileReader();
  reader.onload = () => {
    profileData.value.photo = reader.result;
    localStorage.setItem('vagasync_profile_photo', reader.result);
    showToast('Foto Carregada!', 'Sua foto de perfil foi atualizada.', 'success');
  };
  reader.readAsDataURL(file);
};

// ── Profile and System Settings States ──
const profileData = ref({
  name: localStorage.getItem('vagasync_profile_name') || '',
  email: localStorage.getItem('vagasync_profile_email') || '',
  phone: localStorage.getItem('vagasync_profile_phone') || '',
  company: localStorage.getItem('vagasync_profile_company') || '',
  photo: localStorage.getItem('vagasync_profile_photo') || ''
});

const darkMode = ref(localStorage.getItem('vagasync_dark_mode') !== 'false');

const systemSettings = ref({
  soundEnabled: localStorage.getItem('vagasync_sound_enabled') === 'true',
  autoRefresh: localStorage.getItem('vagasync_auto_refresh') === 'true',
});

const saveProfileData = () => {
  localStorage.setItem('vagasync_profile_name', profileData.value.name);
  localStorage.setItem('vagasync_profile_email', profileData.value.email);
  localStorage.setItem('vagasync_profile_phone', profileData.value.phone);
  localStorage.setItem('vagasync_profile_company', profileData.value.company);
  localStorage.setItem('vagasync_profile_photo', profileData.value.photo);
  showToast('Perfil Atualizado!', 'Suas informações de perfil foram salvas com sucesso.', 'success');
};



const toggleDarkMode = () => {
  localStorage.setItem('vagasync_dark_mode', darkMode.value);
  if (!darkMode.value) {
    document.documentElement.classList.add('light-mode');
  } else {
    document.documentElement.classList.remove('light-mode');
  }
};

const saveSystemSettings = () => {
  localStorage.setItem('vagasync_sound_enabled', systemSettings.value.soundEnabled);
  localStorage.setItem('vagasync_auto_refresh', systemSettings.value.autoRefresh);
  showToast('Configurações Salvas', 'As preferências do sistema foram atualizadas.', 'success');
};

const exportUserData = () => {
  const data = {
    profile: profileData.value,
    notifications: notificationSettings.value,
    config: config.value,
    system: systemSettings.value
  };
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'vagasync-meus-dados.json';
  a.click();
  showToast('Dados Exportados', 'Seu arquivo de exportação de dados (LGPD) foi gerado.', 'success');
};

const deleteAccount = () => {
  if (confirm('Tem certeza absoluta que deseja deletar sua conta? Todos os seus dados serão apagados permanentemente do sistema em conformidade com o direito ao esquecimento da LGPD.')) {
    localStorage.clear();
    showToast('Conta Excluída', 'Seus dados foram permanentemente limpos do sistema.', 'info');
    handleLogout();
  }
};

const getUserEmail = () => {
  const profileEmail = localStorage.getItem('vagasync_profile_email');
  if (profileEmail) return profileEmail;
  return userRole.value === 'candidate' ? 'candidato@vagasync.com.br' : 'recrutador@vagasync.com.br';
};

const getUserName = () => {
  const profileName = localStorage.getItem('vagasync_profile_name');
  if (profileName) return profileName;
  return userRole.value === 'candidate' ? 'Candidato VagaSync' : 'Recrutador VagaSync';
};

const fetchFeed = async () => {
  try {
    const res = await fetch(`${API_BASE}/feed`);
    if (res.ok) {
      feedPosts.value = await res.json();
    }
  } catch (err) {
    console.error("Erro ao carregar o feed:", err);
  }
};

// ── Recrutador IA Insights States ──
const recruiterInsights = ref([]);
const isLoadingRecruiterInsights = ref(false);

const fetchRecruiterInsights = async () => {
  isLoadingRecruiterInsights.value = true;
  try {
    const res = await fetch(`${API_BASE}/feed/recruiter-insights`);
    if (res.ok) {
      recruiterInsights.value = await res.json();
    }
  } catch (err) {
    console.error("Erro ao carregar insights de recrutamento:", err);
  } finally {
    isLoadingRecruiterInsights.value = false;
  }
};

const submitPost = async () => {
  if (!newPostContent.value.trim()) return;
  isSubmittingPost.value = true;
  try {
    const res = await fetch(`${API_BASE}/feed/post`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        author_name: getUserName(),
        author_email: getUserEmail(),
        author_role: userRole.value,
        content: newPostContent.value
      })
    });
    if (res.ok) {
      newPostContent.value = '';
      showToast('Post Compartilhado! 🚀', 'Sua publicação foi compartilhada com a comunidade VagaSync.', 'success');
      await fetchFeed();
    }
  } catch (err) {
    showToast('Erro', 'Não foi possível compartilhar sua publicação.', 'error');
  } finally {
    isSubmittingPost.value = false;
  }
};

const submitComment = async (postId) => {
  const content = commentInputs.value[postId];
  if (!content || !content.trim()) return;
  try {
    const res = await fetch(`${API_BASE}/feed/post/${postId}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        author_name: getUserName(),
        author_email: getUserEmail(),
        author_role: userRole.value,
        content: content
      })
    });
    if (res.ok) {
      commentInputs.value[postId] = '';
      showToast('Comentário Publicado!', 'Seu comentário foi postado com sucesso.', 'success');
      await fetchFeed();
    }
  } catch (err) {
    showToast('Erro', 'Não foi possível postar seu comentário.', 'error');
  }
};

const toggleReaction = async (postId, reactionType) => {
  try {
    const res = await fetch(`${API_BASE}/feed/post/${postId}/react`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_email: getUserEmail(),
        reaction_type: reactionType
      })
    });
    if (res.ok) {
      await fetchFeed();
    }
  } catch (err) {
    console.error("Erro ao reagir:", err);
  }
};

const hasUserReacted = (post, reactionType) => {
  return post.reactions?.some(r => r.user_email === getUserEmail() && r.reaction_type === reactionType);
};

const acceptCookies = () => {
  cookieConsent.value = true;
  localStorage.setItem('vagasync_cookie_consent', 'true');
};

// Notification settings
const notificationSettings = ref({
  enabled: localStorage.getItem('vagasync_notifications_enabled') === 'true' ? true : false,
  onApplications: localStorage.getItem('vagasync_notify_applications') === 'true' ? true : false,
  onRecruiterContact: localStorage.getItem('vagasync_notify_recruiter') === 'true' ? true : false,
  onSearchResults: localStorage.getItem('vagasync_notify_search') === 'true' ? true : false,
  notifyEmail: localStorage.getItem('vagasync_notify_email') !== 'false',
  notifyWhatsApp: localStorage.getItem('vagasync_notify_whatsapp') !== 'false',
  notifyTelegram: localStorage.getItem('vagasync_notify_telegram') === 'true',
  newsletterEnabled: localStorage.getItem('vagasync_notify_newsletter') !== 'false'
});

const saveNotificationSettings = () => {
  localStorage.setItem('vagasync_notifications_enabled', notificationSettings.value.enabled);
  localStorage.setItem('vagasync_notify_applications', notificationSettings.value.onApplications);
  localStorage.setItem('vagasync_notify_recruiter', notificationSettings.value.onRecruiterContact);
  localStorage.setItem('vagasync_notify_search', notificationSettings.value.onSearchResults);
  
  if (notificationSettings.value.enabled && Notification.permission === 'default') {
    Notification.requestPermission();
  }
  showToast('Preferências de notificação', 'Suas configurações foram salvas.', 'info');
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

// LinkedIn Connection States
const linkedinTrigger = ref(0);
const isLinkedinConnected = computed(() => {
  linkedinTrigger.value;
  const localVal = localStorage.getItem('vagasync_linkedin_connected') === 'true';
  const cookieVal = config.value.linkedin_cookie && config.value.linkedin_cookie !== '••••••••••••••••';
  return !!(localVal || cookieVal);
});

// ─── Trial de 7 dias para Candidatos ──────────────────────────────────────────
const CANDIDATE_TRIAL_DAYS = 7;

const candidateTrialStart = computed(() => {
  const ts = localStorage.getItem('vagasync_candidate_trial_start');
  return ts ? parseInt(ts) : null;
});

const candidateTrialDaysLeft = computed(() => {
  if (userRole.value !== 'candidate') return null;
  const start = candidateTrialStart.value;
  if (!start) return CANDIDATE_TRIAL_DAYS;
  const elapsed = Math.floor((Date.now() - start) / (1000 * 60 * 60 * 24));
  return Math.max(0, CANDIDATE_TRIAL_DAYS - elapsed);
});

const candidateTrialExpired = computed(() => {
  if (userRole.value !== 'candidate') return false;
  if (userFeatures.value.ia_ilimitada) return false; // pagou premium
  return candidateTrialDaysLeft.value === 0;
});

const candidateTrialPercent = computed(() => {
  if (candidateTrialDaysLeft.value === null) return 100;
  return Math.round((candidateTrialDaysLeft.value / CANDIDATE_TRIAL_DAYS) * 100);
});

const candidateTrialColor = computed(() => {
  const d = candidateTrialDaysLeft.value;
  if (d > 4) return '#10b981'; // verde
  if (d > 2) return '#f59e0b'; // amarelo
  return '#ef4444';             // vermelho
});
// ─────────────────────────────────────────────────────────────────────────────

// ─── Trial de 30 dias para Recrutadores ──────────────────────────────────────
const TRIAL_DAYS = 30;

const recruiterTrialStart = computed(() => {
  const ts = localStorage.getItem('vagasync_recruiter_trial_start');
  return ts ? parseInt(ts) : null;
});

const recruiterTrialDaysLeft = computed(() => {
  if (userRole.value !== 'recruiter') return null;
  const start = recruiterTrialStart.value;
  if (!start) return TRIAL_DAYS; // nunca definido = trial completo
  const elapsed = Math.floor((Date.now() - start) / (1000 * 60 * 60 * 24));
  return Math.max(0, TRIAL_DAYS - elapsed);
});

const recruiterTrialExpired = computed(() => {
  if (userRole.value !== 'recruiter') return false;
  if (userFeatures.value.recruiter_pro_active) return false; // pagou
  return recruiterTrialDaysLeft.value === 0;
});

const recruiterTrialPercent = computed(() => {
  if (recruiterTrialDaysLeft.value === null) return 100;
  return Math.round((recruiterTrialDaysLeft.value / TRIAL_DAYS) * 100);
});

const recruiterTrialColor = computed(() => {
  const d = recruiterTrialDaysLeft.value;
  if (d > 15) return '#10b981'; // verde
  if (d > 7)  return '#f59e0b'; // amarelo
  return '#ef4444';              // vermelho
});
// ─────────────────────────────────────────────────────────────────────────────
const userFeatures = ref(JSON.parse(localStorage.getItem('vagasync_features')) || {
  impulsionar_vaga_credits: 0,
  empresa_destaque: false,
  ia_triagem: false,
  videoentrevistas: false,
  relatorios_premium: false,
  testes_tecnicos: false,
  curriculo_destaque: false,
  ia_ilimitada: false,
  score_empregabilidade: false,
  perfil_premium: false
});

watch(userFeatures, (val) => {
  localStorage.setItem('vagasync_features', JSON.stringify(val));
}, { deep: true });

// Reinicialização segura dos blocos de anúncios Google AdSense em SPAs (Vue 3)
watch([activeTab, isLoggedIn], () => {
  nextTick(() => {
    try {
      const ads = document.querySelectorAll('ins.adsbygoogle');
      ads.forEach(ad => {
        if (!ad.getAttribute('data-adsbygoogle-status')) {
          (window.adsbygoogle = window.adsbygoogle || []).push({});
        }
      });
    } catch (e) {
      console.warn("Erro ao carregar blocos de anúncio do AdSense:", e);
    }
  });
}, { immediate: true });

const isPremium = computed({
  get: () => userFeatures.value.ia_ilimitada,
  set: (val) => { userFeatures.value.ia_ilimitada = val; }
});

const isRecruiterPro = computed({
  get: () => userFeatures.value.ia_triagem || userFeatures.value.videoentrevistas,
  set: (val) => {
    userFeatures.value.ia_triagem = val;
    userFeatures.value.videoentrevistas = val;
  }
});

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

const showLinkedinOAuthModal = ref(false);

const saveCredentialsAndLoginReal = async () => {
  if (!config.value.linkedin_client_id || !config.value.linkedin_client_secret) {
    showToast('Campos Requeridos', 'Por favor, preencha o Client ID e Client Secret para prosseguir.', 'error');
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/config/init-linkedin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config.value)
    });
    if (res.ok) {
      showToast('Credenciais Salvas', 'Conectando ao LinkedIn para login real...', 'success');
      setTimeout(() => {
        window.location.href = `${API_BASE}/linkedin/login`;
      }, 1000);
    } else {
      showToast('Erro', 'Não foi possível salvar as credenciais no backend.', 'error');
    }
  } catch (e) {
    showToast('Erro de Conexão', 'Falha ao conectar com o backend.', 'error');
  }
};

const handleLinkedinLogin = () => {
  if (!config.value || !config.value.linkedin_client_id || !config.value.linkedin_client_secret) {
    showToast('Configuração Requerida', 'Por favor, configure suas chaves do LinkedIn para prosseguir com o login real.', 'info');
    showLinkedinOAuthModal.value = true;
  } else {
    window.location.href = `${API_BASE}/linkedin/login`;
  }
};

const handleLinkedinCallback = () => {
  const params = new URLSearchParams(window.location.search);
  if (params.get('linkedin_auth') !== 'success') return;

  const profileName = params.get('linkedin_name') || '';
  const profileEmail = params.get('linkedin_email') || '';

  localStorage.setItem('vagasync_logged', 'true');
  localStorage.setItem('vagasync_role', 'candidate');
  userRole.value = 'candidate';
  isLoggedIn.value = true;
  activeTab.value = 'dashboard';
  localStorage.setItem('vagasync_linkedin_connected', 'true');
  linkedinTrigger.value++;

  if (profileName) authForm.value.name = profileName;
  if (profileEmail) authForm.value.email = profileEmail;

  showToast('Login LinkedIn', `Login autorizado pelo LinkedIn${profileName ? ' — ' + profileName : ''}.`, 'success');
  window.history.replaceState({}, document.title, window.location.pathname);
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

  // Registrar início do trial conforme o papel
  if (role === 'recruiter' && !localStorage.getItem('vagasync_recruiter_trial_start')) {
    localStorage.setItem('vagasync_recruiter_trial_start', Date.now().toString());
  } else if (role === 'candidate' && !localStorage.getItem('vagasync_candidate_trial_start')) {
    localStorage.setItem('vagasync_candidate_trial_start', Date.now().toString());
  }

  // Vincular LinkedIn no cadastro de candidato
  if (role === 'candidate' && authForm.value.linkLinkedIn) {
    localStorage.setItem('vagasync_linkedin_connected', 'true');
    linkedinTrigger.value++;
  }

  showToast('Conta Criada!', `Seu perfil de ${role === 'recruiter' ? 'Recrutador (30 dias grátis)' : role === 'super_admin' ? 'Administrador' : 'Candidato (7 dias grátis)'} foi configurado.`, 'success');
};

const handleLogout = () => {
  localStorage.removeItem('vagasync_logged');
  localStorage.removeItem('vagasync_role');
  localStorage.removeItem('vagasync_linkedin_connected');
  linkedinTrigger.value++;
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
  // Initialize dark/light mode
  if (localStorage.getItem('vagasync_dark_mode') === 'false') {
    document.documentElement.classList.add('light-mode');
  } else {
    document.documentElement.classList.remove('light-mode');
  }

  // Handle URL payment callbacks from Mercado Pago
  const urlParams = new URLSearchParams(window.location.search);
  const paymentStatus = urlParams.get('payment') || urlParams.get('status');
  if (paymentStatus === 'success' || paymentStatus === 'approved') {
    const planPaid = urlParams.get('plan_id') || 'candidate_premium';
    if (planPaid === 'candidate_premium') {
      userFeatures.value.ia_ilimitada = true;
      localStorage.setItem('vagasync_premium', 'true');
    } else if (planPaid === 'recruiter_pro') {
      userFeatures.value.ia_triagem = true;
      userFeatures.value.videoentrevistas = true;
      localStorage.setItem('vagasync_recruiter_pro', 'true');
    } else if (planPaid === 'impulsionar_vaga') {
      userFeatures.value.impulsionar_vaga_credits = (userFeatures.value.impulsionar_vaga_credits || 0) + 1;
    } else if (userFeatures.value[planPaid] !== undefined) {
      userFeatures.value[planPaid] = true;
    }
    showToast('Assinatura Confirmada! 💳', 'Seu plano/serviço foi ativado com sucesso e segurança no Mercado Pago.', 'success');
    window.history.replaceState({}, document.title, window.location.pathname);
  } else if (paymentStatus === 'failure' || paymentStatus === 'rejected') {
    showToast('Falha no Pagamento', 'A transação não pôde ser concluída. Tente novamente ou use outra forma de pagamento.', 'error');
    window.history.replaceState({}, document.title, window.location.pathname);
  }

  handleLinkedinCallback();

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
  eventSource = new EventSource(`${API_BASE}/automation/events`);
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
        showToast('✅ Candidatura Registrada!', logData.message, 'success', 'applications');
      } else if (logData.message.includes('CONTATO RECEBIDO') || logData.message.includes('respondeu')) {
        showToast('📞 Contato de Recrutador!', logData.message, 'success', 'recruiterContact');
        playNotificationSound();
      } else if (logData.message.includes('Gemini Web') && logData.message.includes('vagas encontradas')) {
        showToast('🌐 Gemini Web', logData.message, 'info', 'searchResults');
      } else if (logData.message.includes('Gemini LinkedIn') && logData.message.includes('vagas')) {
        showToast('💼 Gemini LinkedIn', logData.message, 'info', 'searchResults');
      }
    } catch (err) {
      console.error("SSE parse error", err);
    }
  };

  // Poll automation status periodically
  pollInterval = setInterval(() => {
    checkAutomationStatus();
    fetchJobs();
  }, 5000);

  // Load community feed and recruiter insights
  fetchFeed();
  fetchRecruiterInsights();

  // Inicialização do Tema Light Mode/Dark Mode
  if (localStorage.getItem('vagasync_dark_mode') === 'false') {
    document.documentElement.classList.add('light-mode');
  }


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

const startChatWithRecruiter = (job) => {
  activeJobIdFromNotification.value = job.id;
  activeTab.value = 'messenger';
};

const showToast = (title, message, type = 'info', notificationType = null) => {
  toast.value = { title, message, type };
  setTimeout(() => toast.value = null, 5000);

  // Send push notification only if enabled and for this specific notification type
  if (notificationSettings.value.enabled && Notification.permission === 'granted') {
    let shouldNotify = false;
    
    switch (notificationType) {
      case 'applications':
        shouldNotify = notificationSettings.value.onApplications;
        break;
      case 'recruiterContact':
        shouldNotify = notificationSettings.value.onRecruiterContact;
        break;
      case 'searchResults':
        shouldNotify = notificationSettings.value.onSearchResults;
        break;
      default:
        shouldNotify = true;
    }
    
    if (shouldNotify) {
      new Notification(title, { body: message });
    }
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
  if (isLinkedinConnected.value) {
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
  if (score >= 70) return 'Muito bom! Complete seu currículo para chegar a 90+ pts (LinkedIn já vinculado).';
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

const checkoutTitle = ref('Upgrade Premium');
const checkoutPrice = ref('R$ 29,90/mês');

// Helper to convert formatted price string to float value
const getNumericPrice = (priceStr) => {
  const clean = priceStr.replace('R$', '').replace('/mês', '').replace('/ano', '').replace('por apenas', '').trim();
  const val = parseFloat(clean.replace('.', '').replace(',', '.'));
  return isNaN(val) ? 29.90 : val;
};

// CRC16 CCITT False calculation for BC BR Code compliance
const calculateCRC16 = (data) => {
  let crc = 0xFFFF;
  for (let i = 0; i < data.length; i++) {
    crc ^= data.charCodeAt(i) << 8;
    for (let j = 0; j < 8; j++) {
      if ((crc & 0x8000) !== 0) {
        crc = ((crc << 1) ^ 0x1021) & 0xFFFF;
      } else {
        crc = (crc << 1) & 0xFFFF;
      }
    }
  }
  return crc.toString(16).toUpperCase().padStart(4, '0');
};

// Generates the standard static EMV BR Code string for Banco Central Pix
const generatePixPayload = (key, amount, receiverName = 'VAGASYNC PAYMENTS', city = 'SAO PAULO') => {
  const formattedAmount = Number(amount).toFixed(2);
  
  const guid = '0014br.gov.bcb.pix';
  const keyBlock = '01' + String(key.length).padStart(2, '0') + key;
  const merchantInfo = guid + keyBlock;
  const block26 = '26' + String(merchantInfo.length).padStart(2, '0') + merchantInfo;
  
  const block52 = '52040000';
  const block53 = '5303986';
  const block54 = '54' + String(formattedAmount.length).padStart(2, '0') + formattedAmount;
  const block58 = '5802BR';
  
  const cleanName = receiverName.normalize('NFD').replace(/[\u0300-\u036f]/g, '').slice(0, 25).toUpperCase();
  const block59 = '59' + String(cleanName.length).padStart(2, '0') + cleanName;
  
  const cleanCity = city.normalize('NFD').replace(/[\u0300-\u036f]/g, '').slice(0, 15).toUpperCase();
  const block60 = '60' + String(cleanCity.length).padStart(2, '0') + cleanCity;
  
  const block62 = '62070503***';
  
  const payloadWithoutCRC = '000201' + block26 + block52 + block53 + block54 + block58 + block59 + block60 + block62 + '6304';
  const crc = calculateCRC16(payloadWithoutCRC);
  
  return payloadWithoutCRC + crc;
};

// Computed properties for QR Code and Copy and Paste Pix code
const pixPayload = computed(() => {
  const key = config.value.pix_key || 'ricardomarchi@outlook.com';
  const amount = getNumericPrice(checkoutPrice.value);
  return generatePixPayload(key, amount);
});

const pixQRCodeUrl = computed(() => {
  return `https://chart.googleapis.com/chart?chs=250x250&cht=qr&chld=M|1&chl=${encodeURIComponent(pixPayload.value)}`;
});

const copyPixCopiaECola = () => {
  navigator.clipboard.writeText(pixPayload.value);
  pixCopied.value = true;
  showToast('Copiado', 'Código Pix Copia e Cola copiado com sucesso!', 'success');
};

const openCheckout = (plan, title = 'Upgrade Premium', price = 'R$ 29,90/mês') => {
  checkoutPlan.value = plan;
  checkoutTitle.value = title;
  checkoutPrice.value = price;
  pixCopied.value = false;
  checkoutOpen.value = true;
};

const handleCheckoutPayment = async () => {
  const userEmail = profileData.value.email || localStorage.getItem('vagasync_profile_email') || 'candidato@vagasync.com.br';
  
  if (checkoutPaymentMethod.value === 'card') {
    try {
      showToast('Processando...', 'Conectando ao Mercado Pago de forma segura...', 'info');
      const response = await fetch(`${API_BASE}/payments/create-preference`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan_id: checkoutPlan.value,
          user_email: userEmail
        })
      });
      if (!response.ok) {
        throw new Error('Falha ao gerar preferência');
      }
      const data = await response.json();
      if (data.checkout_url) {
        showToast('Redirecionando...', 'Redirecionando para o ambiente de pagamento seguro...', 'success');
        setTimeout(() => {
          window.location.href = data.checkout_url;
        }, 1200);
      } else {
        showToast('Erro de Pagamento', 'Não foi possível gerar a página de checkout seguro.', 'error');
      }
    } catch (err) {
      console.error(err);
      showToast('Erro de Conexão', 'Erro ao processar com o Mercado Pago. Tente novamente mais tarde.', 'error');
    }
  } else {
    // Pix: display the locally generated QR Code and wait for approval
    showToast('Pix Gerado!', 'Utilize o QR Code ou copie o código Pix abaixo para pagar.', 'success');
  }
};

const cancelPremium = (plan) => {
  if (plan === 'candidate_premium') {
    userFeatures.value.ia_ilimitada = false;
    localStorage.setItem('vagasync_premium', 'false');
    showToast('Plano Cancelado', 'Você retornou ao Plano Gratuito.', 'info');
  } else if (plan === 'recruiter_pro') {
    userFeatures.value.ia_triagem = false;
    userFeatures.value.videoentrevistas = false;
    localStorage.setItem('vagasync_recruiter_pro', 'false');
    showToast('Plano Cancelado', 'Você retornou ao Plano Gratuito de Recrutador.', 'info');
  } else if (plan) {
    userFeatures.value[plan] = false;
    showToast('Recurso Desativado', `O recurso "${plan}" foi cancelado.`, 'info');
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
const footerClickText = ref('');
const handleFooterClick = () => {
  footerClicks.value++;
  const remaining = 3 - footerClicks.value;
  if (remaining > 0) {
    footerClickText.value = `Clique mais ${remaining} vez${remaining !== 1 ? 'es' : ''} para acessar o painel do proprietário`;
  }
  if (footerClicks.value >= 3) {
    footerClicks.value = 0;
    footerClickText.value = '';
    secretLoginOpen.value = true;
    showToast('Acesso Secreto', 'Painel administrativo secreto ativado.', 'info');
  }
  setTimeout(() => {
    if (footerClicks.value > 0 && footerClicks.value < 3) footerClickText.value = '';
  }, 3000);
};

// Keyboard shortcut for owner access (Shift + O)
// NOTE: Shift+O handler is registered in the main onMounted() to avoid duplicated onMounted() blocks.


// Secret admin login state
const secretLoginOpen = ref(false);
const secretEmail = ref('');
const secretPassword = ref('');
const secret2faOpen = ref(false);
const secret2faCode = ref('');
const tempAdminToken = ref('');
const adminToken = ref(localStorage.getItem('vagasync_admin_token') || '');
const adminRefreshToken = ref(localStorage.getItem('vagasync_admin_refresh') || '');
const admin2faLoading = ref(false);

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
  
  console.log('🔓 Admin Login Attempt:', { email: secretEmail.value });
  
  // For development: Always use mock mode with dev credentials
  if (secretEmail.value === 'admin@vagasync.com' && secretPassword.value === 'admin123') {
    console.log('✅ Dev Credentials Detected - Using Mock Mode');
    tempAdminToken.value = 'dev-temp-token-' + Date.now();
    secret2faOpen.value = true;
    showToast('Credenciais Validadas', '✅ Modo Dev - Insira qualquer código 2FA (ex: 123456).', 'info');
    return;
  }
  
  // Try real server
  try {
    console.log('📡 Attempting server login...');
    const res = await fetch(`${API_BASE}/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: secretEmail.value, password: secretPassword.value })
    });
    console.log('📡 Server Response:', res.status);
    
    if (res.ok) {
      const data = await res.json();
      if (data.needs_2fa) {
        tempAdminToken.value = data.temp_token;
        secret2faOpen.value = true;
        showToast('Credenciais Validadas', 'Por favor, insira o código 2FA de 6 dígitos.', 'info');
      }
    } else {
      const err = await res.json();
      showToast('Erro de Login', err.detail || 'E-mail ou senha do proprietário incorretos.', 'error');
    }
  } catch (err) {
    console.error('❌ Server connection failed:', err);
    showToast('Erro', 'Servidor não respondeu. Use credenciais dev (admin@vagasync.com / admin123).', 'error');
  }
};

const handleAdminVerify2fa = async (e) => {
  if (e) e.preventDefault();
  admin2faLoading.value = true;
  
  console.log('🔐 2FA Verification Started');
  console.log('tempAdminToken:', tempAdminToken.value);
  console.log('secret2faCode:', secret2faCode.value);
  
  try {
    // Check if we're in dev mock mode first
    if (tempAdminToken.value.startsWith('dev-temp-token-')) {
      console.log('✅ Using Dev Mock Mode - Backend Call');
      const mockToken = 'mock-super-admin-token-' + Date.now();
      adminToken.value = mockToken;
      adminRefreshToken.value = mockToken;
      localStorage.setItem('vagasync_admin_token', mockToken);
      localStorage.setItem('vagasync_admin_refresh', mockToken);
      
      userRole.value = 'super_admin';
      localStorage.setItem('vagasync_role', 'super_admin');
      isLoggedIn.value = true;
      localStorage.setItem('vagasync_logged', 'true');
      
      console.log('✅ State Updated:', { isLoggedIn: isLoggedIn.value, userRole: userRole.value });
      
      secret2faOpen.value = false;
      secretLoginOpen.value = false;
      secretEmail.value = '';
      secretPassword.value = '';
      secret2faCode.value = '';
      
      activeTab.value = 'super_admin';
      admin2faLoading.value = false;
      
      await nextTick();
      console.log('✅ DOM Updated');
      
      loadAdminData();
      showToast('Acesso Super Admin', '✅ Bem-vindo, Proprietário! Painel carregando...', 'success');
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
      admin2faLoading.value = false;
      await loadAdminData();
      showToast('Acesso Super Admin', 'Seja bem-vindo de volta, Proprietário do Sistema!', 'success');
    } else {
      const err = await res.json();
      admin2faLoading.value = false;
      showToast('Erro 2FA', err.detail || 'Código 2FA incorreto ou expirado.', 'error');
    }
  } catch (err) {
    console.error('❌ 2FA Error:', err);
    admin2faLoading.value = false;
    showToast('Erro', 'Falha ao validar 2FA: ' + err.message, 'error');
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

// Recruiter apply modal state & actions for candidate
const showApplyRecruiterModal = ref(false);
const selectedJobForApply = ref(null);

const openApplyModal = (job) => {
  selectedJobForApply.value = job;
  showApplyRecruiterModal.value = true;
};

const confirmApplyToRecruiterJob = async () => {
  if (!selectedJobForApply.value) return;

  if (!config.value.resume_text || config.value.resume_text.trim().length < 10) {
    showToast(
      'Currículo Ausente',
      'Você precisa preencher ou fazer upload de seu currículo na aba "Currículo & Perfil IA" para liberar a candidatura.',
      'error'
    );
    activeTab.value = 'resume';
    showApplyRecruiterModal.value = false;
    return;
  }

  const job = selectedJobForApply.value;
  try {
    const res = await fetch(`${API_BASE}/jobs/${job.id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ status: 'applied' })
    });
    
    if (res.ok) {
      const localJob = jobs.value.find(j => j.id === job.id);
      if (localJob) {
        localJob.status = 'applied';
      }
      
      const candidateName = authForm.value.name || 'Candidato VagaSync';
      const candidateEmail = authForm.value.email || 'candidato@vagasync.com';
      
      const newCandidate = {
        id: Date.now(),
        name: candidateName,
        email: candidateEmail,
        role: job.title,
        match: job.match_score || 95,
        status: 'recebidos',
        resume: config.value.resume_text,
        applied_job_id: job.id
      };
      
      recruitedCandidates.value = [newCandidate, ...recruitedCandidates.value];
      saveCandidates();
      
      showToast(
        'Currículo Enviado!',
        'Candidatura realizada com sucesso. O chat com o recrutador foi desbloqueado!',
        'success'
      );
      showApplyRecruiterModal.value = false;
    } else {
      showToast('Erro ao Candidatar', 'Não foi possível atualizar o status da candidatura no servidor.', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Erro de Conexão', 'Erro ao se conectar ao servidor.', 'error');
  }
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

    <!-- Modal de Candidatura para Vaga do Recrutador -->
    <div v-if="showApplyRecruiterModal && selectedJobForApply" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(6, 9, 19, 0.85); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 10000; padding: 1rem;">
      <div class="glass-card" style="width: 100%; max-width: 600px; border: 1px solid rgba(16,185,129,0.3); display: flex; flex-direction: column; gap: 1.5rem; animation: modalFadeIn 0.3s ease;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
          <div>
            <h3 style="margin: 0; font-size: 1.25rem; color: #fff; display: flex; align-items: center; gap: 0.5rem;">
              <i class="fa-solid fa-file-signature" style="color: #34d399;"></i> Enviar Currículo para Recrutador
            </h3>
            <span style="font-size: 0.85rem; color: var(--text-secondary);">
              VagaSync Simplificada • Triagem Direta
            </span>
          </div>
          <button @click="showApplyRecruiterModal = false" style="background: none; border: none; color: var(--text-secondary); font-size: 1.5rem; cursor: pointer; line-height: 1;">&times;</button>
        </div>

        <div style="background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.15); border-radius: 8px; padding: 1rem; display: flex; flex-direction: column; gap: 0.25rem;">
          <div style="font-size: 0.75rem; color: #34d399; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em;">Vaga Selecionada</div>
          <div style="font-size: 1.05rem; font-weight: 700; color: #fff;">{{ selectedJobForApply.title }}</div>
          <div style="font-size: 0.85rem; color: var(--text-secondary);">{{ selectedJobForApply.company }} • {{ selectedJobForApply.location }}</div>
        </div>

        <!-- Currículo Text Preview -->
        <div style="display: flex; flex-direction: column; gap: 0.5rem; flex: 1;">
          <div style="font-weight: 700; font-size: 0.85rem; color: var(--text-primary); display: flex; align-items: center; justify-content: space-between;">
            <span>Seu Currículo Cadastrado</span>
            <span style="font-size: 0.75rem; font-weight: normal; color: var(--text-muted);">
              (Será triado automaticamente pelo RH)
            </span>
          </div>
          
          <div v-if="config.resume_text && config.resume_text.trim().length >= 10" style="
            background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.08); 
            border-radius: 8px; padding: 1rem; font-size: 0.8rem; color: var(--text-secondary); 
            max-height: 200px; overflow-y: auto; white-space: pre-wrap; line-height: 1.6;
          ">
            {{ config.resume_text }}
          </div>
          <div v-else style="background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2); border-radius: 8px; padding: 1rem; text-align: center;">
            <p style="color: #f87171; font-weight: 600; font-size: 0.85rem; margin: 0 0 0.5rem 0;">Nenhum currículo cadastrado no sistema!</p>
            <p style="color: var(--text-secondary); font-size: 0.8rem; margin: 0 0 1rem 0;">Você precisa cadastrar seu currículo antes de prosseguir com a candidatura.</p>
            <button class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.4rem 1rem;" @click="() => { showApplyRecruiterModal = false; activeTab = 'resume'; }">
              Ir para Cadastro de Currículo
            </button>
          </div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 0.75rem; border-top: 1px solid var(--border-color); padding-top: 1rem;">
          <button class="btn btn-secondary" style="font-size: 0.85rem;" @click="showApplyRecruiterModal = false">
            Cancelar
          </button>
          <button 
            v-if="config.resume_text && config.resume_text.trim().length >= 10"
            class="btn btn-primary" 
            style="font-size: 0.85rem; background: linear-gradient(135deg, #10b981, #059669); color: #fff; border: none; font-weight: 700;" 
            @click="confirmApplyToRecruiterJob"
          >
            Confirmar Candidatura
          </button>
        </div>
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
              <i class="fa-solid fa-eye" style="color: var(--text-muted); font-size: 0.85rem; padding-right: 0.25rem;" title="Visualização do Arquivo"></i>
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

            <!-- Se não tiver o recurso de IA Triagem, exibe o bloqueio -->
            <div v-if="!userFeatures.ia_triagem" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; text-align: center; gap: 1rem; min-height: 250px; padding: 1rem;">
              <i class="fa-solid fa-lock" style="font-size: 2.5rem; color: #f59e0b; opacity: 0.85;"></i>
              <h4 style="margin: 0; color: #fff; font-size: 1.05rem;">🔒 Análise IA Bloqueada</h4>
              <p style="font-size: 0.82rem; color: var(--text-secondary); max-width: 250px; line-height: 1.5;">
                A análise técnica profunda feita por Inteligência Artificial é exclusiva para assinantes do recurso **IA Avançada Triagem**.
              </p>
              <button 
                class="btn btn-primary" 
                style="background: linear-gradient(135deg, #00f2fe, #3b82f6); border: none; color: #060913; font-weight: 700; width: 100%; margin-top: 0.5rem;"
                @click="openCheckout('ia_triagem', 'IA Avançada Triagem', 'R$ 9,90/mês'); showCandidateModal = false;"
              >
                Ativar IA Avançada (R$ 9,90)
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

    <!-- LinkedIn OAuth Setup Modal -->
    <div v-if="showLinkedinOAuthModal" class="modal-overlay" style="
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(3, 5, 12, 0.97); backdrop-filter: blur(16px);
      display: flex; align-items: center; justify-content: center; z-index: 10000;
      overflow-y: auto; padding: 1rem;
    ">
      <div class="glass-card" style="width: 500px; padding: 2rem; border: 1px solid rgba(10, 102, 194, 0.4); display: flex; flex-direction: column; gap: 1.25rem; max-height: 95vh; overflow-y: auto; box-shadow: 0 0 60px rgba(10,102,194,0.15);">
        
        <!-- Header -->
        <div style="display: flex; align-items: center; gap: 12px;">
          <div style="background: linear-gradient(135deg, #0a66c2, #0077b5); width: 46px; height: 46px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
            <i class="fa-brands fa-linkedin" style="color: #fff; font-size: 1.4rem;"></i>
          </div>
          <div>
            <h3 style="font-size: 1.15rem; margin: 0; color: #fff;">Conectar com LinkedIn</h3>
            <p style="font-size: 0.78rem; color: var(--text-secondary); margin: 2px 0 0;">OAuth 2.0 — Login seguro e real</p>
          </div>
        </div>

        <!-- Instrução passo a passo -->
        <div style="background: rgba(10, 102, 194, 0.08); border: 1px solid rgba(10, 102, 194, 0.2); border-radius: 10px; padding: 1rem; display: flex; flex-direction: column; gap: 0.6rem;">
          <div style="font-size: 0.82rem; font-weight: 700; color: #60a5fa; margin-bottom: 0.25rem;">📋 Como configurar em 3 passos:</div>
          <div style="font-size: 0.78rem; color: var(--text-secondary); line-height: 1.5;">
            <strong style="color:#fff;">1.</strong> Acesse
            <a href="https://www.linkedin.com/developers/apps" target="_blank" style="color: #60a5fa; text-decoration: underline;">linkedin.com/developers/apps</a>
            e crie ou selecione seu app.<br>
            <strong style="color:#fff;">2.</strong> Em <em>Auth</em>, adicione esta URL de callback:<br>
            <code style="background: rgba(0,0,0,0.4); color: #00f2fe; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; word-break: break-all;">https://vagasync.com.br/api/linkedin/callback</code><br>
            <strong style="color:#fff;">3.</strong> Copie o <strong style="color:#fff;">Client ID</strong> e o <strong style="color:#fff;">Client Secret</strong> abaixo.
          </div>
        </div>

        <!-- Campos OAuth -->
        <div class="form-group" style="margin: 0;">
          <label style="font-size: 0.72rem; color: var(--text-secondary); margin-bottom: 0.3rem; display: block; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;">LinkedIn Client ID</label>
          <input 
            type="text" 
            class="form-input" 
            style="font-size: 0.85rem; padding: 0.5rem 0.75rem; font-family: monospace;" 
            v-model="config.linkedin_client_id" 
            placeholder="Ex: 78abc123def456..."
            autocomplete="off"
          />
        </div>

        <div class="form-group" style="margin: 0;">
          <label style="font-size: 0.72rem; color: var(--text-secondary); margin-bottom: 0.3rem; display: block; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;">LinkedIn Client Secret</label>
          <input 
            type="password" 
            class="form-input" 
            style="font-size: 0.85rem; padding: 0.5rem 0.75rem; font-family: monospace;" 
            v-model="config.linkedin_client_secret" 
            placeholder="••••••••••••••••"
            autocomplete="new-password"
          />
        </div>

        <!-- Botão principal -->
        <button 
          type="button" 
          class="btn btn-primary" 
          style="background: linear-gradient(135deg, #0a66c2, #0077b5); border: none; color: #fff; font-weight: 700; padding: 0.75rem; font-size: 0.9rem; display: flex; align-items: center; justify-content: center; gap: 8px; border-radius: 10px;" 
          @click="saveCredentialsAndLoginReal"
        >
          <i class="fa-brands fa-linkedin"></i> Salvar e Entrar com LinkedIn
        </button>

        <!-- Divisor -->
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <div style="flex: 1; height: 1px; background: var(--border-color);"></div>
          <span style="font-size: 0.72rem; color: var(--text-muted);">ou entre sem LinkedIn</span>
          <div style="flex: 1; height: 1px; background: var(--border-color);"></div>
        </div>

        <!-- Botão fechar / usar email -->
        <button 
          type="button" 
          class="btn btn-secondary" 
          style="padding: 0.6rem; font-size: 0.85rem;"
          @click="showLinkedinOAuthModal = false;"
        >
          Usar e-mail e senha
        </button>
      </div>
    </div>


    <!-- Checkout Modals (Stripe / Pix checkout simulation) -->
    <div v-if="checkoutOpen" class="modal-overlay" style="
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(3, 5, 12, 0.95); backdrop-filter: blur(10px);
      display: flex; align-items: center; justify-content: center; z-index: 10000;
    ">
      <div class="glass-card" style="width: 450px; padding: 2rem; border: 1px solid rgba(59, 130, 246, 0.3);">
        <h3 style="font-size: 1.25rem; margin-bottom: 0.5rem; text-align: center; color: #00f2fe;">{{ checkoutTitle }}</h3>
        <p style="text-align: center; font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1.5rem;">
          Ative agora este recurso por apenas {{ checkoutPrice }}
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

        <!-- Pix Area (Banco Central BR Code) -->
        <div v-if="checkoutPaymentMethod === 'pix'" style="display: flex; flex-direction: column; align-items: center; gap: 0.75rem; background: rgba(0,0,0,0.25); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(0, 242, 254, 0.15);">
          <div style="background: white; padding: 0.75rem; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.25); display: flex; justify-content: center; align-items: center;">
            <!-- Real QR Code dynamic image from Google Charts -->
            <img 
              :src="pixQRCodeUrl" 
              alt="QR Code Pix Oficial Banco Central" 
              style="width: 150px; height: 150px; display: block; object-fit: contain;" 
            />
          </div>
          <span style="font-size: 0.75rem; color: var(--text-secondary); text-align: center; font-weight: 500;">
            Chave Pix configurada: <code style="color: #00f2fe; background: rgba(0,242,254,0.1); padding: 2px 6px; border-radius: 4px;">{{ config.pix_key || 'ricardomarchi@outlook.com' }}</code>
          </span>
          
          <button 
            type="button" 
            class="btn btn-secondary" 
            style="font-size: 0.8rem; width: 100%; display: flex; align-items: center; justify-content: center; gap: 6px;"
            @click="copyPixCopiaECola"
          >
            <i class="fa-solid fa-copy"></i>
            {{ pixCopied ? '✓ Copiado!' : 'Copiar Código Copia e Cola' }}
          </button>
        </div>

        <!-- Card Area -->
        <div v-else style="display: flex; flex-direction: column; gap: 1rem; background: rgba(59, 130, 246, 0.05); padding: 1.25rem; border-radius: 12px; border: 1px solid rgba(59, 130, 246, 0.2); text-align: center; align-items: center;">
          <i class="fa-solid fa-shield-halved" style="font-size: 2rem; color: #00f2fe; margin-bottom: 0.2rem; filter: drop-shadow(0 0 10px rgba(0, 242, 254, 0.3));"></i>
          <span style="font-size: 0.88rem; font-weight: 700; color: #fff;">Pagamento 100% Seguro & Criptografado</span>
          <p style="font-size: 0.78rem; color: var(--text-muted); line-height: 1.5; margin: 0;">
            Seus dados são protegidos por criptografia SSL de ponta a ponta. Você será redirecionado para a plataforma oficial do Mercado Pago para inserir os dados do seu cartão com segurança total.
          </p>
        </div>

        <div style="display: flex; gap: 0.5rem; margin-top: 1.5rem;">
          <button type="button" class="btn btn-primary" style="flex: 1;" @click="handleCheckoutPayment">
            {{ checkoutPaymentMethod === 'card' ? 'Ir para Pagamento Seguro 🔒' : 'Confirmar Pagamento' }}
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
          <button 
            type="submit" 
            class="btn btn-primary" 
            style="width: 100%; margin-top: 0.5rem; background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; font-weight: 700;"
            :disabled="admin2faLoading"
          >
            <span v-if="admin2faLoading">
              <i class="fa-solid fa-spinner fa-spin" style="margin-right: 0.5rem;"></i>Verificando...
            </span>
            <span v-else>
              Confirmar Código 2FA
            </span>
          </button>
          <button 
            type="button" 
            class="btn btn-secondary" 
            @click="secret2faOpen = false; secretLoginOpen = false;" 
            style="width: 100%;"
            :disabled="admin2faLoading"
          >
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
            <img src="/vagasync_logo.png?v=6" alt="Vaga Sync Logo" class="logo-icon-img" style="width: 56px; height: 56px;" />
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
            <h3 style="margin: 1.5rem 0 1.25rem 0; color: var(--color-secondary);">Como Funciona:</h3>
            <div class="step-item" style="align-items: center; margin-bottom: 1.25rem;">
              <div style="flex-shrink:0; width:48px; height:48px; display:flex; align-items:center; justify-content:center; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; transition: transform 0.3s ease, border-color 0.3s, background-color 0.3s;" onmouseover="this.style.transform='scale(1.1) rotate(5deg)'; this.style.borderColor='var(--color-secondary)'; this.style.backgroundColor='rgba(0, 242, 254, 0.05)'" onmouseout="this.style.transform='scale(1) rotate(0deg)'; this.style.borderColor='rgba(255,255,255,0.05)'; this.style.backgroundColor='rgba(255,255,255,0.02)'">
                <img src="/icons/3d/login.png" style="width:34px; height:34px; object-fit:contain;" alt="LinkedIn Logo 3D" />
              </div>
              <div>
                <h4 style="margin: 0 0 0.15rem 0; font-size: 0.95rem; color: #fff;">Vincule seu LinkedIn</h4>
                <p style="margin: 0; font-size: 0.82rem; color: var(--text-secondary); line-height: 1.4;">Conecte seu perfil para puxar e analisar vagas compatíveis diretamente com suas preferências.</p>
              </div>
            </div>
            <div class="step-item" style="align-items: center; margin-bottom: 1.25rem;">
              <div style="flex-shrink:0; width:48px; height:48px; display:flex; align-items:center; justify-content:center; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; transition: transform 0.3s ease, border-color 0.3s, background-color 0.3s;" onmouseover="this.style.transform='scale(1.1) rotate(5deg)'; this.style.borderColor='var(--color-secondary)'; this.style.backgroundColor='rgba(0, 242, 254, 0.05)'" onmouseout="this.style.transform='scale(1) rotate(0deg)'; this.style.borderColor='rgba(255,255,255,0.05)'; this.style.backgroundColor='rgba(255,255,255,0.02)'">
                <img src="/icons/3d/deploy.png" style="width:34px; height:34px; object-fit:contain;" alt="Upload CV 3D" />
              </div>
              <div>
                <h4 style="margin: 0 0 0.15rem 0; font-size: 0.95rem; color: #fff;">Importação e Mapeamento IA</h4>
                <p style="margin: 0; font-size: 0.82rem; color: var(--text-secondary); line-height: 1.4;">Envie seu currículo. A IA do Gemini mapeia suas competências técnicas e alinha seu perfil.</p>
              </div>
            </div>
            <div class="step-item" style="align-items: center; margin-bottom: 1.25rem;">
              <div style="flex-shrink:0; width:48px; height:48px; display:flex; align-items:center; justify-content:center; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; transition: transform 0.3s ease, border-color 0.3s, background-color 0.3s;" onmouseover="this.style.transform='scale(1.1) rotate(5deg)'; this.style.borderColor='var(--color-secondary)'; this.style.backgroundColor='rgba(0, 242, 254, 0.05)'" onmouseout="this.style.transform='scale(1) rotate(0deg)'; this.style.borderColor='rgba(255,255,255,0.05)'; this.style.backgroundColor='rgba(255,255,255,0.02)'">
                <img src="/icons/3d/briefcase.png" style="width:34px; height:34px; object-fit:contain;" alt="Briefcase 3D" />
              </div>
              <div>
                <h4 style="margin: 0 0 0.15rem 0; font-size: 0.95rem; color: #fff;">Agente de Candidatura</h4>
                <p style="margin: 0; font-size: 0.82rem; color: var(--text-secondary); line-height: 1.4;">O robô Playwright realiza candidaturas simplificadas automáticas em segundo plano.</p>
              </div>
            </div>
            <div class="step-item" style="align-items: center; margin-bottom: 1.25rem;">
              <div style="flex-shrink:0; width:48px; height:48px; display:flex; align-items:center; justify-content:center; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 12px; transition: transform 0.3s ease, border-color 0.3s, background-color 0.3s;" onmouseover="this.style.transform='scale(1.1) rotate(5deg)'; this.style.borderColor='var(--color-secondary)'; this.style.backgroundColor='rgba(0, 242, 254, 0.05)'" onmouseout="this.style.transform='scale(1) rotate(0deg)'; this.style.borderColor='rgba(255,255,255,0.05)'; this.style.backgroundColor='rgba(255,255,255,0.02)'">
                <img src="/icons/3d/chat.png" style="width:34px; height:34px; object-fit:contain;" alt="Chat 3D" />
              </div>
              <div>
                <h4 style="margin: 0 0 0.15rem 0; font-size: 0.95rem; color: #fff;">Follow-up de RH & WhatsApp</h4>
                <p style="margin: 0; font-size: 0.82rem; color: var(--text-secondary); line-height: 1.4;">Acompanhamento inteligente de análise do RH e alertas instantâneos no seu celular.</p>
              </div>
            </div>
          </div>

          <!-- ── Bloco de Anúncio AdSense (Home) ── -->
          <div style="margin-top: 1.5rem; width: 100%; border-radius: 14px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.015);">
            <div style="padding: 0.4rem 0.75rem; background: rgba(59,130,246,0.05); border-bottom: 1px solid rgba(59,130,246,0.08); display: flex; align-items: center; gap: 0.4rem;">
              <i class="fa-solid fa-rectangle-ad" style="color: rgba(148,163,184,0.4); font-size: 0.7rem;"></i>
              <span style="font-size: 0.65rem; color: rgba(148,163,184,0.4); letter-spacing: 0.05em; text-transform: uppercase;">Publicidade</span>
            </div>
            <ins class="adsbygoogle"
              style="display:block; min-height: 100px;"
              data-ad-client="ca-pub-1405601693512304"
              data-ad-slot="auto"
              data-ad-format="auto"
              data-full-width-responsive="true">
            </ins>
          </div>
        </div>

        <!-- Right panel: Login/Signup Card -->
        <div class="auth-right">
          <div class="glass-card auth-form-card">
            <!-- Owner/Admin Access Button -->
            <div style="
              background: linear-gradient(135deg, rgba(0, 242, 254, 0.1), rgba(59, 130, 246, 0.1));
              border: 2px solid rgba(0, 242, 254, 0.3);
              border-radius: 12px;
              padding: 1rem;
              margin-bottom: 1.5rem;
              text-align: center;
            ">
              <button
                type="button"
                @click="secretLoginOpen = true"
                style="
                  background: linear-gradient(135deg, #00f2fe, #3b82f6);
                  color: #060913;
                  border: none;
                  padding: 0.75rem 1.5rem;
                  border-radius: 8px;
                  font-weight: 700;
                  cursor: pointer;
                  width: 100%;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  gap: 0.5rem;
                  font-size: 0.95rem;
                  transition: all 0.2s;
                "
                @mouseover="(e) => e.target.style.transform = 'translateY(-2px)'"
                @mouseout="(e) => e.target.style.transform = 'translateY(0)'"
              >
                <i class="fa-solid fa-user-shield"></i> Acessar Painel do Proprietário
              </button>
              <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.5rem;">
                💡 Dica: Você também pode usar Shift+O
              </div>
            </div>

            <form v-if="authMode === 'login'" @submit="handleLogin">
              <h2 style="margin-bottom: 0.5rem; font-size: 1.75rem;">Acesse sua Conta</h2>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1.5rem;">
                Faça login para gerenciar suas candidaturas automatizadas.
              </p>

              <button 
                type="button" 
                class="btn social-btn-linkedin"
                @click="handleLinkedinLogin"
                style="position: relative; overflow: hidden; display: flex; align-items: center; justify-content: center; gap: 8px;"
              >
                <i class="fa-brands fa-linkedin" style="font-size: 1.25rem; color: #fff;"></i>
                Entrar com LinkedIn
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
      <footer class="footer-bar" @click="handleFooterClick" style="cursor: pointer; position: relative;">
        <p>© 2026 Vaga Sync. Todos os direitos reservados. • Conexão Segura SSL • Gemini Core Engine • n8n Connected</p>
        <div v-if="footerClickText" style="
          position: absolute;
          bottom: 100%;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(0, 242, 254, 0.95);
          color: #060913;
          padding: 0.6rem 1rem;
          border-radius: 8px;
          font-size: 0.82rem;
          font-weight: 600;
          white-space: nowrap;
          margin-bottom: 0.5rem;
          animation: slideUp 0.3s ease;
          z-index: 100;
        ">
          {{ footerClickText }}
        </div>
      </footer>
    </template>

    <!-- Main Logged In Application Dashboard -->
    <template v-else>
      <!-- Unified Navigation Bar -->
      <header class="header">
        <div class="logo-container">
          <img src="/vagasync_logo.png?v=6" alt="Vaga Sync Logo" class="logo-icon-img" />
          <span class="logo-text">Vaga Sync</span>
        </div>

        <nav class="nav-menu" v-if="userRole === 'candidate'">
          <button 
            :class="['nav-link-btn', { active: activeTab === 'dashboard' }]"
            @click="activeTab = 'dashboard'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #3b82f6; flex-shrink: 0;"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg> Painel Principal
          </button>
          
          <button 
            :class="['nav-link-btn', { active: activeTab === 'map' }]"
            @click="activeTab = 'map'"
            style="position: relative;"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #10b981; flex-shrink: 0;"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"></polygon><line x1="8" y1="2" x2="8" y2="18"></line><line x1="16" y1="6" x2="16" y2="22"></line></svg> Mapa de Vagas
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
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #ec4899; flex-shrink: 0;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg> Contato com RH
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
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #00f2fe; flex-shrink: 0;"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg> Mensagens
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
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #fbbf24; flex-shrink: 0;"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg> Currículo & Perfil IA
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'career' }]"
            @click="activeTab = 'career'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #a855f7; flex-shrink: 0;"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path></svg> Copiloto IA
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'interview' }]"
            @click="activeTab = 'interview'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #f43f5e; flex-shrink: 0;"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v1a7 7 0 0 1-14 0v-1"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg> Treino Entrevista
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'community_feed' }]"
            @click="activeTab = 'community_feed'; fetchFeed();"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #fb923c; flex-shrink: 0;"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg> Feed Comunidade
          </button>
          
          <button 
            :class="['nav-link-btn', { active: activeTab === 'config' }]"
            @click="activeTab = 'config'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #94a3b8; flex-shrink: 0;"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg> Configurações
          </button>
        </nav>

        <nav class="nav-menu" v-else-if="userRole === 'recruiter'">
          <button 
            :class="['nav-link-btn', { active: activeTab === 'recruiter_dashboard' }]"
            @click="activeTab = 'recruiter_dashboard'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #3b82f6; flex-shrink: 0;"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"></path><path d="M22 12A10 10 0 0 0 12 2v10z"></path></svg> Painel Recrutador
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'recruiter_jobs' }]"
            @click="activeTab = 'recruiter_jobs'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #10b981; flex-shrink: 0;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg> Criar Vaga
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'messenger' }]"
            @click="activeTab = 'messenger'"
            style="position: relative;"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #00f2fe; flex-shrink: 0;"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg> Mensagens
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
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #eab308; flex-shrink: 0;"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line></svg> Faturamento SaaS
          </button>

          <button 
            :class="['nav-link-btn', { active: activeTab === 'community_feed' }]"
            @click="activeTab = 'community_feed'; fetchFeed();"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #fb923c; flex-shrink: 0;"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg> Feed Comunidade
          </button>
        </nav>

        <nav class="nav-menu" v-else-if="userRole === 'super_admin'">
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin' }]"
            @click="activeTab = 'super_admin'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #3b82f6; flex-shrink: 0;"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg> Painel Global
          </button>
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin_monetization' }]"
            @click="activeTab = 'super_admin_monetization'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #10b981; flex-shrink: 0;"><line x1="12" y1="1" x2="12" y2="23"></line><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg> Monetização
          </button>
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin_gateways' }]"
            @click="activeTab = 'super_admin_gateways'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #a855f7; flex-shrink: 0;"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"></path></svg> Gateways
          </button>
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin_tracking' }]"
            @click="activeTab = 'super_admin_tracking'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #00f2fe; flex-shrink: 0;"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg> Rastreamento
          </button>
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin_content' }]"
            @click="activeTab = 'super_admin_content'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #fb923c; flex-shrink: 0;"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg> Conteúdo
          </button>
          <button 
            :class="['nav-link-btn', { active: activeTab === 'super_admin_security' }]"
            @click="activeTab = 'super_admin_security'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 14px; height: 14px; color: #ef4444; flex-shrink: 0;"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg> Segurança
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
          <!-- ── PAYWALL OVERLAY: Trial Candidato Expirado ── -->
          <div v-if="candidateTrialExpired" style="position: absolute; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; background: rgba(6, 9, 19, 0.96); backdrop-filter: blur(15px); padding: 2rem; border-radius: 12px; min-height: 600px;">
            <div style="max-width: 500px; text-align: center; border: 1.5px solid rgba(59, 130, 246, 0.35); background: rgba(13, 20, 38, 0.85); padding: 3rem 2rem; border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.6); position: relative;">
              <img src="/icons/3d/security.png" style="width: 64px; height: 64px; object-fit: contain; margin-bottom: 1.5rem; filter: drop-shadow(0 0 20px rgba(59,130,246,0.4));" alt="Bloqueado" />
              <h2 style="color: #fff; font-size: 1.8rem; margin: 0 0 0.5rem;">Período de Teste de Candidato Encerrado</h2>
              <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 2rem; line-height: 1.6;">
                Seu trial gratuito de <strong style="color: #fff;">7 dias</strong> chegou ao fim. Assine o plano <strong style="color: #00f2fe;">VagaSync Premium</strong> para continuar acessando o painel de candidaturas por IA, treinador de entrevistas e WebRTC.
              </p>
              
              <div style="background: linear-gradient(135deg, rgba(0,242,254,0.08), rgba(59,130,246,0.12)); border: 1.5px solid rgba(0,242,254,0.35); border-radius: 14px; padding: 1.5rem 1.25rem; text-align: left; position: relative; margin-bottom: 1.5rem;">
                <div style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: linear-gradient(90deg, #00f2fe, #3b82f6); color: #fff; font-size: 0.65rem; font-weight: 700; padding: 3px 12px; border-radius: 20px; letter-spacing: 0.05em; box-shadow: 0 4px 10px rgba(0, 242, 254, 0.25);">RECOMENDADO</div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                  <div style="font-size: 0.75rem; color: #00f2fe; text-transform: uppercase; letter-spacing: 0.05em;">Plano Premium</div>
                  <img src="/icons/3d/value.png" style="width: 32px; height: 32px; object-fit: contain; filter: drop-shadow(0 4px 6px rgba(0,242,254,0.15));" alt="Premium Diamond 3D" />
                </div>
                <div style="font-size: 2rem; font-weight: 800; color: #fff;">R$ 29,90<span style="font-size: 1rem; font-weight: 400; color: var(--text-secondary);">/mês</span></div>
                <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem; line-height: 1.5;">Varreduras e candidaturas ilimitadas<br>IA Gemini com match inteligente<br>Treino de entrevistas ilimitado<br>Mensagens com RH e suporte</div>
                <button @click="openCheckout('candidate_premium', 'Assinatura VagaSync Premium', 'R$ 29,90/mês')" class="btn btn-primary" style="width: 100%; margin-top: 1rem; font-size: 0.85rem; background: linear-gradient(90deg, #00f2fe, #3b82f6); color: #060913; font-weight: 700; border: none;">Assinar Premium</button>
              </div>
              <p style="font-size: 0.72rem; color: var(--text-muted); margin: 0;">Pague via Pix ou Cartão - Cancele quando quiser</p>
            </div>
          </div>
            <!-- ── Banner Trial Candidato Ativo ── -->
            <div v-if="candidateTrialDaysLeft !== null && !userFeatures.ia_ilimitada" style="border-radius: 14px; overflow: hidden; border: 1px solid var(--color-primary); background: rgba(255,255,255,0.03); padding: 0; margin-bottom: 1.5rem;">
              <div style="background: linear-gradient(90deg, rgba(59, 130, 246, 0.15), transparent); padding: 0.75rem 1.25rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.75rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                  <img src="/icons/3d/clock.png" style="width: 28px; height: 28px; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15));" alt="Timer 3D" />
                  <div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: #fff;">Período de Teste Gratuito de Candidato</div>
                    <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 1px;">
                      Você tem <span style="color: var(--color-primary); font-weight: 700;">{{ candidateTrialDaysLeft }} dia{{ candidateTrialDaysLeft !== 1 ? 's' : '' }}</span> restante{{ candidateTrialDaysLeft !== 1 ? 's' : '' }} de {{ CANDIDATE_TRIAL_DAYS }} dias grátis. Aproveite para testar a IA de envio automatizado!
                    </div>
                  </div>
                </div>
                <button class="btn btn-primary" style="font-size: 0.8rem; padding: 0.4rem 1.25rem; background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; border: none; font-weight: 700;" @click="openCheckout('candidate_premium', 'Assinatura VagaSync Premium', 'R$ 29,90/mês')">
                  <i class="fa-solid fa-gem" style="margin-right: 4px;"></i> Assinar Premium (R$ 29,90)
                </button>
              </div>
              <div style="height: 3px; background: rgba(255,255,255,0.06); width: 100%;">
                <div :style="{ width: candidateTrialPercent + '%', height: '100%', background: candidateTrialColor, borderRadius: '3px', transition: 'width 0.5s ease' }"></div>
              </div>
            </div>

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
            <div class="glass-card stat-card" style="transition: transform 0.3s ease; cursor: default;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
              <div class="stat-icon" style="background: rgba(255, 255, 255, 0.02); transition: transform 0.3s ease; display: flex; align-items: center; justify-content: center;" onmouseover="this.style.transform='scale(1.15) rotate(5deg)'" onmouseout="this.style.transform='scale(1) rotate(0)'">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px; filter: drop-shadow(0 0 8px rgba(59, 130, 246, 0.4));">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                  <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                </svg>
              </div>
              <div>
                <div class="stat-value">{{ stats.total }}</div>
                <div class="stat-label">Vagas Encontradas</div>
              </div>
            </div>
            <div class="glass-card stat-card" style="transition: transform 0.3s ease; cursor: default;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
              <div class="stat-icon" style="background: rgba(255, 255, 255, 0.02); transition: transform 0.3s ease; display: flex; align-items: center; justify-content: center;" onmouseover="this.style.transform='scale(1.15) rotate(5deg)'" onmouseout="this.style.transform='scale(1) rotate(0)'">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px; filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.4));">
                  <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                  <polyline points="22 4 12 14.01 9 11.01"></polyline>
                </svg>
              </div>
              <div>
                <div class="stat-value">{{ stats.applied }}</div>
                <div class="stat-label">Candidaturas</div>
              </div>
            </div>
            <div class="glass-card stat-card" style="transition: transform 0.3s ease; cursor: default;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
              <div class="stat-icon" style="background: rgba(255, 255, 255, 0.02); transition: transform 0.3s ease; display: flex; align-items: center; justify-content: center;" onmouseover="this.style.transform='scale(1.15) rotate(5deg)'" onmouseout="this.style.transform='scale(1) rotate(0)'">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#a855f7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px; filter: drop-shadow(0 0 8px rgba(168, 85, 247, 0.4));">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                </svg>
              </div>
              <div>
                <div class="stat-value">{{ stats.averageMatch }}%</div>
                <div class="stat-label">Match Médio IA</div>
              </div>
            </div>
            <div class="glass-card stat-card" style="transition: transform 0.3s ease; cursor: default;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
              <div class="stat-icon" style="background: rgba(255, 255, 255, 0.02); transition: transform 0.3s ease; display: flex; align-items: center; justify-content: center;" onmouseover="this.style.transform='scale(1.15) rotate(5deg)'" onmouseout="this.style.transform='scale(1) rotate(0)'">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px; filter: drop-shadow(0 0 8px rgba(0, 242, 254, 0.4));">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
              <div>
                <div class="stat-value">{{ stats.contacted }}</div>
                <div class="stat-label">Retornos de RH</div>
              </div>
            </div>
          </div>

          <!-- ── Bloco de Anúncio AdSense (Painel Candidato) ── -->
          <div v-if="userRole === 'candidate'" style="width: 100%; margin: 0.25rem 0 0.75rem; border-radius: 14px; overflow: hidden; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.015);">
            <div style="padding: 0.35rem 0.75rem; background: rgba(59,130,246,0.05); border-bottom: 1px solid rgba(59,130,246,0.08); display: flex; align-items: center; gap: 0.4rem;">
              <i class="fa-solid fa-rectangle-ad" style="color: rgba(148,163,184,0.4); font-size: 0.65rem;"></i>
              <span style="font-size: 0.6rem; color: rgba(148,163,184,0.35); letter-spacing: 0.05em; text-transform: uppercase;">Publicidade</span>
            </div>
            <ins class="adsbygoogle"
              style="display:block; min-height: 90px;"
              data-ad-client="ca-pub-1405601693512304"
              data-ad-slot="auto"
              data-ad-format="auto"
              data-full-width-responsive="true">
            </ins>
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
                          <button
                            class="link-like-btn"
                            type="button"
                            @click="() => {
                              if (job.source === 'recruiter') {
                                if (job.status === 'found') {
                                  openApplyModal(job);
                                } else {
                                  showToast('Candidatura Concluída', 'Você já enviou seu currículo para esta vaga. O chat está liberado!', 'success');
                                }
                              } else {
                                window.open(job.link, '_blank');
                              }
                            }"
                            style="color: var(--text-primary); font-weight: 600; text-decoration: none; background: transparent; border: none; padding: 0; cursor: pointer;"
                          >
                            {{ job.title }}
                          </button>
                          <span class="job-company">
                            {{ job.company }} • {{ job.location || 'Sem local' }} • 
                            <span :class="['source-badge', job.source === 'linkedin' ? 'linkedin' : 'web']" :style="job.source === 'recruiter' ? 'background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: #34d399;' : undefined">
                              {{ job.source === 'linkedin' ? 'LinkedIn' : job.source === 'recruiter' ? 'VagaSync' : `Gemini ${job.source || 'Web'}` }}
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
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                          <!-- Se for vaga do Recrutador e ainda não candidatou -->
                          <button
                            v-if="job.source === 'recruiter' && job.status === 'found'"
                            class="btn btn-primary"
                            style="padding: 0.25rem 0.5rem; font-size: 0.72rem; display: flex; align-items: center; gap: 4px; background: linear-gradient(135deg, #10b981, #059669); color: #fff; border: none; font-weight: 700;"
                            @click="openApplyModal(job)"
                          >
                            <i class="fa-solid fa-file-arrow-up" style="font-size: 11px;"></i> Enviar Currículo
                          </button>
                          
                          <!-- Caso contrário (vaga externa ou vaga do Recrutador já candidata) -->
                          <template v-else>
                            <button 
                              v-if="job.status === 'applied' || job.status === 'contacted'"
                              class="btn btn-primary" 
                              style="padding: 0.25rem 0.5rem; font-size: 0.72rem; display: flex; align-items: center; gap: 4px; background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; border: none; font-weight: 700;"
                              @click="startChatWithRecruiter(job)"
                            >
                              <MessageSquare :size="12" /> Falar com RH
                            </button>
                            <button 
                              v-else
                              class="btn btn-secondary" 
                              style="padding: 0.25rem 0.5rem; font-size: 0.72rem; display: flex; align-items: center; gap: 4px; opacity: 0.45; cursor: not-allowed;"
                              title="Você só pode enviar mensagens após concluir a candidatura."
                              disabled
                            >
                              <Lock :size="12" /> Falar com RH
                            </button>
                          </template>
                          
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
                <div ref="terminalEndRef"></div>
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
                <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 0.5rem; flex-wrap: wrap; gap: 0.75rem;">
                  <p style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; margin: 0; flex: 1;">
                    💡 <strong>Feedback da IA:</strong> {{ employabilityFeedback }}
                  </p>
                  <div 
                    v-if="isLinkedinConnected"
                    style="background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); color: #34d399; font-size: 0.72rem; font-weight: 700; padding: 4px 10px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px;"
                  >
                    <i class="fa-brands fa-linkedin" style="font-size: 0.85rem;"></i> LinkedIn Vinculado
                  </div>
                  <button 
                    v-else
                    @click="handleLinkedinLogin"
                    style="background: linear-gradient(135deg, #0a66c2, #0077b5); border: none; color: #fff; font-size: 0.72rem; font-weight: 700; padding: 5px 12px; border-radius: 20px; display: inline-flex; align-items: center; gap: 6px; cursor: pointer; transition: transform 0.2s;"
                    onmouseover="this.style.transform='scale(1.05)'"
                    onmouseout="this.style.transform='scale(1)'"
                  >
                    <i class="fa-brands fa-linkedin" style="font-size: 0.85rem;"></i> Vincular LinkedIn
                  </button>
                </div>
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

                <div class="timeline-item" :class="{ completed: userFeatures.ia_ilimitada }">
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
                    v-if="userFeatures.ia_ilimitada"
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
                    @click="openCheckout('candidate_premium', 'Assinatura VagaSync Premium', 'R$ 29,90/mês')"
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
                  v-if="userFeatures.ia_ilimitada"
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

        <!-- ── Aba Feed da Comunidade (Candidatos, Recrutadores e Agente IA) ── -->
        <template v-if="activeTab === 'community_feed'">
          <div style="max-width: 800px; margin: 0 auto; display: flex; flex-direction: column; gap: 1.5rem;">
            
            <!-- Introdução do Feed -->
            <div class="glass-card" style="padding: 1.5rem; display: flex; align-items: center; justify-content: space-between; border: 1px solid rgba(0, 242, 254, 0.2); background: linear-gradient(135deg, rgba(10, 15, 28, 0.9), rgba(0, 242, 254, 0.05));">
              <div>
                <h2 style="margin: 0 0 0.5rem 0; font-size: 1.5rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                  <i class="fa-solid fa-users" style="color: var(--color-secondary);"></i> Comunidade VagaSync
                </h2>
                <p style="margin: 0; font-size: 0.85rem; color: var(--text-secondary); line-height: 1.5;">
                  Compartilhe dicas de carreira, insights de tecnologia e interaja com recrutadores, outros candidatos e nosso <strong>Agente de Recrutamento IA</strong> autônomo.
                </p>
              </div>
              <button class="btn btn-secondary" style="font-size: 0.75rem; padding: 0.5rem 1rem; border-color: rgba(255,255,255,0.15);" @click="fetchFeed">
                <i class="fa-solid fa-rotate" style="margin-right: 4px;"></i> Atualizar Feed
              </button>
            </div>

            <!-- Caixa de Criação de Post -->
            <div class="glass-card" style="padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; border: 1px solid rgba(255, 255, 255, 0.1);">
              <div style="display: flex; gap: 0.75rem; align-items: flex-start;">
                <!-- Avatar -->
                <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, var(--color-primary), var(--color-secondary)); display: flex; align-items: center; justify-content: center; font-size: 1rem; color: #060913; font-weight: 700; flex-shrink: 0; box-shadow: 0 0 10px rgba(0, 242, 254, 0.3);">
                  {{ userRole === 'candidate' ? 'C' : 'R' }}
                </div>
                <div style="flex: 1;">
                  <textarea 
                    class="form-input" 
                    rows="3" 
                    v-model="newPostContent" 
                    placeholder="No que você está pensando hoje? Compartilhe um insight de carreira ou tech..." 
                    style="resize: none; background: rgba(5, 7, 15, 0.6); font-size: 0.88rem; width: 100%;"
                  ></textarea>
                </div>
              </div>
              <div style="display: flex; justify-content: flex-end; align-items: center; gap: 1rem;">
                <span style="font-size: 0.75rem; color: var(--text-muted);">
                  Seu post será lido e poderá receber comentários instantâneos do Agente IA 🤖
                </span>
                <button 
                  class="btn btn-primary" 
                  style="font-size: 0.8rem; padding: 0.5rem 1.5rem; background: linear-gradient(135deg, #00f2fe, #3b82f6); color: #060913; font-weight: 700; border: none;"
                  :disabled="isSubmittingPost || !newPostContent.trim()" 
                  @click="submitPost"
                >
                  <i class="fa-solid fa-paper-plane" style="margin-right: 4px;"></i>
                  {{ isSubmittingPost ? 'Publicando...' : 'Publicar' }}
                </button>
              </div>
            </div>

            <!-- Listagem de Posts -->
            <div v-if="feedPosts.length === 0" style="text-align: center; padding: 4rem 0; color: var(--text-secondary);">
              <i class="fa-solid fa-spinner fa-spin" style="font-size: 2rem; color: var(--color-secondary); margin-bottom: 1rem;"></i>
              <p>Carregando as postagens da comunidade...</p>
            </div>

            <div v-else style="display: flex; flex-direction: column; gap: 1.25rem;">
              <div 
                v-for="post in feedPosts" 
                :key="post.id" 
                class="glass-card" 
                style="padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; border: 1px solid rgba(255,255,255,0.06); transition: transform 0.2s ease, border-color 0.2s;"
                onmouseover="this.style.borderColor='rgba(0, 242, 254, 0.15)'"
                onmouseout="this.style.borderColor='rgba(255,255,255,0.06)'"
              >
                <!-- Header do Post -->
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <!-- Avatar baseado no papel -->
                    <div 
                      style="width: 42px; height: 42px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0;"
                      :style="post.author_role === 'ai_agent' 
                        ? 'background: rgba(0, 242, 254, 0.12); border: 2px solid #00f2fe; color: #00f2fe; box-shadow: 0 0 10px rgba(0,242,254,0.2);' 
                        : post.author_role === 'recruiter'
                        ? 'background: rgba(168, 85, 247, 0.12); border: 2px solid #a855f7; color: #a855f7;'
                        : 'background: rgba(59, 130, 246, 0.12); border: 2px solid #3b82f6; color: #3b82f6;'"
                    >
                      <i v-if="post.author_role === 'ai_agent'" class="fa-solid fa-robot"></i>
                      <i v-else-if="post.author_role === 'recruiter'" class="fa-solid fa-user-tie"></i>
                      <i v-else class="fa-solid fa-user-ninja"></i>
                    </div>
                    
                    <div>
                      <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="font-weight: 700; color: #fff; font-size: 0.92rem;">{{ post.author_name }}</span>
                        <!-- Badges -->
                        <span 
                          v-if="post.author_role === 'ai_agent'" 
                          style="font-size: 0.58rem; font-weight: 800; padding: 2px 6px; border-radius: 4px; background: rgba(0, 242, 254, 0.15); border: 1px solid rgba(0, 242, 254, 0.3); color: #00f2fe; text-transform: uppercase; letter-spacing: 0.05em;"
                        >
                          IA AGENTE
                        </span>
                        <span 
                          v-else-if="post.author_role === 'recruiter'" 
                          style="font-size: 0.58rem; font-weight: 800; padding: 2px 6px; border-radius: 4px; background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.3); color: #c084fc; text-transform: uppercase; letter-spacing: 0.05em;"
                        >
                          RECRUTADOR
                        </span>
                        <span 
                          v-else 
                          style="font-size: 0.58rem; font-weight: 800; padding: 2px 6px; border-radius: 4px; background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.3); color: #93c5fd; text-transform: uppercase; letter-spacing: 0.05em;"
                        >
                          CANDIDATO
                        </span>
                      </div>
                      <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 2px;">
                        {{ new Date(post.created_at).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Conteúdo do Post -->
                <div style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6; white-space: pre-wrap; word-break: break-word;">
                  {{ post.content }}
                </div>

                <!-- Footer do Post: Reações e Botão Comentar -->
                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.06); border-bottom: 1px solid rgba(255,255,255,0.06); padding: 0.5rem 0; margin-top: 0.5rem;">
                  <!-- Reações -->
                  <div style="display: flex; gap: 0.25rem;">
                    <!-- Like -->
                    <button 
                      class="nav-link-btn" 
                      style="font-size: 0.78rem; padding: 4px 10px; border-radius: 6px; border: 1px solid transparent; display: flex; align-items: center; gap: 4px;"
                      :style="hasUserReacted(post, 'like') ? 'background: rgba(0, 242, 254, 0.1); border-color: rgba(0, 242, 254, 0.2); color: #00f2fe;' : 'background: transparent; color: var(--text-secondary);'"
                      @click="toggleReaction(post.id, 'like')"
                    >
                      👍 <span style="font-weight: 600;">{{ post.likes }}</span>
                    </button>
                    <!-- Clap -->
                    <button 
                      class="nav-link-btn" 
                      style="font-size: 0.78rem; padding: 4px 10px; border-radius: 6px; border: 1px solid transparent; display: flex; align-items: center; gap: 4px;"
                      :style="hasUserReacted(post, 'clap') ? 'background: rgba(168, 85, 247, 0.1); border-color: rgba(168, 85, 247, 0.2); color: #c084fc;' : 'background: transparent; color: var(--text-secondary);'"
                      @click="toggleReaction(post.id, 'clap')"
                    >
                      👏 <span style="font-weight: 600;">{{ post.claps }}</span>
                    </button>
                    <!-- Love -->
                    <button 
                      class="nav-link-btn" 
                      style="font-size: 0.78rem; padding: 4px 10px; border-radius: 6px; border: 1px solid transparent; display: flex; align-items: center; gap: 4px;"
                      :style="hasUserReacted(post, 'love') ? 'background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.2); color: #f87171;' : 'background: transparent; color: var(--text-secondary);'"
                      @click="toggleReaction(post.id, 'love')"
                    >
                      ❤️ <span style="font-weight: 600;">{{ post.loves }}</span>
                    </button>
                    <!-- Idea -->
                    <button 
                      class="nav-link-btn" 
                      style="font-size: 0.78rem; padding: 4px 10px; border-radius: 6px; border: 1px solid transparent; display: flex; align-items: center; gap: 4px;"
                      :style="hasUserReacted(post, 'idea') ? 'background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.2); color: #fbbf24;' : 'background: transparent; color: var(--text-secondary);'"
                      @click="toggleReaction(post.id, 'idea')"
                    >
                      💡 <span style="font-weight: 600;">{{ post.ideas }}</span>
                    </button>
                  </div>

                  <!-- Botão Comentários -->
                  <button 
                    class="nav-link-btn" 
                    style="font-size: 0.78rem; display: flex; align-items: center; gap: 6px; color: var(--text-secondary); padding: 4px 10px;"
                    @click="activeCommentsPostId = activeCommentsPostId === post.id ? null : post.id"
                  >
                    <i class="fa-regular fa-comment" :style="activeCommentsPostId === post.id ? 'color: #00f2fe;' : ''"></i>
                    <span>{{ post.comments?.length || 0 }} Comentários</span>
                  </button>
                </div>

                <!-- Área de Comentários (Expansível) -->
                <div v-if="activeCommentsPostId === post.id" style="display: flex; flex-direction: column; gap: 1rem; padding: 0.25rem 0.5rem 0.5rem;">
                  <!-- Campo de escrita de comentário -->
                  <div style="display: flex; gap: 0.6rem; align-items: center; margin-bottom: 0.5rem;">
                    <input 
                      type="text" 
                      class="form-input" 
                      placeholder="Adicione um comentário profissional..." 
                      v-model="commentInputs[post.id]"
                      style="font-size: 0.8rem; background: rgba(5, 7, 15, 0.6); flex: 1; height: 36px;"
                      @keyup.enter="submitComment(post.id)"
                    />
                    <button 
                      class="btn btn-secondary" 
                      style="font-size: 0.75rem; height: 36px; padding: 0 1rem; border-color: rgba(255,255,255,0.15);"
                      @click="submitComment(post.id)"
                    >
                      Enviar
                    </button>
                  </div>

                  <!-- Lista de Comentários -->
                  <div v-if="!post.comments || post.comments.length === 0" style="text-align: center; padding: 1rem 0; font-size: 0.78rem; color: var(--text-muted);">
                    Nenhum comentário publicado ainda. Seja o primeiro!
                  </div>

                  <div v-else style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <div 
                      v-for="comment in post.comments" 
                      :key="comment.id" 
                      style="background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.03); border-radius: 8px; padding: 0.75rem;"
                    >
                      <!-- Header Comentário -->
                      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                          <span style="font-weight: 700; color: #fff; font-size: 0.8rem;">{{ comment.author_name }}</span>
                          <!-- Badges -->
                          <span 
                            v-if="comment.author_role === 'ai_agent'" 
                            style="font-size: 0.5rem; font-weight: 800; padding: 1px 4px; border-radius: 3px; background: rgba(0, 242, 254, 0.15); border: 1px solid rgba(0, 242, 254, 0.3); color: #00f2fe;"
                          >
                            IA AGENTE
                          </span>
                          <span 
                            v-else-if="comment.author_role === 'recruiter'" 
                            style="font-size: 0.5rem; font-weight: 800; padding: 1px 4px; border-radius: 3px; background: rgba(168, 85, 247, 0.12); border: 1px solid rgba(168, 85, 247, 0.2); color: #c084fc;"
                          >
                            RECRUTADOR
                          </span>
                        </div>
                        <span style="font-size: 0.68rem; color: var(--text-muted);">
                          {{ new Date(comment.created_at).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) }}
                        </span>
                      </div>
                      <!-- Conteúdo Comentário -->
                      <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; white-space: pre-wrap; word-break: break-word;">
                        {{ comment.content }}
                      </div>
                    </div>
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

            <!-- ── PAYWALL: Trial Expirado ── -->
            <div v-if="recruiterTrialExpired" style="position: relative; border-radius: 20px; overflow: hidden; background: linear-gradient(135deg, #0a0f1c 0%, #0d1426 100%); border: 2px solid rgba(239,68,68,0.4); padding: 3rem 2rem; text-align: center;">
              <div style="position: absolute; inset: 0; background: radial-gradient(ellipse at center, rgba(239,68,68,0.08) 0%, transparent 70%); pointer-events: none;"></div>
              <img src="/icons/3d/security.png" style="width: 64px; height: 64px; object-fit: contain; margin-bottom: 1rem; filter: drop-shadow(0 0 20px rgba(239,68,68,0.4));" alt="Bloqueado" />
              <h2 style="color: #fff; font-size: 1.8rem; margin: 0 0 0.5rem;">Periodo de Teste Encerrado</h2>
              <p style="color: var(--text-secondary); font-size: 1rem; max-width: 480px; margin: 0 auto 2rem; line-height: 1.6;">
                Seu trial gratuito de <strong style="color: #fff;">30 dias</strong> chegou ao fim. Assine o plano <strong style="color: #00f2fe;">VagaSync Pro Recrutador</strong> para continuar acessando o painel, Kanban, IA de triagem e automacoes de WhatsApp.
              </p>
              <div style="display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
                <div style="background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.25); border-radius: 14px; padding: 1.5rem 1.25rem; min-width: 200px; text-align: left; transition: transform 0.3s ease;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Plano Starter</div>
                    <img src="/icons/3d/store.png" style="width: 32px; height: 32px; object-fit: contain; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.15));" alt="Starter Store 3D" />
                  </div>
                  <div style="font-size: 2rem; font-weight: 800; color: #fff;">R$ 49<span style="font-size: 1rem; font-weight: 400; color: var(--text-secondary);">/mes</span></div>
                  <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem; line-height: 1.5;">Kanban completo<br>3 vagas ativas<br>WhatsApp manual</div>
                  <button @click="openCheckout('recruiter_starter', 'Plano Starter Recrutador', 'R$ 49,90/mes')" class="btn btn-secondary" style="width: 100%; margin-top: 1rem; font-size: 0.85rem;">Assinar Starter</button>
                </div>
                <div style="background: linear-gradient(135deg, rgba(0,242,254,0.08), rgba(59,130,246,0.12)); border: 1.5px solid rgba(0,242,254,0.35); border-radius: 14px; padding: 1.5rem 1.25rem; min-width: 200px; text-align: left; position: relative; transition: transform 0.3s ease;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
                  <div style="position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: linear-gradient(90deg, #00f2fe, #3b82f6); color: #fff; font-size: 0.65rem; font-weight: 700; padding: 3px 12px; border-radius: 20px; letter-spacing: 0.05em; box-shadow: 0 4px 10px rgba(0, 242, 254, 0.25);">MAIS POPULAR</div>
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                    <div style="font-size: 0.75rem; color: #00f2fe; text-transform: uppercase; letter-spacing: 0.05em;">Plano Pro</div>
                    <img src="/icons/3d/value.png" style="width: 32px; height: 32px; object-fit: contain; filter: drop-shadow(0 4px 6px rgba(0,242,254,0.15));" alt="Pro Diamond 3D" />
                  </div>
                  <div style="font-size: 2rem; font-weight: 800; color: #fff;">R$ 99<span style="font-size: 1rem; font-weight: 400; color: var(--text-secondary);">/mes</span></div>
                  <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 0.5rem; line-height: 1.5;">Vagas ilimitadas<br>IA de triagem<br>WhatsApp automatico<br>Relatorios premium</div>
                  <button @click="openCheckout('recruiter_pro', 'Plano Pro Recrutador', 'R$ 99,90/mes')" class="btn btn-primary" style="width: 100%; margin-top: 1rem; font-size: 0.85rem; background: linear-gradient(90deg, #00f2fe, #3b82f6);">Assinar Pro</button>
                </div>
              </div>
              <p style="margin-top: 2rem; font-size: 0.75rem; color: var(--text-muted);">Pague via Pix ou Cartao - Cancele quando quiser - Suporte em ate 24h</p>
            </div>

            <!-- ── Banner Trial Ativo ── -->
            <div v-else-if="recruiterTrialDaysLeft !== null && !userFeatures.recruiter_pro_active" :style="{ borderRadius: '14px', overflow: 'hidden', border: '1px solid ' + recruiterTrialColor, background: 'rgba(255,255,255,0.03)', padding: '0' }">
              <div :style="{ background: 'linear-gradient(90deg, ' + recruiterTrialColor + '15, transparent)', padding: '0.75rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem' }">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                  <img src="/icons/3d/clock.png" style="width: 28px; height: 28px; object-fit: contain; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15));" alt="Timer 3D" />
                  <div>
                    <div style="font-weight: 700; font-size: 0.95rem; color: #fff;">Periodo de Teste Gratuito</div>
                    <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 1px;">
                      <span :style="{ color: recruiterTrialColor, fontWeight: 700 }">{{ recruiterTrialDaysLeft }} dia{{ recruiterTrialDaysLeft !== 1 ? 's' : '' }}</span>
                      restante{{ recruiterTrialDaysLeft !== 1 ? 's' : '' }} de {{ TRIAL_DAYS }} dias gratis
                    </div>
                  </div>
                </div>
                <div style="display: flex; align-items: center; gap: 1rem; flex: 1; justify-content: flex-end;">
                  <!-- Barra de progresso -->
                  <div style="flex: 1; max-width: 180px; height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; overflow: hidden;">
                    <div :style="{ width: recruiterTrialPercent + '%', height: '100%', background: recruiterTrialColor, borderRadius: '3px', transition: 'width 0.5s ease' }"></div>
                  </div>
                  <button @click="openCheckout('recruiter_pro', 'Plano Pro Recrutador', 'R$ 99,90/mes')" class="btn btn-primary" style="font-size: 0.78rem; padding: 0.4rem 1rem; white-space: nowrap; background: linear-gradient(90deg, #00f2fe, #3b82f6);">
                    Assinar Agora
                  </button>
                </div>
              </div>
            </div>

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
              <div class="glass-card stat-card" style="flex-direction: column; align-items: flex-start; gap: 0.5rem; justify-content: center; min-height: 100px; transition: transform 0.3s ease;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                  <span class="stat-label" style="font-weight: 700; color: #fff;">Gestão de Vagas</span>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px; filter: drop-shadow(0 0 6px rgba(59, 130, 246, 0.3));">
                    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                  </svg>
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
              <div class="glass-card stat-card" style="flex-direction: column; align-items: flex-start; gap: 0.5rem; justify-content: center; min-height: 100px; transition: transform 0.3s ease;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                  <span class="stat-label" style="font-weight: 700; color: #fff;">SLA Médio</span>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px; filter: drop-shadow(0 0 6px rgba(245, 158, 11, 0.3));">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
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
              <div class="glass-card stat-card" style="flex-direction: column; align-items: flex-start; gap: 0.5rem; justify-content: center; min-height: 100px; transition: transform 0.3s ease;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                  <span class="stat-label" style="font-weight: 700; color: #fff;">Satisfação (NPS)</span>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#ec4899" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px; filter: drop-shadow(0 0 6px rgba(236, 72, 153, 0.3));">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                  </svg>
                </div>
                <div style="display: flex; align-items: baseline; gap: 6px;">
                  <span class="stat-value" style="font-size: 1.8rem; color: #ec4899; font-weight: 800;">{{ dashboardMetrics.nps }}%</span>
                </div>
                <div style="font-size: 0.68rem; color: var(--text-secondary);">
                  Feedback da Experiência
                </div>
              </div>

              <!-- Velocidade de Resposta -->
              <div class="glass-card stat-card" style="flex-direction: column; align-items: flex-start; gap: 0.5rem; justify-content: center; min-height: 100px; transition: transform 0.3s ease;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
                <div style="display: flex; justify-content: space-between; width: 100%; align-items: center;">
                  <span class="stat-label" style="font-weight: 700; color: #fff;">Tempo de Resposta</span>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#00f2fe" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px; filter: drop-shadow(0 0 6px rgba(0, 242, 254, 0.3));">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
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

            <!-- ── Radar de Insights e Notícias IA para RH ── -->
            <div class="glass-card" style="padding: 1.5rem; border: 1px solid rgba(0, 242, 254, 0.2); background: linear-gradient(135deg, rgba(10, 15, 28, 0.9), rgba(0, 242, 254, 0.03)); display: flex; flex-direction: column; gap: 1.25rem;">
              <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 0.75rem;">
                <h3 style="margin: 0; font-size: 1.15rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                  <i class="fa-solid fa-brain" style="color: #00f2fe;"></i> Radar de Insights & Notícias IA para RH
                </h3>
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                  <span style="font-size: 0.72rem; color: var(--text-muted);">
                    Personalizado com base nas suas vagas ativas
                  </span>
                  <button 
                    class="btn btn-secondary" 
                    style="font-size: 0.72rem; padding: 0.35rem 0.75rem; display: flex; align-items: center; gap: 4px; border-color: rgba(255,255,255,0.15);"
                    :disabled="isLoadingRecruiterInsights"
                    @click="fetchRecruiterInsights"
                  >
                    <i class="fa-solid fa-rotate" :class="{'fa-spin': isLoadingRecruiterInsights}"></i>
                    {{ isLoadingRecruiterInsights ? 'Atualizando...' : 'Regerar IA' }}
                  </button>
                </div>
              </div>

              <!-- Lista de Insights -->
              <div v-if="recruiterInsights.length === 0" style="text-align: center; padding: 2rem 0; color: var(--text-secondary);">
                <i class="fa-solid fa-spinner fa-spin" style="font-size: 1.5rem; color: var(--color-secondary); margin-bottom: 0.75rem;"></i>
                <p style="font-size: 0.8rem; margin: 0;">Analisando suas vagas e gerando notícias de mercado por IA...</p>
              </div>

              <div v-else style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                <div 
                  v-for="insight in recruiterInsights" 
                  :key="insight.id" 
                  class="glass-card" 
                  style="background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); padding: 1.25rem; border-radius: 12px; display: flex; flex-direction: column; gap: 0.75rem; justify-content: space-between; transition: transform 0.2s ease, border-color 0.2s;"
                  onmouseover="this.style.transform='translateY(-3px)'; this.style.borderColor='rgba(0, 242, 254, 0.2)';"
                  onmouseout="this.style.transform='translateY(0)'; this.style.borderColor='rgba(255,255,255,0.04)';"
                >
                  <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                      <span style="font-size: 0.58rem; font-weight: 800; padding: 2px 6px; border-radius: 4px; background: rgba(0, 242, 254, 0.12); color: #00f2fe; text-transform: uppercase;">
                        {{ insight.category }}
                      </span>
                      <span style="font-size: 0.65rem; color: var(--text-muted);">{{ insight.source }}</span>
                    </div>
                    <h4 style="margin: 0; font-size: 0.88rem; font-weight: 700; color: #fff; line-height: 1.4;">
                      {{ insight.title }}
                    </h4>
                    <p style="margin: 0; font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
                      {{ insight.content }}
                    </p>
                  </div>
                  <div style="border-top: 1px solid rgba(255,255,255,0.04); padding-top: 0.5rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.7rem; color: var(--text-muted);">
                    <span>Fonte: Banco Central / BCB & VagaSync IA</span>
                    <span style="color: #00f2fe; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 2px;">
                      Aplicar no Painel <i class="fa-solid fa-arrow-trend-up"></i>
                    </span>
                  </div>
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
                          v-if="userFeatures.videoentrevistas"
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
        </template>

        <!-- ── Aba Mapa de Vagas ── -->
        <template v-if="activeTab === 'map'">
          <div class="glass-card" style="padding: 1.5rem;">
            <JobMap :jobs="jobs" :mapsApiKey="config.google_maps_api_key" />
          </div>
        </template>

        <!-- ── Aba Contato com RH ── -->
        <template v-if="activeTab === 'contato'">
          <ContatoRH 
            :jobs="jobs" 
            :showToast="showToast" 
            :config="config" 
            @apply-recruiter="openApplyModal"
            @start-chat="startChatWithRecruiter"
          />
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
          <div style="display: grid; grid-template-columns: 260px 1fr; gap: 2rem; align-items: start; max-width: 1100px; margin: 0 auto;">
            
            <!-- Sidebar de Configurações -->
            <div class="glass-card" style="padding: 1rem; display: flex; flex-direction: column; gap: 0.35rem; position: sticky; top: 2rem;">
              <div style="padding: 0.5rem 0.75rem; font-size: 0.75rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">
                Configurações
              </div>
              
              <button 
                type="button" 
                style="display: flex; align-items: center; gap: 10px; padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid transparent; background: transparent; color: var(--text-secondary); font-size: 0.85rem; font-weight: 500; text-align: left; cursor: pointer; transition: all 0.2s ease;"
                :style="activeSettingsTab === 'billing' ? {
                  background: 'linear-gradient(90deg, rgba(0, 242, 254, 0.08), rgba(59, 130, 246, 0.08))',
                  borderColor: 'rgba(0, 242, 254, 0.2)',
                  color: '#00f2fe',
                  fontWeight: '700'
                } : {}"
                @click="activeSettingsTab = 'billing'"
              >
                <i class="fa-solid fa-credit-card"></i> Assinatura & Plano
              </button>

              <button 
                type="button" 
                style="display: flex; align-items: center; gap: 10px; padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid transparent; background: transparent; color: var(--text-secondary); font-size: 0.85rem; font-weight: 500; text-align: left; cursor: pointer; transition: all 0.2s ease;"
                :style="activeSettingsTab === 'profile' ? {
                  background: 'linear-gradient(90deg, rgba(0, 242, 254, 0.08), rgba(59, 130, 246, 0.08))',
                  borderColor: 'rgba(0, 242, 254, 0.2)',
                  color: '#00f2fe',
                  fontWeight: '700'
                } : {}"
                @click="activeSettingsTab = 'profile'"
              >
                <i class="fa-solid fa-user"></i> Meu Perfil & Foto
              </button>

              <button 
                type="button" 
                style="display: flex; align-items: center; gap: 10px; padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid transparent; background: transparent; color: var(--text-secondary); font-size: 0.85rem; font-weight: 500; text-align: left; cursor: pointer; transition: all 0.2s ease;"
                :style="activeSettingsTab === 'security' ? {
                  background: 'linear-gradient(90deg, rgba(0, 242, 254, 0.08), rgba(59, 130, 246, 0.08))',
                  borderColor: 'rgba(0, 242, 254, 0.2)',
                  color: '#00f2fe',
                  fontWeight: '700'
                } : {}"
                @click="activeSettingsTab = 'security'"
              >
                <i class="fa-solid fa-lock"></i> Acesso & Segurança
              </button>

              <button 
                type="button" 
                style="display: flex; align-items: center; gap: 10px; padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid transparent; background: transparent; color: var(--text-secondary); font-size: 0.85rem; font-weight: 500; text-align: left; cursor: pointer; transition: all 0.2s ease;"
                :style="activeSettingsTab === 'privacy' ? {
                  background: 'linear-gradient(90deg, rgba(0, 242, 254, 0.08), rgba(59, 130, 246, 0.08))',
                  borderColor: 'rgba(0, 242, 254, 0.2)',
                  color: '#00f2fe',
                  fontWeight: '700'
                } : {}"
                @click="activeSettingsTab = 'privacy'"
              >
                <i class="fa-solid fa-shield-halved"></i> Privacidade & LGPD
              </button>

              <button 
                type="button" 
                style="display: flex; align-items: center; gap: 10px; padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid transparent; background: transparent; color: var(--text-secondary); font-size: 0.85rem; font-weight: 500; text-align: left; cursor: pointer; transition: all 0.2s ease;"
                :style="activeSettingsTab === 'notifications' ? {
                  background: 'linear-gradient(90deg, rgba(0, 242, 254, 0.08), rgba(59, 130, 246, 0.08))',
                  borderColor: 'rgba(0, 242, 254, 0.2)',
                  color: '#00f2fe',
                  fontWeight: '700'
                } : {}"
                @click="activeSettingsTab = 'notifications'"
              >
                <i class="fa-solid fa-bell"></i> Notificações Multi-Canal
              </button>

              <button 
                type="button" 
                style="display: flex; align-items: center; gap: 10px; padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid transparent; background: transparent; color: var(--text-secondary); font-size: 0.85rem; font-weight: 500; text-align: left; cursor: pointer; transition: all 0.2s ease;"
                :style="activeSettingsTab === 'automation' ? {
                  background: 'linear-gradient(90deg, rgba(0, 242, 254, 0.08), rgba(59, 130, 246, 0.08))',
                  borderColor: 'rgba(0, 242, 254, 0.2)',
                  color: '#00f2fe',
                  fontWeight: '700'
                } : {}"
                @click="activeSettingsTab = 'automation'"
              >
                <i class="fa-solid fa-sliders"></i> Automação & Busca
              </button>
            </div>

            <!-- Conteúdo da Configuração -->
            <div style="display: flex; flex-direction: column; gap: 1.5rem;">
              
              <!-- 1. TABA: ASSINATURA E PLANO -->
              <div v-if="activeSettingsTab === 'billing'" style="display: flex; flex-direction: column; gap: 1.5rem;">
                <div class="glass-card" style="position: relative; overflow: hidden; border-left: 4px solid var(--color-secondary);">
                  <div style="position: absolute; top: -50px; right: -50px; width: 150px; height: 150px; background: radial-gradient(circle, rgba(0, 242, 254, 0.15) 0%, transparent 70%); pointer-events: none;"></div>
                  
                  <h3 style="margin: 0 0 1rem 0; font-size: 1.2rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-credit-card" style="color: var(--color-secondary);"></i> Plano & Assinatura Ativa
                  </h3>
                  
                  <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 1.5rem; margin-top: 1rem;">
                    <div>
                      <div style="font-size: 1.4rem; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px;">
                        Plano IA Avançada
                        <span style="font-size: 0.72rem; font-weight: 700; padding: 0.25rem 0.6rem; border-radius: 20px; background: rgba(0,242,254,0.12); color: #00f2fe; border: 1px solid rgba(0,242,254,0.2);">ATIVO</span>
                      </div>
                      <p style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.5rem; line-height: 1.5;">
                        Acesso ilimitado ao copiloto de busca de vagas por IA, candidaturas automáticas multi-canal e geocodificação no Radar de Vagas.
                      </p>
                      <div style="display: flex; flex-direction: column; gap: 0.35rem; margin-top: 1rem; font-size: 0.82rem; color: var(--text-muted);">
                        <div><strong>Valor:</strong> R$ 9,90 / mês</div>
                        <div><strong>Próxima renovação:</strong> 28 de Julho de 2026</div>
                        <div><strong>Método de pagamento:</strong> Cartão de Crédito</div>
                      </div>
                    </div>
                    
                    <!-- Cartão Netflix Style -->
                    <div style="background: linear-gradient(135deg, #0e1628 0%, #060913 100%); border: 1px solid var(--border-color); border-radius: 12px; padding: 1.25rem; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 4px 20px rgba(0,0,0,0.3); height: 160px;">
                      <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <span style="font-weight: 700; color: #3b82f6; font-size: 0.8rem; letter-spacing: 0.05em; text-transform: uppercase;">{{ cardBrand }}</span>
                        <i class="fa-solid fa-signal" style="color: rgba(255,255,255,0.2); font-size: 0.9rem;"></i>
                      </div>
                      <div style="font-family: monospace; font-size: 1.1rem; color: #fff; letter-spacing: 0.15em; margin: 1rem 0;">
                        •••• •••• •••• {{ cardLast4 }}
                      </div>
                      <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                          <div style="font-size: 0.6rem; text-transform: uppercase; color: var(--text-muted);">Validade</div>
                          <div style="font-size: 0.78rem; font-weight: 600; color: #fff;">{{ cardExpiry }}</div>
                        </div>
                        <button 
                          type="button" 
                          class="btn btn-secondary" 
                          style="font-size: 0.72rem; padding: 0.35rem 0.7rem; border-color: rgba(255,255,255,0.08); background: rgba(255,255,255,0.02);"
                          @click="showChangeCardModal = true"
                        >
                          Alterar Cartão
                        </button>
                      </div>
                    </div>
                  </div>
                  
                  <div style="border-top: 1px solid var(--border-color); margin-top: 1.5rem; padding-top: 1rem; display: flex; justify-content: flex-end;">
                    <button 
                      type="button" 
                      class="btn btn-secondary" 
                      style="font-size: 0.8rem; color: var(--color-error); border-color: rgba(239, 68, 68, 0.15);"
                      @click="showToast('Cancelamento', 'Para cancelar seu plano de R$ 9,90/mês, por favor entre em contato com o suporte financeiro.', 'info')"
                    >
                      Cancelar Assinatura
                    </button>
                  </div>
                </div>
              </div>

              <!-- 2. TABA: MEUS DADOS E FOTO -->
              <div v-if="activeSettingsTab === 'profile'" style="display: flex; flex-direction: column; gap: 1.5rem;">
                <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
                  <h3 style="margin: 0; font-size: 1.15rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-user-gear" style="color: var(--color-secondary);"></i> Meu Perfil VagaSync
                  </h3>

                  <!-- Upload de Foto de Perfil -->
                  <div style="display: flex; align-items: center; gap: 1.5rem; background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); padding: 1rem; border-radius: 12px;">
                    <!-- Preview -->
                    <div style="position: relative;">
                      <div 
                        style="width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, var(--color-primary), var(--color-secondary)); display: flex; align-items: center; justify-content: center; overflow: hidden; border: 3px solid #00f2fe; box-shadow: 0 0 15px rgba(0,242,254,0.3); font-weight: 700; color: #060913; font-size: 2rem;"
                      >
                        <img v-if="profileData.photo" :src="profileData.photo" style="width: 100%; height: 100%; object-fit: cover;" />
                        <span v-else>{{ profileData.name ? profileData.name.charAt(0).toUpperCase() : 'U' }}</span>
                      </div>
                    </div>
                    <!-- Ações da Foto -->
                    <div style="display: flex; flex-direction: column; gap: 0.5rem; flex: 1;">
                      <span style="font-size: 0.85rem; font-weight: 600; color: #fff;">Foto de Perfil</span>
                      <span style="font-size: 0.72rem; color: var(--text-muted);">Suporta JPG, PNG. Tamanho máximo 2MB.</span>
                      <div style="display: flex; gap: 0.5rem; margin-top: 0.25rem;">
                        <input 
                          type="file" 
                          id="profile_photo_upload_input" 
                          style="display: none;" 
                          accept="image/*"
                          @change="handleProfilePhotoUpload"
                        />
                        <button 
                          type="button" 
                          class="btn btn-secondary" 
                          style="font-size: 0.75rem; padding: 0.35rem 0.75rem;" 
                          @click="document.getElementById('profile_photo_upload_input').click()"
                        >
                          Carregar Foto
                        </button>
                        <button 
                          v-if="profileData.photo"
                          type="button" 
                          class="btn btn-secondary" 
                          style="font-size: 0.75rem; padding: 0.35rem 0.75rem; color: var(--color-error); border-color: rgba(239,68,68,0.2);" 
                          @click="profileData.photo = ''"
                        >
                          Remover
                        </button>
                      </div>
                    </div>
                  </div>

                  <!-- Formulário de dados -->
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div class="form-group" style="margin: 0;">
                      <label>Nome Completo</label>
                      <input type="text" class="form-input" v-model="profileData.name" placeholder="Digite seu nome..." />
                    </div>
                    <div class="form-group" style="margin: 0;">
                      <label>E-mail de Contato</label>
                      <input type="email" class="form-input" v-model="profileData.email" placeholder="seu@email.com" />
                    </div>
                    <div class="form-group" style="margin: 0;">
                      <label>Telefone de Contato</label>
                      <input type="text" class="form-input" v-model="profileData.phone" placeholder="+55 (11) 99999-9999" />
                    </div>
                    <div class="form-group" style="margin: 0;" v-if="userRole === 'recruiter'">
                      <label>Nome da Empresa / Organização</label>
                      <input type="text" class="form-input" v-model="profileData.company" placeholder="Sua Empresa..." />
                    </div>
                  </div>

                  <div style="display: flex; justify-content: flex-end; margin-top: 0.5rem;">
                    <button type="button" class="btn btn-primary" style="font-size: 0.82rem;" @click="saveProfileData">
                      Salvar Dados Cadastrais
                    </button>
                  </div>
                </div>

                <!-- Tema & Preferências de Sistema -->
                <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
                  <h3 style="margin: 0; font-size: 1.1rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-sliders" style="color: var(--color-secondary);"></i> Preferências & Sistema
                  </h3>

                  <!-- Dark Mode / Tema -->
                  <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.8rem; background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); border-radius: 10px;">
                    <div>
                      <span style="font-size: 0.88rem; font-weight: 700; color: #fff;">Tema Visual (Escuro vs Claro)</span>
                      <p style="font-size: 0.72rem; color: var(--text-muted); margin: 2px 0 0 0;">Alterna entre o Dark Mode original e o Light Mode de leitura.</p>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                      <span style="font-size: 0.75rem; color: var(--text-secondary);">{{ darkMode ? 'Dark Mode 🌙' : 'Light Mode ☀️' }}</span>
                      <input 
                        type="checkbox" 
                        v-model="darkMode" 
                        @change="toggleDarkMode" 
                        style="width: 18px; height: 18px; cursor: pointer;"
                      />
                    </div>
                  </div>

                  <!-- Configurações Adicionais de Sistema -->
                  <div style="display: flex; flex-direction: column; gap: 0.8rem;">
                    <label style="display: flex; align-items: center; gap: 0.6rem; cursor: pointer; padding: 0.6rem; border-radius: 8px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03);">
                      <input
                        type="checkbox"
                        v-model="systemSettings.soundEnabled"
                        style="width: 16px; height: 16px; cursor: pointer;"
                      />
                      <div>
                        <div style="font-size: 0.82rem; font-weight: 600; color: #fff;">🔊 Efeitos Sonoros do Copiloto</div>
                        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 1px;">Tocar avisos sonoros nas varreduras bem-sucedidas do Agente</div>
                      </div>
                    </label>

                    <label style="display: flex; align-items: center; gap: 0.6rem; cursor: pointer; padding: 0.6rem; border-radius: 8px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03);">
                      <input
                        type="checkbox"
                        v-model="systemSettings.autoRefresh"
                        style="width: 16px; height: 16px; cursor: pointer;"
                      />
                      <div>
                        <div style="font-size: 0.82rem; font-weight: 600; color: #fff;">🔄 Auto-Atualização do Painel</div>
                        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 1px;">Recarregar a lista de vagas automaticamente a cada 5 segundos</div>
                      </div>
                    </label>
                  </div>

                  <div style="display: flex; justify-content: flex-end;">
                    <button type="button" class="btn btn-primary" style="font-size: 0.82rem;" @click="saveSystemSettings">
                      Salvar Preferências
                    </button>
                  </div>
                </div>
              </div>

              <!-- 3. TABA: ACESSO E SEGURANÇA -->
              <div v-if="activeSettingsTab === 'security'" style="display: flex; flex-direction: column; gap: 1.5rem;">
                <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
                  <h3 style="margin: 0; font-size: 1.15rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-lock" style="color: var(--color-secondary);"></i> Alterar Senha de Acesso
                  </h3>
                  
                  <div style="display: flex; flex-direction: column; gap: 1rem;">
                    <div class="form-group" style="margin: 0;">
                      <label>Senha Atual</label>
                      <input type="password" class="form-input" v-model="securityData.currentPassword" placeholder="Digite sua senha atual..." />
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                      <div class="form-group" style="margin: 0;">
                        <label>Nova Senha</label>
                        <input type="password" class="form-input" v-model="securityData.newPassword" placeholder="Mínimo 6 caracteres..." />
                      </div>
                      <div class="form-group" style="margin: 0;">
                        <label>Confirmar Nova Senha</label>
                        <input type="password" class="form-input" v-model="securityData.confirmPassword" placeholder="Confirme a nova senha..." />
                      </div>
                    </div>
                  </div>
                  
                  <!-- Autenticação de Dois Fatores (2FA) -->
                  <div style="border-top: 1px solid var(--border-color); padding-top: 1.25rem; margin-top: 0.5rem; display: flex; align-items: center; justify-content: space-between;">
                    <div>
                      <span style="font-weight: 700; font-size: 0.88rem; color: #fff;">Autenticação em Duas Etapas (2FA)</span>
                      <p style="font-size: 0.72rem; color: var(--text-muted); margin: 2px 0 0 0;">Exige um código de segurança enviado ao e-mail/WhatsApp além da senha no login.</p>
                    </div>
                    <input 
                      type="checkbox" 
                      v-model="securityData.twoFactorEnabled" 
                      style="width: 18px; height: 18px; cursor: pointer;"
                    />
                  </div>

                  <div style="display: flex; justify-content: flex-end;">
                    <button type="button" class="btn btn-primary" style="font-size: 0.82rem;" @click="updateSecuritySettings">
                      Atualizar Segurança
                    </button>
                  </div>
                </div>

                <!-- Histórico de Login -->
                <div class="glass-card">
                  <h3 style="margin: 0 0 1rem 0; font-size: 1.1rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-clock-rotate-left" style="color: var(--color-secondary);"></i> Histórico de Dispositivos Conectados
                  </h3>
                  
                  <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                    <div 
                      v-for="(session, i) in loginHistory" :key="i"
                      style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem; background: rgba(255,255,255,0.01); border: 1px solid var(--border-color); border-radius: 8px; font-size: 0.8rem;"
                    >
                      <div>
                        <div style="color: #fff; font-weight: 600;">{{ session.device }}</div>
                        <div style="color: var(--text-muted); font-size: 0.72rem; margin-top: 2px;">{{ session.location }} • IP: {{ session.ip }}</div>
                      </div>
                      <span style="color: var(--color-success); font-weight: 600; font-size: 0.72rem;">{{ session.date }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 4. TABA: PRIVACIDADE E LGPD -->
              <div v-if="activeSettingsTab === 'privacy'" style="display: flex; flex-direction: column; gap: 1.5rem;">
                <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
                  <h3 style="margin: 0; font-size: 1.15rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-shield-halved" style="color: var(--color-secondary);"></i> Preferências de Privacidade
                  </h3>

                  <!-- Visibilidade Recrutadores -->
                  <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.8rem; background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); border-radius: 10px;">
                    <div>
                      <span style="font-size: 0.85rem; font-weight: 700; color: #fff;">Visibilidade de Perfil</span>
                      <p style="font-size: 0.72rem; color: var(--text-muted); margin: 2px 0 0 0;">Permitir que recrutadores localizem seu currículo e perfil na busca global.</p>
                    </div>
                    <input 
                      type="checkbox" 
                      v-model="privacyData.profileVisibleToRecruiters" 
                      style="width: 18px; height: 18px; cursor: pointer;"
                    />
                  </div>

                  <!-- Dados de Publicidade -->
                  <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.8rem; background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); border-radius: 10px;">
                    <div>
                      <span style="font-size: 0.85rem; font-weight: 700; color: #fff;">Dados de Publicidade & Parcerias</span>
                      <p style="font-size: 0.72rem; color: var(--text-muted); margin: 2px 0 0 0;">Permitir anúncios personalizados e sugestões patrocinadas de capacitação de parceiros.</p>
                    </div>
                    <input 
                      type="checkbox" 
                      v-model="privacyData.allowTargetedAds" 
                      style="width: 18px; height: 18px; cursor: pointer;"
                    />
                  </div>

                  <!-- Consentimento de Cookies -->
                  <div style="display: flex; align-items: center; justify-content: space-between; padding: 0.8rem; background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.04); border-radius: 10px;">
                    <div>
                      <span style="font-size: 0.85rem; font-weight: 700; color: #fff;">Banner de Consentimento LGPD (Cookies)</span>
                      <p style="font-size: 0.72rem; color: var(--text-muted); margin: 2px 0 0 0;">Salvar e persistir consentimento de cookies essenciais de análise de navegação.</p>
                    </div>
                    <input 
                      type="checkbox" 
                      v-model="privacyData.cookieConsent" 
                      style="width: 18px; height: 18px; cursor: pointer;"
                    />
                  </div>

                  <div style="display: flex; justify-content: flex-end;">
                    <button type="button" class="btn btn-primary" style="font-size: 0.82rem;" @click="updatePrivacySettings">
                      Salvar Configurações
                    </button>
                  </div>
                </div>

                <!-- LGPD Exclusão/Exportação -->
                <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
                  <h3 style="margin: 0; font-size: 1.1rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-server" style="color: var(--color-secondary);"></i> Tratamento de Dados (Direito ao Esquecimento)
                  </h3>
                  <p style="margin: 0; font-size: 0.8rem; color: var(--text-secondary); line-height: 1.6;">
                    Em conformidade com a Lei Geral de Proteção de Dados (LGPD), você tem controle total sobre o download de suas informações cadastrais e o direito de ser excluído permanentemente de toda a base de IA.
                  </p>

                  <div style="display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.25rem;">
                    <button type="button" class="btn btn-secondary" style="font-size: 0.8rem; display: flex; align-items: center; gap: 4px;" @click="exportUserData">
                      <i class="fa-solid fa-download"></i> Exportar Meus Dados (JSON)
                    </button>
                    <button type="button" class="btn btn-secondary" style="font-size: 0.8rem; display: flex; align-items: center; gap: 4px; color: var(--color-error); border-color: rgba(239,68,68,0.2);" @click="deleteAccount">
                      <i class="fa-solid fa-user-xmark"></i> Excluir Minha Conta Permanentemente
                    </button>
                  </div>
                </div>
              </div>

              <!-- 5. TABA: NOTIFICAÇÕES MULTI-CANAL -->
              <div v-if="activeSettingsTab === 'notifications'" style="display: flex; flex-direction: column; gap: 1.5rem;">
                <!-- Preferências Gerais de Notificações -->
                <div class="glass-card" style="display: flex; flex-direction: column; gap: 1.25rem;">
                  <h3 style="margin: 0; font-size: 1.15rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-bell" style="color: var(--color-secondary);"></i> Canais de Comunicação
                  </h3>
                  
                  <div style="display: flex; flex-direction: column; gap: 0.8rem;">
                    <label style="display: flex; align-items: center; gap: 0.6rem; cursor: pointer; padding: 0.6rem; border-radius: 8px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03);">
                      <input
                        type="checkbox"
                        v-model="notificationSettings.notifyEmail"
                        style="width: 16px; height: 16px; cursor: pointer;"
                      />
                      <div>
                        <div style="font-size: 0.82rem; font-weight: 600; color: #fff;">📩 Notificações por E-mail</div>
                        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 1px;">Receber alertas de novas candidaturas e correspondências de vagas por e-mail</div>
                      </div>
                    </label>

                    <label style="display: flex; align-items: center; gap: 0.6rem; cursor: pointer; padding: 0.6rem; border-radius: 8px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03);">
                      <input
                        type="checkbox"
                        v-model="notificationSettings.notifyWhatsApp"
                        style="width: 16px; height: 16px; cursor: pointer;"
                      />
                      <div>
                        <div style="font-size: 0.82rem; font-weight: 600; color: #fff;">💬 Alertas por WhatsApp</div>
                        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 1px;">Receber relatórios do Agente de IA diretamente no seu número de contato</div>
                      </div>
                    </label>

                    <label style="display: flex; align-items: center; gap: 0.6rem; cursor: pointer; padding: 0.6rem; border-radius: 8px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03);">
                      <input
                        type="checkbox"
                        v-model="notificationSettings.notifyTelegram"
                        style="width: 16px; height: 16px; cursor: pointer;"
                      />
                      <div>
                        <div style="font-size: 0.82rem; font-weight: 600; color: #fff;">🤖 Notificações pelo Bot do Telegram</div>
                        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 1px;">Ativar e testar o envio de mensagens pelo bot do Telegram VagaSync</div>
                      </div>
                    </label>

                    <label style="display: flex; align-items: center; gap: 0.6rem; cursor: pointer; padding: 0.6rem; border-radius: 8px; background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03);">
                      <input
                        type="checkbox"
                        v-model="notificationSettings.newsletterEnabled"
                        style="width: 16px; height: 16px; cursor: pointer;"
                      />
                      <div>
                        <div style="font-size: 0.82rem; font-weight: 600; color: #fff;">📰 Newsletter & Conteúdos de IA</div>
                        <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 1px;">Receber informativos de novas integrações de APIs e dicas de recolocação profissional</div>
                      </div>
                    </label>
                  </div>
                  
                  <div style="display: flex; justify-content: flex-end;">
                    <button type="button" class="btn btn-primary" style="font-size: 0.82rem;" @click="updateNotificationSettings">
                      Salvar Notificações
                    </button>
                  </div>
                </div>

                <!-- Canais Técnicos Existentes -->
                <div class="glass-card">
                  <h2 class="section-title" style="margin-bottom: 0.5rem; font-size: 1.1rem;">
                    <i class="fa-solid fa-network-wired"></i> Fallback Técnico de Canais
                  </h2>
                  <p style="font-size: 0.82rem; color: var(--text-secondary); margin-bottom: 1.5rem; line-height: 1.5;">
                    Configure parâmetros SMTP e bots para o fallback automático das notificações e alertas técnicos.
                  </p>

                  <div style="display: flex; flex-wrap: wrap; gap: 0.6rem; margin-bottom: 1.5rem;">
                    <span 
                      v-if="notifyChannels" 
                      v-for="[canal, status] in Object.entries(notifyChannels)" 
                      :key="canal" 
                      style="font-size: 0.75rem; padding: 0.25rem 0.6rem; border-radius: 20px; font-weight: 600;"
                      :style="{
                        background: status.includes('✅') ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.04)',
                        border: `1px solid ${status.includes('✅') ? 'rgba(16,185,129,0.3)' : 'var(--border-color)'}`,
                        color: status.includes('✅') ? 'var(--color-success)' : 'var(--text-muted)'
                      }"
                    >
                      {{ status }} {{ canal }}
                    </span>
                  </div>

                  <!-- Telegram Bot Configs -->
                  <div style="margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border-color);">
                    <h4 style="font-size: 0.9rem; margin-bottom: 0.75rem; color: var(--color-secondary); display: flex; gap: 0.4rem; align-items: center;">
                      <Smartphone :size="14" /> Telegram Bot
                    </h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                      <div class="form-group" style="margin: 0;">
                        <label>Token do Bot Telegram</label>
                        <input type="password" class="form-input" v-model="config.telegram_token" placeholder="1234567890:ABCDef..." />
                      </div>
                      <div class="form-group" style="margin: 0;">
                        <label>Chat ID</label>
                        <input type="text" class="form-input" v-model="config.telegram_chat_id" placeholder="Ex: 123456789" />
                      </div>
                    </div>
                  </div>

                  <!-- SMTP Configs -->
                  <div style="margin-bottom: 1.5rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border-color);">
                    <h4 style="font-size: 0.9rem; margin-bottom: 0.75rem; color: var(--color-secondary); display: flex; gap: 0.4rem; align-items: center;">
                      <MessageSquare :size="14" /> E-mail (SMTP)
                    </h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; row-gap: 1rem;">
                      <div class="form-group" style="margin: 0;">
                        <label>E-mail Remetente (Login SMTP)</label>
                        <input type="email" class="form-input" v-model="config.smtp_email" placeholder="seu@gmail.com" />
                      </div>
                      <div class="form-group" style="margin: 0;">
                        <label>Senha de App / Senha SMTP</label>
                        <input type="password" class="form-input" v-model="config.smtp_password" placeholder="Senha SMTP..." />
                      </div>
                      <div class="form-group" style="margin: 0;">
                        <label>Host SMTP</label>
                        <input type="text" class="form-input" v-model="config.smtp_host" placeholder="smtp.gmail.com" />
                      </div>
                      <div class="form-group" style="margin: 0;">
                        <label>Porta SMTP</label>
                        <input type="number" class="form-input" v-model="config.smtp_port" placeholder="465" />
                      </div>
                    </div>
                  </div>

                  <!-- Webhook Configs -->
                  <div style="margin-bottom: 1.5rem;">
                    <h4 style="font-size: 0.9rem; margin-bottom: 0.75rem; color: var(--color-secondary); display: flex; gap: 0.4rem; align-items: center;">
                      <Globe :size="14" /> Webhook Genérico (Slack, Discord...)
                    </h4>
                    <div class="form-group" style="margin: 0;">
                      <label>URL do Webhook</label>
                      <input type="text" class="form-input" v-model="config.generic_webhook_url" placeholder="https://hooks.slack.com/..." />
                    </div>
                  </div>

                  <!-- Ações -->
                  <div style="display: flex; gap: 0.75rem; justify-content: flex-end;">
                    <button type="button" class="btn btn-secondary" @click="loadNotifyChannels" style="font-size: 0.85rem;">
                      Verificar Canais
                    </button>
                    <button 
                      type="button" 
                      class="btn btn-primary"
                      @click="testNotification" 
                      :disabled="testingNotify"
                      style="font-size: 0.85rem;"
                    >
                      Testar Todos os Canais
                    </button>
                    <button 
                      type="button" 
                      class="btn btn-primary"
                      @click="async (e) => { await saveConfig(e); loadNotifyChannels(); }"
                      style="font-size: 0.85rem;"
                    >
                      Salvar Integrações
                    </button>
                  </div>
                </div>
              </div>

              <!-- 6. TABA: AUTOMAÇÃO & PARAMETROS DE BUSCA (FORMULÁRIO EXISTENTE) -->
              <div v-if="activeSettingsTab === 'automation'" style="display: flex; flex-direction: column; gap: 1.5rem;">
                <div class="glass-card">
                  <h2 class="section-title">
                    <Settings :size="20" /> Parâmetros de Automação & Busca
                  </h2>
                  
                  <form @submit.prevent="saveConfig">
                    <!-- Gemini API Key status -->
                    <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; border-radius: 10px; background: rgba(16,185,129,0.07); border: 1px solid rgba(16,185,129,0.2); margin-bottom: 1.25rem;">
                      <Sparkles :size="16" style="color: var(--color-success); flex-shrink: 0;" />
                      <div>
                        <span style="font-size: 0.85rem; font-weight: 600; color: var(--color-success);">Gemini AI — Ativo e Configurado</span>
                        <p style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.1rem;">Chave da API armazenada com segurança no servidor.</p>
                      </div>
                      <span style="margin-left: auto; font-size: 0.7rem; padding: 0.2rem 0.6rem; border-radius: 20px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); color: var(--color-success); font-weight: 700; letter-spacing: 0.05em;">🔒 OCULTA</span>
                    </div>

                    <div class="form-group">
                      <label>Palavras-Chave de Busca (separadas por vírgula)</label>
                      <input type="text" class="form-input" v-model="config.keywords" placeholder="Ex: Desenvolvedor React, Python, Node.js" />
                    </div>

                    <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 1rem;">
                      <div class="form-group">
                        <label>Localização da Busca ({{ activeSearchScope.label }})</label>
                        <input type="text" class="form-input" v-model="config.search_location" :placeholder="activeSearchScope.placeholder" />
                      </div>
                      <div class="form-group">
                        <label>Buscar por</label>
                        <select class="form-input" v-model="config.search_scope" style="background: #0d1426; color: var(--text-primary); border: 1px solid var(--border-color);">
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
                      <label for="web_search_chk" style="margin: 0; cursor: pointer; font-size: 0.85rem; color: var(--text-secondary);">
                        Gemini busca vagas na internet junto com o agente (ATS oficiais, Gupy, Greenhouse, Lever, LinkedIn, Indeed, InfoJobs)
                      </label>
                    </div>

                    <div class="form-group" style="background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.22); border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                      <label style="display: flex; align-items: center; gap: 0.4rem; color: var(--color-success); font-weight: 700;">
                        <Map :size="15" /> Mapa Interativo & Geocodificação (Leaflet Ativo)
                      </label>
                      <input type="password" class="form-input" v-model="config.google_maps_api_key" placeholder="Google Maps API Key (opcional para geocodificação externa)..." style="margin-top: 0.7rem;" />
                    </div>

                    <!-- LinkedIn -->
                    <div style="background: rgba(10,102,194,0.06); border: 1px solid rgba(10,102,194,0.25); border-radius: 12px; padding: 1.25rem;">
                      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
                        <label style="margin: 0; font-size: 0.9rem; font-weight: 700; color: #60a5fa; display: flex; align-items: center; gap: 0.4rem;">
                          <Globe :size="15" /> LinkedIn Candidaturas
                        </label>
                        <button
                          type="button"
                          @click="window.open('https://www.linkedin.com/login', '_blank', 'width=900,height=650')"
                          class="linkedin-login-btn"
                          style="display: flex; align-items: center; gap: 0.5rem; padding: 0.45rem 1rem; border: none; background: linear-gradient(135deg, #0a66c2, #0077b5); color: #fff; font-weight: 700; font-size: 0.82rem; cursor: pointer; box-shadow: 0 2px 12px rgba(10,102,194,0.4);"
                        >
                          <Globe :size="14" /> Abrir Login LinkedIn
                        </button>
                      </div>
                      <div class="form-group" style="margin-bottom: 1rem;">
                        <label>LinkedIn Client ID</label>
                        <input type="text" class="form-input" v-model="config.linkedin_client_id" placeholder="Client ID..." />
                      </div>
                      <div class="form-group" style="margin-bottom: 1rem;">
                        <label>LinkedIn Client Secret</label>
                        <input type="password" class="form-input" v-model="config.linkedin_client_secret" placeholder="Client Secret..." />
                      </div>
                      <div style="font-size: 0.75rem; color: var(--text-secondary); background: rgba(0,0,0,0.2); border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.9rem; line-height: 1.7;">
                        <strong style="color: var(--text-primary); display: block; margin-bottom: 0.2rem;">Como obter o Cookie de sessão (li_at):</strong>
                        <ol style="margin: 0; padding-left: 1.1rem;">
                          <li>Faça login pelo botão acima.</li>
                          <li>Pressione F12 -> Application -> Cookies -> linkedin.com -> copie <code>li_at</code>.</li>
                        </ol>
                      </div>
                      <input type="password" class="form-input" v-model="config.linkedin_cookie" placeholder="Cole o cookie 'li_at' aqui..." />
                    </div>

                    <div style="display: flex; justify-content: flex-end; margin-top: 2rem;">
                      <button type="submit" class="btn btn-primary">
                        Salvar Parâmetros
                      </button>
                    </div>
                  </form>
                </div>
              </div>

            </div>

            <!-- Modal para Alterar Cartão (Netflix-style overlay) -->
            <div v-if="showChangeCardModal" style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(5, 7, 15, 0.85); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 9999;">
              <div class="glass-card" style="width: 100%; max-width: 440px; padding: 2rem; display: flex; flex-direction: column; gap: 1.5rem; border: 1px solid rgba(59, 130, 246, 0.3);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <h3 style="margin: 0; font-size: 1.15rem; color: #fff; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-shield-halved" style="color: #00f2fe;"></i> Alterar Cartão de Pagamento
                  </h3>
                  <button type="button" @click="showChangeCardModal = false" style="background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 1.5rem; line-height: 1;">&times;</button>
                </div>
                
                <div style="display: flex; flex-direction: column; gap: 1rem; text-align: center; align-items: center;">
                  <p style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.6; margin: 0;">
                    Por conformidade com os padrões de segurança PCI-DSS e proteção à LGPD, o VagaSync não coleta nem armazena as credenciais completas do seu cartão de crédito.
                  </p>
                  <p style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.6; margin: 0;">
                    Ao clicar no botão abaixo, você abrirá o portal seguro do **Mercado Pago** para atualizar ou reautorizar seu cartão com criptografia de ponta a ponta.
                  </p>
                </div>
                
                <div style="display: flex; gap: 0.75rem; justify-content: flex-end; margin-top: 0.5rem;">
                  <button type="button" class="btn btn-secondary" @click="showChangeCardModal = false">Voltar</button>
                  <button type="button" class="btn btn-primary" @click="() => { showChangeCardModal = false; openCheckout('candidate_premium', 'Atualizar Assinatura', 'R$ 9,90/mês'); }">Abrir Checkout Seguro 🔒</button>
                </div>
              </div>
            </div>

          </div>
        </template>
      </main>

      <footer class="footer-bar" @click="handleFooterClick" style="cursor: pointer; margin-top: 3rem; position: relative;">
        <p>© 2026 Vaga Sync. Todos os direitos reservados. • Conexão Segura SSL • Gemini Core Engine • n8n Connected</p>
        <div v-if="footerClickText" style="
          position: absolute;
          bottom: 100%;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(0, 242, 254, 0.95);
          color: #060913;
          padding: 0.6rem 1rem;
          border-radius: 8px;
          font-size: 0.82rem;
          font-weight: 600;
          white-space: nowrap;
          margin-bottom: 0.5rem;
          animation: slideUp 0.3s ease;
          z-index: 100;
        ">
          {{ footerClickText }}
        </div>
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
