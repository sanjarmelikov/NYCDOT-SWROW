const map = L.map('map').setView([40.7549, -73.9840], 15);

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

fetch('data/lineseg.geojson')
  .then(r => r.json())
  .then(data => {
    const layer = L.geoJSON(data, {
      style: { color: '#ffb74d', weight: 3, opacity: 0.8 },
      onEachFeature: (feature, lyr) => {
        lyr.on('click', () => showPanel(feature.properties));
        lyr.on('mouseover', () => lyr.setStyle({ color: '#ffffff', weight: 6 }));
        lyr.on('mouseout',  () => lyr.setStyle({ color: '#ffb74d', weight: 3 }));
      }
    }).addTo(map);
    map.fitBounds(layer.getBounds());
  })
  .catch(err => console.error('GeoJSON load failed:', err));
