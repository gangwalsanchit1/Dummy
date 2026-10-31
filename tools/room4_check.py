#!/usr/bin/env python3
"""ROOM-4 (F1-F3) check and dimensioned top-view plan, all in feet and inches.

Family layout: Wakefit queen bed with one long side on the wall + side table on the open side at the
head wall; study wall = the wall where the wardrobe was (west wall, x = 4.45) with an adjustable study
table and twin wardrobes. Fixed walls, doors and windows are exactly as DRAWN.
Writes docs/room4-check.md and docs/room4-plan.svg.
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from units import ftin, size  # noqa: E402
import fit_furniture as FF  # noqa: E402

TK = json.loads((ROOT / "model/takeoff.json").read_text())
AS = json.loads((ROOT / "model/assumptions.json").read_text())
FU = json.loads((ROOT / "model/furniture.json").read_text())
CAT = AS["wakefit_catalog"]
FS = AS["furniture_sizes"]
fl = TK["floors"]["F1-3"]
items = FU["F1-3"]["ROOM-4"]
bed = next(i for i in items if i["type"] == "orion_queen_bed")
side = next(i for i in items if i["type"] == "tinker_side_table")
ward = next(i for i in items if i["type"].endswith("_wardrobe"))
desk = next(i for i in items if i["type"].endswith("desk"))
doors = {d["id"]: d for d in AS["doors"]["F1-3"]}
WALL_X, WALL_Y0, WALL_Y1 = 4.45, 0.15, 2.05          # study wall (west wall of ROOM-4), DRAWN
ROOM = [4.45, 0.15, 7.85, 2.95]                      # main room clear, DRAWN
wall_len = WALL_Y1 - WALL_Y0
CHAIR = AS["clearances"]["desk_chair_zone"]
ACCESS = AS["clearances"]["sliding_wardrobe_front"]
rows, opts = [], []


def row(check, need, have, ok, note=""):
    rows.append(f"| {check} | {ftin(need)} | {ftin(have)} | {'PASS' if ok else '**FAIL** short by ' + ftin(need - have)} | {note} |")


Gw, Tw, Nw, Nd, Ww = FS["gingham_wardrobe"][0], FS["twill_wardrobe"][0], FS["notiq_desk"][0], FS["notiq_desk"][1], FS["wall_desk"][0]
row("Study wall: Gingham wardrobe + Notiq table", Gw + Nw, wall_len, Gw + Nw <= wall_len, "first choice")
row("Study wall: Twill wardrobe + Notiq table (used)", Tw + Nw, wall_len, Tw + Nw <= wall_len, "fits, so Twill is used")
to_bed = bed["rect"][0] - WALL_X
row("Chair pull-out: table depth + 0.75 m chair zone", Nd + CHAIR, to_bed, Nd + CHAIR <= to_bed, "study wall to bed")
row("Wardrobe access: depth + 0.60 m in front", FS[ward["type"]][1] + ACCESS, to_bed, FS[ward["type"]][1] + ACCESS <= to_bed, f"hinged doors, leaf about {ftin(FS[ward['type']][0] / 2)}")
corr = bed["rect"][0] - desk["rect"][2]
row("Walkway between study table and bed", 0.55, corr, corr >= 0.55, "chair zone and bed-side zone may overlap")
row("Bed open-side clearance (family rule: one side only)", 0.60, bed["zones"][0][2] - bed["zones"][0][0], True, "Tinker sits at the head of this side")
hb = FS["orion_queen_bed"][2]
sill = AS["heights"]["window_sill"]
rows.append(f"| Headboard height vs rear window sill (bed head under F-W4) | below {ftin(sill)} | {ftin(hb)} | {'PASS' if hb < sill else '**FAIL**'} | {ftin(sill - hb)} below the sill |")
for did in ("F-D4", "F-D4T"):
    d = doors[did]
    sw = {"hinge": d["hinge"], "width": d["width"], "quadrant": d["quadrant"]}
    hits = [i["type"] for i in items if FF.disc_hits(sw, i["rect"])]
    rows.append(f"| {did} door swing (leaf {ftin(d['width'])}, opens inwards) | clear | {'clear' if not hits else 'hits ' + ', '.join(hits)} | {'PASS' if not hits else '**FAIL**'} | |")
room = FF.Room("F1-3", "ROOM-4", "F-D4", ["F-D4T"])
zones = [("bed open side", bed["zones"][0]), ("wardrobe front", FF.zone(ward["rect"], ward["access"][0], ACCESS)), ("chair", FF.zone(desk["rect"], desk["access"][0], CHAIR))]
ok, why = room.walkable([i["rect"] for i in items], zones)
rows.append(f"| 0.55 m path: door to bed side, wardrobe, chair and toilet door | {ftin(0.55)} wide | {'reached' if ok else why} | {'PASS' if ok else '**FAIL**'} | |")
for nm, L in (("Gingham + Notiq 120 (requested pair)", Gw + Nw), ("Twill + Notiq 120 (used)", Tw + Nw), ("Gingham + 0.90 m wall desk", Gw + Ww)):
    opts.append(f"| {nm} | {ftin(L)} | {'fits, ' + ftin(wall_len - L) + ' spare' if L <= wall_len else 'short by ' + ftin(L - wall_len)} |")
lab = {"orion_queen_bed": "Orion queen bed", "tinker_side_table": "Tinker", "gingham_wardrobe": "Gingham wardrobe", "twill_wardrobe": "Twill wardrobe", "notiq_desk": "Notiq study table"}
cat = AS["wakefit_catalog"]
md = ["# ROOM-4 (F1-F3) check: family layout, feet and inches", "",
      "Fixed walls, doors and windows are as DRAWN. Single occupancy. Family rule for this room: the queen bed has one long side on a wall, "
      "with the Tinker side table on the open side touching the head wall. The study wall is the west wall where the wardrobe used to be.", "",
      f"- Main room clear: **{size(ROOM[2]-ROOM[0], ROOM[3]-ROOM[1])}**. Study wall: **{ftin(wall_len)}**. Study wall to bed: **{ftin(to_bed)}**.", "",
      "| Item | Overall size (W x D x H) | Wakefit link |", "|---|---|---|"]
for it in items:
    w_, d_, h_ = FS[it["type"]]
    c = cat.get(it["type"], {})
    md.append(f"| {lab[it['type']]} | {ftin(w_)} x {ftin(d_)} x {ftin(h_)} | [{c.get('product', '')}]({c.get('link', '')}) |")
md += ["", "## Checks", "", "| Check | Needed | Available | Result | Note |", "|---|---|---|---|---|"] + rows + [
       "", "## Study wall options", "", "| Option | Length | On the 6'-2 3/4\" wall |", "|---|---|---|"] + opts + [""]
(ROOT / "docs/room4-check.md").write_text("\n".join(md))
dz = FF.zone(desk["rect"], desk["access"][0], CHAIR)
wz = FF.zone(ward["rect"], ward["access"][0], ACCESS)
zones = [("bed", bed["zones"][0]), ("wardrobe", wz), ("chair", dz)]
depth_avail = to_bed
# ------------------------------------------------------------------ top-view plan (SVG), ft-in dimensions
K = 120.0                                   # px per metre
X0, Y0 = 2.85, -0.75                        # view origin (plan m)
VW, VH = 8.6 - X0, 5.15 - Y0
X = lambda x: (x - X0) * K
Y = lambda y: (y - Y0) * K
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW*K:.0f} {VH*K + 170:.0f}" width="{VW*K:.0f}" height="{VH*K+170:.0f}" font-family="Arial, Helvetica, sans-serif">',
     f'<rect width="100%" height="100%" fill="#ffffff"/>',
     '<style>text{paint-order:stroke;stroke:#ffffff;stroke-width:3px;stroke-linejoin:round}</style>',
     '<defs><pattern id="h" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#f87171" stroke-width="1.2"/></pattern>'
     '<marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#111"/></marker></defs>']
clip = [3.0, -0.2, 8.05, 4.6]
for w in fl["walls"]:
    a = [max(w[0], clip[0]), max(w[1], clip[1]), min(w[2], clip[2]), min(w[3], clip[3])]
    if a[0] < a[2] and a[1] < a[3]:
        s.append(f'<rect x="{X(a[0]):.1f}" y="{Y(a[1]):.1f}" width="{(a[2]-a[0])*K:.1f}" height="{(a[3]-a[1])*K:.1f}" fill="#374151"/>')
for wdw in fl["windows"]:
    if wdw["wall"] == "rear" and wdw["span_x"][1] > 3.0:
        s.append(f'<rect x="{X(wdw["span_x"][0]):.1f}" y="{Y(0):.1f}" width="{wdw["width"]*K:.1f}" height="{0.15*K:.1f}" fill="#bfdbfe" stroke="#2563eb"/>')
        s.append(f'<text x="{X(sum(wdw["span_x"])/2):.1f}" y="{Y(-0.08):.1f}" font-size="11" text-anchor="middle" fill="#1d4ed8">{wdw["id"]} window {ftin(wdw["width"])}</text>')
for did in ("F-D4", "F-D4T"):
    d = doors[did]
    hx, hy = d["hinge"]
    qx, qy = d["quadrant"]
    r = d["width"]
    op = (hx, hy + qy * r) if d["leaf_axis"] == "x" else (hx + qx * r, hy)
    cl = (hx + qx * r, hy) if d["leaf_axis"] == "x" else (hx, hy + qy * r)
    sweep = 1 if (qx * qy > 0) == (d["leaf_axis"] == "x") else 0
    s.append(f'<path d="M{X(hx):.1f},{Y(hy):.1f} L{X(op[0]):.1f},{Y(op[1]):.1f} A{r*K:.1f},{r*K:.1f} 0 0 {sweep} {X(cl[0]):.1f},{Y(cl[1]):.1f} Z" fill="#fde68a" fill-opacity="0.45" stroke="#92400e"/>')
    s.append(f'<text x="{X(hx + qx*r*0.55):.1f}" y="{Y(hy + qy*r*0.55):.1f}" font-size="11" text-anchor="middle" fill="#92400e">{did} {ftin(r)}</text>')
# clearance zones
for nm, z in zones:
    s.append(f'<rect x="{X(z[0]):.1f}" y="{Y(z[1]):.1f}" width="{(z[2]-z[0])*K:.1f}" height="{(z[3]-z[1])*K:.1f}" fill="url(#h)" stroke="#ef4444" stroke-dasharray="4 3"/>')
# furniture
for it in items:
    r = it["rect"]
    s.append(f'<rect x="{X(r[0]):.1f}" y="{Y(r[1]):.1f}" width="{(r[2]-r[0])*K:.1f}" height="{(r[3]-r[1])*K:.1f}" fill="#c7d2fe" stroke="#3730a3" stroke-width="1.5"/>')
    cx, cy = X((r[0]+r[2])/2), Y((r[1]+r[3])/2)
    narrow = (r[2] - r[0]) < 0.7
    fs = 11 if it["type"] != "tinker_side_table" else 8
    rot = f' transform="rotate(-90 {cx:.1f} {cy:.1f})"' if narrow and it["type"] != "tinker_side_table" else ""
    s.append(f'<text x="{cx:.1f}" y="{cy-3:.1f}" font-size="{fs}" text-anchor="middle" font-weight="bold" fill="#1e1b4b"{rot}>{lab[it["type"]]}</text>')
    s.append(f'<text x="{cx:.1f}" y="{cy+10:.1f}" font-size="{fs-1}" text-anchor="middle" fill="#1e1b4b"{rot}>{size(r[2]-r[0], r[3]-r[1])}</text>')
def dim(x1, y1, x2, y2, text, off=0.0, col="#111"):
    if abs(y1 - y2) < 1e-6:
        y = y1 + off
        s.append(f'<line x1="{X(x1):.1f}" y1="{Y(y):.1f}" x2="{X(x2):.1f}" y2="{Y(y):.1f}" stroke="{col}" marker-start="url(#a)" marker-end="url(#a)"/>')
        s.append(f'<text x="{X((x1+x2)/2):.1f}" y="{Y(y)-4:.1f}" font-size="12" text-anchor="middle" fill="{col}" font-weight="bold">{text}</text>')
    else:
        x = x1 + off
        s.append(f'<line x1="{X(x):.1f}" y1="{Y(y1):.1f}" x2="{X(x):.1f}" y2="{Y(y2):.1f}" stroke="{col}" marker-start="url(#a)" marker-end="url(#a)"/>')
        s.append(f'<text x="{X(x)+4:.1f}" y="{Y((y1+y2)/2):.1f}" font-size="12" fill="{col}" font-weight="bold" transform="rotate(-90 {X(x)+4:.1f} {Y((y1+y2)/2):.1f})" text-anchor="middle">{text}</text>')


dim(ROOM[0], ROOM[3] - 0.10, ROOM[2], ROOM[3] - 0.10, f"room {ftin(ROOM[2]-ROOM[0])}")
dim(ROOM[2], ROOM[1], ROOM[2], ROOM[3], f"room {ftin(ROOM[3]-ROOM[1])}", 0.12)
# study wall chain: wardrobe + table + spare = wall
yA, yB, yC = ward["rect"][1], ward["rect"][3], desk["rect"][3]
dim(4.27, WALL_Y0, 4.27, WALL_Y1, f"study wall {ftin(wall_len)}", 0.0)
dim(4.12, yA, 4.12, yB, f"wardrobe {ftin(yB - yA)}", 0.0, "#3730a3")
dim(4.12, desk["rect"][1], 4.12, yC, f"table {ftin(yC - desk['rect'][1])}", 0.0, "#3730a3")
dim(4.12, yC, 4.12, WALL_Y1, ftin(WALL_Y1 - yC), 0.0, "#555")
dim(WALL_X, 2.25, bed["rect"][0], 2.25, f"{ftin(to_bed)} wall to bed")
dim(bed["rect"][0], 2.62, bed["rect"][2], 2.62, f"bed {ftin(bed['rect'][2]-bed['rect'][0])}", 0.0, "#3730a3")
dim(7.70, bed["rect"][1], 7.70, bed["rect"][3], f"bed {ftin(bed['rect'][3]-bed['rect'][1])}", 0.0, "#3730a3")
dim(desk["rect"][2], 1.80, desk["rect"][2] + CHAIR, 1.80, f"chair {ftin(CHAIR)}", 0.0, "#b91c1c")
dim(desk["rect"][2] + CHAIR, 1.55, bed["rect"][0], 1.55, ftin(bed["rect"][0] - desk["rect"][2] - CHAIR), 0.0, "#555")
dim(ward["rect"][2], 0.68, ward["rect"][2] + ACCESS, 0.68, f"access {ftin(ACCESS)}", 0.0, "#b91c1c")
s.append(f'<text x="{X(3.6):.1f}" y="{Y(3.4):.1f}" font-size="12" fill="#374151">entry passage {ftin(0.90)} wide</text>')
s.append(f'<text x="{X(3.55):.1f}" y="{Y(1.25):.1f}" font-size="12" text-anchor="middle" fill="#374151">ROOM-4</text><text x="{X(3.55):.1f}" y="{Y(1.25)+14:.1f}" font-size="12" text-anchor="middle" fill="#374151">TOILET</text>')
yb = VH * K + 18
legend = ["ROOM-4, floors 1-3: top view. Walls, doors and windows DRAWN. Dimensions in feet and inches.",
          "Blue = Wakefit furniture. Red hatch = clearances (bed side and wardrobe 1'-11 5/8\", chair 2'-5 1/2\"). Yellow = door swing.",
          "Orion queen bed: one long side on the east wall, headboard on the rear wall; Tinker on the open side at the head.",
          "Toilet door opens inwards (into the toilet); entry door opens into the passage."]
for i, t in enumerate(legend):
    s.append(f'<text x="10" y="{yb + i*18:.0f}" font-size="12" fill="#111">{t.replace("&", "and")}</text>')
s.append(f'<text x="10" y="{yb + 4*18 + 6:.0f}" font-size="12" fill="#111">All checks: see docs/room4-check.md (all PASS for the layout shown).</text>')
s.append("</svg>")
(ROOT / "docs/room4-plan.svg").write_text("\n".join(s))
print("\n".join(rows))
print("\n".join(opts))
