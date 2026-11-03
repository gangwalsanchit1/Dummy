#!/usr/bin/env python3
"""3D presentation render of one floor with the real Wakefit furniture at true size, in the style of the family's pictures
(top-down "dollhouse" view, walls cut at 1.5 m, warm tiles, labelled rooms).

Usage: THREE_DIR=<folder of the three@0.160.0 npm package> python3 tools/render3d.py <scenario.json> <out.jpg>
       e.g. model/scenarios/final-floor1.json docs/final/floor1-3-render.jpg
            model/scenarios/final-floor4.json docs/final/floor4-render.jpg
       (get three with `npm pack three@0.160.0` and untar it; it is not committed)

Walls, doors, windows and spaces come from the scenario's takeoff (the architect's drawing), columns from
model/structure.json, furniture from the scenario layouts at the sizes in model/assumptions.json. Rugs, plants, lamps,
laptops, WCs and terrace furniture are decoration only. Builds a scene description, then tools/render3d.js draws it.
"""
import json
import math
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from units import ftin as _ftin, sqft  # noqa: E402
from columns import columns  # noqa: E402
from takeoff import load_takeoff  # noqa: E402

FR = {" 1/8": "⅛", " 1/4": "¼", " 3/8": "⅜", " 1/2": "½", " 5/8": "⅝", " 3/4": "¾", " 7/8": "⅞"}


def ft(m):
    t = _ftin(m)
    for a, b in FR.items():
        t = t.replace(a, b)
    return t


SC = json.loads(Path(sys.argv[1]).read_text())
OUT = Path(sys.argv[2])
PK = SC.get("floor", "F1-3")
TK = SC["TK"]
AS = json.loads((ROOT / "model/assumptions.json").read_text())
FS, CAT, HT = AS["furniture_sizes"], AS["wakefit_catalog"], AS["heights"]
RAW = load_takeoff(raw=True)
WH = 1.5                                  # wall cut height in the render (m)
L = TK["outline"][3]
SLAB = max([L] + [s["rects"][0][3] for s in TK["spaces"] if "TERRACE" in s["name"]] + [r[3] for r in TK.get("railings", [])])


def ovl(a, b, t=0.005):
    return min(a[2], b[2]) - max(a[0], b[0]) > t and min(a[3], b[3]) - max(a[1], b[1]) > t


# ---- walls: cut window openings out of the outer walls; terrace edges become parapets; thin walls in the stair are rails
walls = [list(w) for w in TK["walls"]]
windows = []
for w in TK.get("windows", []):
    x0, x1 = w["span_x"]
    for i, r in enumerate(walls):
        horiz = r[2] - r[0] > r[3] - r[1]
        edge = r[1] <= 0.001 if w["wall"] == "rear" else abs(r[3] - L) < 0.001
        if horiz and edge and r[0] <= x0 + 1e-6 and r[2] >= x1 - 1e-6:
            walls[i:i + 1] = [q for q in ([r[0], r[1], x0, r[3]], [x1, r[1], r[2], r[3]]) if q[2] - q[0] > 0.005]
            sill = HT["ventilator_sill"] if w["width"] < HT["ventilator_max_width"] else HT["window_sill"]
            windows.append({"rect": [x0, r[1], x1, r[3]], "sill": sill, "id": w["id"]})
            break
parapets = []
terr = [r for s in TK["spaces"] if "TERRACE" in s["name"] for r in s["rects"]]
for t in terr:
    nxt = []
    for r in walls:
        horiz = r[2] - r[0] > r[3] - r[1]
        outer = r[0] <= 0.001 or r[2] >= 7.999 or r[1] <= 0.001 or abs(r[3] - L) < 0.001
        a = b = None
        if outer and horiz and (abs(r[3] - t[1]) < 0.02 or abs(r[1] - t[3]) < 0.02):
            a, b = max(r[0], t[0]), min(r[2], t[2])
            parts = ([r[0], r[1], a, r[3]], [a, r[1], b, r[3]], [b, r[1], r[2], r[3]])
        elif outer and not horiz and (abs(r[2] - t[0]) < 0.02 or abs(r[0] - t[2]) < 0.02):
            a, b = max(r[1], t[1]), min(r[3], t[3])
            parts = ([r[0], r[1], r[2], a], [r[0], a, r[2], b], [r[0], b, r[2], r[3]])
        if a is not None and b - a > 0.05:
            nxt += [q for k, q in enumerate(parts) if k != 1 and (q[2] - q[0]) * (q[3] - q[1]) > 1e-4]
            parapets.append(parts[1])
        else:
            nxt.append(r)
    walls = nxt
stair = RAW["stair"]
se = stair["enclosure_clear"]
rails = [r for r in walls if r[0] >= se[0] - 0.01 and r[2] <= se[2] + 0.01 and r[1] >= se[1] - 0.01 and r[3] <= se[3] + 0.01 and min(r[2] - r[0], r[3] - r[1]) < 0.12]
walls = [r for r in walls if r not in rails]
cols = [{"name": c["name"], "rect": c["rect"]} for c in columns(PK)]

# ---- lift door (sliding, shown closed) from the drawn opening
lift_doors = []
for o in TK["openings"]:
    if o["type"].startswith("lift"):
        import re
        ys = [float(v) for v in re.findall(r"[\d.]+", o["wall"])]
        lift_doors.append([o["span_x"][0], ys[0], o["span_x"][1], ys[-1]])

# ---- furniture
TAG = {"centaur_single_bed": "Centaur single bed", "orion_queen_bed": "Orion queen bed", "twill_wardrobe": "Twill",
       "gingham_wardrobe": "Gingham", "cabrera_desk": "Cabrera", "sage_desk": "Sage", "flipper_sofa": "Flipper sofa",
       "tv_42": 'TV 42"', "tv_40": 'TV 40"', "tv_32": 'TV 32"'}
TVH = {"tv_42": 0.53, "tv_40": 0.50, "tv_32": 0.41}
QUILT = ["#86A07F", "#D19580", "#C4B08F", "#93ABB1"]
items, bi = [], 0
for room, lay in SC["layouts"].items():
    for it in lay:
        t = it["type"]
        d = {"type": t, "rect": it["rect"], "room": room, "access": it.get("access", []), "head": it.get("head"),
             "h": TVH.get(t, FS[t][2] if len(FS[t]) > 2 else 0.6), "tag": TAG.get(t)}
        if t.endswith("_bed"):
            d["quilt"] = QUILT[bi % 2 if t == "centaur_single_bed" else 2 + bi % 2]
            bi += 1
        if t.endswith("desk") and it.get("zones"):
            d["chair"] = it["zones"][0]
        items.append(d)
for tvi in [i for i in items if i["type"].startswith("tv_")]:      # a TV above a desk: one tag for both
    for dk in items:
        if dk["type"].endswith("desk") and dk["room"] == tvi["room"] and ovl([tvi["rect"][0] - 0.1, tvi["rect"][1] - 0.1, tvi["rect"][2] + 0.1, tvi["rect"][3] + 0.1], dk["rect"]):
            dk["tag"] += " + " + tvi["tag"]
            tvi["tag"] = None

# ---- decoration: a rug beside each bed, a lamp on each Tinker (drawn in JS), plants and terrace furniture
decor = list(SC.get("decor", []))
rugs = []
for it in SC["layouts"].values():
    for b in it:
        if b["type"].endswith("_bed") and b.get("zones"):
            for z in b["zones"]:
                r = [z[0] + 0.06, z[1] + 0.06, z[2] - 0.06, z[3] - 0.06]
                if not any(ovl(r, q) for q in rugs):
                    rugs.append(r)
                    break
decor += [{"type": "rug", "rect": r} for r in rugs]
DECOR = {"F1-3": [{"type": "plant", "rect": [0.26, 0.2, 0.6, 0.56]},          # ROOM-3 lounge nook, beside the sofa
                  {"type": "plant", "rect": [7.42, 0.2, 7.78, 0.56]},          # ROOM-4 window corner
                  {"type": "plant", "rect": [3.2, 5.0, 3.5, 5.3]}],            # lobby
         "F4": [{"type": "plant", "rect": [3.62, 2.25, 3.98, 2.6]},           # suite, by the terrace passage
                {"type": "plant", "rect": [4.19, 4.79, 4.47, 5.07]}]}          # lobby, beside the lift
decor += DECOR.get(PK, [])

# WCs (decoration): centred on the toilet's outer wall
wcs = []
for s in TK["spaces"]:
    if "TOILET" in s["name"]:
        r = s["rects"][0]
        cx = (r[0] + r[2]) / 2
        wcs.append({"x": cx, "y": r[1] if r[1] < 0.2 else r[3], "back": "N" if r[1] < 0.2 else "S"})


# ---- labels
def free_spot(r, avoid):
    best, bp = -1, None
    nx, ny = max(2, int((r[2] - r[0]) / 0.08)), max(2, int((r[3] - r[1]) / 0.08))
    for i in range(1, nx):
        for j in range(1, ny):
            x, y = r[0] + i * (r[2] - r[0]) / nx, r[1] + j * (r[3] - r[1]) / ny
            dm = min([min(x - r[0], r[2] - x, (y - r[1]) * 1.6, (r[3] - y) * 1.6)]
                     + [math.hypot(max(f[0] - x, 0, x - f[2]), (max(f[1] - y, 0, y - f[3])) * 1.6) for f in avoid])
            if dm > best:
                best, bp = dm, (x, y)
    return bp


avoid = [i["rect"] for i in items] + [d["rect"] for d in decor if d["type"] != "rug"]
swings = [[d["hinge"][0] - d["width"], d["hinge"][1] - d["width"], d["hinge"][0] + d["width"], d["hinge"][1] + d["width"]] for d in SC["doors"]]
labels = []
for s in TK["spaces"]:
    nm = s["name"]
    r = max(s["rects"], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
    size = f"{ft(r[2] - r[0])} × {ft(r[3] - r[1])}"
    area = sqft(sum((q[2] - q[0]) * (q[3] - q[1]) for q in s["rects"]))
    if "TOILET" in nm:
        labels.append({"kind": "small", "lines": ["TOILET", size], "at": [(r[0] + r[2]) / 2, (r[1] + r[3]) / 2 + 0.25], "h": 0.05})
    elif nm.startswith("ROOM"):
        x, y = free_spot(r, avoid)
        labels.append({"kind": "room", "lines": [nm.replace(" (suite)", " · SUITE"), size, area], "at": [x, y], "h": 0.05})
    elif nm == "STAIR":
        labels.append({"kind": "room", "lines": ["STAIR", size], "at": [7.35, 6.45], "h": 0.05})
        labels.append({"kind": "up", "lines": ["UP ↑"], "at": [6.25, 5.2], "h": 0.7})
    elif "TERRACE" in nm:
        if r[3] > L:
            labels.append({"kind": "room", "lines": ["FRONT TERRACE", f"{ft(r[2] - r[0])} × {ft(0.8)} clear · no door onto it on the drawing"], "at": [4.0, 11.38], "h": 0.45})
        else:
            x, y = free_spot(r, avoid)
            labels.append({"kind": "room", "lines": ["PRIVATE TERRACE", size], "at": [x, y], "h": 0.05})
    else:
        x, y = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        if nm == "LOBBY":
            x, y = 4.37, 5.9
        labels.append({"kind": "room", "lines": [nm, size], "at": [x, y], "h": 0.05})

# ---- title, dimensions and the Wakefit legend
cnt = Counter(i["type"] for i in items)
LEG = {"centaur_single_bed": "Wakefit Centaur single storage bed", "orion_queen_bed": "Wakefit Orion queen storage bed",
       "tinker_side_table": "Wakefit Tinker bedside table", "twill_wardrobe": "Wakefit Twill 2-door compact wardrobe",
       "gingham_wardrobe": "Wakefit Gingham 2-door wardrobe with mirror", "cabrera_desk": "Wakefit Cabrera study table",
       "sage_desk": "Wakefit Sage study table", "flipper_sofa": "Wakefit Flipper 2-seater sofa cum bed",
       "tv_42": "Wall TV 42\" (any brand)", "tv_40": "Wall TV 40\" (any brand)", "tv_32": "Wall TV 32\" (any brand)"}
legend = [{"name": LEG[t], "size": f"{ft(FS[t][0])} × {ft(FS[t][1])}", "n": cnt[t], "wakefit": not t.startswith("tv_")}
          for t in LEG if cnt[t]]
students = sum(v for t, v in cnt.items() if t.endswith("_bed"))
title = {"F1-3": "TYPICAL FIRST, SECOND & THIRD FLOOR PLAN", "F4": "FOURTH FLOOR PLAN"}.get(PK, PK)
sub = (f"Bella Vita 2 · Plot C-89, Sector 12, Kharghar · {students} students per floor · real Wakefit furniture drawn at true size"
       + (" · family-approved layout 03.11.2026" if PK == "F1-3" else " · layout from the family's fourth-floor picture"))
dims = [{"a": [0, -0.45], "b": [8.0, -0.45], "text": f"{ft(8.0)} overall"},
        {"a": [-0.45, 0], "b": [-0.45, L], "text": f"{ft(L)}" + (" overall" if SLAB <= L + 0.01 else " to the front wall")}]
if SLAB > L + 0.01:
    dims.append({"a": [-0.45, L], "b": [-0.45, SLAB], "text": f"terrace {ft(SLAB - L)}", "small": True})

scene = {"floor": PK, "wh": WH, "outline": TK["outline"], "slab": SLAB, "walls": walls, "parapets": parapets, "rails": rails,
         "railings": TK.get("railings", []), "windows": windows, "cols": cols, "doors": SC["doors"], "lift_doors": lift_doors,
         "spaces": TK["spaces"], "stair": stair, "items": items, "decor": decor, "wcs": wcs, "labels": labels,
         "road": PK == "F1-3", "road_text": f"6.00 M WIDE ROAD ({ft(6.0)}) · FRONT OF BUILDING", "title": title, "sub": sub,
         "legend": legend, "dims": dims,
         "note": "Not Wakefit: TVs (any brand), study chairs (any), and the rugs, plants, lamps, WCs" + (" and terrace furniture" if terr else "") + ", which are decoration. "
                 "Wood finishes are illustrative: choose them on the Wakefit page. Walls, doors and windows from the architect's AFTER O.C. drawing (03-08-2026); "
                 "columns from Agharkar rev R1" + (" (assumed to continue up to this floor; engineer to confirm)" if PK == "F4" else "") + ".",
         "view": {"w": 1200, "h": 1480 if PK == "F1-3" else 1420, "dpr": 2}}
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
    json.dump(scene, f)
if not os.environ.get("THREE_DIR"):
    sys.exit("set THREE_DIR to the folder of the three@0.160.0 npm package (npm pack three@0.160.0, then untar)")
r = subprocess.run(["node", str(ROOT / "tools/render3d.js"), f.name, str(OUT)])
os.unlink(f.name)
sys.exit(r.returncode)
