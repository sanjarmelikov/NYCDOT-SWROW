"""
Stage 0: Download the full NYC Planimetric Sidewalk dataset from NYC Open Data
in chunks via the Socrata API, avoiding the 530MB single-file download limit.

Writes to data/raw/NYC_Planimetric_Database__Sidewalk_20260410.geojson
(overwrites the incomplete file if present).

Usage:
    python scripts/00_download_sidewalk.py
"""
import json
import time
from pathlib import Path
import urllib.request

DATASET_ID = "52n9-sdep"
BASE_URL   = f"https://data.cityofnewyork.us/resource/{DATASET_ID}.geojson"
CHUNK      = 50_000
OUT        = Path(__file__).resolve().parent.parent / "data" / "raw" / \
             "NYC_Planimetric_Database__Sidewalk_20260410.geojson"


def fetch_chunk(limit, offset):
    url = f"{BASE_URL}?$limit={limit}&$offset={offset}"
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.loads(r.read())


def run():
    all_features = []
    offset = 0
    crs = None

    print("Downloading NYC Planimetric Sidewalk data in chunks...")
    while True:
        print(f"  Fetching offset {offset}...")
        chunk = fetch_chunk(CHUNK, offset)
        features = chunk.get("features", [])
        if not features:
            break
        if crs is None:
            crs = chunk.get("crs")
        all_features.extend(features)
        print(f"  Got {len(features)} features — total so far: {len(all_features)}")
        if len(features) < CHUNK:
            break
        offset += CHUNK
        time.sleep(0.5)  # be polite to the API

    print(f"\nDownload complete: {len(all_features)} features total")

    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }
    if crs:
        geojson["crs"] = crs

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(geojson, f)
    print(f"Wrote -> {OUT}")


if __name__ == "__main__":
    run()
