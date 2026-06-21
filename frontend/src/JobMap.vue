<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import * as L from 'leaflet';
// Lucide icons replaced with FontAwesome

const props = defineProps({
  jobs: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['select-job']);

window.selectJobFromMap = (jobId) => {
  emit('select-job', jobId);
};

const BR_STATES = [
  ['AC', 'Acre'], ['AL', 'Alagoas'], ['AP', 'Amapa'], ['AM', 'Amazonas'],
  ['BA', 'Bahia'], ['CE', 'Ceara'], ['DF', 'Distrito Federal'],
  ['ES', 'Espirito Santo'], ['GO', 'Goias'], ['MA', 'Maranhao'],
  ['MT', 'Mato Grosso'], ['MS', 'Mato Grosso do Sul'], ['MG', 'Minas Gerais'],
  ['PA', 'Para'], ['PB', 'Paraiba'], ['PR', 'Parana'], ['PE', 'Pernambuco'],
  ['PI', 'Piaui'], ['RJ', 'Rio de Janeiro'], ['RN', 'Rio Grande do Norte'],
  ['RS', 'Rio Grande do Sul'], ['RO', 'Rondonia'], ['RR', 'Roraima'],
  ['SC', 'Santa Catarina'], ['SP', 'Sao Paulo'], ['SE', 'Sergipe'],
  ['TO', 'Tocantins']
];

const STATE_ALIASES = {
  'sao paulo': 'SP',
  'rio de janeiro': 'RJ',
  'minas gerais': 'MG',
  'parana': 'PR',
  'rio grande do sul': 'RS',
  'santa catarina': 'SC',
  'bahia': 'BA',
  'pernambuco': 'PE',
  'ceara': 'CE',
  'goias': 'GO',
  'distrito federal': 'DF',
  'espirito santo': 'ES'
};

const STATE_COORDINATES = {
  'AC': [-9.0238, -70.5266],
  'AL': [-9.5713, -36.7820],
  'AP': [1.4098, -51.7719],
  'AM': [-3.4168, -64.1830],
  'BA': [-12.5797, -41.7007],
  'CE': [-5.1764, -39.7432],
  'DF': [-15.7998, -47.8645],
  'ES': [-19.1834, -40.3089],
  'GO': [-15.8270, -49.8378],
  'MA': [-5.4745, -45.3605],
  'MT': [-12.6819, -56.9211],
  'MS': [-20.7722, -54.7852],
  'MG': [-18.5122, -44.5550],
  'PA': [-3.4168, -52.2224],
  'PB': [-7.2400, -36.7820],
  'PR': [-24.8937, -51.5578],
  'PE': [-8.2810, -37.8645],
  'PI': [-6.6022, -42.2813],
  'RJ': [-22.9068, -43.1729],
  'RN': [-5.7950, -36.5200],
  'RS': [-30.0346, -51.2177],
  'RO': [-10.8300, -62.8000],
  'RR': [2.1200, -61.3200],
  'SC': [-27.2423, -50.2189],
  'SP': [-23.5505, -46.6333],
  'SE': [-10.5700, -37.3800],
  'TO': [-10.1800, -48.3300]
};

const CITY_COORDINATES = {
  'sao paulo': [-23.5505, -46.6333],
  'guarulhos': [-22.2916, -46.5333],
  'campinas': [-22.9099, -47.0626],
  'sao bernardo do campo': [-23.6939, -46.5649],
  'santo andre': [-23.6666, -46.5333],
  'osasco': [-23.5325, -46.7917],
  'santos': [-23.9608, -46.3338],
  'sao jose dos campos': [-23.2237, -45.9009],
  'ribeirao preto': [-21.1704, -47.8103],
  'sorocaba': [-23.5015, -47.4526],
  'diadema': [-23.6814, -46.6203],
  'indaiatuba': [-23.0903, -47.2181],
  'rio de janeiro': [-22.9068, -43.1729],
  'niteroi': [-22.8858, -43.1153],
  'duque de caxias': [-22.7856, -43.3117],
  'belo horizonte': [-19.9167, -43.9345],
  'uberlandia': [-18.9113, -48.2622],
  'contagem': [-19.9318, -44.0530],
  'juiz de fora': [-21.7642, -43.3503],
  'porto alegre': [-30.0346, -51.2177],
  'caxias do sul': [-29.1685, -51.1794],
  'canoas': [-29.9167, -51.1833],
  'curitiba': [-25.4290, -49.2671],
  'londrina': [-23.3103, -51.1628],
  'maringa': [-23.4210, -51.9331],
  'florianopolis': [-27.5954, -48.5480],
  'joinville': [-26.3045, -48.8464],
  'blumenau': [-26.9194, -49.0661],
  'salvador': [-12.9777, -38.5016],
  'feira de santana': [-12.2664, -38.9662],
  'recife': [-8.0542, -34.8813],
  'jaboatao dos guararapes': [-8.1136, -34.9728],
  'fortaleza': [-3.7319, -38.5267],
  'brasilia': [-15.7998, -47.8645],
  'goiania': [-16.6869, -49.2648],
  'manaus': [-3.1190, -60.0217],
  'belem': [-1.4558, -48.4902],
  'sao luis': [-2.5307, -44.3068],
  'maceio': [-9.6658, -35.7350],
  'natal': [-5.7950, -35.2094],
  'teresina': [-5.0920, -42.8038],
  'joao pessoa': [-7.1195, -34.8450],
  'aracaju': [-10.9472, -37.0731],
  'porto velho': [-8.7612, -63.9039],
  'macapa': [0.0350, -51.0700],
  'rio branco': [-9.9740, -67.8080],
  'boa vista': [2.8235, -60.6758],
  'palmas': [-10.1800, -48.3300],
  'cuiaba': [-15.6010, -56.0974],
  'campo grande': [-20.4428, -54.6064],
  'new york': [40.7128, -74.0060],
  'london': [51.5074, -0.1278],
  'londres': [51.5074, -0.1278],
  'paris': [48.8566, 2.3522],
  'lisboa': [38.7223, -9.1393],
  'lisbon': [38.7223, -9.1393],
  'porto': [41.1579, -8.6291],
  'berlim': [52.5200, 13.4050],
  'berlin': [52.5200, 13.4050],
  'tokyo': [35.6762, 139.6503],
  'toquio': [35.6762, 139.6503],
  'sydney': [-33.8688, 151.2093],
  'toronto': [43.6532, -79.3832]
};

const COUNTRY_MAP = {
  'estados unidos': ['estados unidos', 'united states', 'usa', 'eua', 'new york', 'california', 'texas', 'florida', 'chicago', 'san francisco', 'los angeles', 'seattle', 'boston', 'ny', 'ca', 'tx', 'wa', 'ma'],
  'portugal': ['portugal', 'lisboa', 'lisbon', 'porto', 'coimbra', 'braga'],
  'reino unido': ['reino unido', 'united kingdom', 'uk', 'london', 'londres', 'manchester', 'birmingham'],
  'canada': ['canada', 'toronto', 'vancouver', 'montreal', 'ontario', 'quebec'],
  'alemanha': ['alemanha', 'germany', 'berlim', 'berlin', 'munich', 'munique', 'frankfurt', 'hamburgo', 'hamburg'],
  'franca': ['franca', 'france', 'paris', 'lyon', 'marseille'],
  'espanha': ['espanha', 'spain', 'madrid', 'madri', 'barcelona', 'valencia'],
  'italia': ['italia', 'italy', 'roma', 'rome', 'milano', 'milan'],
  'japao': ['japao', 'japan', 'tokyo', 'toquio', 'osaka', 'kyoto'],
  'australia': ['australia', 'sydney', 'melbourne', 'brisbane'],
  'india': ['india', 'bangalore', 'mumbai', 'delhi'],
  'china': ['china', 'beijing', 'shanghai', 'hong kong']
};

const COUNTRY_COORDINATES = {
  'Brasil': [-14.235, -51.925],
  'Portugal': [39.3999, -8.2245],
  'Estados Unidos': [37.0902, -95.7129],
  'Canada': [56.1304, -106.3468],
  'Alemanha': [51.1657, 10.4515],
  'Reino Unido': [55.3781, -3.4360],
  'França': [46.2276, 2.2137],
  'Espanha': [40.4637, -3.7492],
  'Itália': [41.8719, 12.5674],
  'Japão': [36.2048, 138.2529],
  'Austrália': [-25.2744, 133.7751],
  'China': [35.8617, 104.1954],
  'Índia': [20.5937, 78.9629],
  'Internacional': [20, -40]
};

function normalizeText(value) {
  if (value === null || value === undefined) return '';
  return String(value)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function getMatchColor(score = 0) {
  if (score >= 80) return '#10b981';
  if (score >= 65) return '#f59e0b';
  return '#ef4444';
}

function getStatusLabel(status) {
  return {
    found: 'Encontrada',
    applying: 'Candidatando',
    applied: 'Inscrita',
    contacted: 'Retorno de RH',
    failed: 'Falhou'
  }[status] || status;
}

function detectWorkMode(location = '') {
  const loc = normalizeText(location);
  if (loc.includes('remoto') || loc.includes('remote')) return 'Remoto';
  if (loc.includes('hibrido') || loc.includes('hybrid')) return 'Hibrido';
  return 'Presencial';
}

function detectCountry(location = '') {
  const loc = normalizeText(location);
  if (!loc) return 'Brasil';

  for (const [country, keywords] of Object.entries(COUNTRY_MAP)) {
    if (keywords.some(kw => loc.includes(kw))) {
      return country.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    }
  }

  const hasBrState = BR_STATES.some(([uf, name]) => {
    const ufRegex = new RegExp(`(^|[^a-z])${uf.toLowerCase()}([^a-z]|$)`);
    return ufRegex.test(loc) || loc.includes(normalizeText(name));
  }) || Object.keys(STATE_ALIASES).some(alias => loc.includes(alias));

  const hasBrCity = Object.keys(CITY_COORDINATES).some(city => loc.includes(city));

  if (hasBrState || hasBrCity || loc.includes('brasil') || loc.includes('brazil')) {
    return 'Brasil';
  }

  const parts = location.split(',');
  if (parts.length > 1) {
    const lastPart = parts[parts.length - 1].trim();
    if (lastPart.length > 2 && lastPart.length < 25 && !/^[A-Z]{2}$/.test(lastPart)) {
      return lastPart.charAt(0).toUpperCase() + lastPart.slice(1);
    }
  }

  return 'Internacional';
}

function detectState(location = '') {
  const loc = normalizeText(location);
  for (const [uf, name] of BR_STATES) {
    const nameNorm = normalizeText(name);
    const ufRegex = new RegExp(`(^|[^a-z])${uf.toLowerCase()}([^a-z]|$)`);
    if (ufRegex.test(loc) || loc.includes(nameNorm)) return uf;
  }
  for (const [name, uf] of Object.entries(STATE_ALIASES)) {
    if (loc.includes(name)) return uf;
  }
  
  const country = detectCountry(location);
  if (country === 'Brasil') return 'BR';
  
  const stateMatch = location.match(/,\s*([A-Za-z]{2})\b/);
  if (stateMatch) {
    return stateMatch[1].toUpperCase();
  }
  
  return 'INT';
}

function detectCity(location = '') {
  const locStr = String(location || '');
  const raw = locStr.replace(/\(.*?\)/g, '').trim();
  if (!raw) return 'Nao informado';
  const firstPart = raw.split(',')[0].replace(/\s+-\s+.*$/, '').trim();
  if (/^(remoto|remote|hibrido|hybrid|presencial)$/i.test(firstPart)) return detectCountry(raw);
  return firstPart || 'Nao informado';
}

function detectCoordinates(location = '', state = '') {
  const loc = normalizeText(location);
  const st = (state || '').toUpperCase().trim();

  for (const [cityName, coords] of Object.entries(CITY_COORDINATES)) {
    if (loc.includes(cityName)) {
      return coords;
    }
  }

  if (STATE_COORDINATES[st]) {
    return STATE_COORDINATES[st];
  }

  for (const [uf, coords] of Object.entries(STATE_COORDINATES)) {
    const ufRegex = new RegExp(`(^|[^a-z])${uf.toLowerCase()}([^a-z]|$)`);
    if (ufRegex.test(loc)) {
      return coords;
    }
  }

  const country = detectCountry(location);
  if (COUNTRY_COORDINATES[country]) {
    return COUNTRY_COORDINATES[country];
  }

  return [20, 0];
}

function sourceLabel(source) {
  if (!source) return 'Gemini Web';
  if (source === 'linkedin') return 'LinkedIn';
  return `Gemini ${source}`;
}

const groupBy = ref('state');
const isLocating = ref(false);
const userLocation = ref(null);
const query = ref('');

const mapRef = ref(null);
const mapInstanceRef = ref(null);
const markersRef = ref([]);
const hasFittedBoundsRef = ref(false);
const lastJobsLengthRef = ref(0);

const geocodedCache = ref({});
// Carrega cache do localStorage
onMounted(() => {
  try {
    const saved = localStorage.getItem('vagas_geocoded_cache_v2');
    if (saved) {
      geocodedCache.value = JSON.parse(saved);
    }
  } catch (err) {
    console.error(err);
  }
});

const safeJobs = computed(() => {
  return Array.isArray(props.jobs) ? props.jobs : [];
});

lastJobsLengthRef.value = safeJobs.value.length;

const enrichedJobs = computed(() => {
  return safeJobs.value.map(job => ({
    ...job,
    workMode: detectWorkMode(job.location),
    country: detectCountry(job.location),
    state: detectState(job.location),
    city: detectCity(job.location)
  }));
});

const filteredJobs = computed(() => {
  const q = normalizeText(query.value);
  if (!q) return enrichedJobs.value;
  return enrichedJobs.value.filter(job => {
    const searchString = [
      job.title,
      job.company,
      job.location,
      job.city,
      job.state,
      job.country,
      job.source,
      job.company_address
    ].map(val => normalizeText(val)).join(' ');
    return searchString.includes(q);
  });
});

// Geocodificação sequencial
let geocodeTimeout = null;
let isGeocodingActive = true;

const selectedState = ref('');
const selectedCountry = ref('');
const countryNames = Object.keys(COUNTRY_COORDINATES);

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

const requestLocation = () => {
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

const startGeocoding = () => {
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
      
      if (STATE_COORDINATES[state]) {
        baseLat = STATE_COORDINATES[state][0];
        baseLng = STATE_COORDINATES[state][1];
      } else if (COUNTRY_COORDINATES[country]) {
        baseLat = COUNTRY_COORDINATES[country][0];
        baseLng = COUNTRY_COORDINATES[country][1];
      }
      
      const lat = baseLat + (Math.random() - 0.5) * 1.5;
      const lng = baseLng + (Math.random() - 0.5) * 1.5;
      
      newCacheEntries[addr] = {
        lat,
        lng,
        displayName: addr,
        referencePoints: [`Região de ${addr}`],
        rawAddress: addr
      };
    } catch (err) {
      console.error('Erro na geocodificação para:', addr, err);
    }
  });

  // Assign and save to LocalStorage ONCE to prevent lag
  geocodedCache.value = { ...geocodedCache.value, ...newCacheEntries };
  localStorage.setItem('vagas_geocoded_cache_v2', JSON.stringify(geocodedCache.value));
};

watch(safeJobs, () => {
  startGeocoding();
}, { immediate: true });

onMounted(() => {
  // Inicialização do Mapa
  if (!mapInstanceRef.value && mapRef.value) {
    const map = L.map(mapRef.value, {
      center: [-15.7797, -47.9297], // Centro do Brasil
      zoom: 4,
      zoomControl: true,
      scrollWheelZoom: true,
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 18,
    }).addTo(map);

    mapInstanceRef.value = map;

    setTimeout(() => {
      if (mapInstanceRef.value) {
        mapInstanceRef.value.invalidateSize();
      }
    }, 250);
  }
});

onBeforeUnmount(() => {
  delete window.selectJobFromMap;
  isGeocodingActive = false;
  if (geocodeTimeout) clearTimeout(geocodeTimeout);
  if (mapInstanceRef.value) {
    mapInstanceRef.value.remove();
    mapInstanceRef.value = null;
  }
});

// Atualiza marcadores
const updateMarkers = () => {
  const map = mapInstanceRef.value;
  if (!map) return;

  markersRef.value.forEach(marker => marker.remove());
  markersRef.value = [];

  const groups = {};

  filteredJobs.value.forEach(job => {
    if (job.workMode === 'Remoto') return;

    const addressToUse = job.company_address || job.location;
    
    let lat = null;
    let lng = null;
    let displayName = job.city && job.city !== 'Nao informado' ? `${job.city}, ${job.state}` : job.state || 'Brasil';
    let referencePoints = [];

    if (geocodedCache.value[addressToUse]) {
      const cached = geocodedCache.value[addressToUse];
      lat = cached.lat;
      lng = cached.lng;
      referencePoints = cached.referencePoints || [];
      if (cached.displayName) {
        displayName = cached.displayName.split(',').slice(0, 3).join(',').trim();
      }
    } else {
      const coords = detectCoordinates(job.location || '', job.state || '');
      if (coords) {
        [lat, lng] = coords;
      }
    }

    if (lat === null || lng === null) return;
    const key = `${lat},${lng}`;

    if (!groups[key]) {
      groups[key] = {
        lat,
        lng,
        locationName: displayName,
        jobs: []
      };
    }
    groups[key].jobs.push({
      ...job,
      referencePoints
    });
  });

  Object.values(groups).forEach(group => {
    const { lat, lng, locationName, jobs: groupJobs } = group;

    const avgScore = Math.round(groupJobs.reduce((sum, j) => sum + (j.match_score || 0), 0) / groupJobs.length);
    const count = groupJobs.length;
    const color = getMatchColor(avgScore);

    const isSingle = count === 1;
    const globalIndex = isSingle ? safeJobs.value.findIndex(job => job.id === groupJobs[0].id) + 1 : '';
    const label = isSingle 
      ? `#${globalIndex} - ${(groupJobs[0].title.length > 20 ? groupJobs[0].title.substring(0, 20) + '...' : groupJobs[0].title)}`
      : count;

    let iconHtml = '';

    if (isSingle) {
      iconHtml = `
        <div style="position: absolute; bottom: 0; left: 0; transform: translate(-50%, -4px); display: flex; flex-direction: column; align-items: center; pointer-events: auto; cursor: pointer;">
          <div style="background-color: ${color}; padding: 6px 12px; border-radius: 8px; white-space: nowrap; font-size: 12px; font-weight: 700; color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.2); transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            ${label}
          </div>
          <div style="width: 0; height: 0; border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 8px solid ${color}; filter: drop-shadow(0 2px 2px rgba(0,0,0,0.3)); margin-top: -1px;"></div>
        </div>
      `;
    } else {
      iconHtml = `
        <div style="position: absolute; bottom: 0; left: 0; transform: translate(-50%, 50%); display: flex; align-items: center; justify-content: center; pointer-events: auto; cursor: pointer;">
          <span class="pulse" style="background-color: ${color}; position: absolute; width: 36px; height: 36px; border-radius: 50%; opacity: 0.6; animation: pulse-animation 2s infinite ease-out; z-index: 1;"></span>
          <div style="background-color: ${color}; width: 28px; height: 28px; border-radius: 50%; font-size: 12px; font-weight: 800; display: flex; align-items: center; justify-content: center; color: white; border: 2px solid white; box-shadow: 0 4px 10px rgba(0,0,0,0.5); position: relative; z-index: 2; transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
            ${count}
          </div>
        </div>
      `;
    }

    const customIcon = L.divIcon({
      html: iconHtml,
      className: '', // No extra Leaflet styling
      iconSize: [0, 0], 
      iconAnchor: [0, 0],
      popupAnchor: [0, isSingle ? -36 : -14]
    });

    const marker = L.marker([lat, lng], { icon: customIcon }).addTo(map);

    const popupHtml = `
      <div class="leaflet-custom-popup">
        <div class="popup-header">
          <h4>${locationName}</h4>
          <span class="popup-header-score" style="color: ${color}; border-color: ${color}44; background: ${color}12;">
            Média: ${avgScore}%
          </span>
        </div>
        <div class="popup-jobs-list">
          ${groupJobs.map(j => {
            const srcClass = j.source === 'linkedin' ? 'linkedin' : 'web';
            const srcLabel = j.source === 'linkedin' ? 'LinkedIn' : 'Gemini Web';
            
            const refPointsHtml = j.referencePoints && j.referencePoints.length > 0
              ? `<div class="popup-job-ref-points">
                   ${j.referencePoints.map(p => `<span>📍 ${p}</span>`).join('')}
                 </div>`
              : '';

            const globalIndex = safeJobs.value.findIndex(job => job.id === j.id) + 1;
            return `
              <div class="popup-job-item">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 0.5rem; margin-bottom: 2px;">
                  <div class="popup-job-title"><span style="color: var(--color-secondary); font-weight: 900; margin-right: 4px;">#${globalIndex}</span> ${j.title}</div>
                  <span class="popup-source-badge ${srcClass}">${srcLabel}</span>
                </div>
                <div class="popup-job-company">${j.company}</div>
                
                ${j.company_address ? `
                  <div class="popup-job-address">
                    <i class="fa-solid fa-location-dot" style="font-size: 10px; margin-right: 4px; color: var(--color-primary);"></i>
                    ${j.company_address}
                  </div>
                ` : ''}

                ${refPointsHtml}

                <div class="popup-job-footer">
                  <span class="popup-job-match" style="color: ${getMatchColor(j.match_score)}">Match: ${j.match_score}%</span>
                  <span class="popup-job-status">${getStatusLabel(j.status)}</span>
                </div>
                <div style="display: flex; gap: 0.35rem; margin-top: 0.35rem;">
                  <button onclick="window.selectJobFromMap(${j.id})" class="btn btn-primary" style="flex: 1; margin-top: 0; padding: 0.25rem 0.5rem; font-size: 0.8rem; width: 100%;">
                    Ver Detalhes <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 10px; margin-left: 4px;"></i>
                  </button>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;

    marker.bindPopup(popupHtml, {
      maxWidth: 300,
      minWidth: 260
    });
    markersRef.value.push(marker);
  });

  const jobsChanged = lastJobsLengthRef.value !== safeJobs.value.length;
  lastJobsLengthRef.value = safeJobs.value.length;

  const shouldFitBounds = !hasFittedBoundsRef.value || jobsChanged;

  if (shouldFitBounds && markersRef.value.length > 0) {
    if (markersRef.value.length > 1) {
      const group = new L.featureGroup(markersRef.value);
      map.fitBounds(group.getBounds().pad(0.15));
    } else if (markersRef.value.length === 1) {
      map.setView(markersRef.value[0].getLatLng(), 8);
    }
    hasFittedBoundsRef.value = true;
  }
};

watch([filteredJobs, geocodedCache, mapInstanceRef], () => {
  updateMarkers();
}, { deep: true });

const grouped = computed(() => {
  const keyBy = {
    city: job => job.city,
    state: job => job.state,
    country: job => job.country
  }[groupBy.value];

  const reduceObj = filteredJobs.value.reduce((acc, job) => {
    const key = keyBy(job) || 'Nao informado';
    if (!acc[key]) {
      acc[key] = {
        key,
        jobs: [],
        average: 0,
        remote: 0,
        applied: 0
      };
    }
    acc[key].jobs.push(job);
    if (job.workMode === 'Remoto') acc[key].remote += 1;
    if (job.status === 'applied' || job.status === 'contacted') acc[key].applied += 1;
    return acc;
  }, {});

  return Object.values(reduceObj).map(group => ({
    ...group,
    average: Math.round(group.jobs.reduce((sum, job) => sum + (job.match_score || 0), 0) / group.jobs.length),
    bestJob: [...group.jobs].sort((a, b) => (b.match_score || 0) - (a.match_score || 0))[0]
  })).sort((a, b) => b.average - a.average || b.jobs.length - a.jobs.length);
});

const stats = computed(() => {
  return {
    total: filteredJobs.value.length,
    remote: filteredJobs.value.filter(job => job.workMode === 'Remoto').length,
    hybrid: filteredJobs.value.filter(job => job.workMode === 'Hibrido').length,
    countries: new Set(filteredJobs.value.map(job => job.country)).size,
    bestAverage: grouped.value[0]?.average || 0
  };
});

const topJobs = computed(() => {
  return [...filteredJobs.value]
    .sort((a, b) => (b.match_score || 0) - (a.match_score || 0))
    .slice(0, 8);
});
</script>

<template>
  <div class="location-radar">
    <div class="radar-header">
      <div>
        <h2>
          <i class="fa-solid fa-route" style="font-size: 21px;"></i>
          Radar de Vagas por Localidade
        </h2>
        <p>Mapa interativo com distribuição geográfica, match score médio e status de candidaturas em tempo real.</p>
      </div>
      <div class="radar-search" style="display: flex; gap: 0.5rem; align-items: center; background: transparent; padding: 0;">
        <div style="flex: 1; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.75rem;">
          <i class="fa-solid fa-magnifying-glass" style="font-size: 15px; color: var(--text-muted);"></i>
          <input
            v-model="query"
            placeholder="Filtrar por vaga, empresa ou local"
            style="background: transparent; border: none; color: #fff; width: 100%; outline: none;"
          />
        </div>
        
      </div>
    </div>

    <div class="radar-controls" role="tablist" aria-label="Acessar locais" style="display: flex; gap: 1rem; flex-wrap: wrap; background: rgba(8, 12, 24, 0.4); padding: 1rem; border-radius: 12px; border: 1px solid var(--border-color); align-items: center;">
      <span style="color: var(--text-muted); font-size: 0.85rem; font-weight: 600;"><i class="fa-solid fa-filter"></i> Acessar Localização:</span>
      
      <select v-model="selectedState" @change="zoomToRegion('state', selectedState)" class="radar-select">
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
      </select>

      <select v-model="selectedCountry" @change="zoomToRegion('country', selectedCountry)" class="radar-select">
        <option value="">Selecione um País...</option>
        <option v-for="c in countryNames" :key="c" :value="c">{{ c }}</option>
      </select>

      <button 
        @click="requestLocation"
        :disabled="isLocating"
        style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); color: #10b981; padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; display: flex; align-items: center; gap: 0.5rem; transition: all 0.2s; margin-left: auto;"
      >
        <i :class="isLocating ? 'fa-solid fa-spinner fa-spin' : 'fa-solid fa-location-crosshairs'" style="font-size: 16px;"></i>
        <span style="font-weight: 600; font-size: 0.85rem;">Usar Minha Localização Atual</span>
      </button>
    </div>

    <div class="radar-stats">
      <div>
        <i class="fa-solid fa-briefcase" style="font-size: 18px;"></i>
        <strong>{{ stats.total }}</strong>
        <span>vagas filtradas</span>
      </div>
      <div>
        <i class="fa-solid fa-desktop" style="font-size: 18px;"></i>
        <strong>{{ stats.remote }}</strong>
        <span>remotas</span>
      </div>
      <div>
        <i class="fa-solid fa-building" style="font-size: 18px;"></i>
        <strong>{{ stats.hybrid }}</strong>
        <span>hibridas</span>
      </div>
      <div>
        <i class="fa-solid fa-earth-americas" style="font-size: 18px;"></i>
        <strong>{{ stats.countries }}</strong>
        <span>paises</span>
      </div>
      <div>
        <i class="fa-solid fa-wand-magic-sparkles" style="font-size: 18px;"></i>
        <strong>{{ stats.bestAverage }}%</strong>
        <span>melhor media</span>
      </div>
    </div>

    <!-- Interactive Map View -->
    <div class="radar-map-wrapper">
      <div id="job-map-container" ref="mapRef" class="radar-map" />
      <div class="map-legend">
        <span class="legend-title">Match Médio:</span>
        <span class="legend-item"><span class="legend-dot" style="background-color: #10b981" /> Alto (≥80%)</span>
        <span class="legend-item"><span class="legend-dot" style="background-color: #f59e0b" /> Médio (65-79%)</span>
        <span class="legend-item"><span class="legend-dot" style="background-color: #ef4444" /> Baixo (&lt;65%)</span>
        <span class="legend-tip"><i class="fa-solid fa-wand-magic-sparkles" style="font-size: 12px; color: var(--color-secondary)"></i> Clique nos marcadores para listar vagas locais</span>
      </div>
    </div>

    <div v-if="filteredJobs.length === 0" class="radar-empty">
      <i class="fa-solid fa-location-dot" style="font-size: 40px;"></i>
      <p>Nenhuma vaga encontrada para esse filtro.</p>
    </div>

    <div v-else class="radar-layout">
      <section class="radar-groups">
        <article v-for="group in grouped" :key="group.key" class="radar-group-card">
          <div class="group-card-top">
            <div>
              <span class="group-label">
                {{ groupBy === 'city' ? 'Cidade' : groupBy === 'state' ? 'Estado' : 'Pais' }}
              </span>
              <h3>{{ group.key }}</h3>
            </div>
            <span
              class="group-score"
              :style="{
                color: getMatchColor(group.average),
                borderColor: `${getMatchColor(group.average)}66`,
                background: `${getMatchColor(group.average)}18`
              }"
            >
              {{ group.average }}%
            </span>
          </div>

          <div class="group-bars">
            <span :style="{ width: `${Math.min(group.average, 100)}%`, background: getMatchColor(group.average) }" />
          </div>

          <div class="group-metrics">
            <span>{{ group.jobs.length }} vagas</span>
            <span>{{ group.remote }} remotas</span>
            <span>{{ group.applied }} inscritas</span>
          </div>

          <div class="group-best" style="cursor: pointer;" @click="group.bestJob && emit('select-job', group.bestJob.id)">
            <span>Melhor oportunidade</span>
            <strong>{{ group.bestJob?.title }}</strong>
            <small>{{ group.bestJob?.company }} • {{ sourceLabel(group.bestJob?.source) }} <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 10px; margin-left: 4px;"></i></small>
          </div>
        </article>
      </section>

      <aside class="radar-ranking">
        <h3>
          <i class="fa-solid fa-wand-magic-sparkles" style="font-size: 16px;"></i>
          Melhores matches
        </h3>
        <a
          v-for="job in topJobs"
          :key="job.id"
          class="ranking-item"
          href="#"
          @click.prevent="emit('select-job', job.id)"
        >
          <span
            class="ranking-score"
            :style="{
              color: getMatchColor(job.match_score),
              borderColor: `${getMatchColor(job.match_score)}55`,
              background: `${getMatchColor(job.match_score)}16`
            }"
          >
            {{ job.match_score || 0 }}%
          </span>
          <span class="ranking-copy">
            <strong>{{ job.title }}</strong>
            <small>{{ job.company }} • {{ job.city }} • {{ getStatusLabel(job.status) }}</small>
          </span>
          <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 14px;"></i>
        </a>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.radar-select option {
  color: #111827;
  background-color: #ffffff;
  padding: 8px;
}
.radar-select option {
  color: #111827;
  background-color: #ffffff;
  padding: 8px;
}
.radar-select {
  color-scheme: dark;
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
.radar-select {
  color-scheme: dark;
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
