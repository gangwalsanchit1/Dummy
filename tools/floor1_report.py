#!/usr/bin/env python3
"""Floor 1 summary in feet and inches only (family: 'keep everything in feet and inches, work on floor 1 for now').
Writes docs/floor1.md from the takeoff, the fitted furniture, the model checks and the AC routing results."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from units import ftin, size, sqft  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from takeoff import load_takeoff  # noqa: E402
TK = load_takeoff()
AS = json.loads((ROOT / "model/assumptions.json").read_text())
FU = json.loads((ROOT / "model/furniture.json").read_text())
M = json.loads((ROOT / "model/mep.json").read_text())
fl = TK["floors"]["F1-3"]
CAT = AS["wakefit_catalog"]
FS = AS["furniture_sizes"]
CL = AS["clearances"]
NAME = {"orion_queen_bed": "Orion queen bed", "tinker_side_table": "Tinker side table", "gingham_wardrobe": "Gingham 2-door wardrobe (mirror)",
        "twill_wardrobe": "Twill 2-door compact wardrobe", "notiq_desk": "Notiq adjustable study table (placeholder)", "wall_desk": "Wall desk 3'-0\" (shared)", "sage_desk": "Sage study table (with hutch)", "compact_desk": "Compact study table (2'-11⅜\" × 1'-5¾\", no hutch, ASSUMED size)", "cabrera_desk": "Wakefit Cabrera study table (open shelf under the top)", "nohutch_desk": "Study table without hutch (Sage size, ASSUMED)", "centaur_single_bed": "Centaur single bed", "amata_sofa": "AMATA sofa cum bed"}

_cf = ROOT / "model/changes.json"
CH = json.loads(_cf.read_text()) if _cf.exists() else {}
_n = {r: sum(1 for i in its if i["type"].endswith("_bed")) for r, its in FU["F1-3"].items()}
NSTU = sum(_n.values())
OCC = " ".join(f"{r}: {n} student{'s' if n > 1 else ''} ({'Centaur singles' if n > 1 else 'Orion queen'})." for r, n in _n.items())
md = ["# Floor 1: rooms, furniture and checks (feet and inches)", "",
      "Floors 2 and 3 are identical to floor 1 on the drawing. Walls, doors and windows are DRAWN; furniture positions and electrical/plumbing points are proposals. "
      f"All doors open inwards. {OCC} {NSTU} students on floor 1, every student with the same kit (roommates share only the side table). "
      "**Final version (family, 03.11.2026):** one internal brick wall and two doors moved (see below), so ROOM-3 takes two students.", "",
      "## Changed from the architect's drawing (family-approved 03.11.2026)", ""] + [f"- {c}" for c in CH.get("changes", [])] + [
      "- Never touched: columns, outer walls, windows, lift walls, toilets.",
      "- **Architect:** update the floor 1-3 plans. **Structural engineer:** confirm the floor beam under the moved wall (plinth beam PB3 runs on that line). "
      "Details and what else was tried: `docs/floor1-changes.md`.", "",
      "## Rooms (DRAWN; ROOM-2 and ROOM-3 as changed)", "", "| Room | Main area | Total area | Window |", "|---|---|---|---|"]
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
       "- **Standard kit (family, 03.11.2026):** every student gets the same items: their own bed, Wakefit Cabrera study table + chair, and Twill wardrobe; roommates may share the Tinker side table. The Cabrera (2'-7⅜\" × 1'-5¾\", a real Wakefit table) is used for everyone so the twin rooms fit; two Sage tables do not. The wardrobe is the Twill for everyone, because it is the one that fits every room (ROOM-4's study wall is 5'-3\" beside column C13). The AMATA sofa is dropped, because it fits only ROOM-1.",
       "- **Rules kept:** nothing taller than the window sill stands in front of a window; no bed head against a window; twin beds 1'-0\" or more apart "
       "(in ROOM-3 the two beds sit side by side with one shared Tinker between them, as the family asked); the switch strip beside each room door stays clear.",
       "- **Windows:** in ROOM-3 and ROOM-4 a student can walk right up to the window. In ROOM-1 and ROOM-2 one bed runs along the front window, so that window is opened by leaning over the bed (the bed is below the assumed 2'-11\u215c\" sill).",
       "- **Even look (family, 03.11.2026: uneven things look ugly):** every item stands flush on a plain wall, never on a column face and never "
       "pushed out from the wall by a column (beds excepted: a headboard may rest on a column); matching wardrobes and desks either line up on one wall "
       "or mirror each other on opposite walls; chair space and wardrobe-door space never inside a door swing. Room-by-room result in the audit below.",
       "(the tightest twin room) the two wardrobes form an L at the door corner, because no layout lines up both pairs there.",
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
# full rule audit (tools/check_layout.py), copied in so this page always matches it
_au = ROOT / "docs/layout-audit.md"
if _au.exists():
    md += ["## Layout audit (every rule, every room)", ""] + [l for l in _au.read_text().split("\n") if l.startswith("|")] + [
           "", "ROOM-3 was designed by hand (study nook by the window, wardrobes by the door) and passes the same audit.", ""]
# living in the room: own vs shared, and a per-room check that every student has their own points
md += ["## Living in the room (a student's view)", "",
       "**Each student has their own:** bed (with storage under it), study table, chair, wardrobe, a bedside socket + USB + reading-light switch "
       "within reach of the pillow, and 2 sockets + USB + data at the desk.",
       "**Roommates can share:** the side table (in a twin room it sits between the two bed heads), the room light, the fan, the AC, the Wi-Fi and the toilet.",
       "**Checked in the model for every student:** they get to their bed without climbing over the other bed; "
       "their chair has its own floor space; their wardrobe doors open without hitting anything; "
       "nothing tall blocks a window; the switchboard by the door is reachable; and a walking path reaches all of it.",
       "**To add at fit-out (no space needed on the plan):** a full-length mirror (the Twill has none), "
       "a towel hook outside the toilet, a shoe rack or shelf by the door, curtains or blinds, and a desk lamp for each desk.", "",
       "| Room | Students | Own bedside socket | Own desk socket + data | Own wardrobe | Own chair space |", "|---|---|---|---|---|---|"]
for room, items in FU["F1-3"].items():
    nb = sum(1 for i in items if i["type"].endswith("_bed"))
    pts = [q for q in M["points"] if q["storey"] == "F1" and q["room"] == room]
    nbs = sum(1 for q in pts if q["kind"] == "BS")
    nds = sum(1 for q in pts if q["kind"] == "DESK")
    ndt = sum(1 for q in pts if q["kind"] == "DATA")
    nw = sum(1 for i in items if "wardrobe" in i["type"])
    nd = sum(1 for i in items if i["type"].endswith("desk"))
    ok = lambda c: "yes" if c else "**NO**"
    md.append(f"| {room} | {nb} | {ok(nbs >= nb)} ({nbs}) | {ok(nds >= nd >= nb and ndt >= nb)} ({nds} + {ndt}) | {ok(nw >= nb)} ({nw}) | {ok(nd >= nb)} ({nd}) |")
md += [""]
_acb = []
if "## Indoor units and beds" in ac:
    for l in ac[ac.index("## Indoor units and beds") + 1:]:
        if l.startswith("## ") or l.startswith("Columns are now"):
            break
        if l.startswith("- "):
            _acb.append(l)
md += ["## AC lines (below the bathroom windows)", ""] + [l for l in ac if l.startswith("|")] + [
       "", "**AC indoor units and beds:** a split unit throws its air across the room, away from its own wall, so a bed under the unit is fine. "
       "Checked: no unit on the opposite wall blowing at a bed's pillow end or side within 8'-2\" (a comfort rule of thumb, not a code)."] + _acb + [
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
       "1. Confirm the Wakefit overall sizes from the product pages (beds, Tinker, Twill) and the Cabrera study table.",
       "2. OK the queen beds with one long side on the wall (ROOM-1, ROOM-4).",
       "3. AC clashes: choose what moves (outdoor units, pipes or route).",
       "4. Architect: window sill height and floor height (heights are assumed; the structural drawing does not give them either).",
       "5. Structural engineer: confirm the column schedule covers the fourth floor, and send the floor beam layout.", ""]
(ROOT / "docs/floor1.md").write_text("\n".join(md))
print("wrote docs/floor1.md")
