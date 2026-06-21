const fs = require('fs');

let content = fs.readFileSync('frontend/src/Messenger.vue', 'utf8');

// 1. Add share location method
const scriptEnd = `const copyToClipboard = (text, fieldName) => {`;
const shareLocationLogic = `const isLocating = ref(false);

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
      inputText.value = \`📍 Minha localização atual é: LAT \${lat}, LNG \${lng}. Gere recomendações de vagas ou alertas personalizados próximos a mim.\`;
    },
    (error) => {
      isLocating.value = false;
      props.showToast('Erro', 'Não foi possível obter sua localização. Permita o acesso.', 'error');
    }
  );
};

const copyToClipboard = (text, fieldName) => {`;
content = content.replace(scriptEnd, shareLocationLogic);

// 2. Add AI reply logic for geolocation
const oldAiLogic = `  } else if (text.includes('ajuda') || text.includes('como funciona') || text.includes('olá') || text.includes('ola') || text.includes('bom dia')) {`;
const newAiLogic = `  } else if (text.includes('localização') || text.includes('lat') || text.includes('lng')) {
    reply = \`Excelente! Acabei de mapear suas coordenadas. 📍\\n\\n\` +
      \`Com base na sua região, encontrei um aquecimento no mercado local para as seguintes áreas:\\n\\n\` +
      \`• **Empresas de Tecnologia na Região**: Há um polo de inovação contratando modelos híbridos.\\n\` +
      \`• **Alertas Ativados**: Configurei o Radar VagaSync para notificar você quando surgirem vagas presenciais ou híbridas em um raio de 25km.\\n\\n\` +
      \`Deseja que eu filtre vagas 100% remotas ou foque nas oportunidades presenciais próximas a você?\`;
  } else if (text.includes('ajuda') || text.includes('como funciona') || text.includes('olá') || text.includes('ola') || text.includes('bom dia')) {`;
content = content.replace(oldAiLogic, newAiLogic);

// 3. Add button to the form
const oldForm = `        <form
          @submit="handleSendMessage"
          style="
            padding: 1rem 1.5rem;
            border-top: 1px solid var(--border-color);
            background: rgba(10, 15, 30, 0.4);
            display: flex;
            gap: 0.75rem;
            align-items: center;
          "
        >
          <input
            type="text"`;

const newForm = `        <form
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
          
          <input
            type="text"`;

content = content.replace(oldForm, newForm);

// Make sure handleSendMessage doesn't conflict by replacing @submit with @submit.prevent if not already
content = content.replace('@submit="handleSendMessage"', '@submit.prevent="handleSendMessage"');

fs.writeFileSync('frontend/src/Messenger.vue', content, 'utf8');
console.log("Messenger updated with Geolocation!");
