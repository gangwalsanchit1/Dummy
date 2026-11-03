#!/usr/bin/env python3
"""Floor 1 furniture fit (family brief, feet and inches).

STANDARD KIT (family: "everyone having similar things"; 2 students = 2 of everything), from assumptions.json standard_kit:
ROOM-2         : 2 students - each: Centaur single bed, Tinker, kit wardrobe, kit study table
ROOM-1, 3, 4   : 1 student  - Orion queen bed, Tinker, kit wardrobe, kit study table (no sofa: it fits only one room)
(ROOM-3 was twin; it cannot take two full kits, so the family made it single on 03.11.2026.)
ROOM-4 keeps the family rule (queen with one long side on a wall + Tinker on the open side at the head;
study table and wardrobe on the study wall where the wardrobe was).
Everything else is searched ("move things around and optimise"), with every check: inside the drawn room,
clear of walls / other items / door swings / clearance zones, clearance zones inside the room, and a
1'-9 5/8" (0.55 m) walking path from the door to every clearance zone and the toilet door.
Writes model/furniture.json (F1-3 part) and docs/floor1-fit.md.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import fit_furniture as F  # noqa: E402
from units import ftin  # noqa: E402

FS, CL = F.FS, F.CL
ovl, zone, inside, touches_wall, wall_vals = F.ovl, F.zone, F.inside, F.touches_wall, F.wall_vals
TW, TD = FS["tinker_side_table"][:2]
TRIM = CL["queen_head_table_trim"]
KIT = F.AS["standard_kit"]  # the same items for every student (family: "everyone having similar things")
KNAME = {"twill_wardrobe": "Twill wardrobe", "gingham_wardrobe": "Gingham wardrobe", "sage_desk": "Sage study table"}
KNAME.update({k: v.get("name", k) for k, v in KIT.get("desk_types", {}).items()})
CHAIR, WFRONT, BSIDE, LEG = CL["desk_chair_zone"], CL["sliding_wardrobe_front"], CL["single_bed_access_side"], CL["sofa_legroom"]


def wall_items(room, typ, front, allow_grey=False, only_wall_x=None):
    """Items with their back on a wall; clearance zone of depth `front` in front."""
    w, d = FS[typ][:2]
    out = []
    for (dx, dy) in ((w, d), (d, w)):
        for x in wall_vals(room, room.bb[0], room.bb[2] - dx, dx, "x"):
            for y in wall_vals(room, room.bb[1], room.bb[3] - dy, dy, "y"):
                r = [round(x, 3), round(y, 3), round(x + dx, 3), round(y + dy, 3)]
                backs = [("y", r[1], r[0], r[2], "S"), ("y", r[3], r[0], r[2], "N")] if dx > dy else [("x", r[0], r[1], r[3], "E"), ("x", r[2], r[1], r[3], "W")]
                for b in backs:
                    if not touches_wall(b[:4], room.walls):
                        continue
                    if only_wall_x is not None and not (b[0] == "x" and abs(b[1] - only_wall_x) < 1e-3 and b[4] == "E"):
                        continue
                    in_grey = any(r[0] >= g[0] - 1e-3 and r[2] <= g[2] + 1e-3 and r[1] >= g[1] - 1e-3 and r[3] <= g[3] + 1e-3 for g in room.grey)
                    if not allow_grey and not in_grey and any(ovl(r, g) for g in room.grey):
                        continue
                    z = zone(r, b[4], front)
                    if F.blocks_window(room, r, FS[typ][2]):
                        continue
                    if FS[typ][2] > 1.0 and ovl(r, room.switch_zone):   # keep the switchboard beside the door reachable
                        continue
                    if room.ok_fixed(r, [], []) and inside(z, room.rects) and not any(ovl(z, wl) for wl in room.walls):
                        out.append({"type": typ, "rect": r, "access": [b[4]], "zones": [[round(v, 3) for v in z]], "grey": in_grey, "fixed": [r]})
    return out


def single_beds(room):
    """Centaur single: head or long side on a wall; 0.60 m on the open long side; Tinker at the head on that side."""
    L, W = FS["centaur_single_bed"][:2]
    out = []
    for (lx, ly) in ((L, W), (W, L)):
        long_x = lx > ly
        for x in wall_vals(room, room.bb[0], room.bb[2] - lx, lx, "x"):
            for y in wall_vals(room, room.bb[1], room.bb[3] - ly, ly, "y"):
                r = [round(x, 3), round(y, 3), round(x + lx, 3), round(y + ly, 3)]
                if any(ovl(r, g) for g in room.grey) or not room.ok_fixed(r, [], []):
                    continue
                heads = [("W", ("x", r[0], r[1], r[3])), ("E", ("x", r[2], r[1], r[3]))] if long_x else [("N", ("y", r[1], r[0], r[2])), ("S", ("y", r[3], r[0], r[2]))]
                longs = [("N", ("y", r[1], r[0], r[2])), ("S", ("y", r[3], r[0], r[2]))] if long_x else [("W", ("x", r[0], r[1], r[3])), ("E", ("x", r[2], r[1], r[3]))]
                for hd, he in heads:
                    if not touches_wall(he, room.walls):
                        continue
                    hs = {"W": [r[0], r[1], r[0] + 0.08, r[3]], "E": [r[2] - 0.08, r[1], r[2], r[3]],
                          "N": [r[0], r[1], r[2], r[1] + 0.08], "S": [r[0], r[3] - 0.08, r[2], r[3]]}[hd]
                    if F.blocks_window(room, hs, 9.9):  # no bed head against a window (headboard 0.96 m is above the sill anyway)
                        continue
                    for side, _ in longs:
                        z = zone(r, side, BSIDE)
                        if not inside(z, room.rects) or any(ovl(z, wl) for wl in room.walls):
                            continue
                        t = tinker(r, hd, side, long_x)
                        if not room.ok_fixed(t, [r], []):
                            continue
                        zt = trim(z, hd)
                        walls_long = sum(touches_wall(e, room.walls) for _, e in longs)
                        out.append({"type": "centaur_single_bed", "rect": r, "access": [side], "zones": [[round(v, 3) for v in zt]], "head": hd,
                                    "fixed": [r, t], "table": t, "score": walls_long})
    out.sort(key=lambda it: -it["score"])
    return out


def tinker(r, hd, side, long_x):
    if long_x:
        x0 = r[0] if hd == "W" else r[2] - TD
        y0 = r[3] if side == "S" else r[1] - TW
        return [round(x0, 3), round(y0, 3), round(x0 + TD, 3), round(y0 + TW, 3)]
    y0 = r[1] if hd == "N" else r[3] - TD
    x0 = r[2] if side == "E" else r[0] - TW
    return [round(x0, 3), round(y0, 3), round(x0 + TW, 3), round(y0 + TD, 3)]


def trim(z, hd):
    return {"W": [z[0] + TRIM, z[1], z[2], z[3]], "E": [z[0], z[1], z[2] - TRIM, z[3]],
            "N": [z[0], z[1] + TRIM, z[2], z[3]], "S": [z[0], z[1], z[2], z[3] - TRIM]}[hd]


def queen_beds(room, rule):
    out = []
    for b in F.lux_beds(room, rule):
        B, T = b["bed"], b["table"]
        r = B["rect"]
        hs = {"W": [r[0], r[1], r[0] + 0.08, r[3]], "E": [r[2] - 0.08, r[1], r[2], r[3]],
              "N": [r[0], r[1], r[2], r[1] + 0.08], "S": [r[0], r[3] - 0.08, r[2], r[3]]}[B["head"]]
        if F.blocks_window(room, hs, 9.9):  # no bed head against a window
            continue
        out.append({"type": "orion_queen_bed", "rect": B["rect"], "access": B["access"], "zones": B["zones"], "head": B["head"],
                    "fixed": [B["rect"], T["rect"]], "table": T["rect"], "score": 2 if rule == "both" else 0})
    return out


TWIN_GAP = 0.30  # ASSUMED: two students' single beds never pushed together; at least 1'-0" between them


def compat(a, b):
    if any(ovl(p, q) for p in a["fixed"] for q in b["fixed"]):
        return False
    if a["type"].endswith("desk") and b["type"].endswith("desk") and any(ovl(z, y) for z in a["zones"] for y in b["zones"]):
        return False  # two students' chairs may not use the same floor space
    if a["type"] == b["type"] == "centaur_single_bed":
        ra, rb = a["rect"], b["rect"]
        if max(rb[0] - ra[2], ra[0] - rb[2], rb[1] - ra[3], ra[1] - rb[3]) < TWIN_GAP - 1e-3:
            return False
    return not any(ovl(p, z) for p in a["fixed"] for z in b["zones"]) and not any(ovl(q, z) for q in b["fixed"] for z in a["zones"])


def search(room, slots, max_walk=25000, want=6, optional=None):
    """DFS over slots (list of candidate lists); returns up to `want` complete layouts (+ optional item if it fits)."""
    found, walks = [], [0]

    def walk(placed):
        walks[0] += 1
        ok, _ = room.walkable([r for p in placed for r in p["fixed"]], [(p["type"], z) for p in placed for z in p["zones"]])
        return ok

    def dfs(i, placed, last):
        if len(found) >= want or walks[0] > max_walk:
            return
        if i == len(slots):
            if walk(placed):
                extra = None
                if optional:
                    for o in optional:
                        if all(compat(o, p) for p in placed) and walk(placed + [o]):
                            extra = o
                            break
                found.append((list(placed), extra))
            return
        key, cands = slots[i]
        start = last.get(key, -1) + 1
        for j in range(start, len(cands)):
            c = cands[j]
            if all(compat(c, p) for p in placed):
                placed.append(c)
                prune = i < len(slots) - 1 and slots[i + 1][0] != key
                if not prune or walk(placed):
                    nl = dict(last)
                    nl[key] = j
                    dfs(i + 1, placed, nl)
                placed.pop()
                if len(found) >= want or walks[0] > max_walk:
                    return
    dfs(0, [], {})
    return found


def flatten(layout, extra):
    out = []
    for it in layout + ([extra] if extra else []):
        out.append({k: it[k] for k in ("type", "rect", "access", "zones") if k in it} | ({"head": it["head"]} if "head" in it else {}))
        if it.get("table"):
            out.append({"type": "tinker_side_table", "rect": it["table"], "access": []})
    return out


def main():
    TK = F.TK
    res, rep = {}, []
    rooms = {"ROOM-1": ("F-D1", ["F-D1T"]), "ROOM-2": ("F-D2", ["F-D2T"]), "ROOM-3": ("F-D3", ["F-D3T"]), "ROOM-4": ("F-D4", ["F-D4T"])}
    only = sys.argv[1:]  # optional: re-fit only these rooms, keep the others from model/furniture.json
    old_fu = json.loads((ROOT / "model/furniture.json").read_text())["F1-3"]
    old_rep = {l.split(" | ")[0][2:]: l for l in (ROOT / "docs/floor1-fit.md").read_text().split("\n") if l.startswith("| ROOM")}
    for name, (door, others) in rooms.items():
        if only and name not in only:
            res[name], _ = old_fu[name], rep.append(old_rep[name])
            continue
        room = F.Room("F1-3", name, door, others)
        is4 = name == "ROOM-4"
        chosen, note = None, ""
        if name in KIT["twin_rooms"]:
            beds = single_beds(room)
            wards = wall_items(room, KIT["wardrobe"], WFRONT)
            desks = wall_items(room, KIT["desk"], CHAIR)
            low = wall_items(room, "nohutch_desk", CHAIR)
            global TWIN_GAP
            # 1) full kit, beds apart; 2) beds side by side; 3) beds side by side, one desk without hutch (under a window)
            for gap, dslots, tag in ((0.30, [("desk", desks), ("desk", desks)], "beds 1'-0\" or more apart"),
                                     (0.0, [("desk", desks), ("desk", desks)], "**beds side by side** (the room is too small to keep them apart)"),
                                     (0.0, [("desk", desks), ("desk2", low)], "**beds side by side**, and **one study table without the hutch** because it sits under the window")):
                TWIN_GAP = gap
                found = search(room, [("bed", beds), ("bed", beds), ("ward", wards), ("ward", wards)] + dslots, max_walk=60000)
                if found:
                    chosen = max(found, key=lambda f: sum(p.get("score", 0) for p in f[0]))
                    note = f"2 students, each: Centaur single bed, Tinker, {KNAME[KIT['wardrobe']]}, {KNAME[KIT['desk']]}; {tag}"
                    break
            TWIN_GAP = 0.30
        else:
            for rule in (["wall"] if is4 else ["both", "wall"]):
                beds = queen_beds(room, rule)
                wards = wall_items(room, KIT["wardrobe"], WFRONT, allow_grey=is4, only_wall_x=4.45 if is4 else None)
                desks = wall_items(room, KIT["desk"], CHAIR, allow_grey=is4, only_wall_x=4.45 if is4 else None)
                found = search(room, [("bed", beds), ("ward", wards), ("desk", desks)], max_walk=60000, want=3)
                if found:
                    chosen = found[0]
                    note = (f"1 student: Orion queen ({'0.60 m both sides' if rule == 'both' else 'long side on wall'}), Tinker, "
                            f"{KNAME[KIT['wardrobe']]}, {KNAME[KIT['desk']]}")
                    break
        if not chosen:
            rep.append(f"| {name} | **no layout found** |")
            print(name, "NO LAYOUT", flush=True)
            continue
        res[name] = flatten(*chosen)
        rep.append(f"| {name} | {note} |")
        print(name, note, flush=True)
    FU = json.loads((ROOT / "model/furniture.json").read_text())
    FU["F1-3"] = res
    FU["_about"] = "Floor 1 (F1-3) by tools/fit_floor1.py: standard kit per student (assumptions.json standard_kit). F4 from tools/fit_furniture.py."
    (ROOT / "model/furniture.json").write_text(json.dumps(FU, indent=1))
    md = ["# Floor 1 furniture fit (generated by tools/fit_floor1.py)", "",
          f"Standard kit, the same for every student: bed, Tinker side table, {KNAME[KIT['wardrobe']]}, {KNAME[KIT['desk']]} and chair. "
          "ROOM-2: **two students, two of everything** (Centaur single beds, at least 1'-0\" apart). ROOM-1, ROOM-3 and ROOM-4: **one student** (Orion queen). "
          f"Clearances: bed open side {ftin(BSIDE)}, wardrobe front {ftin(WFRONT)}, chair pull-out {ftin(CHAIR)}, walking path {ftin(0.55)}.", "",
          "| Room | Result |", "|---|---|"] + rep
    (ROOT / "docs/floor1-fit.md").write_text("\n".join(md) + "\n")


if __name__ == "__main__":
    main()
