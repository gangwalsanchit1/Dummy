# Bella Vita 2: Building Coordination Package

This is a student PG at Plot C-89, Sector 12, Kharghar, Navi Mumbai: stilt, four floors and a terrace, with 15 students (single occupancy, ultra-luxury). It is a 3D coordination model with proposed electrical and plumbing, built from the architect's **AFTER O.C.** drawing (03-08-2026). The family and the contractor can use it to check the building before each stage of work.

> **COORDINATION ONLY, NOT FOR CONSTRUCTION.** Structure, and the final electrical and plumbing design, must be done or approved by the structural engineer and licensed consultants. Columns C1–C17 come from the structural engineer's sheet (Agharkar, rev R1 02.11.2026, in `drawings/`). They are on the floor 1 plan and checks now, and will go into the 3D model once floor 1 is finalised. Floor beams are not drawn yet, so none are shown.

## Start here

| I want to… | Open | How |
|---|---|---|
| **FINAL floor 1 drawing (Plan B luxury, family-approved)** | `docs/final/floor1-final.pdf` (A3, 2 pages), `docs/final/floor1-final-plan.png` | Page 1 plan; page 2 room schedule, Wakefit product quantities, audit, open items. Rebuild: `python3 tools/final_sheet.py` then `node tools/print_final.js` |
| **3D pictures with real Wakefit furniture (floors 1–3 and floor 4)** | `docs/final/floor1-3-render.jpg`, `docs/final/floor4-render.jpg` | Top-down 3D views like the family's pictures, every Wakefit piece at true size. Floor 4 layout and open points: `docs/floor4-layout.md`. Rebuild: `THREE_DIR=<three@0.160.0 package> python3 tools/render3d.py model/scenarios/final-floor1.json docs/final/floor1-3-render.jpg` (and `final-floor4.json`) |
| **Floor 1 summary (current focus, feet and inches)** | `docs/floor1.md` | Rooms, Wakefit furniture, checks, AC results, open decisions |
| Walk around the building in 3D | `viewer/bella-vita-2.html` | Download it and double-click it. It works **offline** in Chrome, Edge, Firefox or Safari (see the controls below). |
| Print or share floor plans | `package/pdf/GF.pdf`, `F1-3.pdf`, `F4.pdf`, `TERRACE.pdf` | Any PDF reader. Each file has 3 A3 sheets: **A** architecture and furniture, **E** electrical, **P** plumbing. Scale 1:60 at A3. |
| Give the contractor CAD files | `package/dxf/*.dxf` | Free tools: LibreCAD, QCAD, DraftSight, or the free online viewer at sharecad.org. Units are feet and inches (drawn in inches, architectural units). Layers are listed below. |
| See every point, room by room | `package/pdf/schedules.pdf` or `docs/schedules/points_schedule.csv` | PDF reader, or Excel / Google Sheets |
| Count points and pipe lengths | `docs/schedules/quantities.csv` (also in `schedules.pdf`) | Excel / Google Sheets. Lengths are approximate and no prices are given. |
| Know what must happen **before each slab pour** | `docs/pre-slab-checklist.md` (also in `schedules.pdf`) | Any Markdown viewer, or GitHub |
| Open the BIM model | `model/bella-vita-2.ifc` | Free tools: BlenderBIM/Bonsai, FreeCAD, BIMvision, or https://ifcviewer.com |
| See where the structural columns sit on floor 1 and what they touch | `docs/structure-check.md` | Column-by-column table in feet and inches, plus points for the structural engineer |
| Walk through each room as the students (why each item is where it is) | `docs/floor1-walkthrough.md` | Entry, toilet, beds, desks, wardrobes, AC, room by room |
| Every Wakefit product placed, with sizes, links and quantities (Plan A and Plan B) | `docs/wakefit-products.md` (`python3 tools/product_list.py model/scenarios/*.json`) | Per room, per floor, floors 1-3 |
| Father's alternative (Plan B): luxury singles in ROOM-3 and ROOM-4, no wall or door changes | `docs/plan-b-father.md`, `docs/scenario-dad-plan.png` | 6 students per floor; audited |
| Full luxury theme: Plan A and Plan B with TVs and a sofa where they fit | `docs/luxury-plans.md`, `docs/plan-a-luxury-plan.png`, `docs/plan-b-luxury-plan.png` | Wakefit Flipper sofa; wall-mounted TVs; audited |
| Check every layout rule, room by room | `docs/layout-audit.md` (`python3 tools/check_layout.py`) | Clearances, door swings, walls and columns, windows, even look, walking paths |
| See what was changed from the architect's drawing (one brick wall, two doors) | `docs/floor1-changes.md`, `model/changes.json` | Family-approved 03.11.2026; architect and structural engineer to confirm |
| Read how the drawing was interpreted | `docs/drawing-takeoff.md` | Sizes, conflicts with earlier notes, safety items, **13 open questions** |
| See the floor 1 room layouts (standard kit per student) | `docs/floor1-plan.png`, `docs/floor1.md`, `docs/room4-check.md` | Every student: own bed, Wakefit Cabrera study table + chair, Twill wardrobe, bedside socket (roommates may share the Tinker). ROOM-1, ROOM-2, ROOM-3 twin; ROOM-4 single (Orion queen). 7 students per floor |
| See the PG amenities (matched to the existing Bella Vita) | `docs/amenities.md` | RFID, backup power, RO water, terrace laundry and lounge, sub-meters |
| See where the floors 1–3 AC lines run and what they clash with | `docs/ac-routing.md` | Routed below the bathroom windows |
| Read the model and MEP reports | `docs/phase2-model.md`, `docs/phase3-mep.md` | Includes the code references and their verification status |
| See the check results | `docs/model-checks.md`, `docs/mep-checks.md` | Furniture, clearance, door-swing, dimension and MEP clash checks |
| Compare my reading against the architect's lines | `docs/overlays/takeoff_*.svg` | Open in a browser |

### Viewer controls

- **Floor buttons:** All, GF, F1–F4, Terrace.
  - **Mode** switches between "stack below" and "this floor only".
  - **Roof off** hides the slab above the chosen floor.
- **Electrical set / Plumbing set / Architecture only:** one-click layer presets. Every layer can also be toggled on its own.
- **Click any object** to see its name, source tag (DRAWN, CALCULATED or ASSUMED), exact position and check result.
- **Measure:** click two points to get the distance. "Snap to corners" gives precise wall-to-wall readings.
- **Top view, Road side, 3D view:** camera presets.
- **Direct links:** for example `bella-vita-2.html#floor=F1&isolate=1&view=top&mep=e` (use `mep=p` for plumbing).

### DXF layers

| Layer | Contents |
|---|---|
| A-WALL, A-DOOR, A-WIND, A-FURN, A-TEXT, A-PLOT, A-STAIR, A-TANK | Architecture: walls (hatched), door swings, windows, furniture, room names and sizes, plot line, stair, tanks |
| E-POINT, E-TEXT, E-FEED, E-COND | Electrical points with code and mounting height, feeders and riser, indicative conduits |
| P-FIXT, P-TEXT, P-SOIL, P-WASTE, P-VENT, P-CW, P-HW, P-DT, P-RM, P-RWP, P-UGD, P-SUP | Plumbing fixtures and pipes by system. Circles mark vertical stacks. |
| S-SLEEVE | Sleeves and cast-in items needed before each slab pour |

DXF coordinates are X = plan X and Y = −plan Y, so the drawing reads the same way as the architect's sheet, with the road at the bottom.

### Point codes on the E and P sheets

| Group | Codes |
|---|---|
| Distribution | SB room switchboard · TS toilet switchboard · DB floor DB · MB/MDB/CDB meter, main and common boards · R riser |
| Sockets and outlets | BS bedside · DK desk · D data · AC/ACs AC unit and socket · ODU AC outdoor unit · GZ geyser |
| Lights, fans and devices | L light · WL wall light · F fan · EX exhaust · AP Wi-Fi · CC CCTV |
| Plumbing | WC · B basin · SH shower · HF health faucet · FT floor trap · GZ geyser · SL sleeve |

The number after a code is the mounting height above floor level in metres.

## How every value is tagged

- **DRAWN:** measured from the PDF's vector lines, about ±0.01 m.
- **CALCULATED:** derived from drawn values.
- **ASSUMED:** not on the drawing. This includes all heights and levels, most door swings, furniture positions, and every electrical and plumbing point.

## Status

- [x] Phase 1: drawing takeoff
- [x] Phase 2: architectural 3D model (IFC and viewer)
- [x] Phase 3: electrical and plumbing proposal, with clash checks (0 hard clashes)
- [x] Phase 4: DXF and PDF package, schedules, quantities, pre-slab checklist

**03.11.2026:** one internal brick wall and two doors moved (family-approved, `model/changes.json`; the architect's takeoff is kept as drawn). All tools read the plan through `tools/takeoff.py`.

**02.11.2026 structural update:** floor 1 (plan, furniture, points, checks, `docs/floor1.md`, `docs/structure-check.md`) now includes the columns. The IFC, the 3D viewer and the PDF/DXF package have **not** been rebuilt yet; they will be once floor 1 is final.

The open questions are in `docs/drawing-takeoff.md` §13. The biggest are the column layout, the floor heights and the door swings. Answering them and rebuilding updates everything.

## Rebuild after changing an assumption

All ASSUMED heights and door swings are in `model/assumptions.json`. Columns are read from the structural PDF by `python3 tools/extract_columns.py` (needs pdfplumber; writes `model/structure.json`). Furniture is generated by `python3 tools/fit_furniture.py` (writes `model/furniture.json`; takes about 2 minutes), and the MEP points are in `tools/build_mep.py`.

1. Rebuild the model data. This needs only Python 3.

```bash
python3 tools/build_model.py
```

2. Rebuild the MEP points and checks.

```bash
python3 tools/build_mep.py
```

3. Install the extra Python tools. Use a virtual environment; they are not committed.

```bash
pip install ifcopenshell ezdxf
```

4. Export the IFC file.

```bash
python3 tools/export_ifc.py
```

5. Build the DXF files and SVG sheets.

```bash
python3 tools/build_package.py
```

6. Print the PDFs. This needs Node with Playwright and Chromium.

```bash
node tools/print_pdfs.js
```

7. Download three.js r160 for the viewer. It is MIT-licensed and is not committed.

```bash
npm pack three@0.160.0 && tar xzf three-0.160.0.tgz
```

8. Rebuild the viewer.

```bash
python3 tools/build_viewer.py package
```

To regenerate the plan overlays from the source PDF (this needs pdfplumber):

```bash
python3 tools/extract_plans.py drawings/*.pdf docs/overlays
```

```bash
python3 tools/annotate_overlays.py
```
