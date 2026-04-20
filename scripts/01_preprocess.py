"""
Stage 1: Load raw NYC Open Data planimetric GeoJSONs + LION centerlines,
reproject to EPSG:2263 (NY State Plane Long Island, NAD83 feet),
clean invalid geometries, drop retired features, explode multi-parts,
save as GeoPackage for fast downstream use.

Usage:
    python scripts/01_preprocess.py                   # full city
    python scripts/01_preprocess.py --bbox minx miny maxx maxy  # WGS84 bbox
"""
import argparse
from pathlib import Path
import geopandas as gpd
from shapely.validation import make_valid

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

NY_STATE_PLANE = 2263

SOURCES = {
    "roadbed":      RAW / "NYC_Planimetric_Database__Roadbed_20260410.geojson",
    "sidewalk":     RAW / "NYC_Planimetric_Database__Sidewalk_20260410.geojson",
    "median":       RAW / "NYC_Planimetric_Database__Median_20260410.geojson",
    "centerlines":  RAW / "SIDEWALK_LINE_20260410.geojson",
}


def clean(gdf, layer_name):
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()
    invalid = ~gdf.geometry.is_valid
    if invalid.any():
        gdf.loc[invalid, "geometry"] = gdf.loc[invalid, "geometry"].apply(make_valid)
    if "status" in gdf.columns:
        before = len(gdf)
        # NYC Open Data uses strings: 'Unchanged', 'Updated', 'New' (all active);
        # 'Removed' or 'Deleted' would be retired. Keep everything except explicit retirements.
        RETIRED = {"Removed", "Deleted", "Retired"}
        gdf = gdf[~gdf["status"].astype(str).isin(RETIRED)]
        print(f"  [{layer_name}] dropped {before - len(gdf)} retired features; kept {len(gdf)}")
    return gdf.explode(index_parts=False, ignore_index=True)


def filter_centerlines(gdf):
    if "rw_type" in gdf.columns:
        keep = gdf["rw_type"].astype(str).isin(["1", "2", "3", "9"])
        print(f"  [centerlines] keeping {keep.sum()} of {len(gdf)} by rw_type")
        gdf = gdf[keep].copy()
    return gdf


def run(bbox=None):
    for name, path in SOURCES.items():
        print(f"\nLoading {name} from {path.name} ...")
        gdf = gpd.read_file(path, bbox=bbox, engine="pyogrio")
        print(f"  read {len(gdf)} features, CRS {gdf.crs}")
        gdf = gdf.to_crs(NY_STATE_PLANE)
        gdf = clean(gdf, name)
        if name == "centerlines":
            gdf = filter_centerlines(gdf)
        out = OUT / f"{name}.gpkg"
        gdf.to_file(out, driver="GPKG")
        print(f"  wrote {len(gdf)} features -> {out}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--bbox", nargs=4, type=float,
                   metavar=("MINX", "MINY", "MAXX", "MAXY"))
    args = p.parse_args()
    run(tuple(args.bbox) if args.bbox else None)
