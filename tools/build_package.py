#!/usr/bin/env python3
"""Phase 4: drawing package for Bella Vita 2.

Writes  package/dxf/<FLOOR>.dxf          layered DXF per floor (metres, X = plan X, Y = -plan Y)
        package/sheets/<FLOOR>-<A|E|P>.svg  A3 sheets at 1:60 (architecture / electrical / plumbing)
        package/sheets/schedules.html      point schedule, quantities, pre-slab checklist
PDFs are printed from the SVG/HTML by tools/print_pdfs.js (Chromium via Playwright).
Run with an interpreter that has ezdxf (pip install ezdxf; not committed).
"""
import csv
import html
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import ezdxf
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from units import ftin, size as ftsize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TK = json.loads((ROOT / "model/takeoff.json").read_text())
AS = json.loads((ROOT / "model/assumptions.json").read_text())
FU = json.loads((ROOT / "model/furniture.json").read_text())
SC = json.loads((ROOT / "model/scene.json").read_text())
M = json.loads((ROOT / "model/mep.json").read_text())
FFL = SC["ffl"]
H = AS["heights"]
OUT = ROOT / "package"
(OUT / "dxf").mkdir(parents=True, exist_ok=True)
(OUT / "sheets").mkdir(parents=True, exist_ok=True)
DATE = "2026-10-31"
FLOORS = [("GF", "GF", "GF", "Ground floor (stilt)"), ("F1-3", "F1", "F1-3", "First, second & third floor (typical)"),
          ("F4", "F4", "F4", "Fourth floor"), ("TERRACE", "TERRACE", "TERRACE", "Terrace")]
CODE = {"SB": "SB", "TSW": "TS", "BS": "BS", "DESK": "DK", "DATA": "D", "SKT16": "16A", "WPS": "WP", "ACS": "ACs", "GZP": "GZ",
        "LT": "L", "WL": "WL", "FAN": "F", "EXH": "EX", "ACI": "AC", "ACO": "ODU", "AP": "AP", "CCTV": "CC", "LIFTISO": "LI",
        "PUMPP": "PP", "RISER": "R", "DB": "DB", "MB": "MB", "MDB": "MDB", "CDB": "CDB", "WC": "WC", "BAS": "B", "SHM": "SH",
        "HF": "HF", "FT": "FT", "GZ": "GZ", "SINK": "SK", "TAP": "T", "PUMP": "P", "IC": "IC", "RWO": "RWO", "METER": "M",
        "TCON": "TC", "SLV": "SL", "INV": "INV", "RFID": "RF", "MLOCK": "ML", "RFIDL": "RL", "DISP": "WD", "WM": "WM", "RO": "RO", "COVE": "CV"}
PIPECOL = {"ACP": "#0d9488", "SOIL": "#8b4513", "WASTE": "#d97706", "VENT": "#9ca3af", "RWP": "#16a34a", "UGD": "#78350f", "CW": "#2563eb",
           "HW": "#dc2626", "DT": "#1d4ed8", "RM": "#7c3aed", "SUP": "#0891b2", "FEED": "#ca8a04", "COND": "#fb923c"}
ACI = {"ACP": 4, "SOIL": 30, "WASTE": 40, "VENT": 8, "RWP": 3, "UGD": 32, "CW": 5, "HW": 1, "DT": 150, "RM": 6, "SUP": 4, "FEED": 50, "COND": 30}


def band(storey):
    z0 = FFL[storey]
    return (z0 - 0.5, z0 + 3.0) if storey != "TERRACE" else (z0 - 0.5, 30)


def runs_for(storey, systems):
    """Plan projection of runs overlapping the storey's height band: lines + vertical markers."""
    lo, hi = band(storey)
    lines, verts = [], []
    for r in M["runs"]:
        if r["sys"] not in systems:
            continue
        if r["sys"] == "COND" and r["storey"] != storey:
            continue
        for a, b in zip(r["pts"], r["pts"][1:]):
            zmin, zmax = min(a[2], b[2]), max(a[2], b[2])
            if zmax < lo or zmin > hi:
                continue
            if math.hypot(a[0] - b[0], a[1] - b[1]) < 0.01:
                verts.append((r["sys"], a[0], a[1], r["name"]))
            else:
                lines.append((r["sys"], a, b, r["name"]))
    return lines, verts


def stack_label(name):
    for k in ("S1", "W1", "S2", "W2", "DT-R", "DT-F", "RWP-1", "RWP-2", "RWP-3", "RWP-4"):
        if k in name:
            return k
    if "Rising main" in name:
        return "RM"
    if "riser" in name.lower():
        return "ER"
    return ""


# ===================================================================== DXF
LAYERS = {"A-WALL": 8, "A-DOOR": 2, "A-WIND": 4, "A-FURN": 9, "A-TEXT": 7, "A-PLOT": 30, "A-STAIR": 9, "A-TANK": 5,
          "E-POINT": 30, "E-TEXT": 30, "E-COND": 30, "E-RISER": 50, "P-FIXT": 150, "P-TEXT": 150, "S-SLEEVE": 1}
for sysn, c in ACI.items():
    LAYERS[f"P-{sysn}" if sysn not in ("FEED", "COND") else f"E-{sysn}"] = c


def Y(y):
    return -y


def build_dxf(name, storey, pk, title):
    doc = ezdxf.new("R2018", setup=True)
    doc.header["$INSUNITS"] = 6
    for ln, c in LAYERS.items():
        if ln not in doc.layers:
            doc.layers.add(ln, color=c)
    ms = doc.modelspace()
    fl = TK["floors"][pk]
    for w in fl["walls"] + fl.get("railings", []):
        ms.add_lwpolyline([(w[0], Y(w[1])), (w[2], Y(w[1])), (w[2], Y(w[3])), (w[0], Y(w[3]))], close=True, dxfattribs={"layer": "A-WALL"})
        h = ms.add_hatch(color=8, dxfattribs={"layer": "A-WALL"})
        h.paths.add_polyline_path([(w[0], Y(w[1])), (w[2], Y(w[1])), (w[2], Y(w[3])), (w[0], Y(w[3]))], is_closed=True)
    ms.add_lwpolyline([(0, Y(-0.6)), (8, Y(-0.6)), (8, Y(12.75)), (0, Y(12.75))], close=True, dxfattribs={"layer": "A-PLOT", "linetype": "DASHED"})
    for wdw in fl.get("windows", []):
        y0 = 0.0 if wdw["wall"] == "rear" else fl["outline"][3] - 0.15
        for dy in (0.05, 0.10):
            ms.add_line((wdw["span_x"][0], Y(y0 + dy)), (wdw["span_x"][1], Y(y0 + dy)), dxfattribs={"layer": "A-WIND"})
        ms.add_text(f"{wdw['id']} {wdw['width']:.2f}", height=0.08, dxfattribs={"layer": "A-WIND"}).set_placement(
            ((wdw["span_x"][0] + wdw["span_x"][1]) / 2, Y(y0 - 0.12 if wdw["wall"] == "rear" else y0 + 0.30)), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    for d in AS["doors"].get(pk, []):
        hx, hy = d["hinge"]
        qx, qy = d["quadrant"]
        r = d["width"]
        a0 = math.degrees(math.atan2(-qy, qx)) - 45
        ms.add_arc((hx, Y(hy)), r, a0, a0 + 90, dxfattribs={"layer": "A-DOOR"})
        ms.add_text(d["id"], height=0.07, dxfattribs={"layer": "A-DOOR"}).set_placement((hx + qx * r * 0.45, Y(hy + qy * r * 0.45)))
    for room, items in FU.get(pk, {}).items():
        if room.startswith("_"):
            continue
        for it in items:
            r = it["rect"]
            ms.add_lwpolyline([(r[0], Y(r[1])), (r[2], Y(r[1])), (r[2], Y(r[3])), (r[0], Y(r[3]))], close=True, dxfattribs={"layer": "A-FURN"})
            ms.add_text(f'{it["type"].replace("_", " ")} {ftsize(r[2] - r[0], r[3] - r[1])}', height=0.07, dxfattribs={"layer": "A-FURN"}).set_placement(
                ((r[0] + r[2]) / 2, Y((r[1] + r[3]) / 2)), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    for sp in fl.get("spaces", []):
        r = max(sp["rects"], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
        ms.add_text(sp["name"], height=0.14, dxfattribs={"layer": "A-TEXT"}).set_placement(((r[0] + r[2]) / 2, Y((r[1] + r[3]) / 2) + 0.12), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        ms.add_text(f"{r[2]-r[0]:.2f} x {r[3]-r[1]:.2f}", height=0.09, dxfattribs={"layer": "A-TEXT"}).set_placement(((r[0] + r[2]) / 2, Y((r[1] + r[3]) / 2) - 0.08), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    if pk != "GF" or True:
        for y in [4.10 + 0.25 * i for i in range(8)]:
            for x0, x1 in ((5.75, 6.75), (6.85, 7.85)):
                ms.add_line((x0, Y(y)), (x1, Y(y)), dxfattribs={"layer": "A-STAIR"})
    if pk == "GF":
        t = TK["site"]["ug_tank"]
        for rr in (t["outer"], t["inner"]):
            ms.add_lwpolyline([(rr[0], Y(rr[1])), (rr[2], Y(rr[1])), (rr[2], Y(rr[3])), (rr[0], Y(rr[3]))], close=True, dxfattribs={"layer": "A-TANK"})
    if pk == "TERRACE":
        t = TK["site"]["oht"]["inner"]
        ms.add_lwpolyline([(t[0], Y(t[1])), (t[2], Y(t[1])), (t[2], Y(t[3])), (t[0], Y(t[3]))], close=True, dxfattribs={"layer": "A-TANK"})
    for p in M["points"]:
        if p["storey"] != storey:
            continue
        lay = {"E": "E-POINT", "P": "P-FIXT", "S": "S-SLEEVE"}[p["sys"]]
        tl = {"E": "E-TEXT", "P": "P-TEXT", "S": "S-SLEEVE"}[p["sys"]]
        ms.add_circle((p["x"], Y(p["y"])), 0.07, dxfattribs={"layer": lay})
        ms.add_text(f"{CODE[p['kind']]} {ftin(p['zrel'])}" if p["face"] not in ("C", "F") else CODE[p["kind"]], height=0.06,
                    dxfattribs={"layer": tl}).set_placement((p["x"] + 0.09, Y(p["y"]) + 0.03))
    lines, verts = runs_for(storey, set(PIPECOL))
    for sysn, a, b, nm in lines:
        lay = f"P-{sysn}" if sysn not in ("FEED", "COND") else f"E-{sysn}"
        ms.add_line((a[0], Y(a[1])), (b[0], Y(b[1])), dxfattribs={"layer": lay})
    for sysn, x, y, nm in verts:
        lay = f"P-{sysn}" if sysn not in ("FEED", "COND") else f"E-{sysn}"
        ms.add_circle((x, Y(y)), 0.06, dxfattribs={"layer": lay})
        if stack_label(nm):
            ms.add_text(stack_label(nm), height=0.08, dxfattribs={"layer": lay}).set_placement((x + 0.08, Y(y) - 0.12))
    ms.add_text(f"BELLA VITA 2 - {title} - COORDINATION, NOT FOR CONSTRUCTION - units: feet and inches - floor level {ftin(FFL[storey])} above road (ASSUMED)",
                height=0.25, dxfattribs={"layer": "A-TEXT"}).set_placement((0, Y(14.0)))
    from ezdxf.math import Matrix44
    m = Matrix44.scale(1 / 0.0254)                         # metres -> inches; CAD reads feet-inches
    for e in list(ms):
        try:
            e.transform(m)
        except Exception:
            pass
    doc.header["$INSUNITS"] = 1                              # inches
    doc.header["$LUNITS"] = 4                                # architectural (feet-inches)
    doc.header["$MEASUREMENT"] = 0                           # imperial
    doc.saveas(OUT / "dxf" / f"{name}.dxf")


# ===================================================================== SVG sheets (A3 landscape, 1:60)
KMM = 1000 / 60.0                       # mm per metre at 1:60
OX, OY = 18.0, 30.0


def X_(x):
    return OX + (x + 0.3) * KMM


def Y_(y):
    return OY + (y + 0.8) * KMM


def esc(s):
    return html.escape(str(s))


def sheet(name, storey, pk, title, kind):
    fl = TK["floors"][pk]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297" font-family="Arial, Helvetica, sans-serif">',
         '<rect width="420" height="297" fill="#fff"/>', '<rect x="8" y="8" width="404" height="281" fill="none" stroke="#111" stroke-width="0.5"/>']
    # plot + walls
    s.append(f'<rect x="{X_(0):.2f}" y="{Y_(-0.6):.2f}" width="{8*KMM:.2f}" height="{13.35*KMM:.2f}" fill="none" stroke="#f59e0b" stroke-width="0.3" stroke-dasharray="3 2"/>')
    s.append(f'<text x="{X_(4):.1f}" y="{Y_(13.25):.1f}" font-size="3" text-anchor="middle" fill="#555">6.00 M WIDE ROAD</text>')
    if pk == "GF":
        t = TK["site"]["ug_tank"]["inner"]
        s.append(f'<rect x="{X_(t[0]):.2f}" y="{Y_(t[1]):.2f}" width="{(t[2]-t[0])*KMM:.2f}" height="{(t[3]-t[1])*KMM:.2f}" fill="#dbeafe" stroke="#3b82f6" stroke-width="0.3" stroke-dasharray="2 1"/>')
        s.append(f'<text x="{X_((t[0]+t[2])/2):.1f}" y="{Y_((t[1]+t[3])/2):.1f}" font-size="2.2" text-anchor="middle" fill="#1d4ed8">U.G. TANK 10,000 L</text>')
    if pk == "TERRACE":
        t = TK["site"]["oht"]["inner"]
        s.append(f'<rect x="{X_(t[0]):.2f}" y="{Y_(t[1]):.2f}" width="{(t[2]-t[0])*KMM:.2f}" height="{(t[3]-t[1])*KMM:.2f}" fill="#dbeafe" stroke="#3b82f6" stroke-width="0.3" stroke-dasharray="2 1"/>')
        s.append(f'<text x="{X_(6.8):.1f}" y="{Y_(6.4):.1f}" font-size="2.2" text-anchor="middle" fill="#1d4ed8">O.H.T. 6,500 L (over cabin)</text>')
    for y in [4.10 + 0.25 * i for i in range(8)]:
        for x0, x1 in ((5.75, 6.75), (6.85, 7.85)):
            s.append(f'<line x1="{X_(x0):.2f}" y1="{Y_(y):.2f}" x2="{X_(x1):.2f}" y2="{Y_(y):.2f}" stroke="#bbb" stroke-width="0.2"/>')
    if kind != "A":
        for sp in fl.get("spaces", []):
            pass
    for sp in fl.get("spaces", []):
        if kind == "A":
            for r in sp["rects"]:
                s.append(f'<rect x="{X_(r[0]):.2f}" y="{Y_(r[1]):.2f}" width="{(r[2]-r[0])*KMM:.2f}" height="{(r[3]-r[1])*KMM:.2f}" fill="#fef9c3" opacity="0.6"/>')
    for room, items in FU.get(pk, {}).items():
        if room.startswith("_"):
            continue
        for it in items:
            r = it["rect"]
            s.append(f'<rect x="{X_(r[0]):.2f}" y="{Y_(r[1]):.2f}" width="{(r[2]-r[0])*KMM:.2f}" height="{(r[3]-r[1])*KMM:.2f}" fill="{"#c7d2fe" if kind == "A" else "#f1f5f9"}" stroke="#94a3b8" stroke-width="0.2"/>')
            if kind == "A":
                s.append(f'<text x="{X_((r[0]+r[2])/2):.1f}" y="{Y_((r[1]+r[3])/2)+0.8:.1f}" font-size="1.8" text-anchor="middle" fill="#334155">{esc(it["type"].replace("_", " "))}</text>')
                s.append(f'<text x="{X_((r[0]+r[2])/2):.1f}" y="{Y_((r[1]+r[3])/2)+3.0:.1f}" font-size="1.6" text-anchor="middle" fill="#334155">{esc(ftsize(r[2]-r[0], r[3]-r[1]))}</text>')
    for w in fl["walls"] + fl.get("railings", []):
        s.append(f'<rect x="{X_(w[0]):.2f}" y="{Y_(w[1]):.2f}" width="{(w[2]-w[0])*KMM:.2f}" height="{(w[3]-w[1])*KMM:.2f}" fill="#374151"/>')
    for wdw in fl.get("windows", []):
        y0 = 0.0 if wdw["wall"] == "rear" else fl["outline"][3] - 0.15
        s.append(f'<rect x="{X_(wdw["span_x"][0]):.2f}" y="{Y_(y0):.2f}" width="{wdw["width"]*KMM:.2f}" height="{0.15*KMM:.2f}" fill="#bfdbfe" stroke="#2563eb" stroke-width="0.2"/>')
    for d in AS["doors"].get(pk, []):
        hx, hy = d["hinge"]
        qx, qy = d["quadrant"]
        r = d["width"]
        # leaf open position + arc to closed
        if d["leaf_axis"] == "x":
            open_pt, closed_pt = (hx, hy + qy * r), (hx + qx * r, hy)
        else:
            open_pt, closed_pt = (hx + qx * r, hy), (hx, hy + qy * r)
        sweep = 1 if (qx * qy > 0) == (d["leaf_axis"] == "x") else 0
        s.append(f'<line x1="{X_(hx):.2f}" y1="{Y_(hy):.2f}" x2="{X_(open_pt[0]):.2f}" y2="{Y_(open_pt[1]):.2f}" stroke="#92400e" stroke-width="0.35"/>')
        s.append(f'<path d="M{X_(open_pt[0]):.2f},{Y_(open_pt[1]):.2f} A{r*KMM:.2f},{r*KMM:.2f} 0 0 {sweep} {X_(closed_pt[0]):.2f},{Y_(closed_pt[1]):.2f}" fill="none" stroke="#92400e" stroke-width="0.2" stroke-dasharray="1 0.6"/>')
    # room labels
    for sp in fl.get("spaces", []):
        r = max(sp["rects"], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
        cx, cy = X_((r[0] + r[2]) / 2), Y_((r[1] + r[3]) / 2)
        if kind == "A":
            a = sum((q[2] - q[0]) * (q[3] - q[1]) for q in sp["rects"])
            s.append(f'<text x="{cx:.1f}" y="{cy-2:.1f}" font-size="2.4" font-weight="bold" text-anchor="middle">{esc(sp["name"])}</text>')
            s.append(f'<text x="{cx:.1f}" y="{cy+1:.1f}" font-size="2" text-anchor="middle">{ftin(r[2]-r[0])} x {ftin(r[3]-r[1])} · {a * 10.7639:.0f} sq ft</text>')
            if sp.get("label"):
                s.append(f'<text x="{cx:.1f}" y="{cy+3.6:.1f}" font-size="1.7" text-anchor="middle" fill="#666">drawn label {esc(sp["label"])[:40]}</text>')
        else:
            s.append(f'<text x="{cx:.1f}" y="{cy:.1f}" font-size="1.9" text-anchor="middle" fill="#9ca3af">{esc(sp["name"])}</text>')
    if kind == "A":
        # overall dimensions
        y = -0.55
        s.append(f'<line x1="{X_(0):.2f}" y1="{Y_(y):.2f}" x2="{X_(8):.2f}" y2="{Y_(y):.2f}" stroke="#111" stroke-width="0.2"/>')
        s.append(f'<text x="{X_(4):.1f}" y="{Y_(y)-1:.1f}" font-size="2.2" text-anchor="middle">{ftin(8.0)} (DRAWN)</text>')
        dep = fl["outline"][3]
        s.append(f'<line x1="{X_(-0.2):.2f}" y1="{Y_(0):.2f}" x2="{X_(-0.2):.2f}" y2="{Y_(dep):.2f}" stroke="#111" stroke-width="0.2"/>')
        s.append(f'<text x="{X_(-0.25):.1f}" y="{Y_(dep/2):.1f}" font-size="2.2" text-anchor="middle" transform="rotate(-90 {X_(-0.25):.1f} {Y_(dep/2):.1f})">{ftin(dep)} (DRAWN)</text>')
    # MEP
    legend = Counter()
    if kind in ("E", "P"):
        systems = {"E": {"FEED", "COND", "ACP"}, "P": {"SOIL", "WASTE", "VENT", "RWP", "UGD", "CW", "HW", "DT", "RM", "SUP"}}[kind]
        lines, verts = runs_for(storey, systems)
        for sysn, a, b, nm in lines:
            dash = ' stroke-dasharray="1.2 0.8"' if sysn in ("COND", "UGD") else ""
            s.append(f'<line x1="{X_(a[0]):.2f}" y1="{Y_(a[1]):.2f}" x2="{X_(b[0]):.2f}" y2="{Y_(b[1]):.2f}" stroke="{PIPECOL[sysn]}" stroke-width="{0.25 if sysn == "COND" else 0.45}"{dash} opacity="0.85"/>')
            legend[f"line:{sysn}"] += 1
        seen = set()
        for sysn, x, y, nm in verts:
            key = (round(x, 2), round(y, 2), sysn)
            if key in seen:
                continue
            seen.add(key)
            s.append(f'<circle cx="{X_(x):.2f}" cy="{Y_(y):.2f}" r="1.1" fill="#fff" stroke="{PIPECOL[sysn]}" stroke-width="0.5"/>')
            lab = stack_label(nm)
            if lab:
                s.append(f'<text x="{X_(x):.1f}" y="{Y_(y)+(3.2 if y < 6 else -1.8):.1f}" font-size="2" text-anchor="middle" fill="{PIPECOL[sysn]}" font-weight="bold">{lab}</text>')
        want = {"E": ("E",), "P": ("P",)}[kind]
        for p in M["points"]:
            if p["storey"] != storey or (p["sys"] not in want and not (p["sys"] == "S")):
                continue
            if p["sys"] == "S":
                if (kind == "E" and p["room"] not in ("slab", "fanbox")) or (kind == "P" and p["room"] in ("slab", "fanbox")):
                    continue
                if p["room"] == "sunk":
                    sp = next(q for q in TK["floors"][pk]["spaces"] if f"for {q['name']} (floor trap" in p["note"])
                    r = sp["rects"][0]
                    s.append(f'<rect x="{X_(r[0]):.2f}" y="{Y_(r[1]):.2f}" width="{(r[2]-r[0])*KMM:.2f}" height="{(r[3]-r[1])*KMM:.2f}" fill="url(#hatch)" stroke="#dc2626" stroke-width="0.25"/>')
                    legend["SUNK"] += 1
                    continue
                s.append(f'<rect x="{X_(p["x"])-1:.2f}" y="{Y_(p["y"])-1:.2f}" width="2" height="2" fill="none" stroke="#dc2626" stroke-width="0.4"/>')
                legend["SLV"] += 1
                continue
            col = "#b45309" if p["sys"] == "E" else "#0369a1"
            s.append(f'<circle cx="{X_(p["x"]):.2f}" cy="{Y_(p["y"]):.2f}" r="0.9" fill="{col}"/>')
            lab = CODE[p["kind"]] + ("" if p["face"] in ("C", "F") else f" {ftin(p['zrel'])}")
            s.append(f'<text x="{X_(p["x"])+1.2:.1f}" y="{Y_(p["y"])+0.7:.1f}" font-size="1.7" fill="{col}">{esc(lab)}</text>')
            legend[p["kind"]] += 1
    s.insert(1, '<defs><pattern id="hatch" width="1.5" height="1.5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.5" stroke="#fca5a5" stroke-width="0.5"/></pattern></defs>')
    # scale bar
    sx, sy = X_(0), 287 - 12
    FT4 = 4 * 0.3048 * KMM                                  # 4 ft per segment
    for i in range(4):
        s.append(f'<rect x="{sx + i*FT4:.2f}" y="{sy}" width="{FT4:.2f}" height="1.2" fill="{"#111" if i % 2 == 0 else "#fff"}" stroke="#111" stroke-width="0.15"/>')
    s.append(f'<text x="{sx:.1f}" y="{sy+4}" font-size="2">0</text><text x="{sx+4*FT4:.1f}" y="{sy+4}" font-size="2">16 ft</text><text x="{sx+4*FT4+8:.1f}" y="{sy+1.5}" font-size="2.2">Scale 1:60 at A3</text>')
    # right panel: title block, legend, notes
    px = 200
    kindname = {"A": "Architectural layout & furniture", "E": "Electrical points, riser & conduits (proposal)", "P": "Plumbing & drainage (proposal)"}[kind]
    s.append(f'<text x="{px}" y="24" font-size="7" font-weight="bold">BELLA VITA 2 · {esc(title.upper())}</text>')
    s.append(f'<text x="{px}" y="32" font-size="4.2">{esc(kindname)}</text>')
    s.append(f'<text x="{px}" y="39" font-size="2.8" fill="#555">Plot C-89, Sector 12, Kharghar, Navi Mumbai · student PG · source: AFTER O.C. sheet 03-08-2026</text>')
    s.append(f'<text x="{px}" y="44" font-size="2.8" fill="#555">floor level {ftin(FFL[storey])} above road (ASSUMED) · all dimensions in feet and inches</text>')
    s.append(f'<rect x="{px}" y="48" width="200" height="8" fill="#fee2e2"/><text x="{px+2}" y="53.5" font-size="3.2" fill="#991b1b" font-weight="bold">COORDINATION DRAWING – NOT FOR CONSTRUCTION. Structure &amp; final MEP by licensed consultants.</text>')
    yy = 64
    if kind == "A":
        rows = ["Walls, doors, windows, rooms: DRAWN from the PDF vectors (to about 1/2 inch).",
                "Door swings: DRAWN on F4, ASSUMED elsewhere (takeoff Q6). Furniture: ASSUMED positions, brief sizes.",
                "Room labels show the main rectangle in feet and inches and the total area in sq ft.",
                "No columns or beams are drawn on the source sheet; none shown (takeoff Q1).",
                "Wardrobes sit in the drawn grey 0.55 m strips (takeoff Q7)."]
        if pk == "F1-3":
            rows.append("Typical for F1, F2 and F3 (identical on the drawing).")
        for t in rows:
            s.append(f'<text x="{px}" y="{yy}" font-size="2.8">• {esc(t)}</text>')
            yy += 5
    else:
        s.append(f'<text x="{px}" y="{yy}" font-size="3.4" font-weight="bold">Legend (count on this sheet)</text>')
        yy += 5
        col2 = 0
        items = [k for k in legend if not k.startswith("line:") and k not in ("SLV", "SUNK")]
        for i, k in enumerate(sorted(items)):
            cx = px + (i % 2) * 100
            cy = yy + (i // 2) * 4.4
            colr = "#b45309" if kind == "E" else "#0369a1"
            s.append(f'<circle cx="{cx+1}" cy="{cy-1}" r="0.9" fill="{colr}"/><text x="{cx+3}" y="{cy}" font-size="2.5"><tspan font-weight="bold">{CODE[k]}</tspan> {esc(M["kinds"][k]["desc"][:52])} ×{legend[k]}</text>')
        yy += (len(items) + 1) // 2 * 4.4 + 3
        for k in sorted(x for x in legend if x.startswith("line:")):
            sysn = k[5:]
            s.append(f'<line x1="{px}" y1="{yy-1}" x2="{px+8}" y2="{yy-1}" stroke="{PIPECOL[sysn]}" stroke-width="0.8"/><text x="{px+10}" y="{yy}" font-size="2.5">{esc(M["pipes"][sysn]["desc"])}</text>')
            yy += 4.2
        if legend["SLV"]:
            s.append(f'<rect x="{px}" y="{yy-2.5}" width="2" height="2" fill="none" stroke="#dc2626" stroke-width="0.4"/><text x="{px+4}" y="{yy-0.8}" font-size="2.5">Sleeve / cast-in item before slab pour (see pre-slab checklist) ×{legend["SLV"]}</text>')
            yy += 4.2
        if legend["SUNK"]:
            s.append(f'<rect x="{px}" y="{yy-2.5}" width="4" height="2" fill="url(#hatch)" stroke="#dc2626" stroke-width="0.3"/><text x="{px+6}" y="{yy-0.8}" font-size="2.5">Toilet slab depression 300 mm (ASSUMED) – decide before slab pour ×{legend["SUNK"]}</text>')
            yy += 4.2
        s.append(f'<text x="{px}" y="{yy+1}" font-size="2.5">○ = vertical pipe/riser passing this floor (S1/W1 rear soil/waste, S2/W2 front, DT down-take, RM rising main, ER electrical riser)</text>')
        yy += 6
        notes = {"E": ["Numbers after a code = mounting height above floor in feet and inches (ASSUMED practice).",
                       "Conduits shown are indicative routes in the slab above (pre-slab item) and wall chases.",
                       "Each room: lights+fan 10A, sockets 16A, AC 20A, geyser 20A circuits; RCBO per room (CEA Reg. 44).",
                       "All positions checked: on a wall, clear of windows, door openings, door swings and furniture (docs/mep-checks.md)."],
                 "P": ["External stacks (no shaft drawn). F4 front offset across F4 terrace in parapet sleeves (ASSUMED).",
                       f"Water demand {json.loads((ROOT / 'model/mep_summary.json').read_text())['water_demand_L_day']:,} L/day = (students + 2 staff) x 135 L (IS 1172:1993 Table 1, hostels).",
                       "Top-floor pressure only ~0.5 bar from O.H.T. (CALCULATED from ASSUMED levels): consider booster.",
                       "Fixture heights and pipe sizes: ASSUMED practice, plumbing consultant to confirm."]}[kind]
        for t in notes:
            s.append(f'<text x="{px}" y="{yy}" font-size="2.6">• {esc(t)}</text>')
            yy += 4.6
        if pk == "F1-3":
            s.append(f'<text x="{px}" y="{yy}" font-size="2.6">• Typical for F1, F2 and F3; point ids in the schedule use F1-/F2-/F3- prefixes.</text>')
    s.append(f'<text x="{px}" y="282" font-size="2.6" fill="#555">Sheet {esc(name)}-{kind} · {DATE} · generated by tools/build_package.py · tags: DRAWN / CALCULATED / ASSUMED</text>')
    s.append("</svg>")
    (OUT / "sheets" / f"{name}-{kind}.svg").write_text("\n".join(s))


def furniture_schedule():
    cat = AS.get("wakefit_catalog", {})
    rows = [["floor", "room", "item", "Wakefit product", "link", "width", "depth", "height", "clearance"]]
    clr = {"bed": AS["clearances"]["queen_bed_sides"], "wardrobe": AS["clearances"]["sliding_wardrobe_front"], "desk": AS["clearances"]["desk_chair_zone"]}
    for room, items in FU.get("F1-3", {}).items():                   # floor 1 only (family: work on floor 1 for now)
        for it in items:
            w_, d_, h_ = AS["furniture_sizes"][it["type"]]
            key = "bed" if it["type"].endswith("_bed") else "wardrobe" if "wardrobe" in it["type"] else "desk" if it["type"].endswith("desk") else None
            c = cat.get(it["type"], {})
            cl = clr.get(key)
            rows.append(["F1", room, it["type"].replace("_", " "), c.get("product", ""), c.get("link", ""), ftin(w_), ftin(d_), ftin(h_),
                         (ftin(cl) + (" each open side" if key == "bed" else " in front" if key == "wardrobe" else " chair pull-out")) if cl else ""])
    with open(ROOT / "docs/schedules/furniture_schedule.csv", "w", newline="") as fh:
        csv.writer(fh).writerows(rows)
    return rows


def schedules_html():
    rows = list(csv.DictReader(open(ROOT / "docs/schedules/points_schedule.csv")))
    q = list(csv.reader(open(ROOT / "docs/schedules/quantities.csv")))
    pre = (ROOT / "docs/pre-slab-checklist.md").read_text()
    h = ["<!doctype html><html><head><meta charset='utf-8'><title>Bella Vita 2 schedules</title><style>",
         "body{font:9px Arial;margin:0} h1{font-size:15px;margin:0 0 4px} h2{font-size:12px;margin:10px 0 4px;page-break-after:avoid}",
         "table{border-collapse:collapse;width:100%;margin-bottom:6px} td,th{border:1px solid #ccc;padding:1px 3px;text-align:left;vertical-align:top}",
         "th{background:#eef2f7} .room{page-break-inside:avoid} .warn{background:#fee2e2;color:#991b1b;padding:4px;font-weight:bold}",
         "</style></head><body>", "<h1>Bella Vita 2 – Point schedules, quantities and pre-slab checklist</h1>",
         "<div class='warn'>Coordination proposal, not for construction. All positions ASSUMED; final electrical and plumbing design by licensed consultants; all slab openings by the structural engineer.</div>"]
    h.append("<h2>1. Quantities (counts by floor; run lengths approximate)</h2><table>")
    for i, r in enumerate(q):
        if not r:
            h.append("</table><table>")
            continue
        tag = "th" if i == 0 or r[0] == "run" else "td"
        h.append("<tr>" + "".join(f"<{tag}>{esc(c)}</{tag}>" for c in r) + "</tr>")
    h.append("</table>")
    h.append("<h2>2. Furniture schedule, floor 1 (Wakefit, feet and inches)</h2><table>")
    for i, r in enumerate(furniture_schedule()):
        cells = [r[0], r[1], r[3] or r[2], r[5], r[6], r[7], r[8]] if i else ["Floor", "Room", "Item", "Width", "Depth", "Height", "Clearance"]
        tag = "th" if i == 0 else "td"
        h.append("<tr>" + "".join(f"<{tag}>{esc(c)}</{tag}>" for c in cells) + "</tr>")
    h.append("</table>")
    h.append("<h2>3. Room-by-room point schedule</h2>")
    by = defaultdict(list)
    for r in rows:
        by[(r["storey"], r["room"])].append(r)
    order = {"GF": 0, "F1": 1, "F2": 2, "F3": 3, "F4": 4, "TERRACE": 5}
    for (st, room), rs in sorted(by.items(), key=lambda kv: (order[kv[0][0]], kv[0][1])):
        if st in ("F2", "F3"):
            continue
        h.append(f"<div class='room'><h2>{esc(st if st not in ('F1',) else 'F1 (same for F2, F3)')} · {esc(room)}</h2><table><tr><th>Id</th><th>System</th><th>Item</th><th>X</th><th>Y</th><th>Height above FFL</th><th>Mounting</th><th>Circuit</th><th>Note</th><th>Check</th></tr>")
        for r in rs:
            h.append("<tr>" + "".join(f"<td>{esc(r[k])}</td>" for k in ("point_id", "system", "item", "plan_x_m", "plan_y_m", "height_above_FFL_m", "mounting", "circuit", "note", "clash_check")) + "</tr>")
        h.append("</table></div>")
    h.append("<h2>4. Pre-slab checklist</h2>")
    for line in pre.splitlines():
        if line.startswith("## "):
            h.append(f"<h2>{esc(line[3:])}</h2>")
        elif line.startswith("|") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            h.append("<table><tr>" + "".join(f"<td>{esc(c)}</td>" for c in cells) + "</tr></table>")
        elif line.startswith("- "):
            h.append(f"<p>• {esc(line[2:])}</p>")
    h.append("</body></html>")
    (OUT / "sheets/schedules.html").write_text("\n".join(h))


for name, storey, pk, title in FLOORS:
    build_dxf(name, storey, pk, title)
    for kind in ("A", "E", "P"):
        sheet(name, storey, pk, title, kind)
schedules_html()
print("ok", sorted(p.name for p in (OUT / "dxf").iterdir()), len(list((OUT / "sheets").iterdir())))
