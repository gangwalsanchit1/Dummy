# Bella Vita 2: Building Coordination Model

This is a student PG at Plot C-89, Sector 12, Kharghar, Navi Mumbai: stilt, four floors and a terrace. It is a 3D coordination model built from the architect's AFTER O.C. drawing (03-08-2026), so the family and the contractor can check the building before each stage of work.

> **This is a coordination model, not a stamped design.** Structure, and the final electrical and plumbing design, must be reviewed by the structural engineer and licensed consultants.

## Open these

| What | File | How to open |
|---|---|---|
| 3D viewer | `viewer/bella-vita-2.html` | Download it and double-click it. It works offline in any modern browser. |
| BIM model | `model/bella-vita-2.ifc` | Free tools: BlenderBIM/Bonsai, FreeCAD, BIMvision, or https://ifcviewer.com in a browser |
| Drawing takeoff | `docs/drawing-takeoff.md` | Lists rooms, doors and windows, conflicts, safety items and **open questions** |
| Phase 2 report | `docs/phase2-model.md` | Describes the model and compares it with the takeoff |
| Generated checks | `docs/model-checks.md` | Furniture, clearance, door-swing and dimension checks |
| Plan overlays | `docs/overlays/*.svg` | Open in a browser. These are the architect's lines in metres with my takeoff drawn on top. |
| Source drawing | `drawings/*.pdf` | The architect's AFTER O.C. sheet |

## Status

- [x] Phase 1: drawing takeoff
- [x] Phase 2: architectural 3D model (IFC and viewer)
- [x] Phase 3: electrical and plumbing layers (`docs/phase3-mep.md`, `docs/pre-slab-checklist.md`)
- [ ] Phase 4: DXF/PDF package and schedules

## Rebuild after changing an assumption

All heights and door swings marked ASSUMED are in `model/assumptions.json`. Furniture positions are in `model/furniture.json`.

1. Rebuild the model data. This needs only Python 3.

```bash
python3 tools/build_model.py
```

2. Install IfcOpenShell. Use a virtual environment; it is not committed to the repo.

```bash
pip install ifcopenshell
```

3. Export the IFC file.

```bash
python3 tools/export_ifc.py
```

4. Download three.js r160 for the viewer. It is MIT-licensed and is not committed.

```bash
npm pack three@0.160.0 && tar xzf three-0.160.0.tgz
```

5. Rebuild the viewer.

```bash
python3 tools/build_viewer.py package
```

To regenerate the plan overlays from the PDF (this needs pdfplumber):

```bash
python3 tools/extract_plans.py drawings/*.pdf docs/overlays
```

```bash
python3 tools/annotate_overlays.py
```

## Coordinates

All plan values are in metres:
- **X:** measured from the left outer wall face, as drawn.
- **Y:** measured from the rear outer wall face towards the road.
- **Z:** metres above road level. This datum is ASSUMED.

The IFC uses world Y = 11.75 − plan Y, so the front face of the building is at Y = 0.
