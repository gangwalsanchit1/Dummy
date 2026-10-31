# Phase 2: Architectural 3D Model

## Deliverables

| File | What it is |
|---|---|
| `viewer/bella-vita-2.html` | **Single self-contained viewer.** It works offline: double-click it and it opens in Chrome, Edge, Firefox or Safari. |
| `model/bella-vita-2.ifc` | IFC4 BIM model, schema-validated with 0 issues. It opens in free tools such as BlenderBIM/Bonsai, FreeCAD, IfcOpenShell, BIMvision or the online viewer at ifcviewer.com. |
| `model/scene.json` | The element list that both the IFC and the viewer are generated from. |
| `docs/model-checks.md` | The generated checks: furniture and clearances, door swings, and model-versus-takeoff dimensions. |
| `model/assumptions.json` | **Every ASSUMED height, door swing and clearance in one file.** Edit a value and rebuild (see the README). |
| `model/furniture.json` | Furniture positions for each room. |

## Viewer features

- **Floor buttons:** All, GF, F1–F4 and Terrace.
- **Two display modes:**
  - "Stack below" shows the chosen floor plus everything under it.
  - "This floor only" shows just the chosen floor.
- **Roof off:** hides the slab above the chosen floor. It is on by default.
- **Layer toggles:** walls, slabs, doors, windows, stair, lift, furniture, clearance zones and door swings, room floors, tanks, water, site, and room labels.
- **Room labels:** each label shows the room name, its measured main size and its area.
- **Click any object** to see:
  - its name and IFC class
  - its source tag (DRAWN, CALCULATED or ASSUMED)
  - its exact plan extents and height range
- **Measure:** click two points to get the 3D distance plus the plan X, plan Y and height components.
  - "Snap to corners" locks onto box corners and mid-points within 0.15 m, for precise wall-to-wall readings.
- **View presets:** 3D, Top and Road-side.
- **URL shortcuts:** `bella-vita-2.html#floor=F1&isolate=1&view=top` opens straight into that view.

## What is in the model

| Element | Count | Source |
|---|---|---|
| Walls, including headers over doors and openings, parapets, compound wall and lift-pit walls | 185 | Plan DRAWN. Heights ASSUMED. |
| Windows, each in a real IFC opening void in its host wall | 33 | Width DRAWN. Sill and head ASSUMED. |
| Doors | 34 | Openings DRAWN. Swings DRAWN on F4, ASSUMED elsewhere. |
| Slabs, including the stair mid-landings and the lift-pit base | 50 | Plan DRAWN. Levels ASSUMED. |
| Stair flights: 5 storeys × 16 risers × 187.5 mm, 250 mm going | 5 | Plan DRAWN. Risers CALCULATED from the ASSUMED 3.00 m floor height. |
| Lift car zones (clear shaft 1.40 × 1.50) | 5 | DRAWN |
| Tanks: U.G. 3.00×2.05×1.70 and O.H. 2.10×2.20×1.50 on the stair-cabin roof | 2 | Size DRAWN. Levels ASSUMED. |
| Furniture: 22 beds, 15 wardrobes, 15 desks | 45 | Sizes from the brief. Positions ASSUMED. |
| Spaces | 56 | DRAWN |
| **Columns and beams** | **0** | **Not drawn on the sheet, so none are shown (Q1)** |

**Levels (all ASSUMED):**
- Stilt floor level: +0.30 m
- Floor-to-floor height: 3.00 m
- Slab: 0.15 m
- Finished floor levels: F1 +3.30, F2 +6.30, F3 +9.30, F4 +12.30, Terrace +15.30 m
- Stair-cabin roof: +18.00 m
- Top of the O.H. tank: about +19.80 m

## Model compared with the takeoff

- **Method:** for every space, the builder measures the clear distance between the model's wall faces through the centre of the space, 2.5 m above the floor. That height is above every door and window head, so it measures solid wall. The full table is in `docs/model-checks.md`.
- **Every enclosed space matches the takeoff exactly (0 mm difference), in both directions:**
  - all toilets and WCs
  - pantry
  - lift, both 1.40 × 1.50
  - stair, 2.10 × 3.85
  - ROOM-4
  - F1–3 lobby, 2.45 × 2.20
  - F4 suite, 3.90 × 5.80
  - F4 lobby
- **Expected differences:**
  - **Positive differences** appear wherever a room is open into another part of itself. Examples are the L-shaped ROOM-1 and ROOM-2, the ROOM-3 alcove, and the servant vestibule opening into the servant room. In those cases the "clear" line runs into the other part of the room. This is correct, not an error.
  - **GF lift lobby: −50 mm in depth.** The single drawn line at the stilt entry is modelled as a door header 0.10 m thick centred on that line, which is ASSUMED (Q8).
- **The drawing labels still disagree with the geometry** in the places listed in the takeoff (C4–C8). The model follows the drawn geometry.

## Furniture and clearance checks

**Updated after the family's instructions:**
- Use Wakefit furniture (the sizes from the brief).
- **"Double" means two students sharing: 2 single beds, 2 study tables and 2 wardrobes.** A room is double where that fits; otherwise it is single, with 1 bed, 1 study table and 1 wardrobe.
- Drawn rooms and toilets are unchanged.

The layout is **generated** by `tools/fit_furniture.py`, and the full result is in `docs/furniture-fit.md`. Each room tries, in order:
1. twin with standard desks
2. twin with wall desks
3. single

A layout passes only if all of these hold:
- every item is inside the room and clear of walls, the other items, every door swing and every clearance zone
- each bed has 0.60 m clear on its open side, each wardrobe 0.60 m in front, and each desk a 0.75 m chair zone
- the first wardrobe sits in the architect's grey strip
- a **0.55 m walking path** (ASSUMED) reaches every bed side, wardrobe, chair zone and the toilet or terrace door

| Floor | ROOM-1 | ROOM-2 | ROOM-3 | ROOM-4 | Students |
|---|---|---|---|---|---|
| F1–F3 (each) | **double** (wall desks) | **double** (wall desks) | **double** (wall desks) | single | 7 × 3 = 21 |
| F4 | single | **double** (wall desks) | **double** suite (standard desks) | n/a | 5 |
| **Total** | | | | | **26** |

- **F1–F3 ROOM-4 cannot take two students.** A complete search finds no arrangement of 2 beds, 2 wardrobes and 2 desks with clear walking paths. Its main area is 3.40 × 2.80 m, and the 0.90 m entry passage cannot hold furniture.
- **F4 ROOM-1 cannot take two students.** Its main part is only 1.63 m deep.
- **The standard 1.16 m desk fits two-to-a-room only in the F4 suite.** Every other double uses 0.90 m wall desks.
- **Re-checked:** 0 furniture or clearance violations, and all 18 door swings pass (`docs/model-checks.md`).

## Uncertain, or needs your input

- **Questions Q1–Q13** in `docs/drawing-takeoff.md` are still open. The most important are:
  - Q1: columns
  - Q2: real levels
  - Q6: door swings
  - Q7: what the grey strips are
- **Model behaviour in the meantime:**
  - **Floor 4 private terrace:** modelled as an open-to-sky court surrounded by full-height walls, because the plans show walls there at both F4 level and roof level.
  - **Ground-floor side walls:** modelled full height, as drawn (Q10).
  - **Lift pit:** 1.20 m deep (ASSUMED).
  - **Lift overrun:** taken up to the cabin roof (ASSUMED).

## Structural flags (for the structural engineer)

- **No structure is modelled.** The S2–S4 items in the takeoff still apply:
  - the open stilt has no columns drawn
  - Floor 4 walls sit on the slab, not on walls below
  - the O.H. tank and U.G. tank loads
- Once a column and beam layout is supplied, I will add columns and beams and run the clash checks that Phase 3 needs: points against beams and columns.
