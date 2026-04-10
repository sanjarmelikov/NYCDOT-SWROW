const map = L.map('map').setView([40.7549, -73.9840], 15);

L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 19
}).addTo(map);

const mockData = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: { type: "LineString", coordinates: [[-73.9855, 40.7580], [-73.9845, 40.7560]] },
      properties: { street_name: "Broadway", borough: "Manhattan", direction: "NB", total_row_ft: 120, roadbed_ft: 76, left_sw_ft: 22, right_sw_ft: 22 }
    },
    {
      type: "Feature",
      geometry: { type: "LineString", coordinates: [[-73.9790, 40.7580], [-73.9784, 40.7535]] },
      properties: { street_name: "5th Avenue", borough: "Manhattan", direction: "SB", total_row_ft: 100, roadbed_ft: 64, left_sw_ft: 18, right_sw_ft: 18 }
    },
    {
      type: "Feature",
      geometry: { type: "LineString", coordinates: [[-73.9920, 40.7550], [-73.9800, 40.7550]] },
      properties: { street_name: "42nd Street", borough: "Manhattan", direction: "EB", total_row_ft: 110, roadbed_ft: 70, left_sw_ft: 20, right_sw_ft: 20 }
    }
  ]
};

function showPanel(props) {
  const total = props.total_row_ft;
  const lPct = ((props.left_sw_ft / total) * 100).toFixed(0);
  const rPct = ((props.right_sw_ft / total) * 100).toFixed(0);
  const rdPct = ((props.roadbed_ft / total) * 100).toFixed(0);

  document.getElementById('panel').innerHTML = `
    <div class="seg-name">${props.street_name}</div>
    <div class="seg-meta">${props.borough} &middot; Direction: ${props.direction}</div>
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

L.geoJSON(mockData, {
  style: { color: '#4fc3f7', weight: 5 },
  onEachFeature: (feature, layer) => {
    layer.on('click', () => {
      showPanel(feature.properties);
    });
    layer.on('mouseover', () => layer.setStyle({ color: '#81c784', weight: 7 }));
    layer.on('mouseout', () => layer.setStyle({ color: '#4fc3f7', weight: 5 }));
  }
}).addTo(map);
