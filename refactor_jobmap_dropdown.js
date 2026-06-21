const fs = require('fs');

let content = fs.readFileSync('frontend/src/JobMap.vue', 'utf8');

// 1. Add new refs and logic
const scriptHook = `const requestLocation = () => {`;
const newLogic = `const selectedState = ref('');
const selectedCountry = ref('');

const zoomToRegion = (type, val) => {
  if (!val) {
    query.value = '';
    groupBy.value = 'state';
    return;
  }
  if (type === 'state') {
    selectedCountry.value = '';
    query.value = val;
    groupBy.value = 'city';
    if (STATE_COORDINATES[val] && mapInstanceRef.value) {
      mapInstanceRef.value.flyTo(STATE_COORDINATES[val], 6);
    }
  } else if (type === 'country') {
    selectedState.value = '';
    query.value = val;
    groupBy.value = 'state';
    if (COUNTRY_COORDINATES[val] && mapInstanceRef.value) {
      mapInstanceRef.value.flyTo(COUNTRY_COORDINATES[val], 4);
    }
  }
};

const requestLocation = () => {`;
content = content.replace(scriptHook, newLogic);

// 2. Replace the radar-controls in template
const radarControlsHook = `<div class="radar-controls" role="tablist" aria-label="Agrupar vagas">
      <button
        v-for="[value, label] in [['city', 'Cidade'], ['state', 'Estado'], ['country', 'Pais']]"
        :key="value"
        type="button"
        :class="{ active: groupBy === value }"
        @click="groupBy = value"
      >
        {{ label }}
      </button>
    </div>`;

const newRadarControls = `<div class="radar-controls" role="tablist" aria-label="Acessar locais" style="display: flex; gap: 1rem; flex-wrap: wrap; background: rgba(8, 12, 24, 0.4); padding: 1rem; border-radius: 12px; border: 1px solid var(--border-color); align-items: center;">
      <span style="color: var(--text-muted); font-size: 0.85rem; font-weight: 600;"><i class="fa-solid fa-filter"></i> Acessar Localização:</span>
      
      <select v-model="selectedState" @change="zoomToRegion('state', selectedState)" style="background: #0f172a; color: #fff; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 0.5rem 1rem; outline: none; min-width: 150px; font-size: 0.85rem; cursor: pointer;">
        <option value="">Selecione um Estado...</option>
        <option v-for="st in BR_STATES" :key="st[0]" :value="st[0]">{{ st[1] }}</option>
      </select>

      <select v-model="selectedCountry" @change="zoomToRegion('country', selectedCountry)" style="background: #0f172a; color: #fff; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 0.5rem 1rem; outline: none; min-width: 150px; font-size: 0.85rem; cursor: pointer;">
        <option value="">Selecione um País...</option>
        <option v-for="c in Object.keys(COUNTRY_COORDINATES)" :key="c" :value="c">{{ c }}</option>
      </select>

      <button 
        @click="requestLocation"
        :disabled="isLocating"
        style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); color: #10b981; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; transition: all 0.2s; margin-left: auto;"
      >
        <i :class="isLocating ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-location-crosshairs'" style="font-size: 16px;"></i>
        <span style="font-weight: 600; font-size: 0.85rem;">Usar Minha Localização Atual</span>
      </button>
    </div>`;
content = content.replace(radarControlsHook, newRadarControls);

// 3. Optional: Remove the other Vagas Próximas button from the search bar so there is only one
const oldSearchButtonHook = `<button 
          @click="requestLocation"
          :disabled="isLocating"
          style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); color: #10b981; padding: 0.75rem 1rem; border-radius: 8px; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; transition: all 0.2s;"
        >
          <i :class="isLocating ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-location-crosshairs'" style="font-size: 16px;"></i>
          <span style="font-weight: 600; font-size: 0.85rem;">Vagas Próximas</span>
        </button>`;
content = content.replace(oldSearchButtonHook, '');

fs.writeFileSync('frontend/src/JobMap.vue', content, 'utf8');
console.log("JobMap.vue dropdown selectors applied!");
