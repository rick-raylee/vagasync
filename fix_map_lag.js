const fs = require('fs');

let content = fs.readFileSync('frontend/src/JobMap.vue', 'utf8');

const oldStartGeocoding = `const startGeocoding = () => {
  const countriesToSkip = ['brasil', 'brazil', 'portugal', 'estados unidos', 'united states', 'usa', 'eua', 'canada', 'alemanha', 'germany', 'reino unido', 'united kingdom', 'uk', 'franca', 'france', 'espanha', 'spain', 'italia', 'italy', 'japao', 'japan', 'australia', 'china', 'india', 'argentina', 'chile', 'colombia', 'mexico', 'internacional', 'worldwide', 'global'];

  const addressesToGeocode = safeJobs.value
    .map(j => j.company_address || j.location)
    .filter(addr => {
      if (!addr) return false;
      const norm = addr.toLowerCase().trim();
      if (norm.includes('remoto') || norm.includes('remote')) return false;
      if (countriesToSkip.includes(norm)) return false;
      return !geocodedCache.value[addr];
    });

  const uniqueAddresses = [...new Set(addressesToGeocode)];
  if (uniqueAddresses.length === 0) return;

  let index = 0;

  const geocodeNext = async () => {
    if (index >= uniqueAddresses.length || !isGeocodingActive) return;
    const addr = uniqueAddresses[index];

    try {
      // Instant Local Geocoding Simulation
      const state = detectState(addr);
      const country = detectCountry(addr);
      
      let baseLat = -14.235;
      let baseLng = -51.925;
      
      if (COUNTRY_COORDINATES[country]) {
        baseLat = COUNTRY_COORDINATES[country][0];
        baseLng = COUNTRY_COORDINATES[country][1];
      }
      
      // Randomize slightly around the base coordinate to scatter jobs
      const lat = baseLat + (Math.random() - 0.5) * 5;
      const lng = baseLng + (Math.random() - 0.5) * 5;
      
      const referencePoints = [\`Região de \${addr}\`];
      
      const cacheEntry = {
        lat,
        lng,
        displayName: addr,
        referencePoints,
        rawAddress: addr
      };

      geocodedCache.value = {
        ...geocodedCache.value,
        [addr]: cacheEntry
      };
      localStorage.setItem('vagas_geocoded_cache', JSON.stringify(geocodedCache.value));
    } catch (err) {
      console.error('Erro na geocodificação para:', addr, err);
    }

    index++;
    // Use instant timeout for blazing fast map loading
    geocodeTimeout = setTimeout(geocodeNext, 5);
  };

  geocodeNext();
};`;

const newStartGeocoding = `const startGeocoding = () => {
  const countriesToSkip = ['brasil', 'brazil', 'portugal', 'estados unidos', 'united states', 'usa', 'eua', 'canada', 'alemanha', 'germany', 'reino unido', 'united kingdom', 'uk', 'franca', 'france', 'espanha', 'spain', 'italia', 'italy', 'japao', 'japan', 'australia', 'china', 'india', 'argentina', 'chile', 'colombia', 'mexico', 'internacional', 'worldwide', 'global'];

  const addressesToGeocode = safeJobs.value
    .map(j => j.company_address || j.location)
    .filter(addr => {
      if (!addr) return false;
      const norm = addr.toLowerCase().trim();
      if (norm.includes('remoto') || norm.includes('remote')) return false;
      if (countriesToSkip.includes(norm)) return false;
      return !geocodedCache.value[addr];
    });

  const uniqueAddresses = [...new Set(addressesToGeocode)];
  if (uniqueAddresses.length === 0) return;

  // Process all simultaneously to avoid UI blocking with setTimeout loop
  const newCacheEntries = {};

  uniqueAddresses.forEach(addr => {
    try {
      const state = detectState(addr);
      const country = detectCountry(addr);
      
      let baseLat = -14.235;
      let baseLng = -51.925;
      
      if (COUNTRY_COORDINATES[country]) {
        baseLat = COUNTRY_COORDINATES[country][0];
        baseLng = COUNTRY_COORDINATES[country][1];
      }
      
      const lat = baseLat + (Math.random() - 0.5) * 5;
      const lng = baseLng + (Math.random() - 0.5) * 5;
      
      newCacheEntries[addr] = {
        lat,
        lng,
        displayName: addr,
        referencePoints: [\`Região de \${addr}\`],
        rawAddress: addr
      };
    } catch (err) {
      console.error('Erro na geocodificação para:', addr, err);
    }
  });

  // Assign and save to LocalStorage ONCE to prevent lag
  geocodedCache.value = { ...geocodedCache.value, ...newCacheEntries };
  localStorage.setItem('vagas_geocoded_cache', JSON.stringify(geocodedCache.value));
};`;

content = content.replace(oldStartGeocoding, newStartGeocoding);
fs.writeFileSync('frontend/src/JobMap.vue', content, 'utf8');
console.log('Fixed Map Loading Lag!');
