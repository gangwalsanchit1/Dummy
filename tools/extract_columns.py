#!/usr/bin/env python3
"""Read the column layout off the structural sheet (Agharkar Consulting Engineers, drg 01, rev R1, 02.11.2026)
and write model/structure.json in plan coordinates (metres, X from left outer face, Y from rear outer face).

The "LAYOUT AT PLINTH LEVEL" is a vector plan with no dimensions. Scale and origin are fitted from the outer
column faces, which must match the architect's 8.000 x 11.750 m outline. Each column is drawn as two filled
parts: the upper-floor size (230 wide, used from first floor up) plus a 70 mm strip that makes the 300 wide
plinth-to-first-floor size. Both are kept.
Usage: python3 tools/extract_columns.py "drawings/C-89 SEC-12 KHR RCC DETAILS.pdf"   (needs pdfplumber)
"""
import json
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "drawings/C-89 SEC-12 KHR RCC DETAILS.pdf"
pg = pdfplumber.open(pdf).pages[0]
BOX = (25, 200, 345, 660)  # the plinth-level layout panel, PDF points
inb = lambda o: o["x0"] >= BOX[0] and o["x1"] <= BOX[2] and o["top"] >= BOX[1] and o["bottom"] <= BOX[3]

rects = sorted({(round(o["x0"], 2), round(o["top"], 2), round(o["x1"], 2), round(o["bottom"], 2))
                for o in pg.curves + pg.rects if inb(o) and o.get("fill")})
# drop stair arrows and dimension arrowheads (nothing thinner than 4 pt in both directions is a column)
rects = [r for r in rects if max(r[2] - r[0], r[3] - r[1]) > 12]
x0 = min(r[0] for r in rects); x1 = max(r[2] for r in rects)
y0 = min(r[1] for r in rects); y1 = max(r[3] for r in rects)
kx, ky = (x1 - x0) / 8.0, (y1 - y0) / 11.75
K = (kx + ky) / 2
assert abs(kx - ky) / K < 0.002, (kx, ky)
M = lambda r: [round((r[0] - x0) / K, 3), round((r[1] - y0) / K, 3), round((r[2] - x0) / K, 3), round((r[3] - y0) / K, 3)]
mr = [M(r) for r in rects]

# pair each 0.07 m strip with the body it touches
strips = [r for r in mr if min(r[2] - r[0], r[3] - r[1]) < 0.08]
bodies = [r for r in mr if r not in strips]
cols = []
for b in bodies:
    near = [s for s in strips if (abs(s[1] - b[1]) < 0.01 and abs(s[3] - b[3]) < 0.01 and (abs(s[0] - b[2]) < 0.01 or abs(s[2] - b[0]) < 0.01))
            or (abs(s[0] - b[0]) < 0.01 and abs(s[2] - b[2]) < 0.01 and (abs(s[1] - b[3]) < 0.01 or abs(s[3] - b[1]) < 0.01))]
    full = b if not near else [min(b[0], near[0][0]), min(b[1], near[0][1]), max(b[2], near[0][2]), max(b[3], near[0][3])]
    cols.append({"upper": b, "plinth_to_F1": full})

labels = [(w["text"], (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2) for w in pg.extract_words() if inb(w) and re.fullmatch(r"C\d+", w["text"])]
for c in cols:
    u = c["upper"]
    c["_c"] = ((u[0] + u[2]) / 2 * K + x0, (u[1] + u[3]) / 2 * K + y0)
# lift-core walls are named by position (C3 top, C2 left, C4 right; the C4 label sits inside the pit by the right wall)
lift = [c for c in cols if max(c["upper"][2] - c["upper"][0], c["upper"][3] - c["upper"][1]) > 1.3]
for c in lift:
    u = c["upper"]
    c["name"] = "C3" if (u[2] - u[0]) > 1.0 else ("C2" if u[0] < 4.5 else "C4")
used = {c["name"] for c in lift}
for c in sorted([c for c in cols if "name" not in c], key=lambda c: min((c["_c"][0] - lx) ** 2 + (c["_c"][1] - ly) ** 2 for t, lx, ly in labels if t not in used)):
    t = min([l for l in labels if l[0] not in used], key=lambda l: (c["_c"][0] - l[1]) ** 2 + (c["_c"][1] - l[2]) ** 2)
    c["name"] = t[0]
    used.add(t[0])

SCHED = {  # typed from the SCHEDULE OF COLUMN & FOOTING on the same sheet
    ("C1", "C5", "C6"): ("300x600", "230x600", "8-T16", "6-T16", "1450x1850x600 isolated"),
    ("C2", "C4"): ("150x1800", "150x1800", "26-T10", "26-T10", "refer detail (lift pit raft)"),
    ("C3",): ("150x1400", "150x1400", "20-T10", "20-T10", "refer detail (lift pit raft)"),
    ("C7", "C8"): ("300x600", "230x600", "8-T16", "6-T16", "combined footing 3150x1450"),
    ("C9", "C10", "C11"): ("300x600", "230x600", "8-T16", "6-T16", "refer detail (combined)"),
    ("C15", "C16", "C17"): ("300x450", "230x450", "6-T16", "6-T16", "refer detail (combined)"),
    ("C12", "C13", "C14"): ("300x450", "230x450", "6-T16", "6-T16", "1250x1500x500 isolated"),
}
out = []
for c in sorted(cols, key=lambda c: int(c["name"][1:])):
    s = next(v for k, v in SCHED.items() if c["name"] in k)
    u = c["upper"]
    dims = sorted([round((u[2] - u[0]) * 1000), round((u[3] - u[1]) * 1000)])
    want = sorted(int(v) for v in s[1].split("x"))
    assert all(abs(a - b) <= 15 for a, b in zip(dims, want)), (c["name"], dims, want)
    out.append({"name": c["name"], "upper_rect": u, "plinth_to_F1_rect": c["plinth_to_F1"],
                "size_below_F1": s[0], "size_F1_up": s[1], "bars_below_F1": s[2], "bars_F1_up": s[3], "footing": s[4],
                "tag": "DRAWN (position scaled from the plinth layout, about +/-0.02 m; sizes from the schedule)"})
assert len(out) == 17, len(out)

doc = {
    "_source": f"{pdf.name}: Agharkar Consulting Engineers Pvt Ltd, 'Layout & RCC details of foundation, column & plinth beams', "
               "drg 01, job 119926, rev R1 02.11.2026 'Revised as per after OC columns & released for construction'. M20, Fe500.",
    "_fit": f"scale {K:.3f} pt/m fitted to the outer column faces = 8.000 x 11.750 m (x fit {kx:.3f}, y fit {ky:.3f}); "
            "stair treads on the sheet land at X 5.75-7.84, Y 4.10-5.67, matching the architect's plan",
    "levels_scheduled": ["footing", "plinth", "first floor", "second floor", "third floor", "terrace floor"],
    "columns": out,
    "plinth_beams": {"PB1": "230x500", "PB2": "230x500", "PB3": "230x500", "PB4": "150x500", "PB5": "230x300", "PB6": "150x300"},
    "not_on_sheet": ["floor beams at first floor and above", "slab thickness", "floor-to-floor heights", "any storey above 'third floor lvl to terrace floor lvl'"],
}
(ROOT / "model/structure.json").write_text(json.dumps(doc, indent=1))
for c in out:
    print(c["name"], c["upper_rect"], c["size_F1_up"])
print(doc["_fit"])
