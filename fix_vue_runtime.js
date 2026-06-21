const fs = require('fs');
let content = fs.readFileSync('frontend/src/JobMap.vue', 'utf8');

// Define countryNames in script
content = content.replace(
  `const selectedCountry = ref('');`,
  `const selectedCountry = ref('');\nconst countryNames = Object.keys(COUNTRY_COORDINATES);`
);

// Replace Object.keys in template
content = content.replace(
  `<option v-for="c in Object.keys(COUNTRY_COORDINATES)" :key="c" :value="c">{{ c }}</option>`,
  `<option v-for="c in countryNames" :key="c" :value="c">{{ c }}</option>`
);

fs.writeFileSync('frontend/src/JobMap.vue', content, 'utf8');
console.log("Fixed runtime error for Object.keys");
