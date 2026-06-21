const fs = require('fs');
let content = fs.readFileSync('frontend/src/JobMap.vue', 'utf8');

// Replace inline styles with class or better styles
const selectStateOld = `<select v-model="selectedState" @change="zoomToRegion('state', selectedState)" style="background: #0f172a; color: #fff; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 0.5rem 1rem; outline: none; min-width: 150px; font-size: 0.85rem; cursor: pointer;">
        <option value="">Selecione um Estado...</option>
        <option v-for="st in BR_STATES" :key="st[0]" :value="st[0]">{{ st[1] }}</option>
      </select>`;

const selectStateNew = `<select v-model="selectedState" @change="zoomToRegion('state', selectedState)" class="radar-select">
        <option value="" style="color: #fff; background: #0f172a;">Selecione um Estado...</option>
        <option v-for="st in BR_STATES" :key="st[0]" :value="st[0]" style="color: #fff; background: #0f172a;">{{ st[1] }}</option>
      </select>`;

content = content.replace(selectStateOld, selectStateNew);

const selectCountryOld = `<select v-model="selectedCountry" @change="zoomToRegion('country', selectedCountry)" style="background: #0f172a; color: #fff; border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 0.5rem 1rem; outline: none; min-width: 150px; font-size: 0.85rem; cursor: pointer;">
        <option value="">Selecione um País...</option>
        <option v-for="c in countryNames" :key="c" :value="c">{{ c }}</option>
      </select>`;

const selectCountryNew = `<select v-model="selectedCountry" @change="zoomToRegion('country', selectedCountry)" class="radar-select">
        <option value="" style="color: #fff; background: #0f172a;">Selecione um País...</option>
        <option v-for="c in countryNames" :key="c" :value="c" style="color: #fff; background: #0f172a;">{{ c }}</option>
      </select>`;

content = content.replace(selectCountryOld, selectCountryNew);

// Add the .radar-select class to the style tag
const styleOld = `</style>`;
const styleNew = `.radar-select {
  background-color: #0f172a;
  color: #ffffff;
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 8px;
  padding: 0.6rem 1rem;
  outline: none;
  min-width: 180px;
  font-size: 0.9rem;
  cursor: pointer;
  appearance: auto;
}
.radar-select:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}
</style>`;

content = content.replace(styleOld, styleNew);

fs.writeFileSync('frontend/src/JobMap.vue', content, 'utf8');
console.log("Fixed dropdown CSS!");
