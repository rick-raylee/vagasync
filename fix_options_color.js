const fs = require('fs');

let content = fs.readFileSync('frontend/src/JobMap.vue', 'utf8');

// Clean inline styles from options
content = content.replace(
  /<option value="" style="color: #fff; background: #0f172a;">/g,
  '<option value="">'
);
content = content.replace(
  /<option v-for="st in BR_STATES" :key="st\[0\]" :value="st\[0\]" style="color: #fff; background: #0f172a;">/g,
  '<option v-for="st in BR_STATES" :key="st[0]" :value="st[0]">'
);
content = content.replace(
  /<option v-for="c in countryNames" :key="c" :value="c" style="color: #fff; background: #0f172a;">/g,
  '<option v-for="c in countryNames" :key="c" :value="c">'
);

// Add option styling to the scoped style block
const styleTarget = `.radar-select {`;
const styleReplacement = `.radar-select option {
  color: #111827;
  background-color: #ffffff;
  padding: 8px;
}
.radar-select {`;

content = content.replace(styleTarget, styleReplacement);

fs.writeFileSync('frontend/src/JobMap.vue', content, 'utf8');
console.log('Fixed `<option>` readability bug.');
