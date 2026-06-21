import re

with open('frontend/src/App.vue', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace state declarations
old_state = "const isPremium = ref(localStorage.getItem('vagasync_premium') === 'true');\nconst isRecruiterPro = ref(localStorage.getItem('vagasync_recruiter_pro') === 'true');"
new_state = """const userFeatures = ref(JSON.parse(localStorage.getItem('vagasync_features')) || {
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
}, { deep: true });"""
content = content.replace(old_state, new_state)

# 2. Update checkout state variables
content = content.replace("const checkoutPlan = ref(null);", "const checkoutPlan = ref(null);\nconst checkoutTitle = ref('');\nconst checkoutPrice = ref('');")

# 3. Update openCheckout function
old_open_checkout = """const openCheckout = (plan) => {
  checkoutPlan.value = plan;
  checkoutOpen.value = true;
};"""
new_open_checkout = """const openCheckout = (plan, title = 'Upgrade Premium', price = 'R$ 0,00') => {
  checkoutPlan.value = plan;
  checkoutTitle.value = title;
  checkoutPrice.value = price;
  checkoutOpen.value = true;
};"""
content = content.replace(old_open_checkout, new_open_checkout)

# 4. Update checkout_handler
old_handler = """const handleCheckoutPayment = () => {
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
};"""
new_handler = """const handleCheckoutPayment = () => {
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
};"""
content = content.replace(old_handler, new_handler)

# 5. Replace v-if uses
content = content.replace('v-if="isRecruiterPro"', 'v-if="userFeatures.videoentrevistas"')
content = content.replace('v-if="isPremium"', 'v-if="userFeatures.ia_ilimitada"')
content = content.replace(':class="{ completed: isPremium }"', ':class="{ completed: userFeatures.ia_ilimitada }"')
content = content.replace("isRecruiterPro ? 'Recrutador Pro' : 'Gratuito'", "userFeatures.ia_triagem ? 'Plano Avançado' : 'Gratuito'")
content = content.replace("isRecruiterPro ? 'Recrutador Pro Enterprise' : 'Plano Gratuito de Recrutamento'", "userFeatures.ia_triagem ? 'Selo de Empresa Verificada' : 'Plano Gratuito'")

# 6. Replace Checkout Modal text
content = content.replace('<div style="font-size: 1.1rem; font-weight: 700;">Plano SaaS Premium</div>', '<div style="font-size: 1.1rem; font-weight: 700;">{{ checkoutTitle }}</div>')
content = content.replace('<div style="font-size: 1.1rem; font-weight: 700; color: #10b981;">R$ 49,90<small>/mês</small></div>', '<div style="font-size: 1.1rem; font-weight: 700; color: #10b981;">{{ checkoutPrice }}</div>')

with open('frontend/src/App.vue', 'w', encoding='utf-8') as f:
    f.write(content)
print("State script completed.")
