const map = L.map('map').setView([40.7549, -73.9840], 15);

// Load the basemap tiles (the actual street/building imagery)
L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 19
}).addTo(map);

// Mock data — fake street segments that mimic your real GeoJSON schema
const mockData = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      geometry: {
        type: "LineString",
        coordinates: [[-73.9855, 40.7580], [-73.9845, 40.7560]]
      },
      properties: {
        street_name: "Broadway",
        borough: "Manhattan",
        direction: "NB",
        total_row_ft: 120,
        roadbed_ft: 76,
        left_sw_ft: 22,
        right_sw_ft: 22
      }
    },
    {
      type: "Feature",
      geometry: {
        type: "LineString",
        coordinates: [[-73.9790, 40.7580], [-73.9784, 40.7535]]
      },
      properties: {
        street_name: "5th Avenue",
        borough: "Manhattan",
        direction: "SB",
        total_row_ft: 100,
        roadbed_ft: 64,
        left_sw_ft: 18,
        right_sw_ft: 18
      }
    },
    {
      type: "Feature",
      geometry: {
        type: "LineString",
        coordinates: [[-73.9920, 40.7550], [-73.9800, 40.7550]]
      },
      properties: {
        street_name: "42nd Street",
        borough: "Manhattan",
        direction: "EB",
        total_row_ft: 110,
        roadbed_ft: 70,
        left_sw_ft: 20,
        right_sw_ft: 20
      }
    }
  ]
};

// This function runs when a segment is clicked
// It takes the properties from the clicked feature and builds the sidebar HTML
function showPanel(props) {
  document.getElementById('panel').innerHTML = `
    <h2>${props.street_name}</h2>
    <p>${props.borough} · ${props.direction}</p>
    <hr />
    <p>Total ROW: <strong>${props.total_row_ft} ft</strong></p>
    <p>Roadbed: <strong>${props.roadbed_ft} ft</strong></p>
    <p>Left Sidewalk: <strong>${props.left_sw_ft} ft</strong></p>
    <p>Right Sidewalk: <strong>${props.right_sw_ft} ft</strong></p>
  `;
}

// Load the mock GeoJSON onto the map
L.geoJSON(mockData, {
  style: {
    color: '#4fc3f7',
    weight: 5
  },
  onEachFeature: (feature, layer) => {
    // Attach a click listener to every segment
    layer.on('click', () => {
      showPanel(feature.properties);
    });
  }
}).addTo(map);
