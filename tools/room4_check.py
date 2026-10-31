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
bed = next(i for i in items if i["type"] == "queen_bed_wf")
side = next(i for i in items if i["type"] == "side_table")
wards = [i for i in items if i["type"] == "wardrobe_tartan_2door"]
doors = {d["id"]: d for d in AS["doors"]["F1-3"]}

WALL_X, WALL_Y0, WALL_Y1 = 4.45, 0.15, 2.05          # study wall (west wall of ROOM-4), DRAWN
ROOM = [4.45, 0.15, 7.85, 2.95]                      # main room clear, DRAWN
wall_len = WALL_Y1 - WALL_Y0
depth_avail = bed["rect"][0] - WALL_X                # study wall to foot of bed
W_W, W_D = FS["wardrobe_tartan_2door"][:2]
T160, T120 = FS["study_table_notiq160"][:2], FS["study_table_notiq120"][:2]
CHAIR = AS["clearances"]["desk_chair_zone"]
ACCESS = AS["clearances"]["sliding_wardrobe_front"]
rows, opts = [], []


def row(check, need, have, ok, note=""):
    rows.append(f"| {check} | {ftin(need)} | {ftin(have)} | {'PASS' if ok else '**FAIL** short by ' + ftin(need - have)} | {note} |")


# 1. study wall length
row("Study wall: twin wardrobes + Notiq 160 cm table", 2 * W_W + T160[0], wall_len, 2 * W_W + T160[0] <= wall_len, "as requested")
row("Study wall: twin wardrobes + Notiq 120 cm table", 2 * W_W + T120[0], wall_len, 2 * W_W + T120[0] <= wall_len, "smaller Notiq")
# 2. chair pull-out in front of a study table on that wall (table depth + chair zone vs space to the bed foot)
row("Chair pull-out: table 60 cm deep + 0.75 m chair zone", T160[1] + CHAIR, depth_avail, T160[1] + CHAIR <= depth_avail, "study wall to foot of bed")
# 3. wardrobe access (hinged doors: leaf = half the 80 cm width; standing zone 0.60 m)
front = WALL_X + W_D
row("Wardrobe access: 0.60 m in front of twin wardrobes", W_D + ACCESS, depth_avail, W_D + ACCESS <= depth_avail, f"door leaf {ftin(W_W / 2)} swings within it")
# 4. walkway to bed (open side) and past the side table
corr = ROOM[3] - bed["rect"][3]
row("Walkway along open side of bed (bed to south wall)", 0.60, corr, corr >= 0.60)
past_table = ROOM[3] - side["rect"][3]
row("Walkway past side table to bed head", 0.55, past_table, past_table >= 0.55)
# 5. door swings: entry door (in passage) and bathroom door (opens into toilet) must be clear of furniture
for did in ("F-D4", "F-D4T"):
    d = doors[did]
    sw = {"hinge": d["hinge"], "width": d["width"], "quadrant": d["quadrant"]}
    hits = [i["type"] for i in items if FF.disc_hits(sw, i["rect"])]
    rows.append(f"| {did} door swing (leaf {ftin(d['width'])}) | clear | {'clear' if not hits else 'hits ' + ', '.join(hits)} | {'PASS' if not hits else '**FAIL**'} | opens inwards |")
# 6. 0.55 m path from the room door to every clearance zone and the toilet door (same solver test as all rooms)
room = FF.Room("F1-3", "ROOM-4", "F-D4", ["F-D4T"])
zones = [("bed open side", bed["zones"][0])] + [(f"wardrobe {k+1} front", FF.zone(w["rect"], "E", ACCESS)) for k, w in enumerate(wards)]
ok, why = room.walkable([i["rect"] for i in items], zones)
rows.append(f"| 0.55 m walking path: door to bed, both wardrobes, toilet door | {ftin(0.55)} wide | {'reached' if ok else why} | {'PASS' if ok else '**FAIL**'} | |")

# options that fit the 1.90 m wall (Wakefit items found; ordered by closeness to the request)
cands = [("Twin wardrobes only (table on another wall)", 2 * W_W, None),
         ("1 Tartan 2-door wardrobe + Notiq 120 cm table", W_W + T120[0], T120[1]),
         ("1 Tartan 2-door wardrobe + Wakefit wall desk 0.90 m (earlier family desk)", W_W + 0.90, 0.45),
         ("Twin wardrobes + no table; Notiq on the south wall between band and bed? (see note)", 2 * W_W, None)]
for nm, L, dd in cands[:3]:
    fits = L <= wall_len
    chair_ok = dd is None or (dd + CHAIR) <= depth_avail
    opts.append(f"| {nm} | {ftin(L)} | {'fits, ' + ftin(wall_len - L) + ' spare' if fits else 'short by ' + ftin(L - wall_len)} | "
                f"{'n/a' if dd is None else (('OK, ' + ftin(depth_avail - dd - CHAIR) + ' spare') if chair_ok else 'short by ' + ftin(dd + CHAIR - depth_avail))} |")

md = ["# ROOM-4 (F1-F3) check: family layout, feet and inches", "",
      "All fixed walls, doors and windows are as DRAWN. Furniture positions are the family's layout. "
      "The bed rule for this room is the family's: one long side on the wall, with a side table on the open side at the head.", "",
      "## Room (DRAWN)", "",
      f"- Main room clear: **{size(ROOM[2]-ROOM[0], ROOM[3]-ROOM[1])}** (3.40 x 2.80 m), plus the 0.90 m entry passage and band.",
      f"- Study wall (where the wardrobe was): **{ftin(wall_len)}** long (west wall, from the rear wall to the band opening).",
      f"- Study wall to foot of bed: **{ftin(depth_avail)}**.", "",
      "## Furniture used", "",
      "| Item | Size (W x D) | Wakefit product | Status |", "|---|---|---|---|",
      f"| Queen bed (overall frame) | {size(FS['queen_bed_wf'][0], FS['queen_bed_wf'][1])} | [{CAT['queen_bed_wf']['product']}]({CAT['queen_bed_wf']['link']}) | {CAT['queen_bed_wf']['status']} |",
      f"| Side table | {size(*FS['side_table'][:2])} | not specified | ASSUMED |",
      f"| Twin wardrobes (2 x) | {size(W_W, W_D)} each | [{CAT['wardrobe_tartan_2door']['product']}]({CAT['wardrobe_tartan_2door']['link']}) | {CAT['wardrobe_tartan_2door']['status']} |",
      f"| Adjustable study table | {size(*T160)} | [{CAT['study_table_notiq160']['product']}]({CAT['study_table_notiq160']['link']}) | {CAT['study_table_notiq160']['status']} |",
      f"| Adjustable study table (smaller) | {size(*T120)} | [{CAT['study_table_notiq120']['product']}]({CAT['study_table_notiq120']['link']}) | {CAT['study_table_notiq120']['status']} |", "",
      "wakefit.co blocks automated access, so these sizes come from search-indexed page text. Please confirm each from the product page before ordering. "
      "If the bed's overall frame differs, the 'study wall to foot of bed' figure changes by the same amount.", "",
      "## Checks", "", "| Check | Needed | Available | Result | Note |", "|---|---|---|---|---|"] + rows + [
      "", "## Study wall: closest options that fit (Wakefit items found)", "",
      "| Option | Length on wall | Wall (6'-2 3/4\") | Chair pull-out |", "|---|---|---|---|"] + opts + [
      "", "The model currently shows the **twin wardrobes on the study wall** and **no study table** in ROOM-4, because the requested table does not fit beside them. "
      "Pick an option and I will place it.", ""]
(ROOT / "docs/room4-check.md").write_text("\n".join(md))

# ------------------------------------------------------------------ top-view plan (SVG), ft-in dimensions
K = 120.0                                   # px per metre
X0, Y0 = 2.85, -0.75                        # view origin (plan m)
VW, VH = 8.6 - X0, 5.15 - Y0
X = lambda x: (x - X0) * K
Y = lambda y: (y - Y0) * K
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {VW*K:.0f} {VH*K + 170:.0f}" width="{VW*K:.0f}" height="{VH*K+170:.0f}" font-family="Arial, Helvetica, sans-serif">',
     f'<rect width="100%" height="100%" fill="#ffffff"/>',
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
lab = {"queen_bed_wf": "Queen bed (Wakefit)", "side_table": "Side table", "wardrobe_tartan_2door": "Tartan 2-door wardrobe"}
for it in items:
    r = it["rect"]
    s.append(f'<rect x="{X(r[0]):.1f}" y="{Y(r[1]):.1f}" width="{(r[2]-r[0])*K:.1f}" height="{(r[3]-r[1])*K:.1f}" fill="#c7d2fe" stroke="#3730a3" stroke-width="1.5"/>')
    cx, cy = X((r[0]+r[2])/2), Y((r[1]+r[3])/2)
    fs = 12 if it["type"] != "side_table" else 9
    s.append(f'<text x="{cx:.1f}" y="{cy-3:.1f}" font-size="{fs}" text-anchor="middle" font-weight="bold" fill="#1e1b4b">{lab[it["type"]]}</text>')
    s.append(f'<text x="{cx:.1f}" y="{cy+11:.1f}" font-size="{fs-1}" text-anchor="middle" fill="#1e1b4b">{size(r[2]-r[0], r[3]-r[1])}</text>')
# requested study table that does not fit: ghost beyond the wall end
gy0 = WALL_Y0 + 2 * W_W
s.append(f'<rect x="{X(WALL_X):.1f}" y="{Y(gy0):.1f}" width="{T160[1]*K:.1f}" height="{T160[0]*K:.1f}" fill="none" stroke="#dc2626" stroke-width="2" stroke-dasharray="6 4"/>')
s.append(f'<text x="{X(WALL_X + T160[1]/2):.1f}" y="{Y(gy0 + T160[0]/2):.1f}" font-size="11" text-anchor="middle" fill="#dc2626" transform="rotate(-90 {X(WALL_X + T160[1]/2):.1f} {Y(gy0 + T160[0]/2):.1f})">Notiq 160 table: no room ({ftin(2*W_W + T160[0] - wall_len)} short)</text>')


def dim(x1, y1, x2, y2, text, off=0.0, col="#111"):
    if abs(y1 - y2) < 1e-6:
        y = y1 + off
        s.append(f'<line x1="{X(x1):.1f}" y1="{Y(y):.1f}" x2="{X(x2):.1f}" y2="{Y(y):.1f}" stroke="{col}" marker-start="url(#a)" marker-end="url(#a)"/>')
        s.append(f'<text x="{X((x1+x2)/2):.1f}" y="{Y(y)-4:.1f}" font-size="12" text-anchor="middle" fill="{col}" font-weight="bold">{text}</text>')
    else:
        x = x1 + off
        s.append(f'<line x1="{X(x):.1f}" y1="{Y(y1):.1f}" x2="{X(x):.1f}" y2="{Y(y2):.1f}" stroke="{col}" marker-start="url(#a)" marker-end="url(#a)"/>')
        s.append(f'<text x="{X(x)+4:.1f}" y="{Y((y1+y2)/2):.1f}" font-size="12" fill="{col}" font-weight="bold" transform="rotate(-90 {X(x)+4:.1f} {Y((y1+y2)/2):.1f})" text-anchor="middle">{text}</text>')


dim(ROOM[0], ROOM[3], ROOM[2], ROOM[3], f"room {ftin(ROOM[2]-ROOM[0])}", 0.30)
dim(ROOM[2], ROOM[1], ROOM[2], ROOM[3], f"room {ftin(ROOM[3]-ROOM[1])}", 0.12)
dim(WALL_X, WALL_Y0, WALL_X, WALL_Y1, f"study wall {ftin(wall_len)}", -0.22)
dim(WALL_X, 2.55, bed["rect"][0], 2.55, f"{ftin(depth_avail)} to bed")
dim(bed["rect"][0], 0.55, bed["rect"][2], 0.55, f"bed {ftin(bed['rect'][2]-bed['rect'][0])}", 0.0, "#3730a3")
dim(6.6, bed["rect"][1], 6.6, bed["rect"][3], f"bed {ftin(bed['rect'][3]-bed['rect'][1])}", 0.0, "#3730a3")
dim(6.9, bed["rect"][3], 6.9, ROOM[3], f"walkway {ftin(corr)}", 0.0, "#b91c1c")
dim(front, 1.35, front + ACCESS, 1.35, f"access {ftin(ACCESS)}", 0.0, "#b91c1c")
dim(front + ACCESS, 1.35, bed["rect"][0], 1.35, ftin(bed["rect"][0] - front - ACCESS), 0.0, "#555")
s.append(f'<text x="{X(3.6):.1f}" y="{Y(3.4):.1f}" font-size="12" fill="#374151">entry passage {ftin(0.90)} wide</text>')
s.append(f'<text x="{X(3.75):.1f}" y="{Y(1.0):.1f}" font-size="12" text-anchor="middle" fill="#374151">ROOM-4</text><text x="{X(3.75):.1f}" y="{Y(1.0)+14:.1f}" font-size="12" text-anchor="middle" fill="#374151">TOILET</text>')
yb = VH * K + 18
legend = ["ROOM-4, floors 1-3: top view. Walls, doors and windows DRAWN. Dimensions in feet and inches.",
          "Blue = furniture (Wakefit). Red hatch = clearance (0.60 m / 1'-11 5/8\"). Yellow = door swing. Red dashed = requested table that does not fit.",
          f"Bed: {CAT['queen_bed_wf']['status']}.",
          "Toilet door opens inwards (into the toilet); entry door opens into the passage."]
for i, t in enumerate(legend):
    s.append(f'<text x="10" y="{yb + i*18:.0f}" font-size="12" fill="#111">{t.replace("&", "and")}</text>')
s.append(f'<text x="10" y="{yb + 4*18 + 6:.0f}" font-size="12" fill="#111">Checks: ' + " · ".join(
    r.split("|")[1].strip()[:38] + ": " + ("PASS" if "PASS" in r else "FAIL") for r in rows) [:400].replace("&", "and") + '</text>')
s.append("</svg>")
(ROOT / "docs/room4-plan.svg").write_text("\n".join(s))
print("\n".join(rows))
print("\n".join(opts))
