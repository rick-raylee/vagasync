const fs = require('fs');

let content = fs.readFileSync('frontend/src/Messenger.vue', 'utf8');

// 1. Add Speech Recognition logic
const isLocatingSetup = `const isLocating = ref(false);`;
const speechLogic = `const isLocating = ref(false);
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
`;

content = content.replace(isLocatingSetup, speechLogic);

// 2. Add microphone button to the form
const locBtnEnd = `            <i :class="isLocating ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-location-crosshairs'" style="font-size: 16px;"></i>
          </button>`;

const newBtns = `            <i :class="isLocating ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-location-crosshairs'" style="font-size: 16px;"></i>
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
          </button>`;

content = content.replace(locBtnEnd, newBtns);

fs.writeFileSync('frontend/src/Messenger.vue', content, 'utf8');
console.log("Messenger updated with Speech Recognition!");
