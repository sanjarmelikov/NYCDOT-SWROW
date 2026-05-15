# NYC DOT — Street Width ROW Viewer

An interactive map of New York City's street Right-of-Way (ROW) widths across all 5 boroughs. Each street segment shows its total ROW width broken down into roadbed, left sidewalk, and right sidewalk measurements at 20ft intervals.

**Live map:** [sanjarmelikov.github.io/NYCDOT-SWROW](https://sanjarmelikov.github.io/NYCDOT-SWROW/)

---

## Using the Map

1. Open the live link above in any browser
2. Select a borough from the dropdown to load its street segments
3. Zoom in to street level to see segments appear
4. Click any segment to view its ROW breakdown in the sidebar
5. Use the search bar to jump directly to a specific street by name

---

## Running the Pipeline Locally

Use this if you want to regenerate the data from scratch (e.g. when NYC Open Data releases updated source files).

### Requirements

- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`

### Data Sources

Download the following files from [NYC Open Data](https://opendata.cityofnewyork.us) and place them in `data/raw/`:

| File | Dataset Name |
| ---- | ------------ |
| `NYC_Planimetric_Database__Roadbed_YYYYMMDD.geojson` | NYC Planimetric Database: Roadbed |
| `NYC_Planimetric_Database__Median_YYYYMMDD.geojson` | NYC Planimetric Database: Median |
| `SIDEWALK_LINE_YYYYMMDD.geojson` | LION Centerlines |

The sidewalk data is downloaded automatically by script 00.

### Pipeline Steps

Run scripts in order:

```bash
python scripts/00_download_sidewalk.py   # download sidewalk data from NYC Open Data API
python scripts/01_preprocess.py          # clean and reproject all source layers
python scripts/02_calculate_widths.py    # compute ROW widths via perpendicular transects
python scripts/03_export_geojson.py      # export per-borough GeoJSON files
python scripts/04_tile_geojson.py        # split into viewport tiles for the web map
```

Output tiles are written to `web/data/tiles/` and are served directly by the map.

### Viewing Locally

```bash
cd web
python3 -m http.server 8080
```

Then open `http://localhost:8080` in your browser.

---

## Data Notes

- ROW measurements are calculated using perpendicular transects against NYC Planimetric Database polygons
- Sidewalk widths default to 15ft on streets with no planimetric sidewalk polygon coverage
- Alleys and non-standard street types are excluded (LION rw_type 1, 2, 3, 9 only)
