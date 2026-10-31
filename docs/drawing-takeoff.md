# Bella Vita 2: Drawing Takeoff (Phase 1)

**Building:** Student PG, Plot C-89, Sector 12, Kharghar, Navi Mumbai
**Source:** `drawings/VINOD GANGWAL, PLOT NO.C-89, SEC-12, KHARGHAR, 03-08-2026 3.pdf`, the "AFTER O.C." sheet dated 03-08-2026
**Machine-readable takeoff:** [`model/takeoff.json`](../model/takeoff.json). Every wall rectangle, opening, window and space is listed there, and Phase 2 builds from it.
**Scaled overlays:** `docs/overlays/overlay_<FLOOR>.svg` is the architect's linework redrawn in metres on a 0.5 m grid. `docs/overlays/takeoff_<FLOOR>.svg` is this takeoff drawn over the same linework so you can check it.

Every value is tagged:
- **DRAWN:** measured from the PDF vectors, about ±0.01 m.
- **CALCULATED:** derived from drawn values.
- **ASSUMED:** not on the drawing. Needs your confirmation.

---

## 1. What the source file contains

| Item | Finding |
|---|---|
| File type | A single-page PDF printed from iOS. It is **fully vector**: 1,900 lines, 28 arcs and no raster images, so geometry can be measured precisely. |
| Visible sheet | The "AFTER O.C." set has four plans: Ground (stilt), First/Second/Third (identical), Fourth, and Terrace. |
| Hidden content | Clipped off the left edge of the page is a second set titled **"BEFORE O.C."**: a residential layout with living room, kitchen and bedrooms. It is **superseded and ignored**. It shows the same U.G. tank (3.00×2.05×1.70, 10,000 L), the same O.H. tank (2.10×2.20×1.50, 6,500 L), and a lift labelled 1.40×1.50. |
| DWG / DXF / structural drawings | **None** were in the repo or the upload. |
| Not on the sheet | Sections, elevations, levels and heights, columns, beams, footings, door schedule, window schedule, area statement. |

## 2. Scale and coordinates

- **Scale (CALCULATED).** The drawn 8.000 m plot width spans 118.022 pt on the sheet, which gives 14.753 pt/m.
  - **Check 1:** Floors 1–3 measure 173.389 pt deep, which is 11.753 m against the 11.750 m written on the drawing (+3 mm).
  - **Check 2:** Floor 4 measures 160.074 pt deep, which is 10.850 m against the 10.850 m written on the drawing (exact).
  - Measurement error is therefore about ±5 mm, plus the drafting precision of the original.
- **Plan coordinates used everywhere:**
  - X is measured from the left outer wall face, as drawn.
  - Y is measured from the rear outer wall face towards the road, which is at the bottom of the sheet.
  - The plot runs from Y = −0.60 to Y = 12.75.

## 3. Site

| Item | Value | Tag |
|---|---|---|
| Plot | 8.000 × 13.350 m = 106.80 m² | DRAWN / CALCULATED |
| Depth chain, Floors 1–3 | rear 0.600 + building 11.750 + front 1.000 = 13.350 ✔ | DRAWN |
| Depth chain, Ground Floor | 0.600 + 10.500 + 2.250 = 13.350 ✔. The 10.500 is measured to a red dashed line at Y = 10.50, not to the building face. | DRAWN |
| Depth chain, Floor 4 | 0.600 + 10.850 + 0.900 (front terrace) + 1.000 = 13.350 ✔ | DRAWN |
| Width | The building is the full 8.000 m. The outer wall faces sit on the plot lines, with no side margins. | DRAWN |
| Road | 6.00 m wide, at the **front (bottom of sheet)** | DRAWN |
| Gate | 3.00 m opening in the front compound wall, X 2.50–5.50 | DRAWN |
| Compound wall | 0.15 m thick, drawn on the Ground Floor plan only | DRAWN |
| Footprint, Ground to Floor 3 | 8.00 × 11.75 = 94.00 m² (1,011.8 sq ft) | CALCULATED |
| Footprint, Floor 4 | 8.00 × 10.85 = 86.80 m² (934.3 sq ft), plus a 0.90 m front terrace | CALCULATED |
| Red dashed lines | At Y = 0.90 and Y = 10.50 on every plan. They have no label. They are recorded only; they are not modelled as anything. | DRAWN |

## 4. Walls

| Wall type | Thickness | Tag |
|---|---|---|
| External | 0.15 m | DRAWN |
| Internal | 0.10 m | DRAWN |
| Lift-shaft | 0.15 m | DRAWN |

- Both side walls (X = 0 and X = 8) have **no windows on any floor**. Light and air reach the rooms only from the front and rear faces.
- The exact wall rectangles for each floor are in `model/takeoff.json` under `floors.*.walls`.
- Each wall rectangle was overlaid on the architect's lines and checked by eye (`docs/overlays/takeoff_*.svg`). All of them coincide.

## 5. Floors 1, 2 and 3 (identical)

### Rooms

| Space | Label on drawing | Label in m | Measured clear (DRAWN) | Area m² (CALC.) | Status |
|---|---|---|---|---|---|
| ROOM-3 | 9'6"×12'9" | 2.90×3.89 | 2.90×3.90 main, **plus a 1.60×1.90 alcove** (labelled 5'3"×6'3") at the rear-left with the room's only window | 14.35 | ✔ |
| ROOM-3 toilet | 3'11"×5'11" | 1.19×1.80 | 1.20×1.80 | 2.16 | ✔ |
| ROOM-4 | 11'1"×9'2" | 3.38×2.79 | 3.40×2.80 main, plus a **0.90 m wide entry passage** from the lobby | 12.09 | ✔ |
| ROOM-4 toilet | **3'7"**×5'11" | 1.09×1.80 | **1.20**×1.80 | 2.16 | ✖ Label is 11 cm narrower than drawn (Q4) |
| ROOM-2 | 12'6"×7'8" | 3.81×2.34 | 3.80×2.35 main, plus a 2.90×1.00 entry strip (labelled 9'6"×3'3"), plus a 2.50×2.20 front part (labelled 8'2"×7'3"). The room is L-shaped. | 17.33 | ✔ |
| ROOM-2 toilet | 3'11"×6'11" | 1.19×2.11 | 1.20×2.10 | 2.52 | ✔ |
| ROOM-1 | 12'6"×7'8" | 3.81×2.34 | 3.80×2.35 main, plus a 2.50×2.20 front part (labelled 8'2"×7'3"). The room is L-shaped. | 14.43 | ✔ |
| ROOM-1 toilet | 3'11"×6'11" | 1.19×2.11 | 1.20×2.10 | 2.52 | ✔ |
| LOBBY | 8'4"×7'3" | 2.54×2.21 | 2.45×2.20, plus a 0.90×0.25 nib | 5.61 | ~ 9 cm narrower than labelled |
| LIFT (car shaft clear) | 4'11"×4'11" | 1.50×1.50 | **1.40 (X) × 1.50 (Y)** | 2.10 | ✖ Q3 |
| STAIR enclosure | none | n/a | 2.10×3.85 | 8.08 | see §9 |

### Doors and openings

The drawing shows **openings only on Floors 1–3**. Door leaves and swing directions are not drawn on these floors.

| ID | Where | Width | Tag |
|---|---|---|---|
| F-D3 | Lobby → ROOM-3, in wall X 3.05–3.15, Y 4.50–5.40 | 0.90 | DRAWN |
| F-D4 | Lobby → ROOM-4 passage, at Y 4.50, X 3.15–4.05 | 0.90 | DRAWN |
| F-D2 | Lobby → ROOM-2, in wall X 3.05–3.15, Y 6.05–6.95 | 0.90 | DRAWN |
| F-D1 | Lobby → ROOM-1, at Y 7.00, X 4.60–5.50 | 0.90 | DRAWN |
| F-D3T / F-D4T | ROOM-3 / ROOM-4 toilets (Y 2.00) | 0.65 | DRAWN |
| F-D2T / F-D1T | ROOM-2 / ROOM-1 toilets (Y 9.45) | 0.65 | DRAWN |
| F-L | Lift door opening in the shaft wall | 1.10 | DRAWN |
| F-S | Lobby → stair landing (no door drawn) | 1.10 | DRAWN |

- **Swings: ASSUMED for now.** ROOM-1 and ROOM-2 will copy the Floor 4 swings, which are drawn (hinge positions are in `model/takeoff.json`).
- For ROOM-3, ROOM-4 and all toilet doors I need your input (Q6).

### Windows

All widths are DRAWN. Sill and lintel heights are not drawn.

| Face | Windows |
|---|---|
| Rear | 1.50 (ROOM-3 alcove), 0.60 (ROOM-3 toilet), 0.60 (ROOM-4 toilet), 1.50 (ROOM-4) |
| Front | 1.50 (ROOM-2), 0.60 (ROOM-2 toilet), 0.60 (ROOM-1 toilet), 1.50 (ROOM-1) |

### Grey outlines

- Each room has a 0.55 m deep grey rectangle:
  - ROOM-3: along its front wall
  - ROOM-4: in its rear-left corner
  - ROOM-1 and ROOM-2: against the central wall
- They are read as **built-in wardrobes or lofts (ASSUMED, Q7)**.

## 6. Floor 4

| Space | Label on drawing | Label in m | Measured clear (DRAWN) | Area m² (CALC.) | Status |
|---|---|---|---|---|---|
| ROOM-3 suite | 12'9"×19'0" | 3.89×5.79 | 3.90×5.80, plus a 1.50×0.75 passage to the terrace | 23.83 | ✔ |
| ROOM-3 toilet | 3'11"×5'11" | 1.19×1.80 | **1.50×1.95** | 2.93 | ✖ Drawn bigger than labelled (Q4) |
| Private terrace | 6'10"×9'2" | 2.08×2.79 | 2.10×2.80, open to sky | 5.88 | ✔ |
| ROOM-2 | 12'6"×7'8" | 3.81×2.34 | 3.80×**1.63** main, plus a 2.90×1.00 entry strip, plus a 2.50×2.02 front part | 14.14 | ✖ Q5 |
| ROOM-1 | 12'6"×7'8" | 3.81×2.34 | 3.80×**1.63** main, plus a 2.50×2.02 front part | 11.24 | ✖ Q5 |
| ROOM-1 / ROOM-2 toilets | 3'11"×6'4" | 1.19×1.93 | 1.20×1.92 | 2.30 each | ✔ |
| LOBBY | 8'4"×7'3" (same as Floors 1–3) | 2.54×2.21 | L-shaped: 1.45×2.20 plus 1.00×0.90 | 4.09 | ✖ Smaller than labelled |
| Front terrace | none | n/a | 8.00×0.90, with a 0.10 m railing or parapet drawn | 7.20 | DRAWN |

- **Door swings on Floor 4 (DRAWN arcs, 0.90 m doors):**
  - ROOM-3: hinged at (4.05, 6.05), opens into the room
  - ROOM-2: hinged at (3.15, 6.05), opens into the room
  - ROOM-1: hinged at (4.60, 6.95), opens into the room
- **Other openings (DRAWN):**
  - Toilet doors: 0.65
  - Opening from the ROOM-3 passage to the terrace: 0.75, no leaf drawn
  - Lift door opening: 1.10
- **Windows (DRAWN):**
  - Rear: 1.50 (ROOM-3) and 0.60 (toilet)
  - Front: same positions as Floors 1–3

## 7. Ground floor (stilt)

| Space | Label on drawing | Label in m | Measured clear (DRAWN) | Status |
|---|---|---|---|---|
| WC-1 | 3'×3' | 0.91×0.91 | 0.90×0.90. Door 0.65, opens to the stilt. | ✔ |
| WC-2 | 4'×3' | 1.22×0.91 | 1.20×0.90. Door 0.65, opens from the servant vestibule. | ✔ |
| Servant vestibule | 4'7"×3'3" | 1.40×0.99 | 1.40×1.00. Open to the servant room. Rear window 0.90. | ✔ |
| Pantry | 5'11"×4'11" | 1.80×1.50 | 1.50 (X) × 1.80 (Y), so the label is depth × width. Open to the stilt through 1.20 m with no door. A grey L-line is read as a counter (ASSUMED). | ✔ |
| Servant room | 6'10"×5'11" | 2.08×1.80 | 2.10×1.80. **Door 0.75, opens onto the stair rear landing.** | ✔ |
| Lift and lift lobby | n/a | n/a | Lift 1.40×1.50. Lobby 1.45×2.30. The lobby entry from the stilt is drawn as a single line, 1.35 m wide (Q8). | ? |
| Stilt parking | none | n/a | 3.90 × 11.75 along the left, plus 3.80 × 4.70 at the front-right. **No columns are drawn (Q1).** | ? |
| U.G. tank | 3.00×2.05×1.70, 10,000 L | n/a | Inner 2.05 (X) × 3.00 (Y) at X 5.65–7.70, Y 9.45–12.45. Gross volume 10.46 m³ (CALCULATED). Half under the building, half under the front margin. | ✔ |

- Full-depth walls are drawn along **both side boundaries** at ground level (Q10).
- The rear is open from X 0.15 to 4.05.
- A grey 0.41 × 4.10 m strip runs beside the core at X 3.64–4.05 (Q9).

## 8. Terrace

- **Parapet:** a 0.15 m ring around the roof (DRAWN). The height is not drawn.
- **F4 private terrace:** the area over it is shown as "TERRACE BELOW". It is a 2.10×2.80 m void bounded by parapet walls.
- **Stair cabin (mumty):** 2.10 × 3.85 m clear, entered from the terrace through a 1.10 m opening.
- **Lift shaft:** continues to terrace level, with a door opening drawn at terrace level (Q11).
- **O.H. water tank:** labelled 2.10×2.20×1.50, "CAP= 6500 LTRS", drawn **over the stair cabin** at X 5.75–7.85, Y 4.75–6.95.
  - Gross volume: 6.93 m³ (CALCULATED).
  - The 6,500 L in your notes **is confirmed in the AFTER O.C. set**.

## 9. Stair and lift

- **Stair:**
  - Dog-leg, two 1.00 m flights with a 0.10 m mid wall (DRAWN).
  - 8 tread lines per flight at a 0.25 m going (DRAWN).
  - Rear landing 1.00 m, front (floor) landing 1.10 m (DRAWN).
  - If each line is a riser, that is 16 risers per storey. For example, a 3.00 m floor-to-floor height would give 187.5 mm risers (CALCULATED, illustrative only). The real riser height needs the floor height (Q2).
- **Lift:**
  - Clear 1.40 × 1.50 m. Shaft outer 1.70 × 1.80 m. Structural door opening 1.10 m (all DRAWN).
  - Pit, overrun and machine room are not drawn (Q11).

## 10. Dimension-chain checks (CALCULATED from DRAWN values)

| Chain | Sum | Result |
|---|---|---|
| Floors 1–3 rear, across: wall 0.15 + alcove 1.60 + 0.10 + toilet 1.20 + 0.10 + toilet 1.20 + 0.10 + ROOM-4 3.40 + wall 0.15 | 8.00 | ✔ |
| Floors 1–3 middle, across: 0.15 + ROOM-3 2.90 + 0.10 + passage 0.90 + shaft wall 0.15 + lift 1.40 + 0.15 + stair 2.10 + 0.15 | 8.00 | ✔ |
| Floors 1–3 front, across: 0.15 + 2.50 + 0.10 + 1.20 + 0.10 + 1.20 + 0.10 + 2.50 + 0.15 | 8.00 | ✔ |
| Floors 1–3 left, deep: 0.15 + alcove 1.90 + ROOM-3 3.90 + 0.10 + strip 1.00 + ROOM-2 2.35 + 2.20 + 0.15 | 11.75 | ✔ |
| Floors 1–3 core, deep: 0.15 + ROOM-4 2.80 + 0.15 + stair 3.85 + 0.10 + ROOM-1 2.35 + 2.20 + 0.15 | 11.75 | ✔ |
| Floor 4 left, deep: 0.15 + ROOM-3 5.80 + 0.10 + 1.00 + 1.63 + 0.10 + 1.92 + 0.15 | 10.85 | ✔ |
| Plot, depth (all floors) | 13.35 | ✔ |

**The internal geometry closes on every floor.** The mismatches listed in §11 are between the written labels and the drawn geometry, not between chains.

## 11. Conflicts

The drawing has been followed in every case below.

| # | Topic | Your notes said | Drawing shows |
|---|---|---|---|
| C1 | Margins | Front 0.60 m, rear 1.00 m | **Front (road side) 1.00 m, rear 0.60 m** |
| C2 | 8'2"×7'3" spaces | Circulation; one holds the stair | They are the **front parts of ROOM-1 and ROOM-2**, with the front windows. The stair is a separate 2.10×3.85 m enclosure next to the lift. |
| C3 | Circulation band | Lobby plus two 8'2"×7'3" spaces | Only the lobby, the stair and ROOM-4's 0.90 m passage. ROOM-2 has a 9'6"×3'3" entry strip inside the room. |
| C4 | Lift | About 1.50×1.50 m | 1.40×1.50 m clear. The label "4'11"×4'11"" does not match the drawn geometry. |
| C5 | ROOM-4 toilet | 3'7"×5'11" | Label says 3'7", drawn width is 1.20 m (3'11") |
| C6 | Floor 4 ROOM-1/2 | 12'6"×7'8", same as Floors 1–3 | Floor 4 is 0.90 m shallower. The main part is 1.63 m deep (not 2.34). |
| C7 | Floor 4 ROOM-3 toilet | not stated | Label 3'11"×5'11", drawn 1.50×1.95 |
| C8 | Floor 4 lobby | 8'4"×7'3" | L-shaped, 1.45 m wide at the lift |
| C9 | ROOM-3 (Floors 1–3) | 9'6"×12'9" | Matches, **plus** a 5'3"×6'3" alcove that holds the room's only window |
| C10 | Columns | About 14 columns | **No columns are drawn anywhere** |
| C11 | Tanks | U.G. 10,000 L, O.H. 6,500 L (verify) | Both are confirmed on the AFTER O.C. sheet, with sizes (§7, §8) |
| C12 | Area statement | 5,047.81 sq ft total, 1,011.91 sq ft ground | No area statement on this sheet. The footprint calculates to 1,011.8 sq ft ✔. The total can't be checked against this sheet. |

## 12. Physical-safety items for the architect, structural engineer or fire consultant

These are raised for safety only. They are not comments on approvals.

- **S1.** There is **one staircase**, with 1.00 m flights. It is the only exit route drawn for about 22 occupants over four floors. Please have the architect or fire consultant confirm that the stair width, fire separation and fire door of the stair enclosure are adequate for a PG/hostel use. I will check the NBC 2016 Part 4 clauses in Phase 3 rather than quote them from memory.
- **S2.** No columns are drawn. The stilt has open spans of 3.9 × 11.6 m, and there is a Seismic Zone III requirement. A structural drawing is needed. **I will not invent column positions.**
- **S3.** Floor 4 walls do not sit on the Floor 1–3 walls below. This applies to the Floor 4 front wall at Y = 10.70–10.85, the ROOM-3 suite toilet, and the lobby and suite walls. Each needs a beam beneath it. **For structural engineer review.**
- **S4.** The O.H. tank (about 6.5 t of water plus the tank itself) sits on the stair-cabin roof. The U.G. tank lies under the parking and drive area. Both need structural design for these loads. **For structural engineer review.**
- **S5.** Parapet and railing heights are not drawn for the roof, the Floor 4 front terrace (0.90 m wide) or the Floor 4 private terrace. Please confirm them, because they are fall-protection items.

## 13. Questions (numbered, please answer before or during Phase 2)

1. **Structure.** Is there a structural or column layout drawing (PDF, DWG or a photo)? Without it, Phase 2 will show **no columns or beams**, only a clearly labelled note. Alternatively, do you want me to show "indicative columns at wall junctions, ASSUMED"? I recommend **not** doing that.
2. **Levels.** What is the floor-to-floor height? Typical values for this kind of building are 3.00 m, or 2.85 to 3.15 m. Also:
   - What is the stilt height? Is it 3.0 m?
   - What is the plinth height above road level?
   - What are the parapet, terrace railing and stair-cabin heights?

   Unless you say otherwise I will **ASSUME**:
   - Floor-to-floor: 3.00 m
   - Plinth: 0.45 m
   - Slab: 0.15 m
   - Parapet: 1.00 m
   - Window sill: 0.90 m
   - Window and door heads: 2.10 m
   - Toilet window sill: 1.50 m
3. **Lift.** Is the clear shaft 1.40 × 1.50 m as drawn, or 1.50 × 1.50 as labelled? What lift is planned (make, capacity, machine-room-less or not)? I need the pit depth and overrun.
4. **Toilet sizes.** Should the drawn geometry win over the labels? Specifically:
   - ROOM-4 toilet, Floors 1–3: drawn 1.20 wide, labelled 3'7"
   - ROOM-3 toilet, Floor 4: drawn 1.50 × 1.95, labelled 3'11"×5'11"

   By your rule I will model the drawn geometry.
5. **Floor 4 ROOM-1/2.** Please confirm these really are 0.90 m shallower than Floors 1–3, with a main part of 1.63 m. This affects bed placement.
6. **Door swings.** Floors 1–3 show openings only. Please confirm:
   - **(a)** ROOM-1 and ROOM-2 doors swing the same as on Floor 4, into the room.
   - **(b)** Which side ROOM-3's door is hinged on (lobby wall X = 3.10, Y 4.50–5.40), and whether it opens into the room.
   - **(c)** Whether ROOM-4's door (at Y = 4.50) opens into the passage.
   - **(d)** Whether toilet doors open **outwards** (the usual choice for small toilets).
7. **Grey 0.55 m strips in the rooms.** Are these built-in wardrobes or lofts? They change where the 1.20 m sliding wardrobes go.
8. **Ground-floor lift lobby entry.** Is the single line at Y = 7.05, X 4.15–5.50 an open entry (1.35 m) from the stilt, or a wall or door?
9. **Grey strip beside the Ground-floor core** (X 3.64–4.05, Y 2.95–7.05, 0.41 × 4.10 m). What is it? It could be a ramp, a meter and electrical board niche, a duct or a planter. It may be the natural meter-board spot for Phase 3.
10. **Ground-floor side walls.** Are the stilt's left and right sides full-height masonry walls (as drawn), or open between columns?
11. **Terrace.** Does the lift stop at terrace level (a door opening is drawn there)? How tall is the stair cabin? The O.H. tank sits on it.
12. **Red dashed lines** at Y = 0.90 and Y = 10.50. These are recorded only. Tell me if they represent something physical, such as a beam line or a chajja.
13. **Room-3 window (Floors 1–3).** The room's only window is in the rear alcove. Is that the intended arrangement? This affects fan, AC and exhaust positions in Phase 3.

---

## 14. Room mix check (for Phase 2 furniture)

| Floor | ROOM-1 | ROOM-2 | ROOM-3 | ROOM-4 | Beds |
|---|---|---|---|---|---|
| Floors 1–3 (×3) | single | single | queen double | queen double | 6 × 3 = 18 |
| Floor 4 | single | single | queen suite | n/a | 4 |
| **Total** | | | | | **22 ✔** |

**Early fit check (CALCULATED):**
- ROOM-3 on Floors 1–3 takes a queen across its width with 0.60 m on both sides: 1.58 + 1.20 = 2.78 ≤ 2.90 m. That leaves 0.12 m to spare.
- ROOM-4 takes the same: 2.78 ≤ 2.85 m once the grey 0.55 m strip is excluded.
- Both are tight. Phase 2 will place the furniture and check every clearance.
