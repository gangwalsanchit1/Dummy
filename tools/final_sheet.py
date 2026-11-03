#!/usr/bin/env python3
"""Final floor 1 drawing set (feet and inches), from model/scenarios/final-floor1.json:
  page 1  floor plan with title block (docs/final/floor1-final-plan.svg)
  page 2  room schedule, Wakefit product schedule with quantities, audit result, open items
Writes docs/final/floor1-final.html; tools/print_final.js turns it into docs/final/floor1-final.pdf (A3) and a PNG.
"""
import html
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from units import ftin as _ftin, sqft  # noqa: E402

FR = {" 1/8": "⅛", " 1/4": "¼", " 3/8": "⅜", " 1/2": "½", " 5/8": "⅝", " 3/4": "¾", " 7/8": "⅞"}


def ftin(m):
    t = _ftin(m)
    for a, b in FR.items():
        t = t.replace(a, b)
    return t


def nb(t):
    """keep a size on one line"""
    for a, b in FR.items():
        t = t.replace(a, b)
    return t.replace(" × ", "\u00a0×\u00a0").replace(" ", "\u00a0")

SC_PATH = ROOT / "model/scenarios/final-floor1.json"
SC = json.loads(SC_PATH.read_text())
AS = json.loads((ROOT / "model/assumptions.json").read_text())
CAT, FS = AS["wakefit_catalog"], AS["furniture_sizes"]
ST = json.loads((ROOT / "model/structure.json").read_text())

subprocess.run([sys.executable, str(ROOT / "tools/floor1_plan.py"), str(SC_PATH), "final/floor1-final-plan"], check=True, capture_output=True)
subprocess.run([sys.executable, str(ROOT / "tools/check_layout.py"), str(SC_PATH)], check=True, capture_output=True)
plan_svg = (ROOT / "docs/final/floor1-final-plan.svg").read_text()
audit = [l for l in (ROOT / "docs/final-floor1-audit.md").read_text().split("\n") if l.startswith("| ROOM")]

NAME = {"centaur_single_bed": "Wakefit Centaur single storage bed", "orion_queen_bed": "Wakefit Orion queen storage bed",
        "tinker_side_table": "Wakefit Tinker bedside table", "twill_wardrobe": "Wakefit Twill 2-door compact wardrobe",
        "gingham_wardrobe": "Wakefit Gingham 2-door wardrobe with mirror", "cabrera_desk": "Wakefit Cabrera study table",
        "sage_desk": "Wakefit Sage study table (with hutch)", "flipper_sofa": "Wakefit Flipper 2-seater sofa cum bed",
        "tv_42": "Wall-mounted TV 42\" (any brand)", "tv_40": "Wall-mounted TV 40\" (any brand)", "tv_32": "Wall-mounted TV 32\" (any brand)"}
ORDER = list(NAME)
L = SC["layouts"]
rooms = ["ROOM-1", "ROOM-2", "ROOM-3", "ROOM-4"]
cnt = {r: Counter(i["type"] for i in L[r]) for r in rooms}
tot = sum(cnt.values(), Counter())
students = {r: sum(v for t, v in cnt[r].items() if t.endswith("_bed")) for r in rooms}

# ---- room schedule
sp = {s["name"]: s["rects"] for s in SC["TK"]["spaces"]}
DESC = {"ROOM-1": "Twin. Wardrobes by the entry; beds with heads on the outer wall, clear of both side walls; desks facing each other; shared 42\" TV seen from both beds.",
        "ROOM-2": "Twin (the family's ROOM-1), family's final design: both beds along the outer side wall, one head to the partition and one to the road wall, a Tinker shared between the beds' feet and one at the second bed's head; one Twill beside the first bed, one in the alcove by the toilet; two desks side by side on the toilet wall. No TV.",
        "ROOM-3": "Luxury single, father's hotel layout: queen in the middle, headboard opposite the door, Tinker each side; Flipper sofa in the window nook facing a 32\" TV; Cabrera under the window; Gingham facing the bed.",
        "ROOM-4": "Single: Centaur single bed turned across the room, headboard on the outer side wall, centred, Tinker each side, clear of both long sides; Gingham and Cabrera on the left wall with a 32\" TV above the desk facing the bed."}
room_rows = []
for r in rooms:
    main = max(sp[r], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
    area = sum((q[2] - q[0]) * (q[3] - q[1]) for q in sp[r])
    room_rows.append(f"<tr><td><b>{r}</b></td><td class=n>{students[r]}</td><td>{nb(ftin(main[2]-main[0]) + ' × ' + ftin(main[3]-main[1]))}</td><td>{nb(sqft(area))}</td><td>{html.escape(DESC[r])}</td></tr>")

# ---- product schedule
prod_rows = []
for t in ORDER:
    if not tot[t]:
        continue
    c = CAT.get(t, {})
    w, d = FS[t][0], FS[t][1]
    link = c.get("link")
    nm = f'<a href="{link}">{html.escape(NAME[t])}</a>' if link else html.escape(NAME[t])
    prod_rows.append(f"<tr><td>{nm}</td><td>{html.escape(c.get('size_cm', '-'))}</td><td>{nb(ftin(w) + ' × ' + ftin(d))}</td>"
                     + "".join(f"<td class=n>{cnt[r][t] or '–'}</td>" for r in rooms) + f"<td class=n><b>{tot[t]}</b></td><td class=n><b>{3 * tot[t]}</b></td></tr>")
nbs = sum(v for t, v in tot.items() if t == "centaur_single_bed")
nbq = sum(v for t, v in tot.items() if t == "orion_queen_bed")
nd = sum(v for t, v in tot.items() if t.endswith("desk"))
extra = [f"Wakefit single mattress 78 × 36 in for the Centaur: {nbs} per floor, {3 * nbs} on floors 1–3",
         f"Wakefit queen mattress 78 × 60 in for the Orion: {nbq} per floor, {3 * nbq} on floors 1–3",
         f"Study chair, one per desk: {nd} per floor, {3 * nd} on floors 1–3"]

audit_rows = []
for l in audit:
    c = [x.strip() for x in l.strip("|").split("|")]
    m = html.escape(c[3]).replace('; ', ' · ')
    for a, b in FR.items():
        m = m.replace(a, b)
    audit_rows.append(f"<tr><td><b>{c[0]}</b></td><td class=ok>{c[1]}</td><td>{m}</td></tr>")

S = sum(students.values())
page2 = f"""
<h1>Bella Vita 2 · Floor 1 FINAL LAYOUT · schedules</h1>
<p class=sub>Plot C-89, Sector 12, Kharghar · Plan B luxury (family-approved 03.11.2026) · floors 2 and 3 identical · all sizes in feet and inches ·
<b>{S} students per floor, {3 * S} on floors 1–3</b></p>
<h2>Rooms</h2>
<table><tr><th>Room</th><th>Students</th><th>Main area</th><th>Area</th><th>Layout</th></tr>{''.join(room_rows)}</table>
<h2>Wakefit products and TVs (quantities)</h2>
<table><tr><th>Product</th><th>Size (cm, from listings)</th><th>W × D</th>{''.join(f'<th>{r}</th>' for r in rooms)}<th>Floor 1</th><th>Floors 1–3</th></tr>{''.join(prod_rows)}</table>
<p class=small>Also needed: {' · '.join(extra)}. Confirm every size on the Wakefit product page before ordering (Twill and Gingham sizes are approximate; wakefit.co could not be read automatically).</p>
<h2>Layout audit (tools/check_layout.py): every rule, every room</h2>
<table><tr><th>Room</th><th>Result</th><th>Measured</th></tr>{''.join(audit_rows)}</table>
<p class=small>Rules: every item inside its room and clear of walls, the 17 RCC columns, door swings and each other; bed side 1'-11⅝", wardrobe front 1'-11⅝", desk chair 2'-5½", sofa legroom 1'-5¾";
chairs, wardrobe doors and sofa legroom outside every door swing; wardrobes, desks and sofa flush on plain walls; nothing tall in front of a window; no bed head against a window or a toilet wall;
no bed within 2'-11⅜" of a toilet door; no bed stuck in a corner (both long sides at least 6" from walls); 2'-0" walkways (ROOM-3: 1'-11¼" approved by the family); TVs on walls, not over windows or bed heads.</p>
<h2>Still open before construction</h2>
<ul>
<li><b>Architect:</b> floor-to-floor height, window sill height (assumed 2'-11⅜"), lintel and parapet heights.</li>
<li><b>Structural engineer (Agharkar):</b> the column schedule covers the stilt plus 3 floors, but the architect's drawing shows a fourth floor; please confirm. Floor beams are not yet drawn.</li>
<li><b>Electrical and plumbing points</b> for this final layout: TV sockets and data points, and the bedside and desk sockets, are to be regenerated from it (the saved model still carries Plan A).</li>
<li><b>Family decisions already taken:</b> front twins keep the bed along the window (walk-up window access fails the toilet and walkway rules); ROOM-4 hotel layout moved to ROOM-3 (ROOM-4 too small); ROOM-4 changed to a single Centaur bed with the TV above the desk (03.11.2026). ROOM-2 laid out to the family's own picture (03.11.2026); they accepted the second bed's head under the window and the wardrobes on two walls. The ROOM-4 TV is 32" because the wall beside the Gingham is only 2'-7⅛" long; the Gingham and Cabrera together are 5'-3¼" on a 5'-3" wall, so check both sizes on site before ordering.</li>
</ul>
<p class=foot>Coordination drawing, not for construction. Walls, doors and windows from the architect's AFTER O.C. drawing (03-08-2026); columns from Agharkar Consulting Engineers, rev R1 (02.11.2026); furniture positions are proposals. Source data: model/scenarios/final-floor1.json.</p>
"""
css = """
@page { size: A3 portrait; margin: 10mm; }
body { font-family: Arial, Helvetica, sans-serif; color: #111; margin: 0; }
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
.plan { text-align: center; } .plan svg { height: 396mm; width: auto; display: inline-block; }
h1 { font-size: 20px; margin: 0 0 4px; color: #1e1b4b; } h2 { font-size: 15px; margin: 18px 0 6px; color: #1e1b4b; }
.sub { font-size: 12px; color: #444; margin: 0 0 6px; }
table { border-collapse: collapse; width: 100%; font-size: 11.5px; }
td:first-child, th:first-child { white-space: nowrap; }
th, td { border: 1px solid #c7c7d1; padding: 4px 6px; vertical-align: top; text-align: left; }
th { background: #eef2ff; } td.n { text-align: center; } td.ok { color: #166534; font-weight: bold; }
.small { font-size: 10.5px; color: #333; } .foot { font-size: 10px; color: #555; margin-top: 18px; border-top: 1px solid #ccc; padding-top: 6px; }
ul { font-size: 12px; } a { color: #1d4ed8; text-decoration: none; }
"""
out = f"<!doctype html><html><head><meta charset='utf-8'><title>Bella Vita 2 floor 1 final</title><style>{css}</style></head><body>" \
      f"<div class='page plan'>{plan_svg}</div><div class='page'>{page2}</div></body></html>"
(ROOT / "docs/final/floor1-final.html").write_text(out)
print("wrote docs/final/floor1-final.html")
