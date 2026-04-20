"""Stage 3: export Leaflet-ready GeoJSON."""
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT  = ROOT / "out"
OUT.mkdir(parents=True, exist_ok=True)

BORO = {1: "manhattan", 2: "bronx", 3: "brooklyn", 4: "queens", 5: "staten_island"}


def run():
    seg = gpd.read_file(PROC / "segments.gpkg")
    seg = seg.to_crs(4326)
    seg["borough"] = seg["borocode"].map(
        lambda c: BORO.get(int(c), "unknown") if c is not None else "unknown")
    out_cols = ["segment_id", "physicalid", "street_name", "borough", "direction",
                "total_row_ft", "roadbed_ft", "median_ft",
                "left_sw_ft", "right_sw_ft", "geometry"]
    seg = seg[out_cols]
    seg["geometry"] = seg.geometry.simplify(1e-6, preserve_topology=True)
    full = OUT / "lineseg.geojson"
    if full.exists():
        full.unlink()
    seg.to_file(full, driver="GeoJSON")
    print(f"Wrote {len(seg)} segments -> {full}")
    for _, name in BORO.items():
        sub = seg[seg["borough"] == name]
        if len(sub):
            p = OUT / f"lineseg_{name}.geojson"
            if p.exists(): p.unlink()
            sub.to_file(p, driver="GeoJSON")
            print(f"  {name}: {len(sub)}")


if __name__ == "__main__":
    run()
