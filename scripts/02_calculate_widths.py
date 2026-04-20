"""Stage 2: 20-ft transects + width calculations.

Algorithm:
1. Walk each centerline every 20 ft.
2. Cast a perpendicular transect ±60 ft from the centerline.
3. Clip each half-transect at the FAR edge of the sidewalk on that side
   — this is what defines the ROW boundary and stops cross-street bleed-through
   at intersections.
4. Measure roadbed/median/sidewalk intersections against the clipped transect.
5. Classify left/right using the 2D cross product and trafdir.
"""
import math
from pathlib import Path
import geopandas as gpd
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
from shapely.ops import unary_union, linemerge

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"

INTERVAL_FT = 20.0
HALF_TRANSECT_FT = 60.0          # initial cast length before clipping
ENDPOINT_BUFFER_FT = 15.0        # skip points this close to line endpoints


# ---------- geometry helpers ----------

def tangent_at(line, dist, eps=0.5):
    """Local tangent vector at `dist` along `line`, using a small step ahead."""
    d2 = min(dist + eps, line.length)
    d1 = max(d2 - eps, 0.0)
    p1 = line.interpolate(d1)
    p2 = line.interpolate(d2)
    return (p2.x - p1.x, p2.y - p1.y)


def perp_arms(center, tangent, half_len=HALF_TRANSECT_FT):
    """Return two LineStrings starting at `center` and going ±perpendicular
    to `tangent`. Each arm is ordered [center, outer_end] so coords[-1] is the
    outer tip. Also returns the unit perpendicular vector for left/right
    classification."""
    dx, dy = tangent
    n = math.hypot(dx, dy)
    if n == 0:
        return None, None, None
    px, py = -dy / n, dx / n
    left_end  = Point(center.x + px * half_len, center.y + py * half_len)
    right_end = Point(center.x - px * half_len, center.y - py * half_len)
    left_arm  = LineString([center, left_end])
    right_arm = LineString([center, right_end])
    return left_arm, right_arm, (px, py)


def clip_arm_at_sidewalk(arm, sw_tree, sw_polys):
    """Truncate `arm` (center -> outer) at the FAR side of whatever sidewalk
    polygon it crosses. Returns (clipped_arm, sidewalk_length_on_arm).
    If no sidewalk is hit, returns the arm unchanged (length_on_arm=0)."""
    if sw_tree is None or not sw_polys:
        return arm, 0.0
    candidates = [sw_polys[i] for i in sw_tree.query(arm)
                  if sw_polys[i].intersects(arm)]
    if not candidates:
        return arm, 0.0
    sw_local = unary_union(candidates)
    inter = arm.intersection(sw_local)
    if inter.is_empty:
        return arm, 0.0
    # collect all endpoints of intersection linestrings
    segs = []
    if inter.geom_type == "LineString":
        segs = [inter]
    elif hasattr(inter, "geoms"):
        segs = [g for g in inter.geoms if g.geom_type == "LineString"]
    if not segs:
        return arm, 0.0
    start = Point(arm.coords[0])
    # pick the endpoint with the greatest distance from the center — that's
    # the OUTER edge of the outermost sidewalk the arm enters.
    max_d = 0.0
    for s in segs:
        for coord in (s.coords[0], s.coords[-1]):
            d = start.distance(Point(coord))
            if d > max_d:
                max_d = d
    if max_d <= 0 or max_d >= arm.length:
        return arm, sum(s.length for s in segs)
    # truncate arm to length max_d from its start (center)
    cut_pt = arm.interpolate(max_d)
    clipped = LineString([arm.coords[0], (cut_pt.x, cut_pt.y)])
    # recompute sidewalk-length on the clipped arm
    sw_on_clipped = clipped.intersection(sw_local)
    if sw_on_clipped.is_empty:
        sw_len = 0.0
    elif hasattr(sw_on_clipped, "geoms"):
        sw_len = sum(g.length for g in sw_on_clipped.geoms if hasattr(g, "length"))
    else:
        sw_len = sw_on_clipped.length
    return clipped, sw_len


def length_inside(geom, tree, polys):
    """Length of `geom` clipped by the union of polys whose index hits `geom`."""
    if geom is None or geom.is_empty or tree is None or not polys:
        return 0.0
    hits = [polys[i] for i in tree.query(geom) if polys[i].intersects(geom)]
    if not hits:
        return 0.0
    clipped = geom.intersection(unary_union(hits))
    if clipped.is_empty:
        return 0.0
    if hasattr(clipped, "geoms"):
        return sum(g.length for g in clipped.geoms if hasattr(g, "length"))
    return clipped.length


# ---------- main loop ----------

def run():
    print("Loading processed layers...")
    cl = gpd.read_file(PROC / "centerlines.gpkg")
    rb = gpd.read_file(PROC / "roadbed.gpkg")
    sw = gpd.read_file(PROC / "sidewalk.gpkg")
    md = gpd.read_file(PROC / "median.gpkg")
    print(f"  {len(cl)} centerlines, {len(rb)} roadbed, {len(sw)} sidewalk, {len(md)} median")

    rb_geoms = rb.geometry.tolist(); rb_tree = STRtree(rb_geoms) if rb_geoms else None
    sw_geoms = sw.geometry.tolist(); sw_tree = STRtree(sw_geoms) if sw_geoms else None
    md_geoms = md.geometry.tolist(); md_tree = STRtree(md_geoms) if md_geoms else None

    records = []
    seg_id = 0
    for _, row in cl.iterrows():
        line = row.geometry
        if line is None or line.is_empty:
            continue
        if line.geom_type == "MultiLineString":
            merged = linemerge(line)
            line = merged if merged.geom_type == "LineString" else None
            if line is None:
                continue
        length = line.length
        if length < INTERVAL_FT:
            continue

        trafdir = str(row.get("trafdir", "TW")).strip() or "TW"
        dir_sign = -1 if trafdir == "TF" else 1

        dist = ENDPOINT_BUFFER_FT
        while dist <= length - ENDPOINT_BUFFER_FT:
            center = line.interpolate(dist)
            tangent = tangent_at(line, dist)
            left_arm, right_arm, perp = perp_arms(center, tangent)
            if left_arm is None:
                dist += INTERVAL_FT; continue

            # ---- OPTION A: clip each arm at its far sidewalk edge ----
            left_arm_c,  left_sw_raw  = clip_arm_at_sidewalk(left_arm,  sw_tree, sw_geoms)
            right_arm_c, right_sw_raw = clip_arm_at_sidewalk(right_arm, sw_tree, sw_geoms)
            # rebuilt clipped transect = left_outer -> center -> right_outer
            full_transect = LineString([
                left_arm_c.coords[-1],
                right_arm_c.coords[-1]
            ])

            roadbed_ft = length_inside(full_transect, rb_tree, rb_geoms)
            median_ft  = length_inside(full_transect, md_tree, md_geoms)

            # classify left/right using the cross product sign * direction
            cross = tangent[0]*perp[1] - tangent[1]*perp[0]
            left_is_left_arm = (cross * dir_sign) > 0
            if left_is_left_arm:
                left_sw_ft, right_sw_ft = left_sw_raw, right_sw_raw
            else:
                left_sw_ft, right_sw_ft = right_sw_raw, left_sw_raw

            total_row_ft = roadbed_ft + median_ft + left_sw_ft + right_sw_ft

            records.append({
                "segment_id":  seg_id,
                "physicalid":  row.get("physicalid"),
                "street_name": (row.get("st_label") or "").strip(),
                "borocode":    row.get("borocode"),
                "direction":   trafdir,
                "lion_st_width":  float(row.get("st_width") or 0),
                "total_row_ft":   round(total_row_ft, 1),
                "roadbed_ft":     round(roadbed_ft, 1),
                "median_ft":      round(median_ft, 1),
                "left_sw_ft":     round(left_sw_ft, 1),
                "right_sw_ft":    round(right_sw_ft, 1),
                "geometry":       full_transect,
            })
            seg_id += 1
            dist += INTERVAL_FT

    out = gpd.GeoDataFrame(records, geometry="geometry", crs=cl.crs)
    out_path = PROC / "segments.gpkg"
    out.to_file(out_path, driver="GPKG")
    print(f"Wrote {len(out)} segments -> {out_path}")


if __name__ == "__main__":
    run()
