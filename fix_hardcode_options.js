const fs = require('fs');

let content = fs.readFileSync('frontend/src/JobMap.vue', 'utf8');

const oldStateSelect = `<select v-model="selectedState" @change="zoomToRegion('state', selectedState)" class="radar-select">
        <option value="">Selecione um Estado...</option>
        <option v-for="st in BR_STATES" :key="st[0]" :value="st[0]">{{ st[1] }}</option>
      </select>`;

const newStateSelect = `<select v-model="selectedState" @change="zoomToRegion('state', selectedState)" class="radar-select">
        <option value="">Selecione um Estado...</option>
        <option value="AC">Acre</option>
        <option value="AL">Alagoas</option>
        <option value="AP">Amapa</option>
        <option value="AM">Amazonas</option>
        <option value="BA">Bahia</option>
        <option value="CE">Ceara</option>
        <option value="DF">Distrito Federal</option>
        <option value="ES">Espirito Santo</option>
        <option value="GO">Goias</option>
        <option value="MA">Maranhao</option>
        <option value="MT">Mato Grosso</option>
        <option value="MS">Mato Grosso do Sul</option>
        <option value="MG">Minas Gerais</option>
        <option value="PA">Para</option>
        <option value="PB">Paraiba</option>
        <option value="PR">Parana</option>
        <option value="PE">Pernambuco</option>
        <option value="PI">Piaui</option>
        <option value="RJ">Rio de Janeiro</option>
        <option value="RN">Rio Grande do Norte</option>
        <option value="RS">Rio Grande do Sul</option>
        <option value="RO">Rondonia</option>
        <option value="RR">Roraima</option>
        <option value="SC">Santa Catarina</option>
        <option value="SP">Sao Paulo</option>
        <option value="SE">Sergipe</option>
        <option value="TO">Tocantins</option>
      </select>`;

const oldCountriesSelect = `<select v-model="selectedCountry" @change="zoomToRegion('country', selectedCountry)" class="radar-select">
        <option value="">Selecione um Pas...</option>
        <option v-for="c in countryNames" :key="c" :value="c">{{ c }}</option>
      </select>`;

const newCountriesSelect = `<select v-model="selectedCountry" @change="zoomToRegion('country', selectedCountry)" class="radar-select">
        <option value="">Selecione um País...</option>
        <option value="Brasil">Brasil</option>
        <option value="Portugal">Portugal</option>
        <option value="Estados Unidos">Estados Unidos</option>
        <option value="Canada">Canada</option>
        <option value="Alemanha">Alemanha</option>
      </select>`;

content = content.replace(oldStateSelect, newStateSelect);
content = content.replace(oldCountriesSelect, newCountriesSelect);

fs.writeFileSync('frontend/src/JobMap.vue', content, 'utf8');
console.log("Hardcoded options into HTML");
