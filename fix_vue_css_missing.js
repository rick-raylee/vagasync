const fs = require('fs');

const styleBlock = `
<style scoped>
.radar-select {
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
</style>
`;

fs.appendFileSync('frontend/src/JobMap.vue', styleBlock, 'utf8');
console.log('Appended style to JobMap.vue');
