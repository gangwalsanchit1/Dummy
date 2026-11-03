# Floor 1 proposal: move one brick wall and two doors (feet and inches)

**Status: PROPOSAL, not yet in the main model.** The current plan (`docs/floor1-plan.png`) still follows the architect's drawing. This proposal is drawn in `docs/floor1-proposal.png` (orange = new brick wall, red dashed = brick wall removed).

The family said the internal brickwork can still change (03.11.2026). The question asked: which changes let more rooms take two students with the **same kit** (each student: own bed, own Tinker, own Twill wardrobe, own compact study table + chair, own bedside socket), and with every student able to walk up to their window?

Never touched: columns, lift walls, outer walls, windows, toilets (their drains and sunken floors are fixed).

## The three changes

1. **Move the wall between ROOM-3 and ROOM-2 by 3'-3⅜" towards the road.** It then lines up with the existing lobby wall, so one straight wall runs across the building. On the structural drawing the plinth beam PB3 runs on this same line, so the moved wall is likely to sit over a beam (to be confirmed: floor beams are not drawn yet).
2. **ROOM-2's door moves** from the lobby's side wall to the lobby's front wall (the wall facing ROOM-1's door). Clear width **2'-7½"** (today's room doors are 2'-11⅜"), because the opening sits between two existing walls.
3. **ROOM-3's door slides 5'-1"** along the lobby wall, to the corner next to the moved wall, hinged at that wall.

## Result

| Room | Today (as drawn) | With the proposal |
|---|---|---|
| ROOM-1 | 2 students, 155 sq ft | 2 students (unchanged) |
| ROOM-2 | 2 students, 187 sq ft | 2 students, 155 sq ft |
| ROOM-3 | 1 student, 154 sq ft | **2 students, 186 sq ft**, both desks beside the alcove window |
| ROOM-4 | 1 student, 130 sq ft | 1 student (unchanged) |
| **Floor 1** | **6 students** | **7 students** (21 over floors 1-3) |

Every student keeps the full kit; nobody shares a desk, chair or wardrobe. Each checked: inside the room, clear of walls, columns, door swings and each other; bed side 1'-11⅝", wardrobe front 1'-11⅝", chair 2'-5½"; a 1'-9⅝" walking path to every bed side, wardrobe, chair, the toilet door and (ROOM-3) the window.

## What was tried and did not work

- **ROOM-3 door only** (slid along the lobby wall, either hinge side): still no room for two kits.
- **Wall moved, but ROOM-3's door left where it is**: two kits fit only with the second bed across the window alcove, so the window could not be reached. Rejected.
- **ROOM-3 toilet door moved into the alcove**: does not help.
- **ROOM-4 as a twin**: no. Its main space is 11'-2" × 9'-2"; the rest is a 2'-11" passage that cannot hold a desk or wardrobe. Only a bigger change (moving the ROOM-4 toilet) would do it, and toilets are not touched.
- **Wall moved by only 1'-7¾"**: also works for ROOM-2 and ROOM-3, but the wall would then sit in the middle of the slab, not on the beam line. The 3'-3⅜" move is preferred.

## Before building it

- **Structural engineer (Agharkar):** confirm the floor beam under the new wall line (a 9'-10" brick wall moves onto it) and that removing the old wall is fine.
- **Architect:** update the floor 1-3 plans (and confirm a 2'-7½" door for ROOM-2 is acceptable).
- **Electrical and plumbing points** for ROOM-2 and ROOM-3 will be re-placed once you approve (switchboards move with the doors).

Tool: `tools/explore_walls.py` (each change is a named variant; results in `model/proposals/`).
