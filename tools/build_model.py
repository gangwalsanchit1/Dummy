#!/usr/bin/env python3
"""Phase 2: build the architectural coordination model of Bella Vita 2.

Inputs  : model/takeoff.json (DRAWN), model/assumptions.json (ASSUMED),
          model/furniture.json (ASSUMED positions)
Outputs : model/scene.json            element list used by the IFC exporter and viewer
          docs/model-checks.md        furniture/clearance checks + model-vs-takeoff comparison

Pure standard library. Coordinates: plan X (m, from left outer face), plan Y (m, from
rear outer face towards road), Z (m above road level, ASSUMED datum).
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TK = json.loads((ROOT / "model/takeoff.json").read_text())
AS = json.loads((ROOT / "model/assumptions.json").read_text())
FU = json.loads((ROOT / "model/furniture.json").read_text())
H = AS["heights"]
LV = AS["levels"]
SLAB = LV["slab_thickness"]
FF = LV["floor_to_floor"]
STOREYS = LV["storeys"]
FFL = {s: round(LV["stilt_ffl"] + i * FF, 3) for i, s in enumerate(STOREYS)}
PLAN_OF = {"GF": "GF", "F1": "F1-3", "F2": "F1-3", "F3": "F1-3", "F4": "F4", "TERRACE": "TERRACE"}
CABIN_TOP = round(FFL["TERRACE"] + H["stair_cabin_clear"] + SLAB, 3)

elements = []


def add(cls, name, storey, layer, boxes, tag="DRAWN", **kw):
    e = {"id": f"E{len(elements)+1:04d}", "cls": cls, "name": name, "storey": storey, "layer": layer,
         "boxes": [[round(v, 4) for v in b] for b in boxes if b[3] - b[0] > 1e-4 and b[4] - b[1] > 1e-4 and b[5] - b[2] > 1e-4],
         "tag": tag}
    e.update(kw)
    if e["boxes"]:
        elements.append(e)
    return e


# ---------------------------------------------------------------- geometry helpers
def rect_subtract(outer, holes):
    """Return rectangles covering outer minus holes (grid decomposition, row-merged)."""
    xs = sorted({outer[0], outer[2], *[min(max(h[i], outer[0]), outer[2]) for h in holes for i in (0, 2)]})
    ys = sorted({outer[1], outer[3], *[min(max(h[i], outer[1]), outer[3]) for h in holes for i in (1, 3)]})
    out = []
    for j in range(len(ys) - 1):
        row = []
        for i in range(len(xs) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if any(h[0] < cx < h[2] and h[1] < cy < h[3] for h in holes):
                continue
            if row and abs(row[-1][2] - xs[i]) < 1e-9:
                row[-1][2] = xs[i + 1]
            else:
                row.append([xs[i], ys[j], xs[i + 1], ys[j + 1]])
        out += row
    return [r for r in out if r[2] - r[0] > 1e-6 and r[3] - r[1] > 1e-6]


def ovl(a, b, eps=1e-6):
    return a[0] < b[2] - eps and b[0] < a[2] - eps and a[1] < b[3] - eps and b[1] < a[3] - eps


def wall_axis(r):
    return "x" if (r[2] - r[0]) >= (r[3] - r[1]) else "y"


def window_heights(width):
    if width < H["ventilator_max_width"]:
        return H["ventilator_sill"], H["window_head"], "ventilator"
    return H["window_sill"], H["window_head"], "window"


def window_rect(fl, w):
    """Plan rect of a window opening through its host wall."""
    y1 = fl["outline"][3]
    a, b = w["span_x"]
    if w["wall"] == "rear":
        return [a, 0.0, b, 0.15]
    return [a, y1 - 0.15, b, y1]


def parse_wall(o):
    import re
    nums = [float(v) for v in re.findall(r"[\d.]+", o["wall"])]
    if len(nums) == 1:
        nums = [nums[0] - 0.05, nums[0] + 0.05]
    return nums


def opening_rect(o):
    """Plan rect of a door/opening gap (spans the wall thickness)."""
    a, b = parse_wall(o)
    if "span_x" in o:
        return [o["span_x"][0], a, o["span_x"][1], b]
    return [a, o["span_y"][0], b, o["span_y"][1]]


# ---------------------------------------------------------------- site
site = TK["site"]
add("IfcSite", "Plot ground (8.00 x 13.35)", "SITE", "site", [[0, -0.6, -0.05, 8.0, 12.75, 0.0]], "DRAWN plan / ASSUMED level")
add("IfcBuildingElementProxy", "Road 6.00 m", "SITE", "site", [[-2.0, 12.75, -0.07, 10.0, 18.75, -0.02]], "DRAWN width")
cw = H["compound_wall"]
for r, nm in [([0, -0.6, 8.0, -0.45], "rear"), ([0, -0.6, 0.15, 0.0], "left-rear"), ([7.85, -0.6, 8.0, 0.0], "right-rear"),
              ([0, 11.75, 0.15, 12.75], "left-front"), ([7.85, 11.75, 8.0, 12.75], "right-front"),
              ([0, 12.6, 2.5, 12.75], "front-left of gate"), ([5.5, 12.6, 8.0, 12.75], "front-right of gate")]:
    add("IfcWall", f"Compound wall {nm}", "SITE", "site", [[r[0], r[1], 0, r[2], r[3], cw]], "DRAWN plan / ASSUMED height")

# ---------------------------------------------------------------- slabs
STAIR_HOLE = [5.75, 3.10, 7.85, 5.85]          # flights + mid landing (front floor landing kept)
LIFT_HOLE = [4.20, 3.10, 5.60, 4.60]
PRIV_TERR = [5.75, 0.15, 7.85, 2.95]
z = FFL["GF"]
for r in rect_subtract([0, 0, 8.0, 11.75], [LIFT_HOLE]):
    add("IfcSlab", "Ground (stilt) floor slab on grade", "GF", "slab", [[r[0], r[1], z - SLAB, r[2], r[3], z]], "DRAWN plan / ASSUMED level")
for s in ["F1", "F2", "F3", "F4"]:
    z = FFL[s]
    for r in rect_subtract([0, 0, 8.0, 11.75], [STAIR_HOLE, LIFT_HOLE]):
        add("IfcSlab", f"{s} floor slab", s, "slab", [[r[0], r[1], z - SLAB, r[2], r[3], z]], "DRAWN plan / ASSUMED level")
z = FFL["TERRACE"]
for r in rect_subtract([0, 0, 8.0, 10.85], [STAIR_HOLE, LIFT_HOLE, PRIV_TERR]):
    add("IfcSlab", "Roof (terrace) slab", "TERRACE", "slab", [[r[0], r[1], z - SLAB, r[2], r[3], z]], "DRAWN plan / ASSUMED level")
for r in ([4.05, 2.95, 8.0, 4.75], [5.6, 4.75, 8.0, 7.05]):
    add("IfcSlab", "Stair cabin / lift shaft roof slab", "TERRACE", "slab", [[r[0], r[1], CABIN_TOP - SLAB, r[2], r[3], CABIN_TOP]], "ASSUMED height")
# lift pit
pit = -H["lift_pit_depth"] + FFL["GF"]
add("IfcSlab", "Lift pit base", "GF", "slab", [[4.05, 2.95, pit - SLAB, 5.75, 4.75, pit]], "ASSUMED depth")
for r in ([4.05, 2.95, 4.20, 4.75], [5.60, 2.95, 5.75, 4.75], [4.20, 2.95, 5.60, 3.10], [4.20, 4.60, 5.60, 4.75]):
    add("IfcWall", "Lift pit wall", "GF", "wall", [[r[0], r[1], pit, r[2], r[3], FFL["GF"] - SLAB]], "ASSUMED depth")


# ---------------------------------------------------------------- walls, windows, doors per storey
def storey_top(s):
    if s == "TERRACE":
        return None
    nxt = STOREYS[STOREYS.index(s) + 1]
    return FFL[nxt] - SLAB


def wall_height_terrace(r):
    core = r[0] >= 4.0 and r[1] >= 2.9 and r[3] <= 7.1 and r[0] < 7.86 and not (r[0] >= 7.85)
    if core and not (abs(r[0] - 0) < 1e-6):
        return CABIN_TOP - SLAB, "Stair cabin / lift shaft wall", "ASSUMED height"
    return FFL["TERRACE"] + H["parapet"], "Parapet", "ASSUMED height"


DOORS = AS["doors"]
for s in STOREYS:
    pk = PLAN_OF[s]
    fl = TK["floors"][pk]
    z0 = FFL[s]
    zt = storey_top(s)
    wins = fl.get("windows", [])
    for wi, r in enumerate(fl["walls"]):
        if s == "TERRACE":
            top, nm, tag = wall_height_terrace(r)
            if r[0] >= 7.85 and 2.9 <= r[1] and r[3] <= 7.1:
                top, nm, tag = CABIN_TOP - SLAB, "Stair cabin wall", "ASSUMED height"
            # outer right wall: parapet everywhere except along the cabin -> split
            if r == [7.85, 0, 8.0, 10.85]:
                for seg, t2, n2 in (([7.85, 0, 8.0, 2.95], FFL[s] + H["parapet"], "Parapet"),
                                    ([7.85, 2.95, 8.0, 7.05], CABIN_TOP - SLAB, "Stair cabin wall"),
                                    ([7.85, 7.05, 8.0, 10.85], FFL[s] + H["parapet"], "Parapet")):
                    add("IfcWall", n2, s, "wall", [[seg[0], seg[1], z0, seg[2], seg[3], t2]], "DRAWN plan / ASSUMED height")
                continue
        else:
            top, nm, tag = zt, "Wall", "DRAWN plan / ASSUMED height"
            if s == "GF" and wall_axis(r) == "y" and r[3] - r[1] > 10:
                nm = "Ground-floor side wall (as drawn, Q10)"
        # windows hosted in this wall
        hosted = []
        for w in wins:
            wr = window_rect(fl, w)
            if ovl(wr, r) and wall_axis(r) == "x":
                hosted.append((w, wr))
        if not hosted:
            add("IfcWall", nm, s, "wall", [[r[0], r[1], z0, r[2], r[3], top]], tag)
            continue
        hosted.sort(key=lambda t: t[1][0])
        boxes, voids = [], []
        cur = r[0]
        for w, wr in hosted:
            sill, head, kind = window_heights(w["width"])
            boxes.append([cur, r[1], z0, wr[0], r[3], top])
            boxes.append([wr[0], r[1], z0, wr[2], r[3], z0 + sill])
            boxes.append([wr[0], r[1], z0 + head, wr[2], r[3], top])
            voids.append({"window": w["id"], "box": [wr[0], r[1], z0 + sill, wr[2], r[3], z0 + head]})
            cur = wr[2]
            add("IfcWindow", f"{s} {w['id']} {kind} {w['width']:.2f} m ({w['serves']})", s, "window",
                [[wr[0], (r[1] + r[3]) / 2 - 0.03, z0 + sill, wr[2], (r[1] + r[3]) / 2 + 0.03, z0 + head]],
                f"DRAWN width / ASSUMED sill {sill} head {head}", width=w["width"], sill=sill, head=head,
                host_wall_index=wi)
        boxes.append([cur, r[1], z0, r[2], r[3], top])
        add("IfcWall", nm, s, "wall", boxes, tag, ifc_box=[r[0], r[1], z0, r[2], r[3], top], voids=voids)
    # door / opening headers and door leaves
    dmap = {d["id"]: d for d in DOORS.get(pk, [])}
    for o in fl.get("openings", []):
        orc = opening_rect(o)
        head = z0 + H["door_head"]
        wtop = (CABIN_TOP - SLAB) if s == "TERRACE" else zt
        add("IfcWall", f"Wall over {o['id']} ({o['type']})", s, "wall", [[orc[0], orc[1], head, orc[2], orc[3], wtop]],
            "DRAWN width / ASSUMED head height")
        if o["id"] in dmap:
            d = dmap[o["id"]]
            hx, hy = d["hinge"]
            # closed leaf: 0.04 thick, lying in the opening on the swing side face
            if d["leaf_axis"] == "x":
                x0, x1 = sorted([hx, hx + (-1 if abs(hx - orc[2]) < 0.06 else 1) * d["width"]])
                leaf = [x0, hy - 0.02, x1, hy + 0.02]
            else:
                y0, y1 = sorted([hy, hy + (-1 if abs(hy - orc[3]) < 0.06 else 1) * d["width"]])
                leaf = [hx - 0.02, y0, hx + 0.02, y1]
            add("IfcDoor", f"{s} {o['id']} door {d['width']:.2f} m -> {o.get('to', '')}", s, "door",
                [[leaf[0], leaf[1], z0, leaf[2], leaf[3], head]], f"DRAWN opening / swing {d['tag']}",
                width=d["width"], hinge=d["hinge"], quadrant=d["quadrant"])
            add("IfcBuildingElementProxy", f"{s} {o['id']} door swing zone r={d['width']:.2f}", s, "clearance",
                [[hx, hy, z0 + 0.01, hx + 0.001, hy + 0.001, z0 + 0.02]], d["tag"],
                swing={"hinge": d["hinge"], "r": d["width"], "q": d["quadrant"], "z": z0 + 0.012})
    # railings (F4 front terrace)
    for r in fl.get("railings", []):
        add("IfcRailing", "F4 front terrace parapet/railing", s, "wall",
            [[r[0], r[1], z0, r[2], r[3], z0 + H["f4_front_terrace_parapet"]]], "DRAWN plan / ASSUMED height")
    # spaces
    for sp in fl.get("spaces", []):
        if s == "TERRACE" and "below" in sp["name"].lower():
            continue
        add("IfcSpace", f"{s} {sp['name']}", s, "space",
            [[r[0], r[1], z0 + 0.005, r[2], r[3], z0 + 0.015] for r in sp["rects"]], "DRAWN",
            label=sp.get("label"), area=round(sum((r[2] - r[0]) * (r[3] - r[1]) for r in sp["rects"]), 2))

# ---------------------------------------------------------------- stair and lift
st = TK["stair"]
risers = 16
for i, s in enumerate(STOREYS[:-1]):
    z0 = FFL[s]
    rise = FF / risers
    steps = []
    for k in range(1, 8):              # flight 1, left, going towards rear
        y1 = 5.85 - 0.25 * (k - 1)
        y0 = 5.85 - 0.25 * k
        zt = z0 + k * rise
        steps.append([5.75, y0, max(z0, zt - rise - 0.15), 6.75, y1, zt])
    zl = z0 + 8 * rise
    add("IfcSlab", f"Stair mid-landing {s}-{STOREYS[i+1]}", s, "stair", [[5.75, 3.10, zl - SLAB, 7.85, 4.10, zl]], "DRAWN plan / CALCULATED level")
    for k in range(1, 8):              # flight 2, right, returning towards front
        y0 = 4.10 + 0.25 * (k - 1)
        y1 = 4.10 + 0.25 * k
        zt = zl + k * rise
        steps.append([6.85, y0, zt - rise - 0.15, 7.85, y1, zt])
    add("IfcStair", f"Stair {s} to {STOREYS[i+1]} (16 risers x {rise*1000:.1f} mm, going 250)", s, "stair", steps,
        "DRAWN plan / CALCULATED risers from ASSUMED floor height", risers=risers, riser=round(rise, 4))
for s in STOREYS:
    if s == "TERRACE":
        continue
    add("IfcTransportElement", f"Lift car zone {s} (clear shaft 1.40 x 1.50)", s, "lift",
        [[4.25, 3.15, FFL[s], 5.55, 4.55, FFL[s] + 0.02]], "DRAWN shaft")

# ---------------------------------------------------------------- tanks
ug = site["ug_tank"]
t = H["tank_wall_and_slab"]
o, n = ug["outer"], ug["inner"]
ztop = H["ug_tank_top"]
zb = ztop - t - 1.70
add("IfcTank", "U.G. water tank 3.00x2.05x1.70 (10,000 L label; 10,455 L gross)", "GF", "tank",
    [[o[0], o[1], zb - t, o[2], o[3], zb]] + [[r[0], r[1], zb, r[2], r[3], ztop - t] for r in rect_subtract(o, [n])] +
    [[o[0], o[1], ztop - t, o[2], o[3], ztop]], "DRAWN plan & depth / ASSUMED top level", volume_L=10455)
add("IfcBuildingElementProxy", "U.G. tank water (1.70 deep)", "GF", "water", [[n[0], n[1], zb, n[2], n[3], zb + 1.70]], "DRAWN")
oh = site["oht"]
o, n = oh["outer"], oh["inner"]
zb = CABIN_TOP
add("IfcTank", "O.H. water tank 2.10x2.20x1.50 (6,500 L label; 6,930 L gross)", "TERRACE", "tank",
    [[o[0], o[1], zb, o[2], o[3], zb + t]] + [[r[0], r[1], zb + t, r[2], r[3], zb + t + 1.5] for r in rect_subtract(o, [n])] +
    [[o[0], o[1], zb + t + 1.5, o[2], o[3], zb + 2 * t + 1.5]], "DRAWN plan & size / ASSUMED wall & base", volume_L=6930)
add("IfcBuildingElementProxy", "O.H. tank water", "TERRACE", "water", [[n[0], n[1], zb + t, n[2], n[3], zb + t + 1.5]], "DRAWN")

# ---------------------------------------------------------------- furniture + clearance checks
FS = AS["furniture_sizes"]
CL = AS["clearances"]


def access_zone(rect, side, depth):
    x0, y0, x1, y1 = rect
    return {"N": [x0, y0 - depth, x1, y0], "S": [x0, y1, x1, y1 + depth],
            "W": [x0 - depth, y0, x0, y1], "E": [x1, y0, x1 + depth, y1]}[side]


def quarter_disc_hits_rect(sw, rect):
    hx, hy = sw["hinge"]
    qx, qy = sw["q"]
    r = sw["r"]
    q = [min(hx, hx + qx * r), min(hy, hy + qy * r), max(hx, hx + qx * r), max(hy, hy + qy * r)]
    if not ovl(q, rect, 1e-3):
        return False
    ix = [max(q[0], rect[0]), max(q[1], rect[1]), min(q[2], rect[2]), min(q[3], rect[3])]
    cx = min(max(hx, ix[0]), ix[2])
    cy = min(max(hy, ix[1]), ix[3])
    return math.hypot(cx - hx, cy - hy) < r - 1e-3


def inside_union(rect, rects, step=0.02):
    x = rect[0] + step / 2
    while x < rect[2]:
        y = rect[1] + step / 2
        while y < rect[3]:
            if not any(r[0] - 1e-6 <= x <= r[2] + 1e-6 and r[1] - 1e-6 <= y <= r[3] + 1e-6 for r in rects):
                return False
            y += step
        x += step
    return True


report = []
violations = 0
for pk, rooms in FU.items():
    if pk.startswith("_"):
        continue
    fl = TK["floors"][pk]
    storeys = ["F1", "F2", "F3"] if pk == "F1-3" else ["F4"]
    spaces = {sp["name"]: sp for sp in fl["spaces"]}
    walls = fl["walls"]
    swings = [{"id": d["id"], "hinge": d["hinge"], "r": d["width"], "q": d["quadrant"]} for d in DOORS.get(pk, [])]
    for room, items in rooms.items():
        sp = spaces[room]
        fixed, zones = [], []
        for it in items:
            sz = FS[it["type"]]
            r = it["rect"]
            dims = sorted([round(r[2] - r[0], 3), round(r[3] - r[1], 3)], reverse=True)
            want = sorted([sz[0], sz[1]], reverse=True)
            if any(abs(a - b) > 0.011 for a, b in zip(dims, want)):
                report.append(f"| {pk} | {room} | {it['type']} | SIZE | rect {dims} != catalogue {want} |")
                violations += 1
            fixed.append((it["type"], r))
            dep = {"queen_bed": CL["queen_bed_sides"], "single_bed": CL["single_bed_access_side"],
                   "wardrobe_3door_sliding": CL["sliding_wardrobe_front"]}.get(it["type"], CL["desk_chair_zone"])
            if it.get("zones"):                    # explicit (trimmed) zones, e.g. bed with a bedside table at its head
                zones += [(f"{it['type']} access {it['access'][0]}", z) for z in it["zones"]]
            else:
                for side in it["access"]:
                    zones.append((f"{it['type']} access {side}", access_zone(r, side, dep)))
        lines = []
        # rule: fixed furniture inside room, not overlapping walls/other fixed/any clearance or swing
        for nm, r in fixed:
            ok = inside_union(r, sp["rects"])
            lines.append(("inside room", nm, ok))
            for w in walls:
                if ovl(r, w, 1e-3):
                    lines.append((f"clear of wall {w}", nm, False))
            for nm2, r2 in fixed:
                if r2 is not r and ovl(r, r2, 1e-3):
                    lines.append((f"overlaps {nm2}", nm, False))
            for zn, zr in zones:
                if not zn.startswith(nm) and ovl(r, zr, 1e-3):
                    lines.append((f"intrudes into clearance '{zn}'", nm, False))
            for sw in swings:
                if quarter_disc_hits_rect(sw, r):
                    lines.append((f"intrudes into door swing {sw['id']}", nm, False))
        # rule: clearance zones must be inside the room (usable)
        for zn, zr in zones:
            ok = inside_union(zr, sp["rects"])
            lines.append(("zone inside room", zn, ok))
        bad = [l for l in lines if not l[2]]
        violations += len(bad)
        status = "PASS" if not bad else "FAIL: " + "; ".join(f"{b[1]} {b[0]}" for b in bad)
        report.append(f"| {pk} | {room} | {', '.join(i['type'] for i in items)} | {len(lines)} checks | {status} |")
        for s in storeys:
            z0 = FFL[s]
            for nm, r in fixed:
                hgt = FS[nm][2]
                add("IfcFurniture", f"{s} {room} {nm.replace('_', ' ')}", s, "furniture",
                    [[r[0], r[1], z0, r[2], r[3], z0 + hgt]], "ASSUMED position / brief size")
            for zn, zr in zones:
                add("IfcBuildingElementProxy", f"{s} {room} clearance: {zn}", s, "clearance",
                    [[zr[0], zr[1], z0 + 0.01, zr[2], zr[3], z0 + 0.02]], "ASSUMED")

# door swings vs walls (every door swing must work)
swing_report = []
for pk in ["GF", "F1-3", "F4"]:
    fl = TK["floors"][pk]
    for d in DOORS.get(pk, []):
        sw = {"hinge": d["hinge"], "r": d["width"], "q": d["quadrant"]}
        hits = [w for w in fl["walls"] if quarter_disc_hits_rect(sw, w)]
        swing_report.append(f"| {pk} | {d['id']} | {d['width']:.2f} | {d['tag']} | "
                            f"{'PASS' if not hits else 'FAIL: hits wall ' + str(hits)} |")
        violations += len(hits)


# ---------------------------------------------------------------- model vs takeoff (ray tests on model walls)
def model_clear(storey, rect, axis):
    """Distance between nearest model wall faces through the centre of rect along axis, at FFL+2.5
    (above door/window heads, so headers count as wall)."""
    z = FFL[storey] + 2.5
    cx, cy = (rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2
    lo, hi = -1e9, 1e9
    for e in elements:
        if e["storey"] != storey or e["cls"] not in ("IfcWall", "IfcRailing"):
            continue
        for b in e["boxes"]:
            if not (b[2] <= z <= b[5]):
                continue
            if axis == "x" and b[1] <= cy <= b[4]:
                if b[3] <= cx + 1e-6:
                    lo = max(lo, b[3])
                if b[0] >= cx - 1e-6:
                    hi = min(hi, b[0])
            if axis == "y" and b[0] <= cx <= b[3]:
                if b[4] <= cy + 1e-6:
                    lo = max(lo, b[4])
                if b[1] >= cy - 1e-6:
                    hi = min(hi, b[1])
    return hi - lo if hi < 1e8 and lo > -1e8 else None


cmp_rows = []
for s, pk in [("GF", "GF"), ("F1", "F1-3"), ("F4", "F4")]:
    for sp in TK["floors"][pk]["spaces"]:
        if sp["name"].startswith("STILT") or "TERRACE" in sp["name"]:
            continue
        main = max(sp["rects"], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
        tx, ty = main[2] - main[0], main[3] - main[1]
        mx, my = model_clear(s, main, "x"), model_clear(s, main, "y")
        f = lambda v: "open" if v is None else f"{v:.3f}"
        dx = "" if mx is None else f"{(mx - tx)*1000:+.0f}"
        dy = "" if my is None else f"{(my - ty)*1000:+.0f}"
        cmp_rows.append(f"| {s} | {sp['name']} | {tx:.3f} x {ty:.3f} | {f(mx)} x {f(my)} | {dx} / {dy} | {sp.get('label') or ''} |")

# ---------------------------------------------------------------- outputs
scene = {"about": "Bella Vita 2 coordination model (Phase 2). Coordinates: plan X, plan Y (towards road), Z up (m).",
         "ffl": FFL, "cabin_top": CABIN_TOP, "storeys": STOREYS, "elements": elements}
(ROOT / "model/scene.json").write_text(json.dumps(scene, separators=(",", ":")))

cnt = {}
for e in elements:
    cnt[e["cls"]] = cnt.get(e["cls"], 0) + 1
md = ["# Model checks (Phase 2, generated by tools/build_model.py)", "",
      "## Levels used (ASSUMED, see model/assumptions.json)", "",
      "| Storey | FFL (m above road) |", "|---|---|"] + [f"| {k} | {v:.2f} |" for k, v in FFL.items()] + [
      f"| Stair cabin / lift roof top | {CABIN_TOP:.2f} |", "",
      "## Element count", "", "| IFC class | Count |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(cnt.items())] + [
      "", "## Furniture and clearance checks", "",
      "Rules: fixed furniture inside the room, clear of walls, other furniture, every clearance zone and every door-swing quarter-disc; "
      "every clearance zone inside the room. Clearance zones may overlap each other (allowed by the brief).", "",
      "| Plan | Room | Furniture | Checks | Result |", "|---|---|---|---|---|"] + report + [
      "", "## Door swings vs walls", "", "| Plan | Door | Leaf (m) | Swing source | Result |", "|---|---|---|---|---|"] + swing_report + [
      "", f"**Total violations: {violations}**", "",
      "## Model vs takeoff (clear dimensions)", "",
      "Clear distance between the model's wall faces, measured through the centre of each space's largest rectangle at FFL+2.5 m (above door/window heads) "
      "(X then Y). 'open' = no wall on that line (space opens into another). Difference in mm.", "",
      "| Storey | Space | Takeoff main (m) | Model clear (m) | Diff X / Y (mm) | Drawing label |", "|---|---|---|---|---|---|"] + cmp_rows
(ROOT / "docs/model-checks.md").write_text("\n".join(md) + "\n")
print(f"elements {len(elements)}  violations {violations}")
print("\n".join(report + swing_report))
