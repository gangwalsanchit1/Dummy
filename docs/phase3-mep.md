# Phase 3: Proposed Electrical and Plumbing (Coordination Level)

> **Proposal only.** Every point, route and size here is ASSUMED, chosen so that it fits the DRAWN building and passes the clash checks below.
> The final electrical design must be done and certified by a licensed electrical contractor or consultant. The final plumbing design must be done by a licensed plumber or consultant. Every slab opening, sleeve and depression needs the **structural engineer's** approval.

## How to see it

- **3D viewer:** open `viewer/bella-vita-2.html` and use the **Electrical set** or **Plumbing set** buttons.
  - Each layer can also be switched on separately: points, drainage, water, riser and feeders, conduits, and sleeves.
  - URL shortcut: `#floor=F1&isolate=1&view=top&mep=e` (use `mep=p` for plumbing).
- **IFC:** `model/bella-vita-2.ifc` now also holds 885 MEP elements as proper IFC classes, for example IfcOutlet, IfcLightFixture, IfcSanitaryTerminal and IfcPipeSegment. Pipes are swept along their routes, and each element carries a "PROPOSAL" status property.
- **Supporting files:**
  - Schedules: `docs/schedules/points_schedule.csv` (room by room) and `docs/schedules/quantities.csv`
  - Checks: `docs/mep-checks.md`
  - **Pre-slab checklist: `docs/pre-slab-checklist.md`**

**Amenities matched to the existing Bella Vita** (RFID entry, power backup, RO water, terrace laundry and lounge, room sub-meters) are listed in `docs/amenities.md`.

## Electrical concept

| Item | Proposal | Where |
|---|---|---|
| Supply | 3-phase LT service cable, underground from the road, to the utility meter board | Meter board, MDB and common-services DB in the **grey 0.41 m niche beside the ground-floor core** (stilt side, X 3.64–4.05). This is my reading of the unlabelled grey strip (takeoff Q9). |
| Riser | 200×100 trunking with sleeves through every slab | GF lift lobby to the terrace, on the lobby face of the stair wall at X 5.50–5.60, Y 5.40–5.60. It is clear of the lift door (ends X 5.38) and the stair opening (starts Y 5.85). |
| Floor distribution boards | One per floor, F1–F4: a TPN board with an RCBO per room and 4 circuits per room | Lobby, on the stair wall at Y 4.85–5.30, centred 1.75 m above floor |
| Circuits per room | Lights, fan, toilet light and exhaust (10 A); sockets (16 A); AC (20 A, dedicated); geyser (20 A, dedicated) | |
| Common services DB | Lift, pump, lobby, stair and stilt lights, CCTV, Wi-Fi, terrace | GF niche |
| Lift | Dedicated 3-phase feeder up the riser to an isolator at terrace level beside the shaft. This assumes a machine-room-less lift, which needs your lift maker's confirmation. | |
| Pump | 1 duty + 1 standby transfer pump on the U.G. tank roof in the front margin. Starter panel and level controller on the compound wall. | |

**Points in a typical room** (exact positions are in the schedule):
- **Room:**
  - switchboard at the door's latch side, 1.20 m
  - ceiling fan (box cast in the slab), 2–3 LED lights
  - bedside socket, USB and 2-way light switch at 0.60 m (one per bed; two in twin rooms)
  - desk socket group, USB and Cat6 data point at 0.90 m
  - AC indoor unit and 20 A socket at about 2.4 m, always on an external wall, with the outdoor unit on a bracket outside (Floor 4: on the terraces)
- **Toilet:**
  - switchboard outside the door
  - ceiling light
  - exhaust fan in the ventilator
  - geyser outlet at 2.20 m, at least 0.6 m from the shower zone
- **Lobby:** 2 motion-sensor lights, a Wi-Fi access point and a CCTV camera
- **CCTV, 9 cameras in total:** stilt, gate, terrace and every lobby

## Plumbing concept

| Item | Proposal |
|---|---|
| System | Two-pipe system: separate soil and waste stacks, each vented. **External stacks** on the rear and front faces, because no plumbing shaft is drawn. |
| Rear stacks | S1 soil at X 3.10 and W1 waste at X 3.30, outside the rear wall, on the solid wall between windows on every floor. They serve the ROOM-3 and ROOM-4 toilets on F1–3 and the F4 suite toilet. The F4 branch runs about 1.3 m along the outside of the rear face. |
| Front stacks | S2 soil at X 4.00 and W2 waste at X 4.20, outside the F1–F3 front wall. They serve the ROOM-1 and ROOM-2 toilets. **At F4 they offset 0.9 m across the F4 front terrace** (boxed in, through sleeves in the parapet) to run up the F4 front wall. This is ASSUMED and the architect needs to accept it. |
| Vents | Stacks extended to **2.0 m above the terrace floor**, because the terrace is used. This height is ASSUMED, not a verified code value. |
| Toilet floors | **300 mm sunk slab** in every toilet (ASSUMED), carrying the WC and floor-trap branches to the external stacks. **Pre-slab decision.** |
| Toilet layout | Basin and WC on the stack-side wall, shower at the far end with a floor trap, health faucet, and a 15 L geyser above the WC. The 1.20×1.80 toilets (ROOM-3 and ROOM-4) are compact, with a shower zone of about 1.20×0.65. **All fixtures stay inside the drawn toilets**, as the family asked; no toilet or room is changed. |
| Water supply | Municipal meter → U.G. tank (10,000 L) → pumps → **rising main** up the front face (X 7.60), across the terrace, and up the stair cabin into the O.H. tank (6,500 L). The OHT outlet header runs on the terrace to two **down-takes**: DT-R at X 2.95 (rear) and DT-F at X 3.80 (front). Branches enter each toilet at 2.4 m. |
| Hot water | Geyser in each toilet feeding the shower mixer |
| Drainage below ground | Rear inspection chamber (rear margin) → 150 mm drain under the stilt at X 3.20, kept away from the U.G. tank (X 5.50–7.85) → front inspection chamber → municipal sewer |
| Rainwater | 3 roof outlets, one F4 front-terrace outlet and one private-terrace outlet, cast in the slabs, feeding 4 rainwater pipes. All pipes avoid windows on every floor. |

## Water demand and storage check

| Item | Value | Basis |
|---|---|---|
| Demand | 28 persons (26 students + 2 staff) × 135 L/day = **3,780 L/day** | **IS 1172:1993, clause 4.2, Table 1, item (v) Hostels: 135 L per head per day** (verified from the standard's text) |
| U.G. tank, 10,000 L | about 2.6 days of demand | CALCULATED |
| O.H. tank, 6,500 L | about 1.7 days of demand | CALCULATED |
| WCs, basins and baths | 1 per room (en-suite) is far better than **IS 1172 Table 11, Hostels (clause 5.3): 1 WC, 1 basin and 1 bath per 8 males or 6 females** | Verified |
| Cleaner's sink | IS 1172 Table 11 (vi) lists **1 cleaner's sink per floor (minimum)**. **None is drawn, and the lobby has no room for one.** | Raised for your decision |

## Things you should know (physical and functional)

1. **Low water pressure on the top floors.** The O.H. tank sits on the stair cabin, so its base is about 4.9 m above the F4 shower outlet: roughly 0.5 bar, and about 0.8 bar on F3. That is CALCULATED from the ASSUMED levels. Showers and geysers often perform poorly at these pressures, according to manufacturer data rather than a code. **Consider a small pressure-booster pump for F3–F4**, or raising the OHT.
2. **No electrical or plumbing shaft is drawn.**
   - The electrical riser goes in the lobby, in surface trunking with slab sleeves.
   - The stacks go outside the building.
   - The architect should confirm both, including how the external stacks look on the front facade.
3. **Front stack offset at F4.** The soil, waste, down-take, rising-main and rainwater pipes all cross the 0.9 m F4 front terrace. They must be boxed in and protected, and they need sleeves in the F4 front parapet. The alternative is a recess in the F4 front wall, which is an architect's decision.
4. **Toilet depressions (sunk slabs) must be decided before each slab pour.** If you prefer raised toilet floors instead, tell me and I'll regenerate the checklist.
5. **Cleaner's sink:** none is drawn (see above).
6. **Smoke detection and fire alarm** were not in this scope. Given the single stair (takeoff S1), I recommend asking the fire consultant about a detection system for the lobbies and stair.

## Clash checks (`docs/mep-checks.md`)

- **507 points and 446 runs checked. Hard clashes: 0.** Bedside, desk and data points follow the fitted furniture. Where a desk sits under a window, its socket goes below the desk with a desk-top power module.
- **Wall-mounted points must:**
  - sit on a drawn wall face
  - be outside every window (between sill and head) and every door opening
  - not be behind a door leaf, checked against the quarter-disc of every swing
  - not be hidden by a bed, wardrobe or desk
- **Fans:** each fan's 1.2 m sweep keeps at least 0.15 m from the walls.
- **Geyser outlets:** each one is at least 0.6 m from its shower floor trap.
- **Stacks, down-takes, rising main and rainwater pipes** are clear of every window on all floors.
- **Beams:** none are drawn, so every wall line is treated as a probable beam line.
  - 2 CCTV points sit 0.15 m from a wall line.
  - Riser sleeves sit 0.02 m from the stair wall face.
  - **Flagged for the structural engineer:** the beam position decides whether the riser sleeve moves 100–150 mm into the lobby.
- **Columns:** none are drawn, so this check is **not possible** (takeoff Q1).

## Approximate quantities

These come from `quantities.csv`. Lengths are CALCULATED from the ASSUMED routes plus 10%. They are for a rough budget only, with no prices.

| Run | Approx. length |
|---|---|
| Conduit (indicative, slab and wall) | about 2,290 m |
| Cold water branches | about 262 m |
| Hot water | about 55 m |
| Down-takes and header | about 41 m |
| Rising main | about 29 m |
| Soil (stacks and branches) | about 67 m |
| Waste | about 75 m |
| Rainwater pipes | about 71 m |
| Underground drain | about 19 m |
| Riser and feeders | about 49 m |

**Point totals** (before the amenity additions; see `docs/schedules/quantities.csv` for current counts):
- **Electrical:**
  - 16 room switchboards and 17 toilet switchboards
  - 16 fans, 71 ceiling lights and 16 wall lights
  - one bedside point per bed (26), and one desk and one data point per study table (26 each); see `quantities.csv`
  - 15 AC positions, 15 geyser outlets and 17 exhaust fans
  - 4 Wi-Fi access points and 9 CCTV cameras
  - 4 floor distribution boards, plus the meter board, MDB and common-services DB
- **Plumbing:** 17 WCs, 16 basins, 15 showers, 19 floor traps, 15 geysers, 2 pumps and 5 rainwater outlets.

**Connected load** (CALCULATED from ASSUMED ratings: AC 1.6 kW, geyser 2.0 kW and so on, all before diversity):
- About 16.4 kW per floor on F1–F3, 12.8 kW on F4 and 4.3 kW on GF, plus the lift (about 5.5 kW) and pump (about 1.5 kW).
- That totals **about 74 kW connected**.
- The sanctioned load and the supply application are for the licensed electrical contractor.

## Code references

I cite a clause only where I could read the source. Everything else is labelled as practice.

| Topic | Reference | Status |
|---|---|---|
| Water demand, hostels: 135 L/head/day | IS 1172:1993, cl. 4.2 and Table 1 (v) | **Verified** from the standard's text ([law.resource.org copy](https://law.resource.org/pub/in/bis/S03/is.1172.1993.pdf)) |
| Sanitary fittings for hostels; cleaner's sink per floor | IS 1172:1993, cl. 5.3 and Table 11 | **Verified**, same source |
| RCD (earth-leakage) protection mandatory | CEA (Measures relating to Safety and Electric Supply) Regulations 2023, Regulation 44 | **Verified as cited** by a BIS document ([BIS](https://www.services.bis.gov.in/tmp/tbl5_2024-11-08_1157.pdf)). The 30 mA trip is typical practice per SP 30:2023; I could not read that text. |
| Bathroom zones, socket and geyser distances | IS 732:2019 (follows IEC 60364-7-701) | **Not verified.** The primary text was not accessible. I used ≥0.6 m from the shower zone as practice only ([IEC 60364-7-701 summary](https://www.voltimum.co.uk/articles/section-701-locations-containing-bath-or)). |
| Switch and socket heights | NBC 2016 Part 8 Sec. 2 / common Indian practice | **Not verified.** Heights are ASSUMED practice (switches 1.20 m, sockets 0.30–0.90 m). |
| Vent pipe termination height; trap and branch sizes | NBC 2016 Part 9 Sec. 2 | **Not verified.** 2.0 m above a used terrace is ASSUMED. The plumbing consultant must confirm. |
| Stair width for this occupancy | NBC 2016 Part 4 | **Not verified.** Secondary sources disagree (1.0 to 1.5 m). Raised as safety item S1. |

## What I decided on my own logic (you said to proceed)

- Meter boards in the grey ground-floor niche (Q9).
- Electrical riser on the lobby face of the stair wall.
- External soil, waste and down-take stacks.
- 300 mm sunk toilet slabs.
- Toilet doors opening outwards.
- Machine-room-less lift with its isolator at the terrace.
- Geyser in each toilet.
- AC in every room. Remove the AC from the schedule if some rooms won't have it.
- Wi-Fi access point per floor instead of data points everywhere. One data point at each desk is still included.
