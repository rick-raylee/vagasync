<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  jobs: {
    type: Array,
    default: () => []
  }
});

// ── Helpers ──────────────────────────────────────────────────────
function getStatusColor(s) {
  return { found: '#94a3b8', applying: '#3b82f6', applied: '#a855f7', contacted: '#10b981', failed: '#ef4444' }[s] || '#94a3b8';
}
function getStatusLabel(s) {
  return { found: 'Encontrada', applying: 'Candidatando', applied: 'Inscrita', contacted: 'RH Retornou ✓', failed: 'Falhou' }[s] || s;
}
function getMatchColor(score) {
  if (score >= 80) return '#10b981';
  if (score >= 65) return '#f59e0b';
  return '#ef4444';
}

// ── Gera mensagem de follow-up personalizada ─────────────────────
function buildFollowupMessage(job) {
  const name = job.recruiter_name ? job.recruiter_name.split(' ')[0] : null;
  const greeting = name ? `Olá, ${name}!` : 'Olá!';
  const workType = job.location?.includes('Remoto') ? 'remota'
    : job.location?.includes('Híbrido') ? 'híbrida'
    : 'presencial';

  return `${greeting}

Espero que esteja bem. Entrei em contato para fazer um follow-up da minha candidatura à vaga de ${job.title} na ${job.company}, aplicada recentemente.

Tenho grande interesse nesta oportunidade ${workType} e acredito que meu perfil está bem alinhado com os requisitos da posição. Fico à disposição para uma conversa caso queiram saber mais sobre minha experiência.

Agradeço a atenção e aguardo um retorno quando possível!

Atenciosamente.`;
}

// ── Gera mensagem de primeiro contato ───────────────────────────
function buildFirstContactMessage(job) {
  const name = job.recruiter_name ? job.recruiter_name.split(' ')[0] : null;
  const greeting = name ? `Olá, ${name}!` : 'Olá!';

  return `${greeting}

Vi que há uma oportunidade de ${job.title} na ${job.company} e fiquei muito interessado(a). 

Tenho experiência nas tecnologias e competências descritas na vaga e acredito que posso contribuir de forma significativa para o time. Posso enviar meu currículo completo ou conversar mais sobre o perfil buscado?

Obrigado(a) pelo tempo e aguardo seu retorno!`;
}

// States
const openCards = ref({});
const copiedId = ref(null);
const activeMsgs = ref({});

function toggleCard(jobId, defaultOpen = false) {
  if (openCards.value[jobId] === undefined) {
    openCards.value[jobId] = defaultOpen;
  }
  openCards.value[jobId] = !openCards.value[jobId];
}

function isCardOpen(jobId, defaultOpen = false) {
  if (openCards.value[jobId] === undefined) {
    return defaultOpen;
  }
  return openCards.value[jobId];
}

function getActiveMsg(jobId) {
  return activeMsgs.value[jobId] || 'followup';
}

function setActiveMsg(jobId, type) {
  activeMsgs.value[jobId] = type;
}

function copyText(text, id) {
  navigator.clipboard.writeText(text).catch(() => {
    const ta = document.createElement('textarea');
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
  });
  copiedId.value = id;
  setTimeout(() => {
    if (copiedId.value === id) {
      copiedId.value = null;
    }
  }, 2000);
}

const safeJobs = computed(() => {
  return Array.isArray(props.jobs) ? props.jobs : [];
});

const aplicadas = computed(() => safeJobs.value.filter(j => j.status === 'applied'));
const contatadas = computed(() => safeJobs.value.filter(j => j.status === 'contacted'));
const encontradas = computed(() => safeJobs.value.filter(j => j.status === 'found'));

const actionableJobs = computed(() => [...contatadas.value, ...aplicadas.value, ...encontradas.value]);

</script>

<template>
  <div style="display: flex; flex-direction: column; gap: 1.5rem;">

    <!-- ── Hero / Cabeçalho ───────────────────────────────── -->
    <div style="
      background: linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(168,85,247,0.08) 100%);
      border: 1px solid rgba(59,130,246,0.2);
      border-radius: 14px;
      padding: 1.5rem;
      display: flex; gap: 1.25rem; align-items: flex-start;
    ">
      <div style="width: 52px; height: 52px; border-radius: 12px; background: linear-gradient(135deg,#3b82f6,#a855f7); display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 24px;">
        📞
      </div>
      <div>
        <h2 style="font-size: 1.2rem; font-weight: 800; margin-bottom: 0.35rem; background: linear-gradient(90deg,#60a5fa,#c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
          Como Contatar o RH / Recrutador
        </h2>
        <p style="font-size: 0.85rem; color: var(--text-secondary); line-height: 1.6; max-width: 680px;">
          O Vaga Sync gera automaticamente mensagens personalizadas de follow-up e primeiro contato para cada vaga. 
          Copie a mensagem e envie diretamente no LinkedIn, por e-mail ou WhatsApp.
        </p>
      </div>
    </div>

    <!-- ── Guia passo a passo ─────────────────────────────── -->
    <div class="glass-card" style="padding: 1.5rem;">
      <h3 style="font-size: 1rem; font-weight: 700; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
        <i class="fa-solid fa-bolt" style="font-size: 16px; color: #f59e0b;"></i> Passo a Passo — Como Contatar o Recrutador
      </h3>

      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 0.85rem;">
        <div
          v-for="stepInfo in [
            {
              step: '01', icon: '🔍', title: 'Encontre a Vaga',
              color: '#3b82f6',
              desc: 'Vá ao Painel Principal e identifique uma vaga com status \'Inscrita\' ou \'Encontrada\'. Clique no título para abri-la no LinkedIn.',
            },
            {
              step: '02', icon: '👤', title: 'Identifique o Recrutador',
              color: '#a855f7',
              desc: 'Na página da vaga no LinkedIn, role para baixo e veja quem publicou. Clique no nome para acessar o perfil do recrutador.',
            },
            {
              step: '03', icon: '✉️', title: 'Copie a Mensagem',
              color: '#10b981',
              desc: 'Use a mensagem gerada abaixo, clique em \'Copiar\' e personalize com detalhes específicos da vaga antes de enviar.',
            },
            {
              step: '04', icon: '🚀', title: 'Envie pelo LinkedIn',
              color: '#f59e0b',
              desc: 'No perfil do recrutador, clique em \'Mensagem\' e cole o texto. Seja direto, profissional e mencione a vaga específica.',
            },
          ]"
          :key="stepInfo.step"
          :style="{
            padding: '1rem',
            background: 'rgba(255,255,255,0.02)',
            border: '1px solid var(--border-color)',
            borderRadius: '10px',
            borderTop: `3px solid ${stepInfo.color}`
          }"
        >
          <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
            <span :style="{ fontSize: '0.65rem', fontWeight: 800, color: stepInfo.color, background: `${stepInfo.color}20`, padding: '2px 7px', borderRadius: '20px', letterSpacing: '0.05em' }">
              PASSO {{ stepInfo.step }}
            </span>
            <span style="font-size: 1.1rem;">{{ stepInfo.icon }}</span>
          </div>
          <div style="font-size: 0.88rem; font-weight: 700; color: var(--text-primary); margin-bottom: 0.4rem;">
            {{ stepInfo.title }}
          </div>
          <div style="font-size: 0.78rem; color: var(--text-secondary); line-height: 1.55;">
            {{ stepInfo.desc }}
          </div>
        </div>
      </div>
    </div>

    <!-- ── Dicas de boas práticas ─────────────────────────── -->
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.75rem;">
      <div
        v-for="tipGroup in [
          {
            icon: '⏰', title: 'Melhor horário para enviar',
            color: '#f59e0b',
            tips: ['Terça a quinta, das 9h às 11h', 'Evite segundas pela manhã e sextas à tarde', 'Aguarde no mínimo 5-7 dias após candidatura'],
          },
          {
            icon: '✍️', title: 'Como personalizar a mensagem',
            color: '#3b82f6',
            tips: ['Mencione algo específico sobre a empresa', 'Cite por que aquela vaga te interessa', 'Seja conciso — máximo 3 parágrafos'],
          },
          {
            icon: '📊', title: 'Taxas de resposta no LinkedIn',
            color: '#10b981',
            tips: ['InMail: ~18-25% de resposta', 'Mensagem direta: ~10-15%', 'Nota de conexão personalizada: ~35-45%'],
          },
          {
            icon: '🚫', title: 'O que NÃO fazer',
            color: '#ef4444',
            tips: ['Não envie a mesma mensagem genérica para todos', 'Não insista com mais de 2 follow-ups', 'Não peça urgência — seja paciente e profissional'],
          },
        ]"
        :key="tipGroup.title"
        style="padding: 1rem; background: 'rgba(255,255,255,0.02)'; border: 1px solid var(--border-color); border-radius: 10px;"
      >
        <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.6rem;">
          <span style="font-size: 1.1rem;">{{ tipGroup.icon }}</span>
          <span :style="{ fontSize: '0.85rem', fontWeight: 700, color: tipGroup.color }">{{ tipGroup.title }}</span>
        </div>
        <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.35rem;">
          <li
            v-for="t in tipGroup.tips"
            :key="t"
            style="font-size: 0.78rem; color: var(--text-secondary); display: flex; align-items: flex-start; gap: 0.4rem;"
          >
            <span :style="{ color: tipGroup.color, marginTop: '2px', flexShrink: 0 }">›</span>
            {{ t }}
          </li>
        </ul>
      </div>
    </div>

    <!-- ── Mensagens por vaga ─────────────────────────────── -->
    <div>
      <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
        <h3 style="font-size: 1rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
          <i class="fa-solid fa-comment" style="font-size: 16px; color: #00f2fe;"></i>
          Mensagens por Vaga
          <span style="font-size: 0.75rem; padding: 2px 8px; border-radius: 20px; background: rgba(0,242,254,0.1); border: 1px solid rgba(0,242,254,0.2); color: #00f2fe; font-weight: 600;">
            {{ actionableJobs.length }} vagas
          </span>
        </h3>
        <div v-if="contatadas.length > 0" style="display: flex; align-items: center; gap: 0.4rem; font-size: 0.78rem; color: #10b981; background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); border-radius: 20px; padding: 0.3rem 0.75rem;">
          <i class="fa-solid fa-circle-check" style="font-size: 12px;"></i> {{ contatadas.length }} recrutador(es) já retornou
        </div>
      </div>

      <div v-if="actionableJobs.length === 0" style="text-align: center; padding: 3rem; color: var(--text-secondary); background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); border-radius: 12px;">
        <i class="fa-solid fa-comment" style="font-size: 40px; opacity: 0.15; margin-bottom: 1rem;"></i>
        <p style="font-weight: 600; margin-bottom: 0.5rem;">Nenhuma vaga para contato ainda</p>
        <p style="font-size: 0.82rem;">Inicie o agente para encontrar e se candidatar a vagas. As mensagens aparecerão aqui automaticamente.</p>
      </div>

      <div v-else style="display: flex; flex-direction: column; gap: 0.6rem;">
        <!-- Seção: RH Retornou -->
        <div v-if="contatadas.length > 0">
          <div style="font-size: 0.72rem; font-weight: 800; color: #10b981; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 0.35rem;">
            <i class="fa-solid fa-circle-check" style="font-size: 11px;"></i> RH Retornou — Continue a Conversa
          </div>
          
          <div
            v-for="(job, i) in contatadas"
            :key="job.id"
            :style="{
              border: isCardOpen(job.id, i === 0) ? '1px solid rgba(59,130,246,0.3)' : '1px solid var(--border-color)',
              borderRadius: '12px',
              background: isCardOpen(job.id, i === 0) ? 'rgba(13,20,38,0.8)' : 'rgba(255,255,255,0.02)',
              transition: 'all 0.25s ease',
              overflow: 'hidden',
              marginBottom: '0.6rem'
            }"
          >
            <!-- Card Header -->
            <button
              @click="toggleCard(job.id, i === 0)"
              style="
                width: 100%; text-align: left; display: flex; align-items: center;
                gap: 0.75rem; padding: 1rem 1.25rem;
                background: transparent; border: none; cursor: pointer;
                font-family: Inter, sans-serif;
              "
            >
              <div :style="{
                width: '10px', height: '10px', borderRadius: '50%',
                background: getStatusColor(job.status),
                boxShadow: `0 0 8px ${getStatusColor(job.status)}88`,
                flexShrink: 0
              }" />

              <div style="flex: 1; min-width: 0;">
                <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                  <span style="font-size: 0.9rem; font-weight: 700; color: var(--text-primary);">
                    {{ job.title }}
                  </span>
                  <span :style="{ fontSize: '0.75rem', padding: '2px 7px', borderRadius: '20px', fontWeight: 700, background: `${getMatchColor(job.match_score)}22`, border: `1px solid ${getMatchColor(job.match_score)}44`, color: getMatchColor(job.match_score) }">
                    {{ job.match_score ?? 0 }}%
                  </span>
                  <span :style="{ fontSize: '0.72rem', padding: '2px 7px', borderRadius: '20px', background: `${getStatusColor(job.status)}18`, border: `1px solid ${getStatusColor(job.status)}33`, color: getStatusColor(job.status) }">
                    {{ getStatusLabel(job.status) }}
                  </span>
                </div>
                <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">
                  {{ job.company }} • {{ job.location?.split('(')[0].trim() || 'Remoto' }}
                  <span v-if="job.recruiter_name"> • 👤 {{ job.recruiter_name }}</span>
                </div>
              </div>

              <div style="color: var(--text-muted); flex-shrink: 0;">
                <i v-if="isCardOpen(job.id, i === 0)" class="fa-solid fa-chevron-up" style="font-size: 16px;"></i>
                <i v-else class="fa-solid fa-chevron-down" style="font-size: 16px;"></i>
              </div>
            </button>

            <!-- Card Expanded Content -->
            <div v-if="isCardOpen(job.id, i === 0)" style="padding: 0 1.25rem 1.25rem; display: flex; flex-direction: column; gap: 1rem;">
              <div style="display: flex; gap: 0.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
                <button
                  v-for="msgOpt in [
                    { id: 'followup', label: '🔄 Follow-up de Candidatura', desc: 'Para quando já aplicou e quer saber o status' },
                    { id: 'first',    label: '👋 Primeiro Contato',         desc: 'Para iniciar conversa com o recrutador' },
                  ]"
                  :key="msgOpt.id"
                  @click="setActiveMsg(job.id, msgOpt.id)"
                  :style="{
                    flex: 1, padding: '0.6rem 0.75rem', borderRadius: '8px',
                    border: `1px solid ${getActiveMsg(job.id) === msgOpt.id ? 'rgba(59,130,246,0.4)' : 'var(--border-color)'}`,
                    background: getActiveMsg(job.id) === msgOpt.id ? 'rgba(59,130,246,0.12)' : 'rgba(255,255,255,0.02)',
                    color: getActiveMsg(job.id) === msgOpt.id ? '#60a5fa' : 'var(--text-secondary)',
                    cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                    textAlign: 'left', transition: 'all 0.2s'
                  }"
                >
                  <div style="font-size: 0.8rem; font-weight: 600;">{{ msgOpt.label }}</div>
                  <div style="font-size: 0.7rem; opacity: 0.7; margin-top: 2px;">{{ msgOpt.desc }}</div>
                </button>
              </div>

              <!-- Message Text -->
              <div style="position: relative;">
                <div style="font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.3rem;">
                  <i class="fa-solid fa-wand-magic-sparkles" style="font-size: 11px; color: #a855f7;"></i>
                  Mensagem Gerada pelo Vaga Sync
                </div>
                <pre style="
                  white-space: pre-wrap; word-break: break-word;
                  font-size: 0.83rem; color: var(--text-secondary);
                  background: rgba(0,0,0,0.25);
                  border: 1px solid rgba(255,255,255,0.06);
                  border-radius: 8px; padding: 1rem;
                  font-family: Inter, sans-serif; line-height: 1.65;
                  margin: 0;
                ">{{ getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job) }}</pre>

                <button
                  @click="copyText(getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job), `msg-${job.id}`)"
                  :style="{
                    position: 'absolute', top: '2.25rem', right: '0.5rem',
                    display: 'flex', alignItems: 'center', gap: '0.3rem',
                    padding: '0.35rem 0.65rem', borderRadius: '6px',
                    background: copiedId === `msg-${job.id}` ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.06)',
                    border: `1px solid ${copiedId === `msg-${job.id}` ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.1)'}`,
                    color: copiedId === `msg-${job.id}` ? '#10b981' : 'var(--text-secondary)',
                    cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600,
                    fontFamily: 'Inter, sans-serif', transition: 'all 0.2s'
                  }"
                >
                  <span v-if="copiedId === `msg-${job.id}`" style="display: flex; align-items: center; gap: 0.3rem;">
                    <i class="fa-solid fa-circle-check" style="font-size: 11px;"></i> Copiado!
                  </span>
                  <span v-else style="display: flex; align-items: center; gap: 0.3rem;">
                    <i class="fa-solid fa-copy" style="font-size: 11px;"></i> Copiar
                  </span>
                </button>
              </div>

              <!-- Contact Channels -->
              <div>
                <div style="font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.5rem;">
                  Como enviar esta mensagem
                </div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                  <a
                    :href="job.link"
                    target="_blank"
                    rel="noopener noreferrer"
                    style="display: flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.85rem; border-radius: 8px; background: rgba(10,102,194,0.15); border: 1px solid rgba(10,102,194,0.3); color: #60a5fa; text-decoration: none; font-size: 0.78rem; font-weight: 600; transition: all 0.2s;"
                  >
                    💼 Mensagem no LinkedIn
                    <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 11px;"></i>
                  </a>
                  <a
                    v-if="job.recruiter_contact && job.recruiter_contact.includes('@')"
                    :href="`mailto:${job.recruiter_contact}?subject=Follow-up – Vaga de ${encodeURIComponent(job.title)}&body=${encodeURIComponent(getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job))}`"
                    style="display: flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.85rem; border-radius: 8px; background: rgba(234,88,12,0.12); border: 1px solid rgba(234,88,12,0.25); color: #fb923c; text-decoration: none; font-size: 0.78rem; font-weight: 600; transition: all 0.2s;"
                  >
                    <i class="fa-solid fa-envelope" style="font-size: 12px;"></i> Enviar por E-mail
                  </a>
                  <button
                    @click="copyText(getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job), `copy-${job.id}`)"
                    :style="{
                      display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '0.45rem 0.85rem', borderRadius: '8px',
                      background: copiedId === `copy-${job.id}` ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.04)',
                      border: `1px solid ${copiedId === `copy-${job.id}` ? 'rgba(16,185,129,0.3)' : 'var(--border-color)'}`,
                      color: copiedId === `copy-${job.id}` ? '#10b981' : 'var(--text-secondary)',
                      cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600, fontFamily: 'Inter, sans-serif', transition: 'all 0.2s'
                    }"
                  >
                    <span v-if="copiedId === `copy-${job.id}`" style="display: flex; align-items: center; gap: 0.35rem;">
                      <i class="fa-solid fa-circle-check" style="font-size: 12px;"></i> Copiado!
                    </span>
                    <span v-else style="display: flex; align-items: center; gap: 0.35rem;">
                      <i class="fa-solid fa-copy" style="font-size: 12px;"></i> Copiar Mensagem
                    </span>
                  </button>
                </div>
              </div>

              <!-- Recruiter Info -->
              <div v-if="job.recruiter_name" style="display: flex; gap: 1rem; padding: 0.75rem; background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.15); border-radius: 8px; flex-wrap: wrap;">
                <div>
                  <div style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 2px;">Recrutador detectado</div>
                  <div style="font-size: 0.82rem; color: #10b981; font-weight: 600;">{{ job.recruiter_name }}</div>
                </div>
                <div v-if="job.recruiter_contact">
                  <div style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 2px;">Contato</div>
                  <div style="font-size: 0.82rem; color: var(--text-secondary);">{{ job.recruiter_contact }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Seção: Candidatadas aguardando -->
        <div v-if="aplicadas.length > 0" :style="{ marginTop: contatadas.length > 0 ? '0.5rem' : 0 }">
          <div style="font-size: 0.72rem; font-weight: 800; color: #a855f7; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 0.35rem;">
            <i class="fa-regular fa-clock" style="font-size: 11px;"></i> Inscrito — Aguardando Resposta ({{ aplicadas.length }})
          </div>

          <div
            v-for="job in aplicadas"
            :key="job.id"
            :style="{
              border: isCardOpen(job.id, false) ? '1px solid rgba(59,130,246,0.3)' : '1px solid var(--border-color)',
              borderRadius: '12px',
              background: isCardOpen(job.id, false) ? 'rgba(13,20,38,0.8)' : 'rgba(255,255,255,0.02)',
              transition: 'all 0.25s ease',
              overflow: 'hidden',
              marginBottom: '0.6rem'
            }"
          >
            <!-- Card Header -->
            <button
              @click="toggleCard(job.id, false)"
              style="
                width: 100%; text-align: left; display: flex; align-items: center;
                gap: 0.75rem; padding: 1rem 1.25rem;
                background: transparent; border: none; cursor: pointer;
                font-family: Inter, sans-serif;
              "
            >
              <div :style="{
                width: '10px', height: '10px', borderRadius: '50%',
                background: getStatusColor(job.status),
                boxShadow: `0 0 8px ${getStatusColor(job.status)}88`,
                flexShrink: 0
              }" />

              <div style="flex: 1; min-width: 0;">
                <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                  <span style="font-size: 0.9rem; font-weight: 700; color: var(--text-primary);">
                    {{ job.title }}
                  </span>
                  <span :style="{ fontSize: '0.75rem', padding: '2px 7px', borderRadius: '20px', fontWeight: 700, background: `${getMatchColor(job.match_score)}22`, border: `1px solid ${getMatchColor(job.match_score)}44`, color: getMatchColor(job.match_score) }">
                    {{ job.match_score ?? 0 }}%
                  </span>
                  <span :style="{ fontSize: '0.72rem', padding: '2px 7px', borderRadius: '20px', background: `${getStatusColor(job.status)}18`, border: `1px solid ${getStatusColor(job.status)}33`, color: getStatusColor(job.status) }">
                    {{ getStatusLabel(job.status) }}
                  </span>
                </div>
                <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">
                  {{ job.company }} • {{ job.location?.split('(')[0].trim() || 'Remoto' }}
                  <span v-if="job.recruiter_name"> • 👤 {{ job.recruiter_name }}</span>
                </div>
              </div>

              <div style="color: var(--text-muted); flex-shrink: 0;">
                <i v-if="isCardOpen(job.id, false)" class="fa-solid fa-chevron-up" style="font-size: 16px;"></i>
                <i v-else class="fa-solid fa-chevron-down" style="font-size: 16px;"></i>
              </div>
            </button>

            <!-- Card Expanded Content -->
            <div v-if="isCardOpen(job.id, false)" style="padding: 0 1.25rem 1.25rem; display: flex; flex-direction: column; gap: 1rem;">
              <div style="display: flex; gap: 0.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
                <button
                  v-for="msgOpt in [
                    { id: 'followup', label: '🔄 Follow-up de Candidatura', desc: 'Para quando já aplicou e quer saber o status' },
                    { id: 'first',    label: '👋 Primeiro Contato',         desc: 'Para iniciar conversa com o recrutador' },
                  ]"
                  :key="msgOpt.id"
                  @click="setActiveMsg(job.id, msgOpt.id)"
                  :style="{
                    flex: 1, padding: '0.6rem 0.75rem', borderRadius: '8px',
                    border: `1px solid ${getActiveMsg(job.id) === msgOpt.id ? 'rgba(59,130,246,0.4)' : 'var(--border-color)'}`,
                    background: getActiveMsg(job.id) === msgOpt.id ? 'rgba(59,130,246,0.12)' : 'rgba(255,255,255,0.02)',
                    color: getActiveMsg(job.id) === msgOpt.id ? '#60a5fa' : 'var(--text-secondary)',
                    cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                    textAlign: 'left', transition: 'all 0.2s'
                  }"
                >
                  <div style="font-size: 0.8rem; font-weight: 600;">{{ msgOpt.label }}</div>
                  <div style="font-size: 0.7rem; opacity: 0.7; margin-top: 2px;">{{ msgOpt.desc }}</div>
                </button>
              </div>

              <!-- Message Text -->
              <div style="position: relative;">
                <div style="font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.3rem;">
                  <i class="fa-solid fa-wand-magic-sparkles" style="font-size: 11px; color: #a855f7;"></i>
                  Mensagem Gerada pelo Vaga Sync
                </div>
                <pre style="
                  white-space: pre-wrap; word-break: break-word;
                  font-size: 0.83rem; color: var(--text-secondary);
                  background: rgba(0,0,0,0.25);
                  border: 1px solid rgba(255,255,255,0.06);
                  border-radius: 8px; padding: 1rem;
                  font-family: Inter, sans-serif; line-height: 1.65;
                  margin: 0;
                ">{{ getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job) }}</pre>

                <button
                  @click="copyText(getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job), `msg-${job.id}`)"
                  :style="{
                    position: 'absolute', top: '2.25rem', right: '0.5rem',
                    display: 'flex', alignItems: 'center', gap: '0.3rem',
                    padding: '0.35rem 0.65rem', borderRadius: '6px',
                    background: copiedId === `msg-${job.id}` ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.06)',
                    border: `1px solid ${copiedId === `msg-${job.id}` ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.1)'}`,
                    color: copiedId === `msg-${job.id}` ? '#10b981' : 'var(--text-secondary)',
                    cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600,
                    fontFamily: 'Inter, sans-serif', transition: 'all 0.2s'
                  }"
                >
                  <span v-if="copiedId === `msg-${job.id}`" style="display: flex; align-items: center; gap: 0.3rem;">
                    <i class="fa-solid fa-circle-check" style="font-size: 11px;"></i> Copiado!
                  </span>
                  <span v-else style="display: flex; align-items: center; gap: 0.3rem;">
                    <i class="fa-solid fa-copy" style="font-size: 11px;"></i> Copiar
                  </span>
                </button>
              </div>

              <!-- Contact Channels -->
              <div>
                <div style="font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.5rem;">
                  Como enviar esta mensagem
                </div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                  <a
                    :href="job.link"
                    target="_blank"
                    rel="noopener noreferrer"
                    style="display: flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.85rem; border-radius: 8px; background: rgba(10,102,194,0.15); border: 1px solid rgba(10,102,194,0.3); color: #60a5fa; text-decoration: none; font-size: 0.78rem; font-weight: 600; transition: all 0.2s;"
                  >
                    💼 Mensagem no LinkedIn
                    <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 11px;"></i>
                  </a>
                  <a
                    v-if="job.recruiter_contact && job.recruiter_contact.includes('@')"
                    :href="`mailto:${job.recruiter_contact}?subject=Follow-up – Vaga de ${encodeURIComponent(job.title)}&body=${encodeURIComponent(getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job))}`"
                    style="display: flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.85rem; border-radius: 8px; background: rgba(234,88,12,0.12); border: 1px solid rgba(234,88,12,0.25); color: #fb923c; text-decoration: none; font-size: 0.78rem; font-weight: 600; transition: all 0.2s;"
                  >
                    <i class="fa-solid fa-envelope" style="font-size: 12px;"></i> Enviar por E-mail
                  </a>
                  <button
                    @click="copyText(getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job), `copy-${job.id}`)"
                    :style="{
                      display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '0.45rem 0.85rem', borderRadius: '8px',
                      background: copiedId === `copy-${job.id}` ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.04)',
                      border: `1px solid ${copiedId === `copy-${job.id}` ? 'rgba(16,185,129,0.3)' : 'var(--border-color)'}`,
                      color: copiedId === `copy-${job.id}` ? '#10b981' : 'var(--text-secondary)',
                      cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600, fontFamily: 'Inter, sans-serif', transition: 'all 0.2s'
                    }"
                  >
                    <span v-if="copiedId === `copy-${job.id}`" style="display: flex; align-items: center; gap: 0.35rem;">
                      <i class="fa-solid fa-circle-check" style="font-size: 12px;"></i> Copiado!
                    </span>
                    <span v-else style="display: flex; align-items: center; gap: 0.35rem;">
                      <i class="fa-solid fa-copy" style="font-size: 12px;"></i> Copiar Mensagem
                    </span>
                  </button>
                </div>
              </div>

              <!-- Recruiter Info -->
              <div v-if="job.recruiter_name" style="display: flex; gap: 1rem; padding: 0.75rem; background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.15); border-radius: 8px; flex-wrap: wrap;">
                <div>
                  <div style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 2px;">Recrutador detectado</div>
                  <div style="font-size: 0.82rem; color: #10b981; font-weight: 600;">{{ job.recruiter_name }}</div>
                </div>
                <div v-if="job.recruiter_contact">
                  <div style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 2px;">Contato</div>
                  <div style="font-size: 0.82rem; color: var(--text-secondary);">{{ job.recruiter_contact }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Seção: Encontradas -->
        <div v-if="encontradas.length > 0" style="margin-top: 0.5rem;">
          <div style="font-size: 0.72rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 0.35rem;">
            <i class="fa-solid fa-briefcase" style="font-size: 11px;"></i> Vagas Encontradas — Primeiro Contato
          </div>

          <div
            v-for="job in encontradas"
            :key="job.id"
            :style="{
              border: isCardOpen(job.id, false) ? '1px solid rgba(59,130,246,0.3)' : '1px solid var(--border-color)',
              borderRadius: '12px',
              background: isCardOpen(job.id, false) ? 'rgba(13,20,38,0.8)' : 'rgba(255,255,255,0.02)',
              transition: 'all 0.25s ease',
              overflow: 'hidden',
              marginBottom: '0.6rem'
            }"
          >
            <!-- Card Header -->
            <button
              @click="toggleCard(job.id, false)"
              style="
                width: 100%; text-align: left; display: flex; align-items: center;
                gap: 0.75rem; padding: 1rem 1.25rem;
                background: transparent; border: none; cursor: pointer;
                font-family: Inter, sans-serif;
              "
            >
              <div :style="{
                width: '10px', height: '10px', borderRadius: '50%',
                background: getStatusColor(job.status),
                boxShadow: `0 0 8px ${getStatusColor(job.status)}88`,
                flexShrink: 0
              }" />

              <div style="flex: 1; min-width: 0;">
                <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                  <span style="font-size: 0.9rem; font-weight: 700; color: var(--text-primary);">
                    {{ job.title }}
                  </span>
                  <span :style="{ fontSize: '0.75rem', padding: '2px 7px', borderRadius: '20px', fontWeight: 700, background: `${getMatchColor(job.match_score)}22`, border: `1px solid ${getMatchColor(job.match_score)}44`, color: getMatchColor(job.match_score) }">
                    {{ job.match_score ?? 0 }}%
                  </span>
                  <span :style="{ fontSize: '0.72rem', padding: '2px 7px', borderRadius: '20px', background: `${getStatusColor(job.status)}18`, border: `1px solid ${getStatusColor(job.status)}33`, color: getStatusColor(job.status) }">
                    {{ getStatusLabel(job.status) }}
                  </span>
                </div>
                <div style="font-size: 0.78rem; color: var(--text-secondary); margin-top: 2px;">
                  {{ job.company }} • {{ job.location?.split('(')[0].trim() || 'Remoto' }}
                  <span v-if="job.recruiter_name"> • 👤 {{ job.recruiter_name }}</span>
                </div>
              </div>

              <div style="color: var(--text-muted); flex-shrink: 0;">
                <i v-if="isCardOpen(job.id, false)" class="fa-solid fa-chevron-up" style="font-size: 16px;"></i>
                <i v-else class="fa-solid fa-chevron-down" style="font-size: 16px;"></i>
              </div>
            </button>

            <!-- Card Expanded Content -->
            <div v-if="isCardOpen(job.id, false)" style="padding: 0 1.25rem 1.25rem; display: flex; flex-direction: column; gap: 1rem;">
              <div style="display: flex; gap: 0.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem;">
                <button
                  v-for="msgOpt in [
                    { id: 'followup', label: '🔄 Follow-up de Candidatura', desc: 'Para quando já aplicou e quer saber o status' },
                    { id: 'first',    label: '👋 Primeiro Contato',         desc: 'Para iniciar conversa com o recrutador' },
                  ]"
                  :key="msgOpt.id"
                  @click="setActiveMsg(job.id, msgOpt.id)"
                  :style="{
                    flex: 1, padding: '0.6rem 0.75rem', borderRadius: '8px',
                    border: `1px solid ${getActiveMsg(job.id) === msgOpt.id ? 'rgba(59,130,246,0.4)' : 'var(--border-color)'}`,
                    background: getActiveMsg(job.id) === msgOpt.id ? 'rgba(59,130,246,0.12)' : 'rgba(255,255,255,0.02)',
                    color: getActiveMsg(job.id) === msgOpt.id ? '#60a5fa' : 'var(--text-secondary)',
                    cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                    textAlign: 'left', transition: 'all 0.2s'
                  }"
                >
                  <div style="font-size: 0.8rem; font-weight: 600;">{{ msgOpt.label }}</div>
                  <div style="font-size: 0.7rem; opacity: 0.7; margin-top: 2px;">{{ msgOpt.desc }}</div>
                </button>
              </div>

              <!-- Message Text -->
              <div style="position: relative;">
                <div style="font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.3rem;">
                  <i class="fa-solid fa-wand-magic-sparkles" style="font-size: 11px; color: #a855f7;"></i>
                  Mensagem Gerada pelo Vaga Sync
                </div>
                <pre style="
                  white-space: pre-wrap; word-break: break-word;
                  font-size: 0.83rem; color: var(--text-secondary);
                  background: rgba(0,0,0,0.25);
                  border: 1px solid rgba(255,255,255,0.06);
                  border-radius: 8px; padding: 1rem;
                  font-family: Inter, sans-serif; line-height: 1.65;
                  margin: 0;
                ">{{ getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job) }}</pre>

                <button
                  @click="copyText(getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job), `msg-${job.id}`)"
                  :style="{
                    position: 'absolute', top: '2.25rem', right: '0.5rem',
                    display: 'flex', alignItems: 'center', gap: '0.3rem',
                    padding: '0.35rem 0.65rem', borderRadius: '6px',
                    background: copiedId === `msg-${job.id}` ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.06)',
                    border: `1px solid ${copiedId === `msg-${job.id}` ? 'rgba(16,185,129,0.3)' : 'rgba(255,255,255,0.1)'}`,
                    color: copiedId === `msg-${job.id}` ? '#10b981' : 'var(--text-secondary)',
                    cursor: 'pointer', fontSize: '0.72rem', fontWeight: 600,
                    fontFamily: 'Inter, sans-serif', transition: 'all 0.2s'
                  }"
                >
                  <span v-if="copiedId === `msg-${job.id}`" style="display: flex; align-items: center; gap: 0.3rem;">
                    <i class="fa-solid fa-circle-check" style="font-size: 11px;"></i> Copiado!
                  </span>
                  <span v-else style="display: flex; align-items: center; gap: 0.3rem;">
                    <i class="fa-solid fa-copy" style="font-size: 11px;"></i> Copiar
                  </span>
                </button>
              </div>

              <!-- Contact Channels -->
              <div>
                <div style="font-size: 0.7rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.5rem;">
                  Como enviar esta mensagem
                </div>
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap;">
                  <a
                    :href="job.link"
                    target="_blank"
                    rel="noopener noreferrer"
                    style="display: flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.85rem; border-radius: 8px; background: rgba(10,102,194,0.15); border: 1px solid rgba(10,102,194,0.3); color: #60a5fa; text-decoration: none; font-size: 0.78rem; font-weight: 600; transition: all 0.2s;"
                  >
                    💼 Mensagem no LinkedIn
                    <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 11px;"></i>
                  </a>
                  <a
                    v-if="job.recruiter_contact && job.recruiter_contact.includes('@')"
                    :href="`mailto:${job.recruiter_contact}?subject=Follow-up – Vaga de ${encodeURIComponent(job.title)}&body=${encodeURIComponent(getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job))}`"
                    style="display: flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.85rem; border-radius: 8px; background: rgba(234,88,12,0.12); border: 1px solid rgba(234,88,12,0.25); color: #fb923c; text-decoration: none; font-size: 0.78rem; font-weight: 600; transition: all 0.2s;"
                  >
                    <i class="fa-solid fa-envelope" style="font-size: 12px;"></i> Enviar por E-mail
                  </a>
                  <button
                    @click="copyText(getActiveMsg(job.id) === 'followup' ? buildFollowupMessage(job) : buildFirstContactMessage(job), `copy-${job.id}`)"
                    :style="{
                      display: 'flex', alignItems: 'center', gap: '0.35rem', padding: '0.45rem 0.85rem', borderRadius: '8px',
                      background: copiedId === `copy-${job.id}` ? 'rgba(16,185,129,0.12)' : 'rgba(255,255,255,0.04)',
                      border: `1px solid ${copiedId === `copy-${job.id}` ? 'rgba(16,185,129,0.3)' : 'var(--border-color)'}`,
                      color: copiedId === `copy-${job.id}` ? '#10b981' : 'var(--text-secondary)',
                      cursor: 'pointer', fontSize: '0.78rem', fontWeight: 600, fontFamily: 'Inter, sans-serif', transition: 'all 0.2s'
                    }"
                  >
                    <span v-if="copiedId === `copy-${job.id}`" style="display: flex; align-items: center; gap: 0.35rem;">
                      <i class="fa-solid fa-circle-check" style="font-size: 12px;"></i> Copiado!
                    </span>
                    <span v-else style="display: flex; align-items: center; gap: 0.35rem;">
                      <i class="fa-solid fa-copy" style="font-size: 12px;"></i> Copiar Mensagem
                    </span>
                  </button>
                </div>
              </div>

              <!-- Recruiter Info -->
              <div v-if="job.recruiter_name" style="display: flex; gap: 1rem; padding: 0.75rem; background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.15); border-radius: 8px; flex-wrap: wrap;">
                <div>
                  <div style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 2px;">Recrutador detectado</div>
                  <div style="font-size: 0.82rem; color: #10b981; font-weight: 600;">{{ job.recruiter_name }}</div>
                </div>
                <div v-if="job.recruiter_contact">
                  <div style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 2px;">Contato</div>
                  <div style="font-size: 0.82rem; color: var(--text-secondary);">{{ job.recruiter_contact }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Aviso de automação de follow-up ───────────────── -->
    <div style="display: flex; gap: 0.75rem; align-items: flex-start; padding: 1rem; background: rgba(59,130,246,0.06); border: 1px solid rgba(59,130,246,0.15); border-radius: 10px;">
      <i class="fa-solid fa-circle-info" style="font-size: 16px; color: #60a5fa; margin-top: 1px; flex-shrink: 0;"></i>
      <div style="font-size: 0.82rem; color: var(--text-secondary); line-height: 1.6;">
        <strong style="color: var(--text-primary);">Follow-up Automático Ativo:</strong> O Vaga Sync envia automaticamente mensagens de acompanhamento para vagas onde você foi inscrito, após 5 dias sem resposta — via WhatsApp, Telegram ou e-mail configurado nas Configurações. Os textos acima são para você enviar <em>manualmente</em> e de forma mais personalizada.
      </div>
    </div>
  </div>
</template>
