const map = L.map('map', { preferCanvas: true }).setView([40.7549, -73.9840], 15);

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 19
}).addTo(map);

const DIRECTION_LABELS = {
  FT: "From-To (with digitization)",
  TF: "To-From (against digitization)",
  TW: "Two-way"
};

function capitalize(s) {
  if (!s) return s;
  return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
}

function showPanel(props) {
  const total = props.total_row_ft;
  const lPct = ((props.left_sw_ft / total) * 100).toFixed(0);
  const rPct = ((props.right_sw_ft / total) * 100).toFixed(0);
  const rdPct = ((props.roadbed_ft / total) * 100).toFixed(0);
  const boroughDisplay = capitalize(props.borough);
  const directionDisplay = DIRECTION_LABELS[props.direction] || props.direction;

  document.getElementById('panel').innerHTML = `
    <div class="seg-name">${props.street_name}</div>
    <div class="seg-meta">${boroughDisplay} &middot; Direction: ${directionDisplay}</div>
    <div class="metric-grid">
      <div class="metric-card full">
        <div class="metric-label">Total ROW Width</div>
        <div class="metric-value">${total}<span class="metric-unit">ft</span></div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Roadbed</div>
        <div class="metric-value">${props.roadbed_ft}<span class="metric-unit">ft</span></div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Left Sidewalk</div>
        <div class="metric-value">${props.left_sw_ft}<span class="metric-unit">ft</span></div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Right Sidewalk</div>
        <div class="metric-value">${props.right_sw_ft}<span class="metric-unit">ft</span></div>
      </div>
    </div>
    <hr class="divider" />
    <div class="bar-label">ROW Cross-Section</div>
    <div class="row-bar">
      <div class="bar-sw" style="flex:${lPct}">${lPct}%</div>
      <div class="bar-road" style="flex:${rdPct}">${rdPct}%</div>
      <div class="bar-sw" style="flex:${rPct}">${rPct}%</div>
    </div>
  `;
}

// --- tile loading ---

const CELL = 0.01;
const MIN_ZOOM = 16;
const loadedTiles = new Set();
const tileGroup = L.layerGroup().addTo(map);
let currentBorough = 'manhattan';
let searchQuery = '';
let streetIndex = {};  // loaded per borough

function segmentStyle() {
  return { color: '#ffb74d', weight: 3, opacity: 0.8 };
}

function tileKey(lon, lat) {
  const xi = Math.floor(lon / CELL);
  const yi = Math.floor(lat / CELL);
  return `${xi}_${yi}`;
}

function viewportTileKeys(bounds) {
  const keys = new Set();
  const xiMin = Math.floor(bounds.getWest()  / CELL);
  const xiMax = Math.floor(bounds.getEast()  / CELL);
  const yiMin = Math.floor(bounds.getSouth() / CELL);
  const yiMax = Math.floor(bounds.getNorth() / CELL);
  for (let xi = xiMin; xi <= xiMax; xi++)
    for (let yi = yiMin; yi <= yiMax; yi++)
      keys.add(`${xi}_${yi}`);
  return keys;
}

function featureMatchesSearch(feature) {
  if (!searchQuery) return true;
  return (feature.properties.street_name || '').toLowerCase().includes(searchQuery);
}

function addTileToMap(data) {
  const features = data.features.filter(featureMatchesSearch);
  if (!features.length) return;
  L.geoJSON({ type: 'FeatureCollection', features }, {
    style: segmentStyle(),
    onEachFeature: (feature, lyr) => {
      lyr.on('click', () => showPanel(feature.properties));
      lyr.on('mouseover', () => lyr.setStyle({ color: '#ffffff', weight: 6 }));
      lyr.on('mouseout',  () => lyr.setStyle(segmentStyle()));
    }
  }).addTo(tileGroup);
}

function loadTile(borough, key) {
  const id = `${borough}/${key}`;
  if (loadedTiles.has(id)) return;
  loadedTiles.add(id);
  fetch(`data/tiles/${borough}/${key}.geojson`)
    .then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(data => addTileToMap(data))
    .catch(() => loadedTiles.delete(id));
}

function updateViewport() {
  if (!currentBorough || map.getZoom() < MIN_ZOOM) {
    setStatus(map.getZoom() < MIN_ZOOM ? 'Zoom in further to load segments' : 'Select a borough');
    return;
  }
  const center = map.getCenter();
  const key = tileKey(center.lng, center.lat);
  loadTile(currentBorough, key);
  setStatus(`Viewing ${currentBorough.replace('_', ' ')}`);
}

function setBorough(borough) {
  if (borough === currentBorough) return;
  currentBorough = borough;
  streetIndex = {};
  loadedTiles.clear();
  tileGroup.clearLayers();
  document.getElementById('search').value = '';
  searchQuery = '';
  if (borough) loadStreetIndex(borough);
  updateViewport();
}

function applySearch() {
  searchQuery = document.getElementById('search').value.trim().toLowerCase();
  loadedTiles.clear();
  tileGroup.clearLayers();

  if (searchQuery && streetIndex) {
    // find all tile keys whose streets match the query
    const matchingKeys = new Set();
    for (const [name, keys] of Object.entries(streetIndex)) {
      if (name.includes(searchQuery)) keys.forEach(k => matchingKeys.add(k));
    }
    if (matchingKeys.size) {
      matchingKeys.forEach(key => loadTile(currentBorough, key));
      setStatus(`Found on ${matchingKeys.size} tile${matchingKeys.size !== 1 ? 's' : ''}`);
      return;
    }
    setStatus('No matching streets found');
    return;
  }

  updateViewport();
}

function loadStreetIndex(borough) {
  fetch(`data/tiles/${borough}/street_index.json`)
    .then(r => r.json())
    .then(idx => { streetIndex = idx; })
    .catch(() => { streetIndex = {}; });
}

function setStatus(msg) {
  const el = document.getElementById('result-count');
  if (el) el.textContent = msg;
}

// add status line below filters
const countEl = document.createElement('div');
countEl.id = 'result-count';
document.getElementById('filters').appendChild(countEl);

document.getElementById('search').addEventListener('input', applySearch);
document.getElementById('borough-filter').addEventListener('change', e => {
  setBorough(e.target.value || null);
});

map.on('moveend', updateViewport);
map.on('zoomend', updateViewport);

// boot with manhattan
document.getElementById('borough-filter').value = 'manhattan';
loadStreetIndex('manhattan');
updateViewport();
