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
from columns import columns  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeoff import load_takeoff  # noqa: E402
TK = load_takeoff()
AS = json.loads((ROOT / "model/assumptions.json").read_text())
FU = json.loads((ROOT / "model/furniture.json").read_text())
fl = TK["floors"]["F1-3"]
# optional: draw a PROPOSAL (internal brick walls / doors changed) from a variant file
#   python3 tools/floor1_plan.py <variant.json> <out-name> "<one-line description>"
VAR = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else None
OUT = sys.argv[2] if len(sys.argv) > 2 else "floor1-plan"
DESC = sys.argv[3] if len(sys.argv) > 3 else ""
WALLS0 = [list(w) for w in load_takeoff(raw=True)["floors"]["F1-3"]["walls"]]   # the architect's drawing
if VAR:
    fl = VAR["TK"]
    AS["doors"]["F1-3"] = VAR["doors"]
    for rn, lay in VAR["layouts"].items():
        if lay:
            FU["F1-3"][rn] = lay
    for rn, items in FU["F1-3"].items():   # drop any kept item that now overlaps a new wall
        FU["F1-3"][rn] = [i for i in items if not any(min(i["rect"][2], w[2]) - max(i["rect"][0], w[0]) > 0.01 and min(i["rect"][3], w[3]) - max(i["rect"][1], w[1]) > 0.01 for w in fl["walls"])]
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
W, H = int(MX * 2 + 8.0 * K + 40), int(MY + 11.75 * K + 250)
s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Arial, Helvetica, sans-serif">',
     '<rect width="100%" height="100%" fill="#ffffff"/>',
     '<style>text{paint-order:stroke;stroke:#fff;stroke-width:3px;stroke-linejoin:round}</style>',
     '<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#111"/></marker></defs>']
s.append(f'<text x="{MX}" y="34" font-size="22" font-weight="bold" fill="{"#c2410c" if VAR else "#111"}">Bella Vita 2 · Floor 1 (floors 2 and 3 identical){" · PROPOSAL" if VAR else ""}</text>')
s.append(f'<text x="{MX}" y="58" font-size="13" fill="#444">Every student: own bed, compact study table + chair, Twill wardrobe, bedside socket. Twin rooms: A and B; roommates may share the Tinker. Feet and inches.</text>')
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
        "twill_wardrobe": "Twill", "notiq_desk": "Study table", "sage_desk": "Sage study table", "compact_desk": "Study table", "nohutch_desk": "Study table (no hutch)", "wall_desk": "Wall desk", "centaur_single_bed": "Centaur single bed", "amata_sofa": "AMATA sofa"}
furn = []


def owners(items):
    """Twin rooms: give each item a student letter (A/B), pairing every item type with the nearest bed."""
    beds = [it for it in items if it["type"].endswith("_bed")]
    if len(beds) < 2:
        return {}
    c = lambda r: ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)
    d = lambda a, b: math.dist(c(a["rect"]), c(b["rect"]))
    own = {id(beds[0]): "A", id(beds[1]): "B"}
    kind = lambda t: "desk" if t.endswith("desk") else t
    for typ in {kind(it["type"]) for it in items} - {beds[0]["type"]}:
        grp = [it for it in items if kind(it["type"]) == typ]
        if len(grp) == 2:
            keep = d(grp[0], beds[0]) + d(grp[1], beds[1]) <= d(grp[0], beds[1]) + d(grp[1], beds[0])
            own[id(grp[0])], own[id(grp[1])] = ("A", "B") if keep else ("B", "A")
    return own


for room, items in FU["F1-3"].items():
    own = owners(items)
    for it in items:
        if it["type"].endswith("desk") and it.get("access"):   # chair in front of every study table
            r = it["rect"]
            sd = it["access"][0]
            cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
            cx, cy = {"N": (cx, r[1] - 0.30), "S": (cx, r[3] + 0.30), "W": (r[0] - 0.30, cy), "E": (r[2] + 0.30, cy)}[sd]
            s.append(f'<circle cx="{X(cx):.1f}" cy="{Y(cy):.1f}" r="{0.21*K:.1f}" fill="#e0e7ff" stroke="#3730a3" stroke-dasharray="3 2"/>')
            s.append(f'<text x="{X(cx):.1f}" y="{Y(cy)+3:.1f}" font-size="8" text-anchor="middle" fill="#3730a3">chair</text>')
    for it in items:
        r = it["rect"]
        furn.append(r)
        s.append(f'<rect x="{X(r[0]):.1f}" y="{Y(r[1]):.1f}" width="{(r[2]-r[0])*K:.1f}" height="{(r[3]-r[1])*K:.1f}" fill="#c7d2fe" stroke="#3730a3" stroke-width="1.4"/>')
        cx, cy = X((r[0] + r[2]) / 2), Y((r[1] + r[3]) / 2)
        w_, d_ = r[2] - r[0], r[3] - r[1]
        small = it["type"] == "tinker_side_table"
        rot = f' transform="rotate(-90 {cx:.1f} {cy:.1f})"' if (h := d_ > w_ * 1.3) else ""
        fs = 9 if small else 12
        nm = NAME.get(it["type"], it["type"]) + (f" {own[id(it)]}" if id(it) in own else "") + (" (shared)" if it.get("shared") else "")
        if small:
            s.append(f'<text x="{cx:.1f}" y="{cy+3:.1f}" font-size="9" text-anchor="middle" font-weight="bold" fill="#1e1b4b"{rot}>{nm}</text>')
        else:
            s.append(f'<text x="{cx:.1f}" y="{cy-2:.1f}" font-size="{fs}" text-anchor="middle" font-weight="bold" fill="#1e1b4b"{rot}>{nm}</text>')
            s.append(f'<text x="{cx:.1f}" y="{cy+12:.1f}" font-size="{fs-1}" text-anchor="middle" fill="#1e1b4b"{rot}>{sz(max(w_, d_), min(w_, d_))}</text>')
# walls
for w in fl["walls"]:
    s.append(f'<rect x="{X(w[0]):.1f}" y="{Y(w[1]):.1f}" width="{(w[2]-w[0])*K:.1f}" height="{(w[3]-w[1])*K:.1f}" fill="#292524"/>')
# structural columns (Agharkar RCC sheet, rev R1): 230-wide from first floor up
for c in columns("F1-3"):
    r = c["rect"]
    s.append(f'<rect x="{X(r[0]):.1f}" y="{Y(r[1]):.1f}" width="{(r[2]-r[0])*K:.1f}" height="{(r[3]-r[1])*K:.1f}" fill="#b91c1c" stroke="#450a0a" stroke-width="1"/>')
    cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
    lx = X(r[0]) - 4 if cx < 0.5 else X(r[2]) + 4      # outer columns labelled outside the building
    anc = "end" if cx < 0.5 else "start"
    if cx < 0.5 or cx > 7.5 or c["name"] in ("C10", "C13", "C16", "C7"):
        s.append(f'<text x="{lx:.1f}" y="{Y(cy)+4:.1f}" font-size="10" font-weight="bold" text-anchor="{anc}" fill="#b91c1c">{c["name"]}</text>')
def wall_minus(a_list, b_list):
    """Parts of walls in a_list not covered by walls in b_list (5 cm raster, merged into runs)."""
    import itertools
    out = []
    for a in a_list:
        nx, ny = max(1, round((a[2] - a[0]) / 0.05)), max(1, round((a[3] - a[1]) / 0.05))
        horiz = nx >= ny
        cells = []
        for i, j in itertools.product(range(nx), range(ny)):
            cx, cy = a[0] + (i + 0.5) * (a[2] - a[0]) / nx, a[1] + (j + 0.5) * (a[3] - a[1]) / ny
            if not any(b[0] - 1e-6 <= cx <= b[2] + 1e-6 and b[1] - 1e-6 <= cy <= b[3] + 1e-6 for b in b_list):
                cells.append(i if horiz else j)
        for _, g in itertools.groupby(enumerate(sorted(set(cells))), lambda t: t[1] - t[0]):
            g = [c for _, c in g]
            if horiz:
                out.append([a[0] + g[0] * (a[2] - a[0]) / nx, a[1], a[0] + (g[-1] + 1) * (a[2] - a[0]) / nx, a[3]])
            else:
                out.append([a[0], a[1] + g[0] * (a[3] - a[1]) / ny, a[2], a[1] + (g[-1] + 1) * (a[3] - a[1]) / ny])
    return out


REMOVED, ADDED = wall_minus(WALLS0, fl["walls"]), wall_minus(fl["walls"], WALLS0)
if REMOVED or ADDED:   # changed brickwork vs the architect's drawing: removed walls dashed, new walls orange
    for w in REMOVED:
        s.append(f'<rect x="{X(w[0]):.1f}" y="{Y(w[1]):.1f}" width="{(w[2]-w[0])*K:.1f}" height="{(w[3]-w[1])*K:.1f}" fill="#fff" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="5 3"/>')
    for w in ADDED:
        s.append(f'<rect x="{X(w[0]):.1f}" y="{Y(w[1]):.1f}" width="{(w[2]-w[0])*K:.1f}" height="{(w[3]-w[1])*K:.1f}" fill="#f97316"/>')
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
_occ = {r: sum(1 for i in its if i["type"].endswith("_bed")) for r, its in FU["F1-3"].items()}
_txt = ", ".join(f"{r} {n}" for r, n in _occ.items())
for i, t in enumerate([f"Blue = Wakefit furniture. Students per room: {_txt} = {sum(_occ.values())} on this floor. Twin rooms use Centaur singles, single rooms the Orion queen.",
                       "Yellow = door swing; every door opens inwards. Light blue on walls = windows.",
                       "Red = RCC columns from the structural drawing (Agharkar, rev R1, 02.11.2026), 9\" wide on this floor; they stand out of the 6\" walls.",
                       "Walls, doors and windows from the architect's AFTER O.C. drawing. Furniture positions are proposals."]):
    s.append(f'<text x="{MX}" y="{lg + i*18:.0f}" font-size="12" fill="#333">{t}</text>')
s.append("</svg>")
if REMOVED or ADDED:
    note = DESC or "ROOM-3/ROOM-2 wall moved 3'-3 3/8\" towards the road; ROOM-2 and ROOM-3 doors moved (docs/floor1-changes.md)."
    s.insert(-1, f'<text x="{MX}" y="{lg + 4*18:.0f}" font-size="12" font-weight="bold" fill="#c2410c">Orange = new brick wall; red dashed = brick wall removed. Changed from the architect\'s drawing, family-approved 03.11.2026:</text>')
    s.insert(-1, f'<text x="{MX}" y="{lg + 5*18:.0f}" font-size="12" font-weight="bold" fill="#c2410c">{note}</text>')
(ROOT / f"docs/{OUT}.svg").write_text("\n".join(s))
print(f"wrote docs/{OUT}.svg", W, H)
