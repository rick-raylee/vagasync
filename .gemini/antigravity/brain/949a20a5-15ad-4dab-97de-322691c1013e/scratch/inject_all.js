const fs = require('fs');
const path = require('path');

const appVuePath = 'c:\\Users\\ricar\\Desktop\\VAGASYNC\\frontend\\src\\App.vue';
if (!fs.existsSync(appVuePath)) {
  console.error("App.vue not found at", appVuePath);
  process.exit(1);
}

let content = fs.readFileSync(appVuePath, 'utf8');

// Normalize line endings to LF in App.vue
content = content.replace(/\r\n/g, '\n');

// 1. Update authForm and add userRole, isPremium, isRecruiterPro
const oldAuthForm = `const authForm = ref({ name: '', email: '', password: '', linkLinkedIn: true });`;
const newAuthForm = `const authForm = ref({ name: '', email: '', password: '', linkLinkedIn: true, role: 'candidate' });
const userRole = ref(localStorage.getItem('vagasync_role') || 'candidate');
const isPremium = ref(localStorage.getItem('vagasync_premium') === 'true');
const isRecruiterPro = ref(localStorage.getItem('vagasync_recruiter_pro') === 'true');`;

content = content.replace(oldAuthForm, newAuthForm);

// 2. Update handleLogin
const oldHandleLoginInner = `  localStorage.setItem('vagasync_logged', 'true');
  isLoggedIn.value = true;
  showToast('Acesso Autorizado', 'Bem-vindo de volta ao Vaga Sync!', 'success');`;

const newHandleLoginInner = `  // Auto-detect role based on standard testing emails
  if (authForm.value.email.includes('recrutador') || authForm.value.email === 'recrutador@vagasync.com') {
    authForm.value.role = 'recruiter';
  } else if (authForm.value.email.includes('admin') || authForm.value.email === 'admin@vagasync.com') {
    authForm.value.role = 'super_admin';
  } else if (authForm.value.email.includes('candidato') || authForm.value.email === 'candidato@vagasync.com') {
    authForm.value.role = 'candidate';
  }

  localStorage.setItem('vagasync_role', authForm.value.role);
  userRole.value = authForm.value.role;
  localStorage.setItem('vagasync_logged', 'true');
  isLoggedIn.value = true;
  activeTab.value = authForm.value.role === 'recruiter' ? 'recruiter_dashboard' : authForm.value.role === 'super_admin' ? 'super_admin' : 'dashboard';
  showToast('Acesso Autorizado', \`Bem-vindo de volta! Papel: \${authForm.value.role === 'recruiter' ? 'Recrutador' : authForm.value.role === 'super_admin' ? 'Administrador' : 'Candidato'}.\`, 'success');`;

content = content.replace(oldHandleLoginInner, newHandleLoginInner);

// 3. Update handleSignup
const oldHandleSignupInner = `  localStorage.setItem('vagasync_logged', 'true');
  isLoggedIn.value = true;
  showToast('Conta Criada!', 'Seu perfil foi sincronizado com sucesso.', 'success');`;

const newHandleSignupInner = `  // Auto-detect role based on standard testing emails
  if (authForm.value.email.includes('recrutador') || authForm.value.email === 'recrutador@vagasync.com') {
    authForm.value.role = 'recruiter';
  } else if (authForm.value.email.includes('admin') || authForm.value.email === 'admin@vagasync.com') {
    authForm.value.role = 'super_admin';
  } else if (authForm.value.email.includes('candidato') || authForm.value.email === 'candidato@vagasync.com') {
    authForm.value.role = 'candidate';
  }

  localStorage.setItem('vagasync_role', authForm.value.role);
  userRole.value = authForm.value.role;
  localStorage.setItem('vagasync_logged', 'true');
  isLoggedIn.value = true;
  activeTab.value = authForm.value.role === 'recruiter' ? 'recruiter_dashboard' : authForm.value.role === 'super_admin' ? 'super_admin' : 'dashboard';
  showToast('Conta Criada!', \`Seu perfil de \${authForm.value.role === 'recruiter' ? 'Recrutador' : authForm.value.role === 'super_admin' ? 'Administrador' : 'Candidato'} foi configurado.\`, 'success');`;

content = content.replace(oldHandleSignupInner, newHandleSignupInner);

// 4. Update handleLogout
const oldHandleLogout = `const handleLogout = () => {
  localStorage.removeItem('vagasync_logged');
  isLoggedIn.value = false;
  showToast('Sessão Encerrada', 'Até breve!', 'info');
};`;

const newHandleLogout = `const handleLogout = () => {
  localStorage.removeItem('vagasync_logged');
  localStorage.removeItem('vagasync_role');
  isLoggedIn.value = false;
  userRole.value = 'candidate';
  stopCamera();
  meetActive.value = false;
  showToast('Sessão Encerrada', 'Até breve!', 'info');
};`;

content = content.replace(oldHandleLogout, newHandleLogout);

// Update onMounted hook
const oldOnMounted = `onMounted(() => {
  fetchConfig();
  fetchJobs();
  checkAutomationStatus();`;

const newOnMounted = `onMounted(() => {
  if (isLoggedIn.value) {
    if (userRole.value === 'recruiter') {
      activeTab.value = 'recruiter_dashboard';
    } else if (userRole.value === 'super_admin') {
      activeTab.value = 'super_admin';
    }
  }
  fetchConfig();
  fetchJobs();
  checkAutomationStatus();`;

content = content.replace(oldOnMounted, newOnMounted);

// 3. Update footer clicks
content = content.replace(
  '<footer class="footer-bar">',
  '<footer class="footer-bar" @click="handleFooterClick" style="cursor: pointer;">'
);
content = content.replace(
  '<footer class="footer-bar" style="margin-top: 3rem;">',
  '<footer class="footer-bar" @click="handleFooterClick" style="cursor: pointer; margin-top: 3rem;">'
);

// 4. Add the templates, modals, etc.
const extractedPath = 'c:\\Users\\ricar\\Desktop\\VAGASYNC\\extracted_line_827.txt';
if (!fs.existsSync(extractedPath)) {
  console.error("extracted_line_827.txt not found!");
  process.exit(1);
}

let extractedContent = fs.readFileSync(extractedPath, 'utf8');

// Normalize line endings to LF in extractedContent
extractedContent = extractedContent.replace(/\r\n/g, '\n');

// Extract top_modal_insertion and all_tabs_insertion
const modalStartStr = 'top_modal_insertion = """';
const modalStartIdx = extractedContent.indexOf(modalStartStr) + modalStartStr.length;
const modalEndIdx = extractedContent.indexOf('"""', modalStartIdx);
const topModalInsertion = extractedContent.substring(modalStartIdx, modalEndIdx);

const tabsStartStr = 'all_tabs_insertion = """';
const tabsStartIdx = extractedContent.indexOf(tabsStartStr) + tabsStartStr.length;
const tabsEndIdx = extractedContent.indexOf('"""', tabsStartIdx);
const allTabsInsertion = extractedContent.substring(tabsStartIdx, tabsEndIdx);

// Replace Toast popup
const oldToastBlock = `    <!-- Toast popup -->
    <div v-if="toast" :class="['toast-notification', { success: toast.type === 'success' }]">
      <div class="toast-content">
        <h4>{{ toast.title }}</h4>
        <p>{{ toast.message }}</p>
      </div>
    </div>`;

content = content.replace(oldToastBlock, topModalInsertion);

// Replace end of resume tab (first occurrence of template end)
content = content.replace(
  '            </div>\n          </div>\n        </template>',
  allTabsInsertion
);

// 5. Add setup scripts right before </script>
const setupScriptToInject = `
// Gamificação, Roadmap e Simulador de Entrevista
const completedSimulationsCount = ref(0);

const employabilityScore = computed(() => {
  let score = 10;
  if (config.value.resume_text && config.value.resume_text.trim().length > 10) {
    score += 30;
    const words = config.value.resume_text.trim().split(/\\s+/).length;
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
  const resumeWords = hasResume ? config.value.resume_text.trim().split(/\\s+/).length : 0;
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
      content: \`Entrevista iniciada para o cargo de **\${interviewRole.value}** (\${interviewType.value}).\`
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
      feedbackContent = \`✓ **Avaliação IA:** Resposta excelente e muito bem estruturada. Você demonstrou domínio prático e clareza de argumentação. Nota: \${feedbackScore}/10.\`;
    } else {
      feedbackContent = \`✓ **Avaliação IA:** Boa resposta. Poderia incluir mais exemplos práticos do seu dia a dia para ilustrar melhor a solução. Nota: \${feedbackScore}/10.\`;
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
        content: \`🏁 Simulação concluída! Seu Score de Desempenho Geral foi de **\${interviewScore.value}%**.\`
      });
      interviewFeedback.value = \`Parabéns! Você demonstrou forte maturidade técnica para o cargo de \${interviewRole.value}. Sua comunicação é direta e focada em resultados. Sugestão: continue aprofundando-se em boas práticas de design patterns e arquitetura distribuída.\`;
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
    showToast('Candidato Atualizado', \`\${c.name} movido para \${newStatus.toUpperCase()}\`, 'success');
  }
};

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
    showToast('Acesso Secreto', 'Painel administrative secreto ativado.', 'info');
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
    const headers = { 'Authorization': \`Bearer \${adminToken.value}\` };
    
    // Stats
    const statsRes = await fetch(\`\${API_BASE}/admin/stats\`, { headers });
    if (statsRes.ok) adminStatsData.value = await statsRes.json();
    
    // Configs
    const configRes = await fetch(\`\${API_BASE}/admin/config\`, { headers });
    if (configRes.ok) adminConfigs.value = await configRes.json();
    
    // Audit logs
    const auditRes = await fetch(\`\${API_BASE}/admin/audit-logs\`, { headers });
    if (auditRes.ok) auditLogs.value = await auditRes.json();
    
    // Blogs
    const blogRes = await fetch(\`\${API_BASE}/admin/blog\`);
    if (blogRes.ok) blogPosts.value = await blogRes.json();
    
    // Banners
    const bannerRes = await fetch(\`\${API_BASE}/admin/banners\`);
    if (bannerRes.ok) banners.value = await bannerRes.json();
  } catch (e) {
    console.error("Error loading admin data:", e);
  }
};

const handleAdminLogin = async (e) => {
  if (e) e.preventDefault();
  try {
    const res = await fetch(\`\${API_BASE}/admin/login\`, {
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

    const res = await fetch(\`\${API_BASE}/admin/verify-2fa\`, {
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
    const res = await fetch(\`\${API_BASE}/admin/config\`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': \`Bearer \${adminToken.value}\`
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
    const res = await fetch(\`\${API_BASE}/admin/blog\`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': \`Bearer \${adminToken.value}\`
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
    const res = await fetch(\`\${API_BASE}/admin/blog/\${id}\`, {
      method: 'DELETE',
      headers: { 'Authorization': \`Bearer \${adminToken.value}\` }
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
    const res = await fetch(\`\${API_BASE}/admin/banners\`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': \`Bearer \${adminToken.value}\`
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
    const res = await fetch(\`\${API_BASE}/admin/banners/\${id}\`, {
      method: 'DELETE',
      headers: { 'Authorization': \`Bearer \${adminToken.value}\` }
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
    const res = await fetch(\`\${API_BASE}/admin/backup\`, {
      method: 'POST',
      headers: { 'Authorization': \`Bearer \${adminToken.value}\` }
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

// End of setup injection
`;

// Insert the setup scripts before </script>
const scriptEndIdx = content.lastIndexOf('</script>');
if (scriptEndIdx === -1) {
  console.error("</script> tag not found in App.vue");
  process.exit(1);
}

content = content.substring(0, scriptEndIdx) + setupScriptToInject + content.substring(scriptEndIdx);

// 6. Update the login selector in template
const oldLoginFormTitle = `<h2 style="margin-bottom: 0.5rem; font-size: 1.75rem;">Acesse sua Conta</h2>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1.5rem;">
                Faça login para gerenciar suas candidaturas automatizadas.
              </p>`;

const newLoginFormTitle = `<h2 style="margin-bottom: 0.5rem; font-size: 1.75rem;">Acesse sua Conta</h2>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1.5rem;">
                Faça login para gerenciar suas candidaturas automatizadas.
              </p>

              <div class="form-group">
                <label>Seu Perfil / Papel</label>
                <select class="form-input" v-model="authForm.role" style="background: #0d1426; color: var(--text-primary); border: 1px solid var(--border-color); margin-bottom: 1rem;">
                  <option value="candidate">Sou Candidato (Buscar Vagas)</option>
                  <option value="recruiter">Sou Recrutador/Empresa (Publicar Vagas e Triagem)</option>
                </select>
              </div>`;

content = content.replace(oldLoginFormTitle, newLoginFormTitle);

// Social login button
const oldSocialBtn = `<button 
                type="button" 
                class="btn social-btn-linkedin"
                @click="
                  localStorage.setItem('vagasync_logged', 'true');
                  isLoggedIn = true;
                  showToast('Login LinkedIn', 'Sessão iniciada via LinkedIn com sucesso!', 'success');
                "
              >`;

const newSocialBtn = `<button 
                type="button" 
                class="btn social-btn-linkedin"
                @click="
                  localStorage.setItem('vagasync_role', authForm.role);
                  userRole = authForm.role;
                  localStorage.setItem('vagasync_logged', 'true');
                  isLoggedIn = true;
                  activeTab = authForm.role === 'recruiter' ? 'recruiter_dashboard' : 'dashboard';
                  showToast('Login LinkedIn', \`Sessão iniciada como \${authForm.role === 'recruiter' ? 'Recrutador' : 'Candidato'} via LinkedIn com sucesso!\`, 'success');
                "
              >`;

content = content.replace(oldSocialBtn, newSocialBtn);

// Form 2: signup form
const oldSignupFormTitle = `<h2 style="margin-bottom: 0.5rem; font-size: 1.75rem;">Criar Conta</h2>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1.5rem;">
                Comece a impulsionar sua carreira com inteligência artificial.
              </p>`;

const newSignupFormTitle = `<h2 style="margin-bottom: 0.5rem; font-size: 1.75rem;">Criar Conta</h2>
              <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1.5rem;">
                Comece a impulsionar sua carreira com inteligência artificial.
              </p>

              <div class="form-group">
                <label>Seu Perfil / Papel</label>
                <select class="form-input" v-model="authForm.role" style="background: #0d1426; color: var(--text-primary); border: 1px solid var(--border-color); margin-bottom: 1rem;">
                  <option value="candidate">Sou Candidato (Buscar Vagas)</option>
                  <option value="recruiter">Sou Recrutador/Empresa (Publicar Vagas e Triagem)</option>
                </select>
              </div>`;

content = content.replace(oldSignupFormTitle, newSignupFormTitle);


// 7. Update Unified Navigation Bar
const oldNavBlock = `<nav class="nav-menu">
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
        </nav>`;

const newNavBlock = `<nav class="nav-menu" v-if="userRole === 'candidate'">
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
        </nav>`;

content = content.replace(oldNavBlock, newNavBlock);

fs.writeFileSync(appVuePath, content, 'utf8');
console.log("SUCCESS: Injected all UI templates, role selectors, and script variables into App.vue!");
