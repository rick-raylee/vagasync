<template>
  <!-- BottomNav: visible only on mobile via CSS -->
  <div class="bottom-nav-wrapper">

    <!-- Speed-Dial backdrop -->
    <div v-if="speedDialOpen" class="bottom-nav-backdrop" @click="speedDialOpen = false" />
    <!-- Overflow menu backdrop -->
    <div v-if="overflowOpen" class="bottom-nav-backdrop" @click="overflowOpen = false" />
    <!-- Context menu backdrop -->
    <div v-if="contextMenu.visible" class="bottom-nav-backdrop" @click="contextMenu.visible = false" />

    <!-- Speed Dial Actions -->
    <div v-if="speedDialOpen" class="speed-dial-container animate-scale">
      <button
        v-for="(action, i) in speedDialActions"
        :key="action.id"
        class="speed-dial-item"
        :style="{ animationDelay: `${i * 0.05}s` }"
        @click="handleSpeedDialAction(action)"
      >
        <span class="speed-dial-icon" v-html="action.icon" />
        <span class="speed-dial-label">{{ action.label }}</span>
      </button>
    </div>

    <!-- Overflow dropdown menu -->
    <div v-if="overflowOpen" class="overflow-menu animate-slide-up">
      <div class="overflow-header">
        <div class="overflow-avatar" :class="{ recruiter: userRole === 'recruiter', admin: userRole === 'super_admin' }">{{ userInitials }}</div>
        <div class="overflow-user-info">
          <span class="overflow-user-name">{{ displayName }}</span>
          <span class="overflow-user-role">{{ roleLabel }}</span>
        </div>
      </div>
      <div class="overflow-divider" />
      <button v-for="item in overflowItems" :key="item.id" class="overflow-item" @click="handleOverflowAction(item)">
        <span v-html="item.icon" /><span>{{ item.label }}</span>
      </button>
      <div class="overflow-divider" />
      <button class="overflow-item overflow-logout" @click="handleLogoutAction">
        <span v-html="logoutIcon" /><span>Sair da Conta</span>
      </button>
    </div>

    <!-- Context menu -->
    <div v-if="contextMenu.visible" class="context-menu animate-slide-up" :style="{ left: contextMenu.x + 'px' }">
      <div class="context-menu-title">{{ contextMenu.item && contextMenu.item.label }}</div>
      <div class="overflow-divider" />
      <button v-for="action in contextMenu.actions" :key="action.id" class="overflow-item" @click="action.fn(); contextMenu.visible = false">
        <span v-html="action.icon" /><span>{{ action.label }}</span>
      </button>
    </div>

    <!-- Bottom Navigation Bar -->
    <nav class="bottom-nav">
      <button
        v-for="item in visibleNavItems"
        :key="item.tab"
        class="bottom-nav-item"
        :class="{ active: activeTab === item.tab }"
        @click="navigate(item)"
      >
        <div class="bottom-nav-icon-wrap">
          <span class="bottom-nav-icon" v-html="item.icon" />
          <span v-if="item.badge && item.badge > 0" class="bottom-nav-badge">{{ item.badge > 99 ? '99+' : item.badge }}</span>
        </div>
        <span class="bottom-nav-label">{{ item.label }}</span>
        <span v-if="activeTab === item.tab" class="bottom-nav-active-pill" />
      </button>

      <!-- Speed Dial FAB -->
      <div class="bottom-nav-fab-wrap">
        <button class="bottom-nav-fab" :class="{ open: speedDialOpen }" @click="speedDialOpen = !speedDialOpen" aria-label="Acoes rapidas">
          <svg class="fab-plus" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </button>
      </div>

      <!-- Overflow / User button -->
      <button class="bottom-nav-item" :class="{ active: overflowOpen }" @click="overflowOpen = !overflowOpen" aria-label="Mais opcoes">
        <div class="bottom-nav-icon-wrap">
          <div class="bottom-nav-avatar" :class="{ recruiter: userRole === 'recruiter', admin: userRole === 'super_admin' }">{{ userInitials }}</div>
        </div>
        <span class="bottom-nav-label" style="font-size:0.6rem;margin-top:2px;">{{ firstWord }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue';

const props = defineProps({
  activeTab:          { type: String,  default: 'dashboard' },
  userRole:           { type: String,  default: 'candidate' },
  isLoggedIn:         { type: Boolean, default: false },
  userName:           { type: String,  default: '' },
  jobsCount:          { type: Number,  default: 0 },
  messagesCount:      { type: Number,  default: 0 },
  notificationsCount: { type: Number,  default: 0 }
});

const emit = defineEmits(['navigate', 'logout', 'speed-dial-action']);

const speedDialOpen = ref(false);
const overflowOpen  = ref(false);
const contextMenu   = ref({ visible: false, x: 0, item: null, actions: [] });
let longPressTimer  = null;

const displayName = computed(() => {
  const name = props.userName || '';
  if (typeof name === 'string' && name.trim()) return name;
  if (props.userRole === 'recruiter')   return 'Recrutador';
  if (props.userRole === 'super_admin') return 'Administrador';
  return 'Candidato';
});

const firstWord = computed(() => {
  const name = displayName.value || '';
  return name.split(' ')[0] || '';
});

const userInitials = computed(() => {
  const name = displayName.value || '';
  const parts = name.trim().split(' ').filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
});

const roleLabel = computed(() => {
  if (props.userRole === 'recruiter')   return 'Recrutador Pro';
  if (props.userRole === 'super_admin') return 'Super Admin';
  return 'Candidato';
});

const iconDashboard   = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>';
const iconMap         = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/></svg>';
const iconMsg         = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';
const iconAI          = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>';
const iconChart       = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>';
const iconPlus        = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/></svg>';
const iconLayers      = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>';
const iconGlobe       = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>';
const iconMoney       = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>';
const iconShield      = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>';
const iconPin         = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>';
const iconSearch      = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>';
const iconFile        = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';
const iconMic         = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v1a7 7 0 0 1-14 0v-1"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>';
const iconUser        = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>';
const iconBell        = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>';
const iconCard        = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>';
const iconUsers       = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>';
const iconBar         = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>';
const logoutIcon      = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>';

const candidateItems = computed(() => [
  { tab: 'dashboard', label: 'Painel',      icon: iconDashboard, badge: 0, contextActions: [{ id: 'r', label: 'Atualizar', icon: iconSearch, fn: () => emit('navigate', 'dashboard') }] },
  { tab: 'map',       label: 'Vagas',       icon: iconMap,       badge: props.jobsCount, contextActions: [{ id: 'f', label: 'Filtrar vagas', icon: iconSearch, fn: () => emit('navigate', 'map') }] },
  { tab: 'messenger', label: 'Mensagens',   icon: iconMsg,       badge: props.messagesCount, contextActions: [] },
  { tab: 'career',    label: 'Copiloto IA', icon: iconAI,        badge: 0, contextActions: [] }
]);

const recruiterItems = computed(() => [
  { tab: 'recruiter_dashboard',  label: 'Painel',      icon: iconChart,  badge: 0, contextActions: [] },
  { tab: 'recruiter_jobs',       label: 'Vagas',       icon: iconPlus,   badge: 0, contextActions: [] },
  { tab: 'messenger',            label: 'Mensagens',   icon: iconMsg,    badge: props.messagesCount, contextActions: [] },
  { tab: 'recruiter_assessments',label: 'Testes',      icon: iconLayers, badge: 0, contextActions: [] }
]);

const adminItems = computed(() => [
  { tab: 'super_admin',                label: 'Global',      icon: iconGlobe,  badge: 0, contextActions: [] },
  { tab: 'super_admin_monetization',   label: 'Monetização', icon: iconMoney,  badge: 0, contextActions: [] },
  { tab: 'super_admin_security',       label: 'Segurança',   icon: iconShield, badge: 0, contextActions: [] },
  { tab: 'super_admin_tracking',       label: 'Tracking',    icon: iconPin,    badge: 0, contextActions: [] }
]);

const visibleNavItems = computed(() => {
  if (props.userRole === 'recruiter')   return recruiterItems.value;
  if (props.userRole === 'super_admin') return adminItems.value;
  return candidateItems.value;
});

const speedDialActions = computed(() => {
  if (props.userRole === 'recruiter')   return [
    { id: 'nova_vaga',   label: 'Criar Nova Vaga',    icon: iconPlus },
    { id: 'triagem',     label: 'Triagem IA',         icon: iconAI },
    { id: 'msg',         label: 'Enviar Mensagem',    icon: iconMsg }
  ];
  if (props.userRole === 'super_admin') return [
    { id: 'usuarios',   label: 'Ver Usuarios',        icon: iconUsers },
    { id: 'relatorio',  label: 'Relatorio Global',    icon: iconBar }
  ];
  return [
    { id: 'busca_vaga',  label: 'Buscar Vagas',       icon: iconSearch },
    { id: 'curriculo',   label: 'Atualizar Curriculo', icon: iconFile },
    { id: 'entrevista',  label: 'Treinar Entrevista',  icon: iconMic }
  ];
});

const overflowItems = computed(() => {
  const base = [
    { id: 'profile', label: 'Meu Perfil',     icon: iconUser, tab: 'config' },
    { id: 'notif',   label: 'Notificacoes',   icon: iconBell, tab: null }
  ];
  if (props.userRole === 'candidate') base.push({ id: 'billing', label: 'Faturamento & Planos', icon: iconCard, tab: 'candidate_billing' });
  if (props.userRole === 'recruiter') base.push({ id: 'billing', label: 'Faturamento SaaS',     icon: iconCard, tab: 'recruiter_billing' });
  return base;
});

function navigate(item) { emit('navigate', item.tab); }
function handleSpeedDialAction(action) { speedDialOpen.value = false; emit('speed-dial-action', action.id); }
function handleOverflowAction(item) { overflowOpen.value = false; if (item.tab) emit('navigate', item.tab); }
function handleLogoutAction() { overflowOpen.value = false; emit('logout'); }

function showContextMenu(event, item) {
  if (!item.contextActions || item.contextActions.length === 0) return;
  const rect = event.currentTarget.getBoundingClientRect();
  contextMenu.value = {
    visible: true,
    x: Math.max(8, Math.min(rect.left, window.innerWidth - 188)),
    item,
    actions: item.contextActions
  };
}

function startLongPress(event, item) {
  cancelLongPress();
  longPressTimer = setTimeout(() => showContextMenu(event, item), 500);
}
function cancelLongPress() {
  if (longPressTimer) { clearTimeout(longPressTimer); longPressTimer = null; }
}
onBeforeUnmount(cancelLongPress);
</script>

<style scoped>
.bottom-nav-wrapper { display: none; position: fixed; bottom: 0; left: 0; right: 0; z-index: 99999 !important; pointer-events: auto !important; }
@media (max-width: 768px) { .bottom-nav-wrapper { display: block; } }

.bottom-nav-backdrop { position: fixed; inset: 0; z-index: 998; background: rgba(6,9,19,0.55); backdrop-filter: blur(2px); }

.bottom-nav {
  display: flex; align-items: center; justify-content: space-around;
  padding: 0.4rem 0.25rem calc(0.4rem + env(safe-area-inset-bottom));
  background: rgba(10,15,28,0.92); backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
  border-top: 1px solid rgba(59,130,246,0.18);
  box-shadow: 0 -4px 24px rgba(0,0,0,0.5), 0 -1px 0 rgba(0,242,254,0.06);
  position: relative; z-index: 99999 !important; pointer-events: auto !important;
}

.bottom-nav-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  min-width: 52px; padding: 0.35rem 0.5rem 0.2rem;
  background: transparent; border: none; cursor: pointer;
  border-radius: 14px; position: relative;
  transition: background 0.2s ease, transform 0.15s ease;
  -webkit-tap-highlight-color: transparent;
  pointer-events: auto !important;
  transition: background 0.2s ease, transform 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}
.bottom-nav-item:active { transform: scale(0.9); }
.bottom-nav-item.active { background: rgba(59,130,246,0.12); }

.bottom-nav-icon-wrap { position: relative; width: 26px; height: 26px; display: flex; align-items: center; justify-content: center; }
.bottom-nav-icon { display: flex; align-items: center; justify-content: center; }
.bottom-nav-icon :deep(svg) { width: 22px; height: 22px; stroke: rgba(148,163,184,0.8); transition: stroke 0.2s ease, filter 0.2s ease; }
.bottom-nav-item.active .bottom-nav-icon :deep(svg) { stroke: #00f2fe; filter: drop-shadow(0 0 6px rgba(0,242,254,0.55)); }

.bottom-nav-label { font-size: 0.62rem; font-weight: 500; color: rgba(148,163,184,0.75); transition: color 0.2s; white-space: nowrap; }
.bottom-nav-item.active .bottom-nav-label { color: #00f2fe; font-weight: 700; }

.bottom-nav-active-pill { position: absolute; bottom: -2px; left: 50%; transform: translateX(-50%); width: 18px; height: 3px; border-radius: 2px; background: linear-gradient(90deg,#3b82f6,#00f2fe); box-shadow: 0 0 8px rgba(0,242,254,0.6); }

.bottom-nav-badge { position: absolute; top: -5px; right: -7px; min-width: 17px; height: 17px; border-radius: 9px; background: linear-gradient(135deg,#ef4444,#f59e0b); color: #fff; font-size: 0.58rem; font-weight: 800; display: flex; align-items: center; justify-content: center; padding: 0 3px; box-shadow: 0 0 6px rgba(239,68,68,0.5); border: 1.5px solid rgba(10,15,28,0.9); }

.bottom-nav-avatar { width: 26px; height: 26px; border-radius: 50%; background: linear-gradient(135deg,#3b82f6,#00f2fe); color: #060913; font-size: 0.7rem; font-weight: 800; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px rgba(0,242,254,0.3); border: 1.5px solid rgba(0,242,254,0.4); }
.bottom-nav-avatar.recruiter { background: linear-gradient(135deg,#a855f7,#7c3aed); box-shadow: 0 0 10px rgba(168,85,247,0.4); border-color: rgba(168,85,247,0.5); }
.bottom-nav-avatar.admin     { background: linear-gradient(135deg,#ef4444,#f59e0b); box-shadow: 0 0 10px rgba(239,68,68,0.4); border-color: rgba(239,68,68,0.5); }

.bottom-nav-fab-wrap { display: flex; align-items: center; justify-content: center; position: relative; z-index: 1002; margin-top: -24px; }
.bottom-nav-fab { width: 54px; height: 54px; border-radius: 50%; border: none; background: linear-gradient(135deg,#3b82f6,#00f2fe); color: #060913; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 4px 20px rgba(0,242,254,0.5), 0 0 0 3px rgba(0,242,254,0.12); transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.3s ease; -webkit-tap-highlight-color: transparent; }
.bottom-nav-fab:active { transform: scale(0.88); }
.bottom-nav-fab.open { transform: rotate(45deg) scale(1.05); box-shadow: 0 6px 28px rgba(0,242,254,0.7), 0 0 0 4px rgba(0,242,254,0.2); }
.fab-plus { width: 24px; height: 24px; stroke: #060913; }

.speed-dial-container { position: fixed; bottom: 90px; left: 50%; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; gap: 0.65rem; z-index: 999; }
.speed-dial-item { display: flex; align-items: center; gap: 0.65rem; padding: 0.65rem 1rem; background: rgba(13,20,42,0.97); border: 1px solid rgba(59,130,246,0.3); border-radius: 28px; color: #e2e8f0; cursor: pointer; backdrop-filter: blur(12px); box-shadow: 0 4px 20px rgba(0,0,0,0.4); white-space: nowrap; animation: fabItemIn 0.25s ease both; transition: background 0.2s ease, transform 0.15s ease; -webkit-tap-highlight-color: transparent; }
.speed-dial-item:active { transform: scale(0.94); background: rgba(59,130,246,0.15); }
.speed-dial-icon { display: flex; align-items: center; width: 20px; height: 20px; flex-shrink: 0; }
.speed-dial-icon :deep(svg) { width: 18px; height: 18px; stroke: #00f2fe; }
.speed-dial-label { font-size: 0.82rem; font-weight: 600; color: #cbd5e1; }
@keyframes fabItemIn { from { opacity:0; transform: translateY(10px) scale(0.9); } to { opacity:1; transform: translateY(0) scale(1); } }

.overflow-menu { position: fixed; bottom: calc(72px + env(safe-area-inset-bottom)); right: 8px; width: min(300px, calc(100vw - 16px)); background: rgba(10,15,28,0.98); border: 1px solid rgba(59,130,246,0.2); border-radius: 18px; padding: 1rem; display: flex; flex-direction: column; gap: 0.25rem; box-shadow: 0 -4px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(0,242,254,0.06); backdrop-filter: blur(20px); z-index: 999; }
.overflow-header { display: flex; align-items: center; gap: 0.75rem; padding-bottom: 0.75rem; }
.overflow-avatar { width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg,#3b82f6,#00f2fe); color: #060913; font-size: 1rem; font-weight: 800; display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 0 14px rgba(0,242,254,0.35); border: 2px solid rgba(0,242,254,0.3); }
.overflow-avatar.recruiter { background: linear-gradient(135deg,#a855f7,#7c3aed); }
.overflow-avatar.admin     { background: linear-gradient(135deg,#ef4444,#f59e0b); }
.overflow-user-info { display: flex; flex-direction: column; gap: 2px; }
.overflow-user-name { font-size: 0.9rem; font-weight: 700; color: #f1f5f9; }
.overflow-user-role { font-size: 0.72rem; font-weight: 500; color: #00f2fe; background: rgba(0,242,254,0.08); padding: 1px 8px; border-radius: 10px; width: fit-content; }
.overflow-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 0.35rem 0; }
.overflow-item { display: flex; align-items: center; gap: 0.65rem; padding: 0.65rem 0.75rem; border: none; background: transparent; color: #94a3b8; border-radius: 10px; cursor: pointer; font-size: 0.83rem; font-weight: 500; transition: background 0.15s ease, color 0.15s ease; text-align: left; -webkit-tap-highlight-color: transparent; }
.overflow-item:active, .overflow-item:hover { background: rgba(59,130,246,0.1); color: #e2e8f0; }
.overflow-item :deep(svg) { width: 16px; height: 16px; stroke: #64748b; flex-shrink: 0; transition: stroke 0.15s; }
.overflow-item:hover :deep(svg), .overflow-item:active :deep(svg) { stroke: #3b82f6; }
.overflow-logout { color: #f87171; }
.overflow-logout :deep(svg) { stroke: #f87171; }
.overflow-logout:hover, .overflow-logout:active { background: rgba(239,68,68,0.1); color: #fca5a5; }

.context-menu { position: fixed; bottom: calc(72px + env(safe-area-inset-bottom)); min-width: 180px; background: rgba(10,15,28,0.98); border: 1px solid rgba(59,130,246,0.25); border-radius: 14px; padding: 0.75rem; display: flex; flex-direction: column; gap: 0.15rem; box-shadow: 0 -4px 24px rgba(0,0,0,0.5); backdrop-filter: blur(16px); z-index: 999; }
.context-menu-title { font-size: 0.78rem; font-weight: 700; color: #00f2fe; padding: 0 0.25rem 0.4rem; }

.animate-scale {
  animation: fabScaleIn 0.2s ease both;
}
@keyframes fabScaleIn {
  from { opacity: 0; transform: translateX(-50%) scale(0.85); }
  to { opacity: 1; transform: translateX(-50%) scale(1); }
}

.animate-slide-up {
  animation: slideUpIn 0.22s cubic-bezier(0.22,1,0.36,1) both;
}
@keyframes slideUpIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
