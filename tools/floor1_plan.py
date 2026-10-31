#!/usr/bin/env python3
"""Clean 2D plan of floor 1 (same as F2/F3) in feet and inches: walls, windows, doors with swings,
rooms with sizes and sq ft, Wakefit furniture with names and sizes. Writes docs/floor1-plan.svg."""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from units import ftin  # noqa: E402

TK = json.loads((ROOT / "model/takeoff.json").read_text())
AS = json.loads((ROOT / "model/assumptions.json").read_text())
FU = json.loads((ROOT / "model/furniture.json").read_text())
fl = TK["floors"]["F1-3"]
FR = {" 1/8": "⅛", " 1/4": "¼", " 3/8": "⅜", " 1/2": "½", " 5/8": "⅝", " 3/4": "¾", " 7/8": "⅞"}


def ft(m):
    s = ftin(m)
    for a, b in FR.items():
        s = s.replace(a, b)
    return s


def sz(w, d):
    return f"{ft(w)} × {ft(d)}"


K = 105.0
MX, MY = 70, 125
X = lambda x: MX + x * K
Y = lambda y: MY + y * K
W, H = int(MX * 2 + 8.0 * K + 40), int(MY + 11.75 * K + 210)
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Arial, Helvetica, sans-serif">',
     '<rect width="100%" height="100%" fill="#ffffff"/>',
     '<style>text{paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round}</style>',
     '<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#111"/></marker></defs>']
s.append(f'<text x="{MX}" y="34" font-size="22" font-weight="bold" fill="#111">Bella Vita 2 · Floor 1 (floors 2 and 3 identical)</text>')
s.append(f'<text x="{MX}" y="58" font-size="13" fill="#444">2D plan · ROOM-1 and ROOM-4 single (queen) · ROOM-2 and ROOM-3 twin · all dimensions in feet and inches · rear at top, road at bottom</text>')
# room floors
for sp in fl["spaces"]:
    col = "#eef2ff" if sp["name"].startswith("ROOM-") and "TOILET" not in sp["name"] else "#ecfeff" if "TOILET" in sp["name"] else "#f5f5f4"
    for r in sp["rects"]:
        s.append(f'<rect x="{X(r[0]):.1f}" y="{Y(r[1]):.1f}" width="{(r[2]-r[0])*K:.1f}" height="{(r[3]-r[1])*K:.1f}" fill="{col}"/>')
# stair treads
for y in [4.10 + 0.25 * i for i in range(8)]:
    for x0, x1 in ((5.75, 6.75), (6.85, 7.85)):
        s.append(f'<line x1="{X(x0):.1f}" y1="{Y(y):.1f}" x2="{X(x1):.1f}" y2="{Y(y):.1f}" stroke="#a8a29e"/>')
# furniture
NAME = {"orion_queen_bed": "Orion queen bed", "tinker_side_table": "Tinker", "gingham_wardrobe": "Gingham",
        "twill_wardrobe": "Twill", "notiq_desk": "Study table", "sage_desk": "Sage study table", "wall_desk": "Wall desk", "centaur_single_bed": "Centaur single bed", "amata_sofa": "AMATA sofa"}
furn = []
for room, items in FU["F1-3"].items():
    for it in items:
        r = it["rect"]
        furn.append(r)
        s.append(f'<rect x="{X(r[0]):.1f}" y="{Y(r[1]):.1f}" width="{(r[2]-r[0])*K:.1f}" height="{(r[3]-r[1])*K:.1f}" fill="#c7d2fe" stroke="#3730a3" stroke-width="1.4"/>')
        cx, cy = X((r[0] + r[2]) / 2), Y((r[1] + r[3]) / 2)
        w_, d_ = r[2] - r[0], r[3] - r[1]
        small = it["type"] == "tinker_side_table"
        rot = f' transform="rotate(-90 {cx:.1f} {cy:.1f})"' if (h := d_ > w_ * 1.3) else ""
        fs = 9 if small else 12
        nm = NAME.get(it["type"], it["type"])
        if small:
            s.append(f'<text x="{cx:.1f}" y="{cy+3:.1f}" font-size="9" text-anchor="middle" font-weight="bold" fill="#1e1b4b"{rot}>Tinker</text>')
        else:
            s.append(f'<text x="{cx:.1f}" y="{cy-2:.1f}" font-size="{fs}" text-anchor="middle" font-weight="bold" fill="#1e1b4b"{rot}>{nm}</text>')
            s.append(f'<text x="{cx:.1f}" y="{cy+12:.1f}" font-size="{fs-1}" text-anchor="middle" fill="#1e1b4b"{rot}>{sz(max(w_, d_), min(w_, d_))}</text>')
# walls
for w in fl["walls"]:
    s.append(f'<rect x="{X(w[0]):.1f}" y="{Y(w[1]):.1f}" width="{(w[2]-w[0])*K:.1f}" height="{(w[3]-w[1])*K:.1f}" fill="#292524"/>')
# windows
for wdw in fl["windows"]:
    y0 = 0.0 if wdw["wall"] == "rear" else 11.6
    s.append(f'<rect x="{X(wdw["span_x"][0]):.1f}" y="{Y(y0):.1f}" width="{wdw["width"]*K:.1f}" height="{0.15*K:.1f}" fill="#bfdbfe" stroke="#1d4ed8"/>')
    ty = Y(-0.12) if wdw["wall"] == "rear" else Y(11.95)
    s.append(f'<text x="{X(sum(wdw["span_x"])/2):.1f}" y="{ty:.1f}" font-size="10" text-anchor="middle" fill="#1d4ed8">window {ft(wdw["width"])}</text>')
# doors (open inwards), lift opening, stair opening
for d in AS["doors"]["F1-3"]:
    hx, hy = d["hinge"]
    qx, qy = d["quadrant"]
    r = d["width"]
    op = (hx, hy + qy * r) if d["leaf_axis"] == "x" else (hx + qx * r, hy)
    cl = (hx + qx * r, hy) if d["leaf_axis"] == "x" else (hx, hy + qy * r)
    sweep = 1 if (qx * qy > 0) == (d["leaf_axis"] == "x") else 0
    s.append(f'<path d="M{X(hx):.1f},{Y(hy):.1f} L{X(op[0]):.1f},{Y(op[1]):.1f} A{r*K:.1f},{r*K:.1f} 0 0 {sweep} {X(cl[0]):.1f},{Y(cl[1]):.1f} Z" fill="#fde68a" fill-opacity="0.5" stroke="#92400e"/>')
    s.append(f'<line x1="{X(hx):.1f}" y1="{Y(hy):.1f}" x2="{X(op[0]):.1f}" y2="{Y(op[1]):.1f}" stroke="#92400e" stroke-width="2.5"/>')


# room labels at the free spot farthest from furniture
def free_spot(rects):
    best, bp = -1, None
    for r in rects:
        nx, ny = max(2, int((r[2] - r[0]) / 0.1)), max(2, int((r[3] - r[1]) / 0.1))
        for i in range(1, nx):
            for j in range(1, ny):
                x, y = r[0] + i * (r[2] - r[0]) / nx, r[1] + j * (r[3] - r[1]) / ny
                dm = min([min(x - r[0], r[2] - x, y - r[1], r[3] - y)] + [math.hypot(max(f[0] - x, 0, x - f[2]), max(f[1] - y, 0, y - f[3])) for f in furn])
                if dm > best:
                    best, bp = dm, (x, y)
    return bp


for sp in fl["spaces"]:
    r = max(sp["rects"], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
    a = sum((q[2] - q[0]) * (q[3] - q[1]) for q in sp["rects"])
    toilet = "TOILET" in sp["name"]
    x, y = free_spot(sp["rects"]) if not toilet and sp["name"].startswith("ROOM") else ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
    cx, cy = X(x), Y(y)
    if toilet:
        s.append(f'<text x="{cx:.1f}" y="{cy-6:.1f}" font-size="11" text-anchor="middle" font-weight="bold" fill="#0e7490">TOILET</text>')
        s.append(f'<text x="{cx:.1f}" y="{cy+8:.1f}" font-size="10" text-anchor="middle" fill="#0e7490">{ft(r[2]-r[0])} ×</text>')
        s.append(f'<text x="{cx:.1f}" y="{cy+20:.1f}" font-size="10" text-anchor="middle" fill="#0e7490">{ft(r[3]-r[1])}</text>')
    else:
        s.append(f'<text x="{cx:.1f}" y="{cy-6:.1f}" font-size="16" text-anchor="middle" font-weight="bold" fill="#111">{sp["name"]}</text>')
        s.append(f'<text x="{cx:.1f}" y="{cy+11:.1f}" font-size="12" text-anchor="middle" fill="#111">{sz(r[2]-r[0], r[3]-r[1])}</text>')
        s.append(f'<text x="{cx:.1f}" y="{cy+26:.1f}" font-size="11" text-anchor="middle" fill="#444">{a * 10.7639:.0f} sq ft</text>')


def dim(x1, y1, x2, y2, text, horizontal=True):
    s.append(f'<line x1="{X(x1):.1f}" y1="{Y(y1):.1f}" x2="{X(x2):.1f}" y2="{Y(y2):.1f}" stroke="#111" marker-start="url(#a)" marker-end="url(#a)"/>')
    if horizontal:
        s.append(f'<text x="{X((x1+x2)/2):.1f}" y="{Y(y1)-5:.1f}" font-size="13" font-weight="bold" text-anchor="middle">{text}</text>')
    else:
        tx, ty = X(x1) - 6, Y((y1 + y2) / 2)
        s.append(f'<text x="{tx:.1f}" y="{ty:.1f}" font-size="13" font-weight="bold" text-anchor="middle" transform="rotate(-90 {tx:.1f} {ty:.1f})">{text}</text>')


dim(0, -0.45, 8.0, -0.45, f"{ft(8.0)} overall")
dim(-0.35, 0, -0.35, 11.75, f"{ft(11.75)} overall", False)
s.append(f'<text x="{X(4):.1f}" y="{Y(12.45):.1f}" font-size="14" text-anchor="middle" fill="#57534e">ROAD ({ft(6.0)} wide) · front of building</text>')
lg = Y(12.85)
for i, t in enumerate(["Blue = furniture: Wakefit Orion queen / Centaur single beds, Tinker side tables, Gingham / Twill wardrobes, Sage study tables; AMATA sofa (Amazon).",
                       "Yellow = door swing; every door opens inwards. Light blue on walls = windows.",
                       "Walls, doors and windows from the architect's AFTER O.C. drawing. Furniture positions are proposals."]):
    s.append(f'<text x="{MX}" y="{lg + i*18:.0f}" font-size="12" fill="#333">{t}</text>')
s.append("</svg>")
(ROOT / "docs/floor1-plan.svg").write_text("\n".join(s))
print("wrote docs/floor1-plan.svg", W, H)
