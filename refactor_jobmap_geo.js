const fs = require('fs');

let content = fs.readFileSync('frontend/src/JobMap.vue', 'utf8');

// Add "Minha Localização" logic
const importHook = `import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';`;
const newImportHook = `import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';\nimport { distance } from 'leaflet';`;

// Add isLocating ref
const refHook = `const groupBy = ref('state');`;
const newRefHook = `const groupBy = ref('state');\nconst isLocating = ref(false);\nconst userLocation = ref(null);`;
content = content.replace(refHook, newRefHook);

// Add location methods
const methodsHook = `const startGeocoding = () => {`;
const newMethodsHook = `const requestLocation = () => {
  if (!navigator.geolocation) {
    alert('Geolocalização não suportada pelo navegador.');
    return;
  }
  isLocating.value = true;
  navigator.geolocation.getCurrentPosition(
    (position) => {
      isLocating.value = false;
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      userLocation.value = { lat, lng };
      
      if (mapInstanceRef.value) {
        mapInstanceRef.value.flyTo([lat, lng], 11);
        L.marker([lat, lng], {
          icon: L.divIcon({
            html: '<div style="font-size: 28px; color: #10b981; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); animation: bounce 2s infinite;"><i class="fa-solid fa-street-view"></i></div>',
            className: ''
          }),
          zIndexOffset: 1000
        }).bindPopup('<b>Você está aqui!</b><br>Mostrando vagas próximas.').addTo(mapInstanceRef.value).openPopup();
      }
    },
    (error) => {
      isLocating.value = false;
      alert('Não foi possível obter sua localização. Verifique as permissões do navegador.');
    }
  );
};

const startGeocoding = () => {`;
content = content.replace(methodsHook, newMethodsHook);


// Add the button to the template
const templateHook = `<div class="radar-search">
        <i class="fa-solid fa-magnifying-glass" style="font-size: 15px;"></i>
        <input
          v-model="query"
          placeholder="Filtrar por vaga, empresa ou local"
        />
      </div>`;

const newTemplateHook = `<div class="radar-search" style="display: flex; gap: 0.5rem; align-items: center; background: transparent; padding: 0;">
        <div style="flex: 1; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.75rem;">
          <i class="fa-solid fa-magnifying-glass" style="font-size: 15px; color: var(--text-muted);"></i>
          <input
            v-model="query"
            placeholder="Filtrar por vaga, empresa ou local"
            style="background: transparent; border: none; color: #fff; width: 100%; outline: none;"
          />
        </div>
        <button 
          @click="requestLocation"
          :disabled="isLocating"
          style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); color: #10b981; padding: 0.75rem 1rem; border-radius: 8px; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; transition: all 0.2s;"
        >
          <i :class="isLocating ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-location-crosshairs'" style="font-size: 16px;"></i>
          <span style="font-weight: 600; font-size: 0.85rem;">Vagas Próximas</span>
        </button>
      </div>`;
content = content.replace(templateHook, newTemplateHook);

fs.writeFileSync('frontend/src/JobMap.vue', content, 'utf8');
console.log("JobMap.vue refactored for Geolocation!");
