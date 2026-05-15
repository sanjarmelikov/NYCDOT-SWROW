"""
Stage 4: Split per-borough GeoJSONs into a viewport-loadable grid of tiles.
Each tile covers a 0.01° × 0.01° cell. The web app fetches only tiles
that intersect the current map viewport.

Usage:
    python scripts/04_tile_geojson.py
"""
import json
import math
from pathlib import Path
from collections import defaultdict

CELL = 0.01  # degrees per tile side
BOROUGHS = ['manhattan', 'bronx', 'brooklyn', 'queens', 'staten_island']

ROOT = Path(__file__).resolve().parent.parent
WEB  = ROOT / 'web' / 'data'
TILES = WEB / 'tiles'


def tile_key(lon, lat):
    xi = math.floor(lon / CELL)
    yi = math.floor(lat / CELL)
    return f"{xi}_{yi}"


def run():
    for borough in BOROUGHS:
        src = WEB / f"lineseg_{borough}.geojson"
        if not src.exists():
            print(f"Skipping {borough} — file not found")
            continue

        out_dir = TILES / borough
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"Tiling {borough}...")
        with open(src) as f:
            data = json.load(f)

        tiles = defaultdict(list)
        street_index = defaultdict(set)  # street_name -> set of tile keys

        for feature in data['features']:
            coords = feature['geometry']['coordinates']
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            cx = sum(lons) / len(lons)
            cy = sum(lats) / len(lats)
            key = tile_key(cx, cy)
            tiles[key].append(feature)
            name = (feature['properties'].get('street_name') or '').strip().lower()
            if name:
                street_index[name].add(key)

        for key, features in tiles.items():
            out = out_dir / f"{key}.geojson"
            with open(out, 'w') as f:
                json.dump({'type': 'FeatureCollection', 'features': features}, f)

        # write street index: { "broadway": ["-7401_4073", ...], ... }
        idx_out = TILES / borough / 'street_index.json'
        with open(idx_out, 'w') as f:
            json.dump({k: list(v) for k, v in street_index.items()}, f)

        print(f"  {borough}: {len(tiles)} tiles, {len(street_index)} streets, {len(data['features'])} segments")


if __name__ == '__main__':
    run()
