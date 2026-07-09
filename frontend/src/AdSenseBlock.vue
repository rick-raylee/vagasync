<template>
  <div ref="adContainer" class="adsbygoogle-container">
    <ins class="adsbygoogle"
      :style="style"
      :data-ad-client="client"
      :data-ad-slot="slot"
      :data-ad-format="format"
      :data-full-width-responsive="responsive"
    ></ins>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue';

const props = defineProps({
  style: { type: String, default: 'display:block; min-height: 90px;' },
  client: { type: String, default: 'ca-pub-1405601693512304' },
  slot: { type: String, default: 'auto' },
  format: { type: String, default: 'auto' },
  responsive: { type: String, default: 'true' }
});

const adContainer = ref(null);

onMounted(() => {
  try {
    (window.adsbygoogle = window.adsbygoogle || []).push({});
  } catch (e) {
    console.warn("Erro ao carregar bloco de anúncio:", e);
  }
});

onBeforeUnmount(() => {
  // Clear mutated DOM elements before Vue unmounts to prevent Virtual DOM mismatch crashes
  if (adContainer.value) {
    adContainer.value.innerHTML = '';
  }
});
</script>
