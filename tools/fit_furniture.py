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
from collections import deque
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
        free = [row[:] for row in self.base]
        for r in fixed:
            i0, j0 = self.cell(r[0] + 1e-6, r[1] + 1e-6)
            i1, j1 = self.cell(r[2] - 1e-6, r[3] - 1e-6)
            for i in range(max(i0, 0), min(i1 + 1, self.nx)):
                for j in range(max(j0, 0), min(j1 + 1, self.ny)):
                    free[i][j] = False
        k = int(round(PATH_R / STEP))
        # erosion via summed-area table: passable if the (2k-1)^2 cell square around it is all free
        nx, ny = self.nx, self.ny
        S = [[0] * (ny + 1) for _ in range(nx + 1)]
        for i in range(nx):
            run = 0
            for j in range(ny):
                run += 0 if free[i][j] else 1
                S[i + 1][j + 1] = S[i][j + 1] + run
        pas = [[False] * ny for _ in range(nx)]
        for i in range(k - 1, nx - k + 1):
            for j in range(k - 1, ny - k + 1):
                if free[i][j]:
                    a0, a1, b0, b1 = i - k + 1, i + k, j - k + 1, j + k
                    pas[i][j] = (S[a1][b1] - S[a0][b1] - S[a1][b0] + S[a0][b0]) == 0
        def seeds(rect):
            i0, j0 = self.cell(rect[0] + 1e-6, rect[1] + 1e-6)
            i1, j1 = self.cell(rect[2] - 1e-6, rect[3] - 1e-6)
            return {(i, j) for i in range(max(i0, 0), min(i1 + 1, self.nx)) for j in range(max(j0, 0), min(j1 + 1, self.ny)) if pas[i][j]}

        def sq(d):
            hx, hy = d["hinge"]
            qx, qy = d["quadrant"]
            R = d["width"]
            return [min(hx, hx + qx * R), min(hy, hy + qy * R), max(hx, hx + qx * R), max(hy, hy + qy * R)]

        start = seeds(sq(self.door))
        if not start:
            return False, "door swing area not passable"
        seen, dq = set(start), deque(start)
        while dq:
            i, j = dq.popleft()
            for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
                if 0 <= a < self.nx and 0 <= b < self.ny and pas[a][b] and (a, b) not in seen:
                    seen.add((a, b))
                    dq.append((a, b))
        for nm, z in zones:
            if not (seeds(z) & seen):
                return False, f"no 0.55 m path to {nm}"
        for d in self.targets_doors:
            if not (seeds(sq(d)) & seen):
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
                if not any(touches_wall(h, room.walls) for h in heads):
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


def solve(room, double, wd=None):
    bed = "queen_bed" if double else "single_bed"
    wd = wd or ("standard_desk" if double else "wall_desk")
    desks = desk_candidates(room, wd)
    best = None
    tried = 0
    for r, sides in bed_candidates(room, bed):
        side_sets = [sides] if double else [[sides[0]], [sides[1]]]
        for ss in side_sets:
            bz = [(f"bed side {s}", zone(r, s, CL["queen_bed_sides" if double else "single_bed_access_side"])) for s in ss]
            if not all(inside(z, room.rects) for _, z in bz) or any(ovl(z, w) for _, z in bz for w in room.walls):
                continue
            # wardrobe: in the grey strip if one exists, front facing into the room
            wcands = []
            Ww, Wd, _ = FS["wardrobe_3door_sliding"]
            strips = room.grey or []
            for g in strips:
                vertical = (g[3] - g[1]) > (g[2] - g[0])
                if vertical:
                    face = "E" if not touches_wall(("x", g[2], g[1], g[3]), room.walls) else "W"
                    for y in grid_vals(g[1], g[3] - Ww):
                        wcands.append(([g[0], y, g[0] + Wd, round(y + Ww, 3)] if face == "E" else [g[2] - Wd, y, g[2], round(y + Ww, 3)], face))
                else:
                    face = "N" if touches_wall(("y", g[3], g[0], g[2]), room.walls) else "S"
                    for x in grid_vals(g[0], g[2] - Ww):
                        wcands.append(([x, g[3] - Wd, round(x + Ww, 3), g[3]] if face == "N" else [x, g[1], round(x + Ww, 3), g[1] + Wd], face))
            for wr, wf in wcands:
                wz = ("wardrobe access", zone(wr, wf, CL["sliding_wardrobe_front"]))
                if not room.ok_fixed(wr, [r], [z for _, z in bz]) or not inside(wz[1], room.rects) or ovl(wz[1], r):
                    continue
                for dr, dside, dzr in desks:
                    if True:
                        if True:
                            zones = [z for _, z in bz] + [wz[1]]
                            if ovl(dr, r) or ovl(dr, wr) or any(ovl(dr, z) for z in zones):
                                continue
                            if ovl(dzr, r) or ovl(dzr, wr):
                                continue
                            dz = ("desk chair zone", dzr)
                            bk = [(None, None, None, None, dside)]
                            tried += 1
                            ok, why = room.walkable([r, wr, dr], bz + [wz, dz])
                            if not ok:
                                continue
                            # score: desk near a window, bed far from the room door
                            hx, hy = room.door["hinge"]
                            sc = math.hypot((r[0] + r[2]) / 2 - hx, (r[1] + r[3]) / 2 - hy)
                            fl = TK["floors"][room.pk]
                            for wdw in fl["windows"]:
                                wy = 0.0 if wdw["wall"] == "rear" else fl["outline"][3]
                                d = math.hypot((dr[0] + dr[2]) / 2 - (wdw["span_x"][0] + wdw["span_x"][1]) / 2, (dr[1] + dr[3]) / 2 - wy)
                                sc -= 0.5 * min(d, 4) / 4
                            if best is None or sc > best[0]:
                                best = (sc, [{"type": bed, "rect": r, "access": ss}, {"type": "wardrobe_3door_sliding", "rect": wr, "access": [wf]},
                                             {"type": wd, "rect": dr, "access": [bk[0][4]]}])
                            if tried > 150 and best:
                                return best[1]
                            if tried > 6000:
                                return best[1] if best else None
    return best[1] if best else None


def main():
    out = {"_about": "GENERATED by tools/fit_furniture.py - double (shared queen) where it fits, else single. Sizes from the brief (Wakefit per PG chat). Positions ASSUMED; drawn rooms unchanged."}
    rep = ["# Furniture fit (generated by tools/fit_furniture.py)", "",
           "Rule from the family: **double (shared queen bed) where there is enough space, otherwise single.** Room and toilet geometry is exactly as DRAWN.",
           "Furniture sizes are from the brief, taken as the Wakefit models from the PG chat: single bed 2.05×0.95, queen 2.05×1.58, 3-door sliding wardrobe 1.20 wide (0.55 deep, fits the drawn grey strips), wall desk 0.90×0.45, standard desk 1.16×0.57. "
           "These were not independently verified against Wakefit's catalogue, so please send the exact model links if they differ.", "",
           "A layout passes only if every item is inside the room and clear of walls, the other items, every door swing and every clearance zone. "
           "It also needs a **0.55 m walking path** (ASSUMED) from the room door to every bed side, the wardrobe front, the desk chair zone, and the toilet or terrace door.", "",
           "| Floor | Room | Result | Furniture | Beds |", "|---|---|---|---|---|"]
    beds_total = 0
    for pk, rooms in ROOMS.items():
        out[pk] = {}
        for name, (door, others) in rooms.items():
            room = Room(pk, name, door, others)
            sol = solve(room, True)
            kind = "DOUBLE (queen + standard desk)"
            why = ""
            if sol is None:
                sol = solve(room, True, "wall_desk")
                kind = "DOUBLE (queen + wall desk; standard desk does not fit)"
            if sol is None:
                why = "no queen position with 0.60 m on both sides + wardrobe + desk + 0.55 m paths"
                sol = solve(room, False)
                kind = "SINGLE"
            if sol is None:
                rep.append(f"| {pk} | {name} | NO LAYOUT FOUND | - | 0 |")
                continue
            out[pk][name] = sol
            nb = (2 if kind.startswith("DOUBLE") else 1) * (3 if pk == "F1-3" else 1)
            beds_total += nb
            desc = "; ".join(f"{i['type'].replace('_', ' ')} {i['rect']}" for i in sol)
            rep.append(f"| {pk} | {name} | {kind}{' - ' + why if why else ''} | {desc} | {nb} |")
            print(pk, name, kind)
    rep += ["", f"**Total beds: {beds_total}** (F1-3 counted × 3)."]
    (ROOT / "model/furniture.json").write_text(json.dumps(out, indent=1))
    (ROOT / "docs/furniture-fit.md").write_text("\n".join(rep) + "\n")
    print("beds", beds_total)


if __name__ == "__main__":
    main()
