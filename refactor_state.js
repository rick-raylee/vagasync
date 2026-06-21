const fs = require('fs');

let content = fs.readFileSync('frontend/src/App.vue', 'utf8');

const old_state = "const isPremium = ref(localStorage.getItem('vagasync_premium') === 'true');\nconst isRecruiterPro = ref(localStorage.getItem('vagasync_recruiter_pro') === 'true');";
const new_state = `const userFeatures = ref(JSON.parse(localStorage.getItem('vagasync_features')) || {
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
}, { deep: true });`;

content = content.replace(old_state, new_state);

content = content.replace("const checkoutPlan = ref(null);", "const checkoutPlan = ref(null);\nconst checkoutTitle = ref('');\nconst checkoutPrice = ref('');");

const old_open_checkout = `const openCheckout = (plan) => {
  checkoutPlan.value = plan;
  checkoutOpen.value = true;
};`;
const new_open_checkout = `const openCheckout = (plan, title = 'Upgrade Premium', price = 'R$ 0,00') => {
  checkoutPlan.value = plan;
  checkoutTitle.value = title;
  checkoutPrice.value = price;
  checkoutOpen.value = true;
};`;
content = content.replace(old_open_checkout, new_open_checkout);

const old_handler = `const handleCheckoutPayment = () => {
  checkoutProcessing.value = true;
  
  setTimeout(() => {
    checkoutProcessing.value = false;
    checkoutOpen.value = false;
    checkoutSuccess.value = true;
    
    if (checkoutPlan.value === 'candidate_premium') {
      isPremium.value = true;
      localStorage.setItem('vagasync_premium', 'true');
    } else if (checkoutPlan.value === 'recruiter_pro') {
      isRecruiterPro.value = true;
      localStorage.setItem('vagasync_recruiter_pro', 'true');
    }
    
    setTimeout(() => {
      checkoutSuccess.value = false;
    }, 3000);
  }, 2000);
};`;
const new_handler = `const handleCheckoutPayment = () => {
  checkoutProcessing.value = true;
  
  setTimeout(() => {
    checkoutProcessing.value = false;
    checkoutOpen.value = false;
    checkoutSuccess.value = true;
    
    if (checkoutPlan.value === 'impulsionar_vaga') {
        userFeatures.value.impulsionar_vaga_credits += 1;
    } else if (checkoutPlan.value) {
        userFeatures.value[checkoutPlan.value] = true;
    }
    
    setTimeout(() => {
      checkoutSuccess.value = false;
    }, 3000);
  }, 2000);
};`;
content = content.replace(old_handler, new_handler);

// Do a global replace for v-if uses
content = content.split('v-if="isRecruiterPro"').join('v-if="userFeatures.videoentrevistas"');
content = content.split('v-if="isPremium"').join('v-if="userFeatures.ia_ilimitada"');
content = content.split(':class="{ completed: isPremium }"').join(':class="{ completed: userFeatures.ia_ilimitada }"');
content = content.split("isRecruiterPro ? 'Recrutador Pro' : 'Gratuito'").join("userFeatures.ia_triagem ? 'Plano Avançado' : 'Gratuito'");
content = content.split("isRecruiterPro ? 'Recrutador Pro Enterprise' : 'Plano Gratuito de Recrutamento'").join("userFeatures.ia_triagem ? 'Selo de Empresa Verificada' : 'Plano Gratuito'");

// Modal titles
content = content.split('<div style="font-size: 1.1rem; font-weight: 700;">Plano SaaS Premium</div>').join('<div style="font-size: 1.1rem; font-weight: 700;">{{ checkoutTitle }}</div>');
content = content.split('<div style="font-size: 1.1rem; font-weight: 700; color: #10b981;">R$ 49,90<small>/mês</small></div>').join('<div style="font-size: 1.1rem; font-weight: 700; color: #10b981;">{{ checkoutPrice }}</div>');

fs.writeFileSync('frontend/src/App.vue', content, 'utf8');
console.log("State refactored in App.vue!");
