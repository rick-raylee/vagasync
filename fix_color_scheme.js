const fs = require('fs');

let content = fs.readFileSync('frontend/src/JobMap.vue', 'utf8');

const targetStyle = `.radar-select {
  background-color: #0f172a;`;

const replacementStyle = `.radar-select {
  color-scheme: dark;
  background-color: #0f172a;`;

content = content.replace(targetStyle, replacementStyle);
fs.writeFileSync('frontend/src/JobMap.vue', content, 'utf8');
console.log('Added color-scheme: dark');
