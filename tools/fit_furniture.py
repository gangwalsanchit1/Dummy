#!/usr/bin/env python3
"""Fit furniture into the DRAWN rooms: double (shared queen) where it fits, otherwise single.

For every room on F1-3 and F4 the script searches positions (0.05 m grid) for
  bed (queen first, single if no queen layout passes), 1 sliding wardrobe, 1 desk
and accepts a layout only if:
  * every item is inside the drawn room, clear of walls, the other items, every door-swing
    quarter-disc and every clearance zone; every clearance zone lies inside the room
    (queen: 0.60 m on both long sides - brief; single: 0.60 m one side; wardrobe front 0.60;
    desk chair zone 0.75 - ASSUMED)
  * the wardrobe sits in the architect's grey strip where one is drawn (takeoff Q7)
  * a 0.55 m wide walking path (ASSUMED) connects the room door to every clearance zone and
    to the toilet / terrace door.
Room and toilet geometry is never changed. Furniture sizes are from the brief (Wakefit models
from the PG chat - sizes not independently verified).
Writes model/furniture.json and docs/furniture-fit.md.
"""
import json
import math
import sys
from collections import deque

import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TK = json.loads((ROOT / "model/takeoff.json").read_text())
AS = json.loads((ROOT / "model/assumptions.json").read_text())
FS = AS["furniture_sizes"]
CL = AS["clearances"]
STEP = 0.05
PATH_R = 0.275
ROOMS = {"F1-3": {"ROOM-1": ("F-D1", ["F-D1T"]), "ROOM-2": ("F-D2", ["F-D2T"]), "ROOM-3": ("F-D3", ["F-D3T"]), "ROOM-4": ("F-D4", ["F-D4T"])},
         "F4": {"ROOM-1": ("F4-D1", ["F4-D1T"]), "ROOM-2": ("F4-D2", ["F4-D2T"]), "ROOM-3 (suite)": ("F4-D3", ["F4-D3T", "F4-DT"])}}


def ovl(a, b, e=1e-3):
    return a[0] < b[2] - e and b[0] < a[2] - e and a[1] < b[3] - e and b[1] < a[3] - e


def inside(r, rects):
    x = r[0] + 0.025
    while x < r[2]:
        y = r[1] + 0.025
        while y < r[3]:
            if not any(q[0] - 1e-6 <= x <= q[2] + 1e-6 and q[1] - 1e-6 <= y <= q[3] + 1e-6 for q in rects):
                return False
            y += 0.05
        x += 0.05
    return True


def disc_hits(sw, r):
    hx, hy = sw["hinge"]
    qx, qy = sw["quadrant"]
    R = sw["width"]
    q = [min(hx, hx + qx * R), min(hy, hy + qy * R), max(hx, hx + qx * R), max(hy, hy + qy * R)]
    if not ovl(q, r):
        return False
    ix = [max(q[0], r[0]), max(q[1], r[1]), min(q[2], r[2]), min(q[3], r[3])]
    cx, cy = min(max(hx, ix[0]), ix[2]), min(max(hy, ix[1]), ix[3])
    return math.hypot(cx - hx, cy - hy) < R - 1e-3


def zone(r, side, d):
    x0, y0, x1, y1 = r
    return {"N": [x0, y0 - d, x1, y0], "S": [x0, y1, x1, y1 + d], "W": [x0 - d, y0, x0, y1], "E": [x1, y0, x1 + d, y1]}[side]


def touches_wall(edge, walls):
    """edge = ('x', x, y0, y1) or ('y', y, x0, x1): True if a wall face covers it."""
    ax, c, a0, a1 = edge
    for w in walls:
        if ax == "x" and (abs(w[0] - c) < 0.011 or abs(w[2] - c) < 0.011) and w[1] <= a0 + 0.01 and w[3] >= a1 - 0.01:
            return True
        if ax == "y" and (abs(w[1] - c) < 0.011 or abs(w[3] - c) < 0.011) and w[0] <= a0 + 0.01 and w[2] >= a1 - 0.01:
            return True
    return False


def grid_vals(lo, hi):
    out, v = [], math.ceil(lo / STEP - 1e-9) * STEP
    while v <= hi + 1e-9:
        out.append(round(v, 3))
        v += STEP
    return out


class Room:
    def __init__(self, pk, name, door, others):
        fl = TK["floors"][pk]
        self.pk, self.name = pk, name
        self.rects = next(s for s in fl["spaces"] if s["name"] == name)["rects"]
        self.walls = fl["walls"]
        dmap = {d["id"]: d for d in AS["doors"][pk]}
        self.swings = list(dmap.values())
        self.door = dmap[door]
        self.targets_doors = [dmap[o] for o in others]
        self.grey = [g["rect"] for g in fl.get("grey_items", []) if inside(g["rect"], self.rects)]
        xs = [c for r in self.rects for c in (r[0], r[2])]
        ys = [c for r in self.rects for c in (r[1], r[3])]
        self.bb = [min(xs), min(ys), max(xs), max(ys)]
        self.nx = int(round((self.bb[2] - self.bb[0]) / STEP))
        self.ny = int(round((self.bb[3] - self.bb[1]) / STEP))
        self.base = [[inside([self.bb[0] + i * STEP, self.bb[1] + j * STEP, self.bb[0] + (i + 1) * STEP, self.bb[1] + (j + 1) * STEP], self.rects)
                      for j in range(self.ny)] for i in range(self.nx)]

    def ok_fixed(self, r, placed, zones):
        if not inside(r, self.rects):
            return False
        if any(ovl(r, w) for w in self.walls) or any(ovl(r, p) for p in placed) or any(ovl(r, z) for z in zones):
            return False
        return not any(disc_hits(sw, r) for sw in self.swings)

    def cell(self, x, y):
        return int((x - self.bb[0]) / STEP), int((y - self.bb[1]) / STEP)

    def walkable(self, fixed, zones):
        free = np.array(self.base, dtype=bool)
        for r in fixed:
            i0, j0 = self.cell(r[0] + 1e-6, r[1] + 1e-6)
            i1, j1 = self.cell(r[2] - 1e-6, r[3] - 1e-6)
            free[max(i0, 0):i1 + 1, max(j0, 0):j1 + 1] = False
        k = int(round(PATH_R / STEP))
        w = 2 * k - 1
        blocked = (~free).astype(np.int32)
        S = np.zeros((self.nx + 1, self.ny + 1), dtype=np.int32)
        S[1:, 1:] = blocked.cumsum(0).cumsum(1)
        pas = np.zeros_like(free)
        if self.nx >= w and self.ny >= w:
            win = S[w:, w:] - S[:-w, w:] - S[w:, :-w] + S[:-w, :-w]
            pas[k - 1:k - 1 + win.shape[0], k - 1:k - 1 + win.shape[1]] = (win == 0)
        pas &= free

        def region(rect, grow=0.0):
            i0, j0 = self.cell(rect[0] - grow + 1e-6, rect[1] - grow + 1e-6)
            i1, j1 = self.cell(rect[2] + grow - 1e-6, rect[3] + grow - 1e-6)
            m = np.zeros_like(pas)
            m[max(i0, 0):max(min(i1 + 1, self.nx), 0), max(j0, 0):max(min(j1 + 1, self.ny), 0)] = True
            return m & pas

        def sq(d):
            hx, hy = d["hinge"]
            qx, qy = d["quadrant"]
            R = d["width"]
            return [min(hx, hx + qx * R), min(hy, hy + qy * R), max(hx, hx + qx * R), max(hy, hy + qy * R)]

        reach = region(sq(self.door), 0.45)
        if not reach.any():
            return False, "door area not passable"
        while True:                       # flood fill by 4-neighbour dilation
            g = reach.copy()
            g[1:, :] |= reach[:-1, :]
            g[:-1, :] |= reach[1:, :]
            g[:, 1:] |= reach[:, :-1]
            g[:, :-1] |= reach[:, 1:]
            g &= pas
            if (g == reach).all():
                break
            reach = g
        for nm, z in zones:
            if not (region(z) & reach).any():
                return False, f"no 0.55 m path to {nm}"
        for d in self.targets_doors:      # target = room-side area around the door (door may swing out of the room)
            if not (region(sq(d), 0.45) & reach).any():
                return False, f"no 0.55 m path to {d['id']}"
        return True, ""


def bed_candidates(room, kind):
    L, W, _ = FS[kind]
    out = []
    for (lx, ly) in ((L, W), (W, L)):
        for x in grid_vals(room.bb[0], room.bb[2] - lx):
            for y in grid_vals(room.bb[1], room.bb[3] - ly):
                r = [x, y, round(x + lx, 3), round(y + ly, 3)]
                long_x = lx > ly
                # headboard = a short side against a wall
                heads = [("x", r[0], r[1], r[3]), ("x", r[2], r[1], r[3])] if long_x else [("y", r[1], r[0], r[2]), ("y", r[3], r[0], r[2])]
                longs = [("y", r[1], r[0], r[2]), ("y", r[3], r[0], r[2])] if long_x else [("x", r[0], r[1], r[3]), ("x", r[2], r[1], r[3])]
                head_ok = any(touches_wall(h, room.walls) for h in heads)
                if not head_ok and not (kind == "single_bed" and any(touches_wall(e, room.walls) for e in longs)):
                    continue
                if not room.ok_fixed(r, [], []):
                    continue
                sides = ["N", "S"] if long_x else ["W", "E"]
                out.append((r, sides))
    return out


def desk_candidates(room, wd):
    Dl, Dd, _ = FS[wd]
    out = []
    for (dx, dy) in ((Dl, Dd), (Dd, Dl)):
        for x in grid_vals(room.bb[0], room.bb[2] - dx):
            for y in grid_vals(room.bb[1], room.bb[3] - dy):
                dr = [x, y, round(x + dx, 3), round(y + dy, 3)]
                backs = [("y", dr[1], dr[0], dr[2], "S"), ("y", dr[3], dr[0], dr[2], "N")] if dx > dy else [("x", dr[0], dr[1], dr[3], "E"), ("x", dr[2], dr[1], dr[3], "W")]
                bk = [b for b in backs if touches_wall(b[:4], room.walls)]
                if not bk or any(ovl(dr, g) for g in room.grey) or not room.ok_fixed(dr, [], []):
                    continue
                dz = zone(dr, bk[0][4], CL["desk_chair_zone"])
                if not inside(dz, room.rects) or any(ovl(dz, w) for w in room.walls):
                    continue
                out.append((dr, bk[0][4], dz))
    return out


def items_beds(room):
    out = []
    for r, sides in bed_candidates(room, "single_bed"):
        if any(ovl(r, g) for g in room.grey):
            continue
        walls_long = sum(touches_wall(e, room.walls) for e in ((("y", r[1], r[0], r[2]), ("y", r[3], r[0], r[2])) if sides == ["N", "S"] else (("x", r[0], r[1], r[3]), ("x", r[2], r[1], r[3]))))
        for sd in sides:
            z = zone(r, sd, CL["single_bed_access_side"])
            if inside(z, room.rects) and not any(ovl(z, w) for w in room.walls):
                out.append({"type": "single_bed", "rect": r, "access": [sd], "zones": [z], "score": walls_long})
    out.sort(key=lambda it: -it["score"])
    return out


def items_wardrobes(room):
    Ww, Wd, _ = FS["wardrobe_3door_sliding"]
    grey, other = [], []
    for g in room.grey:
        vertical = (g[3] - g[1]) > (g[2] - g[0])
        if vertical:
            face = "E" if not touches_wall(("x", g[2], g[1], g[3]), room.walls) else "W"
            for y in grid_vals(g[1], g[3] - Ww):
                grey.append(([g[0], y, g[0] + Wd, round(y + Ww, 3)] if face == "E" else [g[2] - Wd, y, g[2], round(y + Ww, 3)], face))
        else:
            face = "N" if touches_wall(("y", g[3], g[0], g[2]), room.walls) else "S"
            for x in grid_vals(g[0], g[2] - Ww):
                grey.append(([x, g[3] - Wd, round(x + Ww, 3), g[3]] if face == "N" else [x, g[1], round(x + Ww, 3), g[1] + Wd], face))
    for (dx, dy) in ((Ww, Wd), (Wd, Ww)):
        for x in grid_vals(room.bb[0], room.bb[2] - dx):
            for y in grid_vals(room.bb[1], room.bb[3] - dy):
                r = [x, y, round(x + dx, 3), round(y + dy, 3)]
                backs = [("y", r[1], r[0], r[2], "S"), ("y", r[3], r[0], r[2], "N")] if dx > dy else [("x", r[0], r[1], r[3], "E"), ("x", r[2], r[1], r[3], "W")]
                bk = [bb for bb in backs if touches_wall(bb[:4], room.walls)]
                if bk and not any(ovl(r, g) for g in room.grey):
                    other.append((r, bk[0][4]))
    out = []
    for lst, tag in ((grey, 1), (other, 0)):
        for r, f in lst:
            z = zone(r, f, CL["sliding_wardrobe_front"])
            if room.ok_fixed(r, [], []) and inside(z, room.rects) and not any(ovl(z, w) for w in room.walls):
                out.append({"type": "wardrobe_3door_sliding", "rect": r, "access": [f], "zones": [z], "grey": tag})
    return out


def items_desks(room, wd):
    fl = TK["floors"][room.pk]
    out = []
    for dr, side, dz in desk_candidates(room, wd):
        dmin = 9
        for wdw in fl["windows"]:
            wy = 0.0 if wdw["wall"] == "rear" else fl["outline"][3]
            dmin = min(dmin, math.hypot((dr[0] + dr[2]) / 2 - (wdw["span_x"][0] + wdw["span_x"][1]) / 2, (dr[1] + dr[3]) / 2 - wy))
        out.append({"type": wd, "rect": dr, "access": [side], "zones": [dz], "score": -dmin})
    out.sort(key=lambda it: -it["score"])
    return out


def compat(a, b):
    if ovl(a["rect"], b["rect"]):
        return False
    return not any(ovl(a["rect"], z) for z in b["zones"]) and not any(ovl(b["rect"], z) for z in a["zones"])


def solve_layout(room, nbeds, wd, max_walk=20000, want=4):
    beds, wards, desks = items_beds(room), items_wardrobes(room), items_desks(room, wd)
    if room.grey:                                   # first wardrobe must use the architect's grey strip
        ward1 = [w for w in wards if w["grey"]]
    else:
        ward1 = wards
    slots = [("bed", beds)] * nbeds + [("ward1", ward1)] + [("ward", wards)] * (nbeds - 1) + [("desk", desks)] * nbeds
    found, walks = [], [0]

    def walk_ok(placed):
        walks[0] += 1
        ok, _ = room.walkable([p["rect"] for p in placed], [(p["type"], z) for p in placed for z in p["zones"]])
        return ok

    def dfs(i, placed, last_idx):
        if len(found) >= want or walks[0] > max_walk:
            return
        if i == len(slots):
            if walk_ok(placed):
                found.append(list(placed))
            return
        kind, cands = slots[i]
        start = last_idx.get(kind, -1) + 1 if kind in ("bed", "desk", "ward") else 0
        for j in range(start, len(cands)):
            c = cands[j]
            if kind == "ward" and any(p is c for p in placed):
                continue
            if all(compat(c, p) for p in placed):
                placed.append(c)
                prune = (kind == "bed" and sum(1 for p in placed if p["type"] == "single_bed") == nbeds) or (i == len(slots) - nbeds - 1)
                if not prune or walk_ok(placed):
                    li = dict(last_idx)
                    li[kind] = j
                    dfs(i + 1, placed, li)
                placed.pop()
                if len(found) >= want or walks[0] > max_walk:
                    return

    dfs(0, [], {})
    if not found:
        return None
    hx, hy = room.door["hinge"]

    def score(sol):
        sc = sum(it.get("score", 0) for it in sol if it["type"].endswith("desk"))
        sc += 0.3 * sum(it.get("score", 0) for it in sol if it["type"] == "single_bed")
        sc += sum(0.5 for it in sol if it.get("grey"))
        return sc
    best = max(found, key=score)
    return [{"type": it["type"], "rect": it["rect"], "access": it["access"]} for it in best]


NS = 0.40          # bedside table size (ASSUMED)
NS_TRIM = 0.45     # bed access zone shortened at the head end by this much


def add_nightstands(room, sol):
    """Add a 0.40 m bedside table at the head of each bed, in its access strip (shared when twin beds meet).
    Each table is kept only if all checks (walls, swings, other items and their zones, 0.55 m paths) still pass."""
    hx0, hy0 = room.door["hinge"]
    beds = [it for it in sol if it["type"] == "single_bed"]
    others = [it for it in sol if it["type"] != "single_bed"]

    def bed_zone(it):
        return zone(it["rect"], it["access"][0], CL["single_bed_access_side"])

    def head_end(r):
        long_x = (r[2] - r[0]) > (r[3] - r[1])
        ends = [("W", ("x", r[0], r[1], r[3])), ("E", ("x", r[2], r[1], r[3]))] if long_x else [("N", ("y", r[1], r[0], r[2])), ("S", ("y", r[3], r[0], r[2]))]
        walled = [e for e, edge in ends if touches_wall(edge, room.walls)]
        if len(walled) == 1:
            return walled[0]
        c = {"W": (r[0], (r[1] + r[3]) / 2), "E": (r[2], (r[1] + r[3]) / 2), "N": ((r[0] + r[2]) / 2, r[1]), "S": ((r[0] + r[2]) / 2, r[3])}
        return max([e for e, _ in ends], key=lambda e: math.hypot(c[e][0] - hx0, c[e][1] - hy0))

    def ns_rect(it, head):
        r, s_ = it["rect"], it["access"][0]
        if head in ("W", "E"):
            x0 = r[0] if head == "W" else r[2] - NS
            y0 = r[3] if s_ == "S" else r[1] - NS
        else:
            y0 = r[1] if head == "N" else r[3] - NS
            x0 = r[2] if s_ == "E" else r[0] - NS
        return [round(x0, 3), round(y0, 3), round(x0 + NS, 3), round(y0 + NS, 3)]

    def trimmed(it, head):
        z = bed_zone(it)
        if head == "W":
            return [z[0] + NS_TRIM, z[1], z[2], z[3]]
        if head == "E":
            return [z[0], z[1], z[2] - NS_TRIM, z[3]]
        if head == "N":
            return [z[0], z[1] + NS_TRIM, z[2], z[3]]
        return [z[0], z[1], z[2], z[3] - NS_TRIM]

    tables, bedz = [], {id(b): bed_zone(b) for b in beds}
    for b in beds:
        head = head_end(b["rect"])
        t = ns_rect(b, head)
        shared = next((u for u in tables if ovl(u, t, 0.05)), None)
        trial_tables = tables if shared else tables + [t]
        trial_z = dict(bedz)
        trial_z[id(b)] = trimmed(b, head)
        # every other bed whose zone the table sits in must also have its head at that end
        ok = room.ok_fixed(t, [o["rect"] for o in others] + [x["rect"] for x in beds], [])
        for b2 in beds:
            if ovl(t, trial_z[id(b2)]):
                h2 = head_end(b2["rect"])
                tz = trimmed(b2, h2)
                if ovl(t, tz):
                    ok = False
                else:
                    trial_z[id(b2)] = tz
        for o in others:
            dep = CL["sliding_wardrobe_front"] if o["type"].startswith("wardrobe") else CL["desk_chair_zone"]
            if ovl(t, zone(o["rect"], o["access"][0], dep)):
                ok = False
        if ok:
            fixed = [x["rect"] for x in sol] + trial_tables
            zs = [("bed", trial_z[id(x)]) for x in beds] + [(o["type"], zone(o["rect"], o["access"][0], CL["sliding_wardrobe_front"] if o["type"].startswith("wardrobe") else CL["desk_chair_zone"])) for o in others]
            ok, _ = room.walkable(fixed, zs)
        if ok:
            tables, bedz = trial_tables, trial_z
    for b in beds:
        b["zones"] = [[round(v, 3) for v in bedz[id(b)]]]
    return sol + [{"type": "bedside_table", "rect": t, "access": []} for t in tables], len(tables)


def main():
    out = {"_about": "GENERATED by tools/fit_furniture.py - DOUBLE = twin sharing (2 single beds, 2 desks, 2 wardrobes) where it fits, else SINGLE. Sizes from the brief (Wakefit, confirmed by the family). Positions ASSUMED; drawn rooms unchanged."}
    rep = ["# Furniture fit (generated by tools/fit_furniture.py)", "",
           "Rule from the family: **double = two students sharing (2 single beds, 2 study tables, 2 wardrobes) where there is enough space, otherwise single** "
           "(1 bed, 1 study table, 1 wardrobe). Room and toilet geometry is exactly as DRAWN.",
           "Furniture sizes are from the brief, taken as the Wakefit models from the PG chat: single bed 2.05×0.95, 3-door sliding wardrobe 1.20 wide (0.55 deep, fits the drawn grey strips), "
           "standard desk 1.16×0.57, wall desk 0.90×0.45. All furniture is Wakefit, with measurements confirmed by the family.", "",
           "A layout passes only if every item is inside the room and clear of walls, the other items, every door swing and every clearance zone "
           "(each bed 0.60 m on its open side, each wardrobe 0.60 m in front, each desk a 0.75 m chair zone). It also needs a **0.55 m walking path** (ASSUMED) "
           "from the room door to every bed side, wardrobe front, chair zone, and the toilet or terrace door. The first wardrobe goes in the architect's grey strip (takeoff Q7). "
           "Order tried: twin with standard desks, then twin with wall desks, then single.", "",
           "| Floor | Room | Result | Furniture | Students |", "|---|---|---|---|---|"]
    beds_total = 0
    only = sys.argv[1:]
    for pk, rooms in ROOMS.items():
        out[pk] = {}
        for name, (door, others) in rooms.items():
            if only and f"{pk}:{name}" not in only:
                continue
            room = Room(pk, name, door, others)
            sol, kind = solve_layout(room, 2, "standard_desk"), "DOUBLE (2 beds, 2 standard desks, 2 wardrobes)"
            if sol is None:
                sol, kind = solve_layout(room, 2, "wall_desk"), "DOUBLE (2 beds, 2 wall desks, 2 wardrobes)"
            if sol is None:
                sol, kind = solve_layout(room, 1, "wall_desk"), "SINGLE (twin sharing does not fit)"
            if sol is None:
                rep.append(f"| {pk} | {name} | NO LAYOUT FOUND | - | 0 |")
                print(pk, name, "NO LAYOUT", flush=True)
                continue
            sol, nt = add_nightstands(room, sol)
            kind += f" + {nt} bedside table{'s' if nt != 1 else ''}"
            out[pk][name] = sol
            nb = (2 if kind.startswith("DOUBLE") else 1) * (3 if pk == "F1-3" else 1)
            beds_total += nb
            desc = "; ".join(f"{i['type'].replace('_', ' ')} {i['rect']}" for i in sol)
            rep.append(f"| {pk} | {name} | {kind} | {desc} | {nb} |")
            print(pk, name, kind, flush=True)
    rep += ["", f"**Total students: {beds_total}** (F1-3 counted × 3)."]
    if only:
        prev = json.loads((ROOT / "model/furniture.json").read_text())
        for pk in ROOMS:
            prev.setdefault(pk, {}).update(out.get(pk, {}))
        prev["_about"] = out["_about"]
        out = prev
    (ROOT / "model/furniture.json").write_text(json.dumps(out, indent=1))
    if not only:
        (ROOT / "docs/furniture-fit.md").write_text("\n".join(rep) + "\n")
    print("students", beds_total)


if __name__ == "__main__":
    main()
