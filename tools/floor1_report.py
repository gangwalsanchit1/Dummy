#!/usr/bin/env python3
"""Floor 1 summary in feet and inches only (family: 'keep everything in feet and inches, work on floor 1 for now').
Writes docs/floor1.md from the takeoff, the fitted furniture, the model checks and the AC routing results."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from units import ftin, size, sqft  # noqa: E402

TK = json.loads((ROOT / "model/takeoff.json").read_text())
AS = json.loads((ROOT / "model/assumptions.json").read_text())
FU = json.loads((ROOT / "model/furniture.json").read_text())
M = json.loads((ROOT / "model/mep.json").read_text())
fl = TK["floors"]["F1-3"]
CAT = AS["wakefit_catalog"]
FS = AS["furniture_sizes"]
CL = AS["clearances"]
NAME = {"orion_queen_bed": "Orion queen bed", "tinker_side_table": "Tinker side table", "gingham_wardrobe": "Gingham 2-door wardrobe (mirror)",
        "twill_wardrobe": "Twill 2-door compact wardrobe", "notiq_desk": "Notiq adjustable study table (placeholder)", "wall_desk": "Wall desk 3'-0\" (shared)", "sage_desk": "Sage study table (with hutch)", "nohutch_desk": "Study table without hutch (Sage size, ASSUMED)", "centaur_single_bed": "Centaur single bed", "amata_sofa": "AMATA sofa cum bed"}

md = ["# Floor 1: rooms, furniture and checks (feet and inches)", "",
      "Floors 2 and 3 are identical to floor 1 on the drawing. Walls, doors and windows are DRAWN; furniture positions and electrical/plumbing points are proposals. "
      "All doors open inwards. ROOM-1, ROOM-3 and ROOM-4: one student each (Orion queen). ROOM-2: two students (Centaur singles), two of everything. 5 students on floor 1, every student with the same kit. ROOM-3 became single on 03.11.2026: it cannot take two full kits (every arrangement checked).", "",
      "## Rooms (DRAWN)", "", "| Room | Main area | Total area | Window |", "|---|---|---|---|"]
for sp in fl["spaces"]:
    r = max(sp["rects"], key=lambda q: (q[2] - q[0]) * (q[3] - q[1]))
    a = sum((q[2] - q[0]) * (q[3] - q[1]) for q in sp["rects"])
    wins = ", ".join(f"{w['id']} {ftin(w['width'])}" for w in fl["windows"] if w["serves"].split(" ")[0] == sp["name"].split(" ")[0] and ("TOILET" in w["serves"].upper()) == ("TOILET" in sp["name"].upper()))
    md.append(f"| {sp['name']} | {size(r[2]-r[0], r[3]-r[1])} | {sqft(a)} | {wins or '-'} |")
md += ["", "## Furniture (Wakefit)", "", "| Room | Item | Width x Depth x Height | Clearance kept | Link |", "|---|---|---|---|---|"]
for room, items in FU["F1-3"].items():
    for it in items:
        w_, d_, h_ = FS[it["type"]]
        if it["type"].endswith("_bed"):
            cl = f"{ftin(CL['queen_bed_sides'])} on {'both sides' if len(it['access']) == 2 else 'the open side (long side on wall)'}"
        elif "wardrobe" in it["type"]:
            cl = f"{ftin(CL['sliding_wardrobe_front'])} in front"
        elif it["type"].endswith("desk"):
            cl = f"{ftin(CL['desk_chair_zone'])} chair pull-out"
        else:
            cl = "at the bed head, on the open side"
        link = CAT.get(it["type"], {}).get("link", "")
        md.append(f"| {room} | {NAME.get(it['type'], it['type'])} | {ftin(w_)} x {ftin(d_)} x {ftin(h_)} | {cl} | {'[link](' + link + ')' if link else '-'} |")
fit = [l for l in (ROOT / "docs/floor1-fit.md").read_text().split("\n") if l.startswith("| ROOM")]
md += ["", "## Checks", "",
       f"- Every item is inside its room and clear of walls, the other items, every door swing and every clearance; a {ftin(0.55)} walking path reaches every bed side, wardrobe front, chair and the toilet door. **All rooms PASS.**",
       "- Layout search results:", ""] + ["  " + l for l in fit] + ["",
       "- **Standard kit (family, 03.11.2026):** every student gets the same items, and a twin room gets two of everything. The wardrobe is the Twill for everyone, because it is the one that fits every room (ROOM-4's study wall is 5'-3\" beside column C13). The AMATA sofa is dropped, because it fits only ROOM-1.",
       "- **Rules kept:** nothing taller than the window sill stands in front of a window; no bed head against a window; twin beds kept 1'-0\" or more apart wherever the room allows it.",
       f"- **Queens in ROOM-1 and ROOM-4** have one long side on the wall where needed (family rule in ROOM-4).",
       f"- **Headboards vs window sill (assumed {ftin(AS['heights']['window_sill'])}):** Orion {ftin(FS['orion_queen_bed'][2])}, Centaur {ftin(FS['centaur_single_bed'][2])}. No bed head sits under a window in this floor-1 layout (checked); keep it that way if beds move, because the Centaur headboard is taller than the assumed sill.", ""]
ac = (ROOT / "docs/ac-routing.md").read_text().split("\n")
# per-room kit count (two of everything in twin rooms)
from collections import Counter as _C  # noqa: E402
md += ["## Kit per room (count)", "", "| Room | Students | Beds | Tinker side tables | Wardrobes | Study tables |", "|---|---|---|---|---|---|"]
for room, items in FU["F1-3"].items():
    k = _C(i["type"] for i in items)
    beds = sum(v for t, v in k.items() if t.endswith("_bed"))
    desks = ", ".join(f"{v} {NAME[t]}" for t, v in k.items() if t.endswith("desk"))
    wards = ", ".join(f"{v} {NAME[t]}" for t, v in k.items() if "wardrobe" in t)
    md.append(f"| {room} | {beds} | {beds} | {k['tinker_side_table']} | {wards} | {desks} |")
md += [""]
md += ["## AC lines (below the bathroom windows)", ""] + [l for l in ac if l.startswith("|")] + [
       "", "Nothing has been moved; you decide what moves. Columns are checked against the structural drawing (no AC wall sleeve passes through a column). Floor beams are not drawn yet, so beam clashes cannot be checked.", "",
       "## Structural columns (Agharkar RCC drawing, rev R1, 02.11.2026)", "",
       "- 17 columns, C1-C17, scaled from the structural layout to within about ¾\". On this floor they are 9\" wide and stand about 3⅛\" out of the 6\" walls (6\" into the ROOM-1 toilet).",
       "- Furniture was re-fitted with the columns as solid obstacles; nothing stands on a column. Where a bed, desk or wardrobe stands against a column, it has a gap of up to 3⅛\" behind it along the rest of the wall.",
       "- Electrical points that fell on a column moved onto the column face (conduit cast in before the pour). The ROOM-1 toilet WC moved just clear of column C10.",
       "- **For the structural engineer:** the column schedule covers the stilt plus 3 floors, but the architect's sheet shows the stilt plus 4 floors. Please confirm the fourth floor is covered.",
       "- Full table: `docs/structure-check.md`.", "",
       "## Points on floor 1", ""]
from collections import Counter  # noqa: E402
c = Counter(M["kinds"][p["kind"]]["desc"] for p in M["points"] if p["storey"] == "F1" and p["sys"] in ("E", "P"))
md += ["| Item | Count |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(c.items())] + [
       "", "Mounting heights and positions are in `docs/schedules/points_schedule.csv` and on sheet F1-3-E / F1-3-P (feet and inches).", "",
       "## Open decisions for floor 1", "",
       "1. Confirm the Wakefit overall sizes from the product pages (beds, Tinker, Twill, Sage).",
       "2. OK the queen beds with one long side on the wall (ROOM-1, ROOM-4).",
       "3. AC clashes: choose what moves (outdoor units, pipes or route).",
       "4. Architect: window sill height and floor height (heights are assumed; the structural drawing does not give them either).",
       "5. Structural engineer: confirm the column schedule covers the fourth floor, and send the floor beam layout.", ""]
(ROOT / "docs/floor1.md").write_text("\n".join(md))
print("wrote docs/floor1.md")
