const fs = require('fs');

let content = fs.readFileSync('frontend/src/JobMap.vue', 'utf8');

const targetStr = `      if (COUNTRY_COORDINATES[country]) {
        baseLat = COUNTRY_COORDINATES[country][0];
        baseLng = COUNTRY_COORDINATES[country][1];
      }
      
      const lat = baseLat + (Math.random() - 0.5) * 5;
      const lng = baseLng + (Math.random() - 0.5) * 5;`;

const replaceStr = `      if (STATE_COORDINATES[state]) {
        baseLat = STATE_COORDINATES[state][0];
        baseLng = STATE_COORDINATES[state][1];
      } else if (COUNTRY_COORDINATES[country]) {
        baseLat = COUNTRY_COORDINATES[country][0];
        baseLng = COUNTRY_COORDINATES[country][1];
      }
      
      const lat = baseLat + (Math.random() - 0.5) * 1.5;
      const lng = baseLng + (Math.random() - 0.5) * 1.5;`;

content = content.replace(targetStr, replaceStr);

// Also we should clear the cache when we run this to force re-geocoding
const targetCacheStr = `localStorage.setItem('vagas_geocoded_cache', JSON.stringify(geocodedCache.value));`;
const replaceCacheStr = `localStorage.setItem('vagas_geocoded_cache', JSON.stringify(geocodedCache.value));`;

// Wait, clearing the cache can be done dynamically by just doing geocodedCache.value = {} if needed.
// I'll just change the cache key so it forces a new cache.
content = content.replace(/'vagas_geocoded_cache'/g, "'vagas_geocoded_cache_v2'");
content = content.replace(/localStorage\.getItem\('vagas_geocoded_cache'\)/g, "localStorage.getItem('vagas_geocoded_cache_v2')");

fs.writeFileSync('frontend/src/JobMap.vue', content, 'utf8');
console.log("Fixed mock geocoding coordinates!");
