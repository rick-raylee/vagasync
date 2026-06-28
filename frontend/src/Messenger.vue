<script setup>
import { ref, computed, watch, onBeforeUnmount, nextTick } from 'vue';


const props = defineProps({
  jobs: {
    type: Array,
    default: () => []
  },
  showToast: {
    type: Function,
    default: () => {}
  },
  activeJobIdFromNotification: {
    type: [Number, String, null],
    default: null
  },
  clearNotificationSelection: {
    type: Function,
    default: () => {}
  }
});

const API_BASE = 'http://localhost:8000/api';

const selectedJobId = ref(null);
const messages = ref([]);
const inputText = ref('');
const loading = ref(false);
const sending = ref(false);
const copiedField = ref(null);

const messagesEndRef = ref(null);
let pollInterval = null;

const contactedJobs = computed(() => {
  const list = Array.isArray(props.jobs) ? props.jobs : [];
  const contacted = list.filter(j => j.status === 'contacted' || j.status === 'applied');
  
  const aiCoachContact = {
    id: 'ai-coach',
    company: '🤖 Coach de Carreira',
    title: 'Especialista em RH & Empregabilidade',
    recruiter_name: 'Mentor Vaga Sync',
    status: 'contacted',
    applied_at: new Date().toISOString(),
    recruiter_phone: 'Suporte IA',
    recruiter_contact: 'coach@vagasync.ai',
    company_address: 'Nuvem Gemini AI'
  };
  
  return [aiCoachContact, ...contacted];
});

const activeJob = computed(() => {
  return contactedJobs.value.find(j => j.id === selectedJobId.value);
});

// Sync with selected job from notification if any, or default selection
watch(
  [() => props.activeJobIdFromNotification, contactedJobs],
  ([notifId, list]) => {
    if (notifId) {
      selectedJobId.value = notifId;
      if (props.clearNotificationSelection) {
        props.clearNotificationSelection();
      }
    } else if (list.length > 0 && selectedJobId.value === null) {
      selectedJobId.value = list[0].id;
    }
  },
  { immediate: true, deep: true }
);

// Fetch messages when selected job changes
watch(
  selectedJobId,
  (newJobId) => {
    if (pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }

    if (!newJobId) {
      messages.value = [];
      return;
    }

    if (newJobId === 'ai-coach') {
      loadAiCoachMessages();
      return;
    }

    fetchMessages(newJobId, true);

    // Setup polling every 3 seconds to fetch recruiter automatic replies
    pollInterval = setInterval(() => {
      fetchMessages(newJobId, false);
    }, 3000);
  },
  { immediate: true }
);

// Scroll to bottom when messages load/change
watch(
  messages,
  () => {
    nextTick(() => {
      scrollToBottom();
    });
  },
  { deep: true }
);

onBeforeUnmount(() => {
  if (pollInterval) {
    clearInterval(pollInterval);
  }
});

const scrollToBottom = () => {
  if (messagesEndRef.value) {
    messagesEndRef.value.scrollIntoView({ behavior: 'smooth' });
  }
};

const fetchMessages = async (jobId, showLoadingState = false) => {
  if (showLoadingState) loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}/messages`);
    if (res.ok) {
      const data = await res.json();
      messages.value = data;
    }
  } catch (err) {
    console.error("Error fetching messages:", err);
  } finally {
    if (showLoadingState) loading.value = false;
  }
};

const handleSendMessage = async (e) => {
  if (e) e.preventDefault();
  if (!inputText.value.trim() || !selectedJobId.value || sending.value) return;

  const textToSend = inputText.value;
  inputText.value = '';
  sending.value = true;

  // Optimistically add message to UI
  const tempMsg = {
    id: Date.now(),
    job_id: selectedJobId.value,
    sender: 'user',
    content: textToSend,
    timestamp: new Date().toISOString()
  };

  if (selectedJobId.value === 'ai-coach') {
    aiCoachMessages.value = [...aiCoachMessages.value, tempMsg];
    messages.value = aiCoachMessages.value;
    localStorage.setItem('vagasync_ai_coach_messages', JSON.stringify(aiCoachMessages.value));
    
    setTimeout(() => {
      generateAiCoachReply(textToSend);
    }, 1000);
    
    sending.value = false;
    return;
  }

  messages.value = [...messages.value, tempMsg];

  try {
    const res = await fetch(`${API_BASE}/jobs/${selectedJobId.value}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: textToSend })
    });
    
    if (res.ok) {
      // Fetch official messages (includes recruiter simulated reply)
      setTimeout(() => fetchMessages(selectedJobId.value, false), 1600);
    } else {
      props.showToast('Erro ao enviar', 'Não foi possível enviar a mensagem.', 'error');
      // Rollback optimistic update
      messages.value = messages.value.filter(m => m.id !== tempMsg.id);
    }
  } catch (err) {
    props.showToast('Erro de Conexão', 'Não foi possível se conectar ao servidor.', 'error');
    messages.value = messages.value.filter(m => m.id !== tempMsg.id);
  } finally {
    sending.value = false;
  }
};

// AI Coach integration
const aiCoachMessages = ref([
  {
    id: 'ai-initial',
    job_id: 'ai-coach',
    sender: 'recruiter',
    content: 'Olá! Sou o seu Coach de Carreira Vaga Sync, alimentado por Inteligência Artificial. Posso te ajudar a refinar seu currículo, treinar para entrevistas, sugerir habilidades técnicas e dar insights de remuneração. O que você gostaria de discutir hoje?',
    timestamp: new Date().toISOString()
  }
]);

const loadAiCoachMessages = () => {
  const stored = localStorage.getItem('vagasync_ai_coach_messages');
  if (stored) {
    try {
      aiCoachMessages.value = JSON.parse(stored);
    } catch {}
  }
  messages.value = aiCoachMessages.value;
};

const generateAiCoachReply = (userText) => {
  const text = userText.toLowerCase();
  let reply = '';

  if (text.includes('currículo') || text.includes('curriculo') || text.includes('cv')) {
    reply = `Analisando seu perfil cadastrado no Vaga Sync, vejo que podemos melhorar alguns pontos no seu currículo:\n\n` +
      `1. **Palavras-chave**: Adicione mais verbos de ação como "Desenvolvi", "Liderei", "Otimizei".\n` +
      `2. **Seção de Projetos**: Destaque as tecnologias usadas e o impacto (ex: "redução de 20% no tempo de resposta").\n` +
      `3. **Certificações**: Liste certificações em evidência (ex: AWS Cloud Practitioner, SCRUM Master).\n\n` +
      `Deseja que eu analise um trecho específico? Cole-o aqui!`;
  } else if (text.includes('entrevista') || text.includes('treinar') || text.includes('simular')) {
    reply = `Excelente iniciativa! Treinar é o melhor caminho para a aprovação. \n\n` +
      `Eu recomendo que você utilize nossa aba **"Treino de Entrevista"** no menu principal. Lá você pode selecionar o cargo desejado e fazer uma simulação interativa completa, com feedbacks e notas de IA para cada resposta sua!`;
  } else if (text.includes('salário') || text.includes('salario') || text.includes('pretensão') || text.includes('remuneração')) {
    reply = `De acordo com as vagas coletadas recentemente e o mercado de TI em 2026, as faixas salariais para suas competências são:\n\n` +
      `• **Desenvolvedor Júnior**: R$ 4.500 - R$ 6.800\n` +
      `• **Desenvolvedor Pleno**: R$ 8.000 - R$ 12.500\n` +
      `• **Desenvolvedor Sênior**: R$ 14.000 - R$ 22.000\n\n` +
      `Dica: Sempre informe sua pretensão salarial como uma faixa negociável (ex: "entre R$ 9.000 e R$ 11.000") baseada em benefícios.`;
  } else if (text.includes('localização') || text.includes('lat') || text.includes('lng')) {
    reply = `Excelente! Acabei de mapear suas coordenadas. 📍\n\n` +
      `Com base na sua região, encontrei um aquecimento no mercado local para as seguintes áreas:\n\n` +
      `• **Empresas de Tecnologia na Região**: Há um polo de inovação contratando modelos híbridos.\n` +
      `• **Alertas Ativados**: Configurei o Radar VagaSync para notificar você quando surgirem vagas presenciais ou híbridas em um raio de 25km.\n\n` +
      `Deseja que eu filtre vagas 100% remotas ou foque nas oportunidades presenciais próximas a você?`;
  } else if (text.includes('localização') || text.includes('lat') || text.includes('lng')) {
    reply = `Excelente! Acabei de mapear suas coordenadas. 📍\n\n` +
      `Com base na sua região, encontrei um aquecimento no mercado local para as seguintes áreas:\n\n` +
      `• **Empresas de Tecnologia na Região**: Há um polo de inovação contratando modelos híbridos.\n` +
      `• **Alertas Ativados**: Configurei o Radar VagaSync para notificar você quando surgirem vagas presenciais ou híbridas em um raio de 25km.\n\n` +
      `Deseja que eu filtre vagas 100% remotas ou foque nas oportunidades presenciais próximas a você?`;
  } else if (text.includes('ajuda') || text.includes('como funciona') || text.includes('olá') || text.includes('ola') || text.includes('bom dia')) {
    reply = `Olá! Estou aqui para acelerar sua contratação. Você pode me perguntar sobre:\n\n` +
      `• Como melhorar o seu currículo.\n` +
      `• Faixas salariais no mercado de tecnologia.\n` +
      `• Como se preparar para perguntas difíceis em entrevistas.\n` +
      `• Dicas de networking e contato com recrutadores.`;
  } else {
    reply = `Compreendo. Essa é uma excelente questão no planejamento de carreira. Para te ajudar melhor:\n\n` +
      `1. Mantenha seu perfil técnico atualizado com as palavras-chave mais buscadas do momento.\n` +
      `2. Customize suas candidaturas focando em vagas com match superior a 70%.\n` +
      `3. Estude a cultura das empresas que você marcar no mapa para se destacar.\n\n` +
      `Há mais alguma dúvida sobre mercado, entrevistas ou currículo que eu possa esclarecer?`;
  }

  const coachMsg = {
    id: Date.now() + 1,
    job_id: 'ai-coach',
    sender: 'recruiter',
    content: reply,
    timestamp: new Date().toISOString()
  };

  aiCoachMessages.value = [...aiCoachMessages.value, coachMsg];
  messages.value = aiCoachMessages.value;
  localStorage.setItem('vagasync_ai_coach_messages', JSON.stringify(aiCoachMessages.value));
};

const isLocating = ref(false);
const isRecording = ref(false);
let recognition = null;

if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new SpeechRecognition();
  recognition.lang = 'pt-BR';
  recognition.continuous = false;
  recognition.interimResults = true;
  
  recognition.onresult = (event) => {
    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }
    
    // Append to current input text
    if (finalTranscript) {
      inputText.value = (inputText.value + ' ' + finalTranscript).trim();
    }
  };
  
  recognition.onend = () => {
    isRecording.value = false;
  };
  
  recognition.onerror = (event) => {
    isRecording.value = false;
    console.error("Erro no reconhecimento de fala", event.error);
  };
}

const toggleRecording = () => {
  if (!recognition) {
    props.showToast('Erro', 'Reconhecimento de fala não suportado no seu navegador.', 'error');
    return;
  }
  
  if (isRecording.value) {
    recognition.stop();
    isRecording.value = false;
  } else {
    recognition.start();
    isRecording.value = true;
  }
};

const shareLocationWithAI = () => {
  if (!navigator.geolocation) {
    props.showToast('Erro', 'Geolocalização não suportada pelo navegador.', 'error');
    return;
  }
  isLocating.value = true;
  navigator.geolocation.getCurrentPosition(
    (position) => {
      isLocating.value = false;
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      inputText.value = `📍 Minha localização atual é: LAT ${lat}, LNG ${lng}. Gere recomendações de vagas ou alertas personalizados próximos a mim.`;
    },
    (error) => {
      isLocating.value = false;
      props.showToast('Erro', 'Não foi possível obter sua localização. Permita o acesso.', 'error');
    }
  );
};

const copyToClipboard = (text, fieldName) => {
  navigator.clipboard.writeText(text).then(() => {
    copiedField.value = fieldName;
    setTimeout(() => {
      if (copiedField.value === fieldName) {
        copiedField.value = null;
      }
    }, 2000);
    props.showToast('Copiado!', `${fieldName} copiado para a área de transferência.`, 'success');
  }).catch(() => {});
};

</script>

<template>
  <div style="
    display: grid;
    grid-template-columns: 320px 1fr;
    height: calc(100vh - 180px);
    min-height: 550px;
    background: rgba(10, 15, 30, 0.6);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    overflow: hidden;
  ">
    
    <!-- ── Painel Esquerdo: Lista de Conversas ── -->
    <div style="
      border-right: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      background: rgba(13, 20, 38, 0.4);
    ">
      <div style="
        padding: 1.25rem;
        border-bottom: 1px solid var(--border-color);
        display: flex;
        align-items: center;
        gap: 0.5rem;
      ">
        <i class="fa-solid fa-comment" style="font-size: 18px; color: #00f2fe;"></i>
        <h3 style="font-size: 0.95rem; font-weight: 700; margin: 0; color: var(--text-primary);">
          Conversas com RH
        </h3>
        <span style="
          margin-left: auto;
          font-size: 0.7rem;
          padding: 2px 8px;
          border-radius: 20px;
          background: rgba(0, 242, 254, 0.1);
          color: #00f2fe;
          font-weight: 700;
        ">
          {{ contactedJobs.length }} ativos
        </span>
      </div>

      <div style="flex: 1; overflow-y: auto; padding: 0.75rem;">
        <div v-if="contactedJobs.length === 0" style="
          text-align: center;
          padding: 2rem 1rem;
          color: var(--text-secondary);
          font-size: 0.82rem;
        ">
          <i class="fa-solid fa-comment" style="font-size: 32px; opacity: 0.15; margin-bottom: 0.75rem;"></i>
          <p style="margin: 0;">Nenhum retorno de RH recebido ainda.</p>
          <p style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.8;">
            Aguarde o retorno de recrutadores reais após a candidatura.
          </p>
        </div>

        <div v-else>
          <button
            v-for="job in contactedJobs"
            :key="job.id"
            @click="selectedJobId = job.id"
            :style="{
              width: '100%',
              textAlign: 'left',
              padding: '0.9rem 1rem',
              borderRadius: '8px',
              border: '1px solid ' + (job.id === selectedJobId ? 'rgba(0, 242, 254, 0.3)' : 'transparent'),
              background: job.id === selectedJobId ? 'rgba(0, 242, 254, 0.08)' : 'transparent',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.25rem',
              transition: 'all 0.2s',
              marginBottom: '0.4rem',
              fontFamily: 'inherit'
            }"
            class="conversation-item-btn"
          >
            <div style="
              display: flex;
              justify-content: space-between;
              align-items: center;
              width: 100%;
            ">
              <span :style="{
                fontWeight: 700,
                fontSize: '0.85rem',
                color: job.id === selectedJobId ? '#00f2fe' : 'var(--text-primary)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                flex: 1
              }">
                {{ job.company }}
              </span>
              <span style="
                font-size: 0.7rem;
                color: var(--text-muted);
              ">
                {{ job.applied_at ? new Date(job.applied_at).toLocaleDateString(undefined, {day: 'numeric', month: 'short'}) : '' }}
              </span>
            </div>
            <span style="
              font-size: 0.78rem;
              color: var(--text-secondary);
              white-space: nowrap;
              overflow: hidden;
              text-overflow: ellipsis;
            ">
              {{ job.title }}
            </span>
            <span v-if="job.recruiter_name" style="
              font-size: 0.72rem;
              color: var(--text-muted);
              display: flex;
              align-items: center;
              gap: 4px;
              margin-top: 4px;
            ">
              <i class="fa-solid fa-user" style="font-size: 10px;"></i> {{ job.recruiter_name }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- ── Painel Direito: Chat do Recrutador ── -->
    <div style="
      display: flex;
      flex-direction: column;
      background: rgba(8, 12, 24, 0.3);
    ">
      <template v-if="activeJob">
        <!-- Header com Info de Contato (Endereço, Telefone, Email) -->
        <div style="
          padding: 1rem 1.5rem;
          border-bottom: 1px solid var(--border-color);
          background: rgba(13, 20, 38, 0.6);
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        ">
          <div style="
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 0.75rem;
          ">
            <div>
              <h4 style="margin: 0; font-size: 1.05rem; font-weight: 800; color: var(--text-primary);">
                {{ activeJob.recruiter_name || 'Recrutador' }}
              </h4>
              <p style="margin: 2px 0 0 0; font-size: 0.8rem; color: var(--text-secondary);">
                Recrutamento & Seleção na <strong>{{ activeJob.company }}</strong> para <em>{{ activeJob.title }}</em>
              </p>
            </div>

            <div style="display: flex; gap: 0.5rem;">
              <a
                v-if="activeJob.source !== 'recruiter'"
                :href="activeJob.link"
                target="_blank"
                rel="noopener noreferrer"
                style="
                  display: inline-flex;
                  align-items: center;
                  gap: 0.35rem;
                  padding: 0.4rem 0.8rem;
                  border-radius: 6px;
                  background: rgba(10, 102, 194, 0.15);
                  border: 1px solid rgba(10, 102, 194, 0.3);
                  color: #60a5fa;
                  text-decoration: none;
                  font-size: 0.75rem;
                  font-weight: 600;
                  transition: all 0.2s;
                "
              >
                Vaga no LinkedIn <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 12px; margin-left: 2px;"></i>
              </a>
              <span
                v-else
                style="
                  display: inline-flex;
                  align-items: center;
                  gap: 0.35rem;
                  padding: 0.4rem 0.8rem;
                  border-radius: 6px;
                  background: rgba(16, 185, 129, 0.15);
                  border: 1px solid rgba(16, 185, 129, 0.3);
                  color: #34d399;
                  font-size: 0.75rem;
                  font-weight: 600;
                "
              >
                Vaga VagaSync ✓
              </span>
            </div>
          </div>

          <!-- Informações detalhadas do RH (Endereço e Contatos) -->
          <div style="
            display: flex;
            flex-wrap: wrap;
            gap: 1.25rem;
            margin-top: 0.4rem;
            padding-top: 0.6rem;
            border-top: 1px solid rgba(255,255,255,0.04);
            font-size: 0.78rem;
          ">
            <div 
              v-if="activeJob.recruiter_phone"
              @click="copyToClipboard(activeJob.recruiter_phone, 'Telefone')"
              style="
                display: flex;
                align-items: center;
                gap: 0.4rem;
                color: var(--text-secondary);
                cursor: pointer;
              "
              title="Clique para copiar"
            >
              <i class="fa-solid fa-phone" style="font-size: 13px; color: #10b981;"></i>
              <span>{{ activeJob.recruiter_phone }}</span>
              <span v-if="copiedField === 'Telefone'" style="color: #10b981; font-size: 0.65rem;">(copiado!)</span>
            </div>

            <div 
              v-if="activeJob.recruiter_contact"
              @click="copyToClipboard(activeJob.recruiter_contact, 'Email')"
              style="
                display: flex;
                align-items: center;
                gap: 0.4rem;
                color: var(--text-secondary);
                cursor: pointer;
              "
              title="Clique para copiar"
            >
              <i class="fa-solid fa-envelope" style="font-size: 13px; color: #fb923c;"></i>
              <span>{{ activeJob.recruiter_contact }}</span>
              <span v-if="copiedField === 'Email'" style="color: #fb923c; font-size: 0.65rem;">(copiado!)</span>
            </div>

            <div 
              v-if="activeJob.company_address"
              style="
                display: flex;
                align-items: center;
                gap: 0.4rem;
                color: var(--text-secondary);
              "
            >
              <i class="fa-solid fa-map-pin" style="font-size: 13px; color: #3b82f6;"></i>
              <span>{{ activeJob.company_address }}</span>
              <a
                :href="`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(activeJob.company_address)}`"
                target="_blank"
                rel="noopener noreferrer"
                style="
                  color: #60a5fa;
                  text-decoration: underline;
                  margin-left: 4px;
                  display: inline-flex;
                  align-items: center;
                  gap: 2px;
                "
              >
                Mapa <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 10px; margin-left: 2px;"></i>
              </a>
            </div>
          </div>
        </div>

        <!-- Chat Messages scroll area -->
        <div style="
          flex: 1;
          overflow-y: auto;
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 1rem;
        ">
          <div v-if="loading && messages.length === 0" style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--text-secondary);
          ">
            <i class="fa-solid fa-spinner fa-spin" style="font-size: 24px; margin-bottom: 0.5rem;"></i>
            <span>Carregando histórico...</span>
          </div>

          <template v-else>
            <div style="
              text-align: center;
              margin: 0.5rem 0 1rem 0;
            ">
              <span style="
                font-size: 0.7rem;
                padding: 4px 10px;
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.06);
                color: var(--text-muted);
              ">
                Conexão de Chat segura estabelecida
              </span>
            </div>
            
            <div
              v-for="msg in messages"
              :key="msg.id"
              :style="{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                width: '100%'
              }"
            >
              <div :style="{
                maxWidth: '70%',
                padding: '0.8rem 1rem',
                borderRadius: '12px',
                borderTopRightRadius: msg.sender === 'user' ? '2px' : '12px',
                borderTopLeftRadius: msg.sender === 'user' ? '12px' : '2px',
                background: msg.sender === 'user' 
                  ? 'linear-gradient(135deg, #1d4ed8, #0369a1)' 
                  : 'rgba(255, 255, 255, 0.05)',
                border: msg.sender === 'user' 
                  ? '1px solid rgba(59, 130, 246, 0.4)' 
                  : '1px solid rgba(255, 255, 255, 0.08)',
                color: '#ffffff',
                fontSize: '0.85rem',
                lineHeight: 1.5,
                wordBreak: 'break-word',
                boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)'
              }">
                {{ msg.content }}
              </div>
              <span style="
                font-size: 0.68rem;
                color: var(--text-muted);
                margin-top: 4px;
                padding: 0 4px;
              ">
                {{ new Date(msg.timestamp).toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'}) }}
              </span>
            </div>
            
            <div v-if="sending" style="
              align-self: flex-end;
              display: flex;
              align-items: center;
              gap: 0.4rem;
              font-size: 0.72rem;
              color: var(--text-muted);
              padding-right: 0.5rem;
            ">
              <i class="fa-solid fa-spinner fa-spin" style="font-size: 10px;"></i>
              <span>Enviando...</span>
            </div>
            
            <div ref="messagesEndRef" />
          </template>
        </div>

        <!-- Message input bar -->
        <form
          @submit.prevent="handleSendMessage"
          style="
            padding: 1rem 1.5rem;
            border-top: 1px solid var(--border-color);
            background: rgba(10, 15, 30, 0.4);
            display: flex;
            gap: 0.75rem;
            align-items: center;
          "
        >
          <button
            v-if="activeJob.id === 'ai-coach'"
            type="button"
            @click="shareLocationWithAI"
            :disabled="isLocating"
            title="Compartilhar Localização"
            style="
              background: rgba(16, 185, 129, 0.15);
              border: 1px solid rgba(16, 185, 129, 0.3);
              color: var(--color-success);
              width: 38px;
              height: 38px;
              border-radius: 8px;
              display: flex;
              align-items: center;
              justify-content: center;
              cursor: pointer;
              transition: all 0.2s;
            "
          >
            <i :class="isLocating ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-location-crosshairs'" style="font-size: 16px;"></i>
          </button>

          <button
            v-if="activeJob.id === 'ai-coach'"
            type="button"
            @click="toggleRecording"
            :title="isRecording ? 'Parar Gravação' : 'Falar por Voz'"
            :style="{
              background: isRecording ? 'rgba(239, 68, 68, 0.15)' : 'rgba(59, 130, 246, 0.15)',
              border: isRecording ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(59, 130, 246, 0.3)',
              color: isRecording ? 'var(--color-error)' : '#3b82f6',
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s',
              animation: isRecording ? 'pulse 1.5s infinite' : 'none'
            }"
          >
            <i :class="isRecording ? 'fa-solid fa-stop' : 'fa-solid fa-microphone'" style="font-size: 16px;"></i>
          </button>

          <button
            v-if="activeJob.id === 'ai-coach'"
            type="button"
            @click="toggleRecording"
            :title="isRecording ? 'Parar Gravação' : 'Falar por Voz'"
            :style="{
              background: isRecording ? 'rgba(239, 68, 68, 0.15)' : 'rgba(59, 130, 246, 0.15)',
              border: isRecording ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(59, 130, 246, 0.3)',
              color: isRecording ? 'var(--color-error)' : '#3b82f6',
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              transition: 'all 0.2s',
              animation: isRecording ? 'pulse 1.5s infinite' : 'none'
            }"
          >
            <i :class="isRecording ? 'fa-solid fa-stop' : 'fa-solid fa-microphone'" style="font-size: 16px;"></i>
          </button>
          
          <input
            type="text"
            v-model="inputText"
            :placeholder="`Mande uma mensagem para ${activeJob.recruiter_name || 'o recrutador'}...`"
            style="
              flex: 1;
              background: #070b19;
              border: 1px solid var(--border-color);
              color: #ffffff;
              padding: 0.75rem 1rem;
              border-radius: 8px;
              font-size: 0.85rem;
              outline: none;
              transition: border-color 0.2s;
            "
            class="chat-input"
          />
          <button
            type="submit"
            :disabled="!inputText.trim() || sending"
            :style="{
              background: 'linear-gradient(135deg, #3b82f6, #00f2fe)',
              border: 'none',
              color: '#ffffff',
              width: '38px',
              height: '38px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: inputText.trim() && !sending ? 'pointer' : 'default',
              opacity: inputText.trim() && !sending ? 1 : 0.4,
              transition: 'all 0.2s'
            }"
          >
            <i class="fa-solid fa-paper-plane" style="font-size: 16px;"></i>
          </button>
        </form>
      </template>

      <div v-else style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--text-secondary);
        padding: 2rem;
        text-align: center;
      ">
        <i class="fa-solid fa-comment" style="font-size: 48px; opacity: 0.1; margin-bottom: 1rem;"></i>
        <h4 style="margin: 0; font-size: 1rem; color: var(--text-primary);">
          Nenhuma conversa ativa selecionada
        </h4>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.82rem; max-width: 320px;">
          Selecione um recrutador na lista à esquerda para visualizar as informações de contato e iniciar o chat.
        </p>
      </div>
    </div>

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
.chat-input:focus {
  border-color: #00f2fe !important;
}
.conversation-item-btn:hover {
  background: rgba(255, 255, 255, 0.02);
}
</style>
