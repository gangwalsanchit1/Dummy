#!/usr/bin/env python3
"""Audit the floor 1 furniture layout (model/furniture.json, F1-3) against every rule, room by room.
Works the same for solver layouts and hand-designed ones. Writes docs/layout-audit.md (feet and inches).

Rules: inside the room; clear of walls, columns, door swings and each other; every clearance (bed side, wardrobe front,
chair) inside the room and free of furniture; chair and wardrobe-door space outside every door swing; two students never share a chair space or a wardrobe-door space;
wardrobes and desks flush on a plain wall (never on or proud of a column); bed heads on a wall; nothing taller than the
sill in front of a window; no bed head against a window; no tall item in the switch strip by the door; matching
wardrobes / desks line up on one wall or mirror each other (facing pairs that are offset are reported); no bed within
2'-11 3/8" of the toilet door and no bed head on a toilet wall (family: not right next to the bathroom); bed access strips stop
1'-0" short of the foot end (you get into bed at the pillow end or the middle); a 2'-0" walking path
from the door to every clearance, the toilet door and the room's window.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import fit_furniture as F  # noqa: E402
import fit_floor1 as G  # noqa: E402
from units import ftin  # noqa: E402

FU = json.loads((ROOT / "model/furniture.json").read_text())["F1-3"]
OUT = "docs/layout-audit.md"
BED_GAP = 0.0
WALK_OVR = {}
PK = "F1-3"
if len(sys.argv) > 1:      # audit a scenario file instead: python3 tools/check_layout.py model/scenarios/<name>.json
    SC = json.loads(Path(sys.argv[1]).read_text())
    PK = SC.get("floor", "F1-3")       # "F4" for the fourth floor
    F.TK["floors"][PK] = SC["TK"]
    F.AS["doors"][PK] = SC["doors"]
    FU = SC["layouts"]
    BED_GAP = SC.get("bed_side_gap", 0.0)
    WALK_OVR = SC.get("walk_override", {})
    OUT = f"docs/{Path(sys.argv[1]).stem}-audit.md"
DOORS = {"ROOM-1": ("F-D1", ["F-D1T"]), "ROOM-2": ("F-D2", ["F-D2T"]), "ROOM-3": ("F-D3", ["F-D3T"]), "ROOM-4": ("F-D4", ["F-D4T"])}
if PK == "F4":   # room door, then the toilet door first and any other door the room leads to (the suite's terrace)
    DOORS = {"ROOM-1": ("F4-D1", ["F4-D1T"]), "ROOM-2": ("F4-D2", ["F4-D2T"]), "ROOM-3 (suite)": ("F4-D3", ["F4-D3T", "F4-DT"])}
FS = F.FS
WALK = 0.60          # clear walking width everywhere a person walks (2'-0")
TOILET_GAP = 0.90    # family: you don't want your bed right next to the bathroom (no bed within 2'-11 3/8" of the toilet door)
TK = F.TK["floors"][PK]
AS_DOORS = {d["id"]: d for d in F.AS["doors"][PK]}


def rdist(a, b):
    return ((max(b[0] - a[2], a[0] - b[2], 0)) ** 2 + (max(b[1] - a[3], a[1] - b[3], 0)) ** 2) ** 0.5


def head_backed(e, walls):
    """bed head edge backed by wall faces up to 0.09 m behind it along its whole length (a column may leave a gap)."""
    ax, c, a0, a1 = e
    i, j = (0, 2) if ax == "x" else (1, 3)
    segs = sorted(((w[1], w[3]) if ax == "x" else (w[0], w[2])) for w in walls if abs(w[i] - c) < 0.1 or abs(w[j] - c) < 0.1)
    reach = a0 + 0.01
    for s0, s1 in segs:
        if s0 <= reach:
            reach = max(reach, s1)
    return reach >= a1 - 0.01


def toilet_walls(name):
    t = next(sp["rects"] for sp in TK["spaces"] if sp["name"] == name.split(" (")[0] + " TOILET")
    return [w for w in TK["walls"] if any(rdist(w, q) < 0.02 for q in t)]


def toilet_door(name):
    d = AS_DOORS[DOORS[name][1][0]]
    hx, hy = d["hinge"]
    qx, qy = d["quadrant"]
    w = d["width"]
    import re
    op = next(o for o in TK["openings"] if o["id"] == d["id"])          # the doorway in the wall, as drawn
    a, b = sorted(float(v) for v in re.findall(r"[\d.]+", op["wall"])[:2]) if "-" in op["wall"] else (float(re.findall(r"[\d.]+", op["wall"])[0]),) * 2
    if "span_x" in op:
        return [op["span_x"][0], a, op["span_x"][1], b]
    return [a, op["span_y"][0], b, op["span_y"][1]]


TWALLS = {n: toilet_walls(n) for n in FU}
TDOOR = {n: toilet_door(n) for n in TWALLS}


def edge_of(it):
    r = it["rect"]
    if it["type"].endswith("_bed"):
        sd = it["head"]
        return {"W": ("x", r[0], r[1], r[3]), "E": ("x", r[2], r[1], r[3]), "N": ("y", r[1], r[0], r[2]), "S": ("y", r[3], r[0], r[2])}[sd]
    sd = it["access"][0]
    return {"E": ("x", r[0], r[1], r[3]), "W": ("x", r[2], r[1], r[3]), "N": ("y", r[3], r[0], r[2]), "S": ("y", r[1], r[0], r[2])}[sd]


def audit(name, items):
    room = F.Room(PK, name, *DOORS[name])
    probs, notes = [], []
    tvs = [it for it in items if it["type"].startswith("tv_")]
    items = [it for it in items if not it["type"].startswith("tv_")]
    for tvi in tvs:            # wall-mounted TV: above the floor (bottom edge about 1.1 m), so only walls, windows, bed heads and tall items matter
        r = tvi["rect"]
        F.FLUSH = True
        if not F.touches_wall(edge_of(tvi), room.walls):
            probs.append("TV not on a plain wall")
        if F.blocks_window(room, r, 9.9):
            probs.append("TV over or beside a window opening")
        for o in items:
            if FS[o["type"]][2] > 1.05 and F.ovl([r[0] - 0.02, r[1] - 0.02, r[2] + 0.02, r[3] + 0.02], o["rect"]):
                probs.append(f"TV clashes with {o['type']}")
            if o["type"].endswith("_bed"):
                e = edge_of(o)
                hs = {"x": [e[1] - 0.1, e[2], e[1] + 0.1, e[3]], "y": [e[2], e[1] - 0.1, e[3], e[1] + 0.1]}[e[0]]
                if F.ovl(r, hs):
                    probs.append("TV above a bed head")
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        for o in items:
            if o["type"].endswith("_bed"):
                e = edge_of(o)
                px, py = ((e[1] + (0.3 if o["head"] == "W" else -0.3)), (e[2] + e[3]) / 2) if e[0] == "x" else ((e[2] + e[3]) / 2, e[1] + (0.3 if o["head"] == "N" else -0.3))
                notes.append(f"TV {ftin(((cx - px) ** 2 + (cy - py) ** 2) ** 0.5)} from a pillow")
            if o["type"].endswith("sofa"):
                q = o["rect"]
                notes.append(f"TV {ftin(((cx - (q[0] + q[2]) / 2) ** 2 + (cy - (q[1] + q[3]) / 2) ** 2) ** 0.5)} from the sofa")
    for i, it in enumerate(items):
        r, k = it["rect"], G.KIND(it["type"])
        if not F.inside(r, room.rects):
            probs.append(f"{it['type']} outside the room")
        if any(F.ovl(r, w) for w in room.walls):
            probs.append(f"{it['type']} hits a wall or column")
        if any(F.disc_hits(sw, r) for sw in room.swings):
            probs.append(f"{it['type']} inside a door swing")
        for z in it.get("zones", []):
            if not F.inside(z, room.rects) or any(F.ovl(z, w) for w in room.walls):
                probs.append(f"{it['type']} clearance runs out of the room")
            if (k in ("desk", "wardrobe") or it["type"].endswith("sofa")) and any(F.disc_hits(sw, z) for sw in room.swings):
                probs.append(f"{it['type']} {'chair' if k == 'desk' else 'legroom' if 'sofa' in k else 'door'} space is inside a door swing")
        for o in items[i + 1:]:
            if F.ovl(r, o["rect"]):
                probs.append(f"{it['type']} overlaps {o['type']}")
            for a, b in ((it, o), (o, it)):
                if any(F.ovl(a["rect"], z) for z in b.get("zones", [])) and not (a["type"] == "tinker_side_table" and b["type"].endswith("_bed")):
                    probs.append(f"{a['type']} stands in the clearance of {b['type']}")
            if G.KIND(o["type"]) == k and k in ("desk", "wardrobe"):
                if any(F.ovl(z, y) for z in it.get("zones", []) for y in o.get("zones", [])):
                    probs.append(f"two {k}s share one clearance")
                (sa, ba), (sb, bb) = G.orient(it), G.orient(o)
                if sa == sb and abs(ba - bb) < 0.005:
                    notes.append(f"{k}s line up on one wall")
                elif sa == G.OPP[sb] and G.span(it) == G.span(o):
                    notes.append(f"{k}s mirror each other")
                elif sa == G.OPP[sb]:
                    (a0, _), (b0, _) = G.span(it), G.span(o)
                    notes.append(f"{k}s face each other across the room, offset {ftin(abs(a0 - b0))}")
                else:
                    probs.append(f"{k}s are on walls at right angles")
        if k in ("desk", "wardrobe") or it["type"].endswith("sofa"):
            F.FLUSH = True
            if not F.touches_wall(edge_of(it), room.walls):
                probs.append(f"{it['type']} not flush on a plain wall")
            if F.blocks_window(room, r, FS[it["type"]][2]):
                probs.append(f"{it['type']} stands in front of a window")
            if FS[it["type"]][2] > 1.0 and F.ovl(r, room.switch_zone):
                probs.append(f"{it['type']} blocks the switchboard beside the door")
        if k == "bed" and BED_GAP:      # father: no bed in a corner; both long sides clear of walls and columns
            lx = (r[2] - r[0]) > (r[3] - r[1])
            g = [r[0] + 0.02, r[1] - BED_GAP, r[2] - 0.02, r[3] + BED_GAP] if lx else [r[0] - BED_GAP, r[1] + 0.02, r[2] + BED_GAP, r[3] - 0.02]
            if any(F.ovl(g, w, 0.0) for w in room.walls):
                probs.append(f"bed long side closer than {ftin(BED_GAP)} to a wall (stuck in a corner)")
            else:
                gaps = []
                for side in ((r[1], -1), (r[3], 1)) if lx else ((r[0], -1), (r[2], 1)):
                    c, sg = side
                    d = min([(w[1] - c) if sg > 0 else (c - w[3]) for w in room.walls if lx and w[0] < r[2] and w[2] > r[0] and ((w[1] >= c) if sg > 0 else (w[3] <= c))]
                            + [(w[0] - c) if sg > 0 else (c - w[2]) for w in room.walls if not lx and w[1] < r[3] and w[3] > r[1] and ((w[0] >= c) if sg > 0 else (w[2] <= c))] or [9])
                    gaps.append(d)
                notes.append(f"bed clear of walls on both long sides ({ftin(min(gaps))} min)")
        if k == "bed":
            e = edge_of(it)
            if not head_backed(e, room.walls):
                probs.append("bed head not against a wall")
            if head_backed(e, TWALLS[name]):
                probs.append("bed head against the toilet wall (flushing at night)")
            dd = rdist(r, TDOOR[name])
            if dd < TOILET_GAP:
                probs.append(f"bed only {ftin(dd)} from the toilet door (needs {ftin(TOILET_GAP)})")
            else:
                notes.append(f"bed {ftin(dd)} from the toilet door")
            hs = {"x": [e[1] - 0.04, e[2], e[1] + 0.04, e[3]], "y": [e[2], e[1] - 0.04, e[3], e[1] + 0.04]}[e[0]]
            if F.blocks_window(room, hs, 9.9):
                probs.append("bed head against a window")
            if F.blocks_window(room, r, 9.9):
                notes.append("a bed runs along a window (window opened over the bed)")
    for w in TK["windows"]:
        if w["serves"].split(" ")[0] == name.split(" ")[0] and "toilet" not in w["serves"].lower():
            cx = (w["span_x"][0] + w["span_x"][1]) / 2 - 0.225
            y0 = 0.15 if w["wall"] == "rear" else TK["outline"][3] - 0.15 - 0.45
            room.targets_doors.append({"id": "window " + w["id"], "hinge": [cx, y0], "quadrant": [1, 1], "width": 0.45})
    wk = WALK_OVR.get(name, WALK)
    if wk < WALK:
        notes.append(f"walkway {ftin(wk)} allowed here by the family (rule {ftin(WALK)})")
    F.PATH_R = wk / 2
    ok, why = room.walkable([it["rect"] for it in items], [(it["type"], z) for it in items for z in it.get("zones", [])])
    if not ok:
        if "window" in why:
            notes.append("window reached over a bed (no standing path to it)")
            room.targets_doors = [d for d in room.targets_doors if not d["id"].startswith("window")]
            ok, why = room.walkable([it["rect"] for it in items], [(it["type"], z) for it in items for z in it.get("zones", [])])
        if not ok:
            probs.append("walking path: " + why)
    return probs, sorted(set(notes))


if __name__ == "__main__":
    md = ["# Floor 1 layout audit (generated by tools/check_layout.py)", "",
          "Every room's final layout checked against every rule (see the tool's header). Walking path "
          f"{ftin(WALK)}; no bed within {ftin(TOILET_GAP)} of the toilet door and no bed head on a toilet wall; bed side {ftin(G.BSIDE)}; wardrobe front {ftin(G.WFRONT)}; chair {ftin(G.CHAIR)}.", "",
          "| Room | Result | Problems | Notes |", "|---|---|---|---|"]
    allok = True
    for name, items in FU.items():
        pr, nt = audit(name, items)
        allok &= not pr
        md.append(f"| {name} | {'PASS' if not pr else '**FAIL**'} | {'; '.join(sorted(set(pr))) or '-'} | {'; '.join(nt) or '-'} |")
        print(name, "PASS" if not pr else "FAIL", sorted(set(pr)), nt)
    (ROOT / OUT).write_text("\n".join(md) + "\n")
    sys.exit(0 if allok else 1)
