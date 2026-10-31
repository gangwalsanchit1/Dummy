#!/usr/bin/env python3
"""Phase 3: proposed electrical and plumbing points for Bella Vita 2 (coordination level).

Inputs : model/takeoff.json, model/assumptions.json, model/furniture.json, model/scene.json
Outputs: model/mep.json                     points + runs (used by the viewer and IFC export)
         docs/mep-checks.md                 clash checks
         docs/schedules/points_schedule.csv room-by-room point schedule
         docs/schedules/quantities.csv      point counts and approximate run lengths
Every position here is ASSUMED (a proposal); building geometry it is checked against is DRAWN.
All final electrical and plumbing design must be done/approved by licensed consultants.
"""
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TK = json.loads((ROOT / "model/takeoff.json").read_text())
AS = json.loads((ROOT / "model/assumptions.json").read_text())
FU = json.loads((ROOT / "model/furniture.json").read_text())
SC = json.loads((ROOT / "model/scene.json").read_text())
FFL = SC["ffl"]
CEIL = AS["levels"]["floor_to_floor"] - AS["levels"]["slab_thickness"]      # 2.85 clear
CABIN_TOP = SC["cabin_top"]
PLAN_OF = {"GF": "GF", "F1": "F1-3", "F2": "F1-3", "F3": "F1-3", "F4": "F4", "TERRACE": "TERRACE"}

# kind -> (system, layer, description, size [w, d, h] m, IFC class)
K = {
    "MB": ("E", "elec", "Utility meter board (3-phase)", [0.30, 0.20, 0.60], "IfcElectricDistributionBoard"),
    "MDB": ("E", "elec", "Main distribution board", [0.30, 0.20, 0.60], "IfcElectricDistributionBoard"),
    "CDB": ("E", "elec", "Common-services DB (lift, pump, common lights, CCTV, Wi-Fi)", [0.30, 0.15, 0.45], "IfcElectricDistributionBoard"),
    "DB": ("E", "elec", "Floor DB (TPN, RCBO + prepaid energy sub-meter per room)", [0.45, 0.12, 0.50], "IfcElectricDistributionBoard"),
    "SB": ("E", "elec", "Room switchboard at door (incl. 2-way for light)", [0.25, 0.05, 0.15], "IfcSwitchingDevice"),
    "TSW": ("E", "elec", "Toilet switchboard outside toilet (light, exhaust, geyser DP+indicator)", [0.20, 0.05, 0.12], "IfcSwitchingDevice"),
    "BS": ("E", "elec", "Bedside: 6A socket + USB + 2-way light switch", [0.20, 0.05, 0.10], "IfcOutlet"),
    "DESK": ("E", "elec", "Study desk: 2 x 6A socket + USB", [0.25, 0.05, 0.10], "IfcOutlet"),
    "DATA": ("E", "elec", "Data outlet (Cat6) at desk", [0.08, 0.05, 0.08], "IfcOutlet"),
    "SKT16": ("E", "elec", "16A power socket", [0.10, 0.05, 0.10], "IfcOutlet"),
    "WPS": ("E", "elec", "Weatherproof 16A socket (IP55)", [0.12, 0.08, 0.12], "IfcOutlet"),
    "ACS": ("E", "elec", "AC socket 20A (dedicated circuit)", [0.10, 0.05, 0.10], "IfcOutlet"),
    "GZP": ("E", "elec", "Geyser connection unit 20A (switched outside toilet)", [0.10, 0.05, 0.10], "IfcOutlet"),
    "LT": ("E", "elec", "Ceiling light point (LED)", [0.20, 0.20, 0.04], "IfcLightFixture"),
    "WL": ("E", "elec", "Wall light point", [0.15, 0.08, 0.10], "IfcLightFixture"),
    "FAN": ("E", "elec", "Ceiling fan point (1200 mm sweep, fan box cast in slab)", [0.25, 0.25, 0.30], "IfcFan"),
    "EXH": ("E", "elec", "Exhaust fan (in ventilator, IPX4)", [0.25, 0.10, 0.25], "IfcFan"),
    "ACI": ("E", "elec", "AC indoor unit position (~0.90 wide)", [0.90, 0.25, 0.30], "IfcUnitaryEquipment"),
    "ACO": ("E", "elec", "AC outdoor unit on bracket", [0.75, 0.30, 0.55], "IfcUnitaryEquipment"),
    "AP": ("E", "elec", "Wi-Fi access point (ceiling)", [0.20, 0.20, 0.04], "IfcCommunicationsAppliance"),
    "CCTV": ("E", "elec", "CCTV camera (PoE)", [0.12, 0.12, 0.10], "IfcCommunicationsAppliance"),
    "LIFTISO": ("E", "elec", "Lift isolator / controller supply (3-phase)", [0.25, 0.15, 0.30], "IfcSwitchingDevice"),
    "PUMPP": ("E", "elec", "Pump starter panel + level controller", [0.30, 0.15, 0.40], "IfcElectricDistributionBoard"),
    "RISER": ("E", "elec", "Electrical riser trunking 200x100", [0.20, 0.10, 0.10], "IfcCableCarrierSegment"),
    "INV": ("E", "elec", "Power backup: inverter + Li-ion battery (common lights, CCTV, Wi-Fi, RFID, lift ARD)", [0.35, 0.25, 1.20], "IfcElectricFlowStorageDevice"),
    "RFID": ("E", "elec", "RFID card reader (entry access)", [0.10, 0.04, 0.15], "IfcSensor"),
    "MLOCK": ("E", "elec", "Electromagnetic lock + exit button (entry door)", [0.25, 0.05, 0.05], "IfcActuator"),
    "RFIDL": ("E", "elec", "RFID door lock (battery, no wiring) on room door", [0.07, 0.07, 0.25], "IfcDiscreteAccessory"),
    "DISP": ("E", "elec", "Drinking-water dispenser (floor) + 16A socket", [0.35, 0.35, 1.00], "IfcElectricAppliance"),
    "WM": ("P", "plumb", "Washing machine (front load) on terrace laundry", [0.60, 0.60, 0.85], "IfcElectricAppliance"),
    "RO": ("P", "plumb", "RO purifier (under/over pantry sink)", [0.30, 0.15, 0.40], "IfcElectricAppliance"),
    "WC": ("P", "plumb", "Water closet (EWC, wall-outlet)", [0.38, 0.65, 0.40], "IfcSanitaryTerminal"),
    "BAS": ("P", "plumb", "Wash basin (compact)", [0.45, 0.35, 0.80], "IfcSanitaryTerminal"),
    "SHM": ("P", "plumb", "Shower mixer + overhead shower", [0.15, 0.10, 0.15], "IfcSanitaryTerminal"),
    "HF": ("P", "plumb", "Health faucet", [0.08, 0.08, 0.08], "IfcSanitaryTerminal"),
    "FT": ("P", "plumb", "Floor trap 100 mm (nahani)", [0.15, 0.15, 0.02], "IfcWasteTerminal"),
    "GZ": ("P", "plumb", "Geyser 15 L (wall-mounted)", [0.35, 0.35, 0.50], "IfcElectricAppliance"),
    "SINK": ("P", "plumb", "Pantry sink", [0.60, 0.45, 0.20], "IfcSanitaryTerminal"),
    "TAP": ("P", "plumb", "Bib tap", [0.08, 0.08, 0.08], "IfcValve"),
    "PUMP": ("P", "plumb", "Transfer pump (1 duty + 1 standby)", [0.45, 0.30, 0.35], "IfcPump"),
    "IC": ("P", "plumb", "Inspection chamber", [0.60, 0.60, 0.05], "IfcDistributionChamberElement"),
    "RWO": ("P", "plumb", "Rainwater outlet (khurra), cast in slab", [0.20, 0.20, 0.02], "IfcWasteTerminal"),
    "METER": ("P", "plumb", "Municipal water meter + valve", [0.25, 0.15, 0.20], "IfcFlowMeter"),
    "TCON": ("P", "plumb", "Tank connection (puddle flange, cast in)", [0.15, 0.15, 0.15], "IfcPipeFitting"),
    "SLV": ("S", "sleeve", "Sleeve / cast-in item", [0.15, 0.15, 0.20], "IfcBuildingElementProxy"),
}
PIPE = {  # run system -> (layer, nominal dia m, colour key, description)
    "SOIL": ("plumb", 0.110, "soil", "Soil stack/branch 110 mm"),
    "WASTE": ("plumb", 0.075, "waste", "Waste stack/branch 75 mm"),
    "VENT": ("plumb", 0.075, "vent", "Vent pipe 75 mm"),
    "CW": ("plumb", 0.025, "cw", "Cold water 25/20 mm"),
    "HW": ("plumb", 0.020, "hw", "Hot water 20/15 mm"),
    "DT": ("plumb", 0.040, "cw", "Down-take 40 mm"),
    "RM": ("plumb", 0.040, "rm", "Rising main 40 mm"),
    "RWP": ("plumb", 0.110, "rwp", "Rainwater pipe 110 mm"),
    "UGD": ("plumb", 0.150, "soil", "Underground drain 150 mm"),
    "SUP": ("plumb", 0.025, "cw", "Municipal supply 25 mm"),
    "FEED": ("elec", 0.050, "feed", "Feeder / riser cable"),
    "COND": ("conduit", 0.020, "cond", "Conduit (indicative)"),
}

points, runs = [], []
PID = Counter()


def P(kind, storey, room, x, y, z, face, note="", circuit="", tag="ASSUMED"):
    """z is relative to the storey FFL; face = 'C' ceiling, 'F' floor, or wall facing '+x','-x','+y','-y', 'O' outside."""
    PID[(storey, kind)] += 1
    pid = f"{storey}-{kind}{PID[(storey, kind)]}"
    zabs = (FFL[storey] if storey in FFL else 0.0) + z
    points.append({"id": pid, "kind": kind, "sys": K[kind][0], "storey": storey, "room": room, "x": round(x, 3),
                   "y": round(y, 3), "z": round(zabs, 3), "zrel": round(z, 3), "face": face, "note": note,
                   "circuit": circuit, "tag": tag})
    return points[-1]


def R(system, storey, name, pts, tag="ASSUMED indicative route"):
    runs.append({"sys": system, "storey": storey, "name": name, "pts": [[round(a, 3) for a in p] for p in pts], "tag": tag})
    return runs[-1]


def length(run):
    return sum(math.dist(a, b) for a, b in zip(run["pts"], run["pts"][1:]))


# ===================================================================== room templates
# ---- rooms on F1-3 and F4 (coordinates in plan metres; z relative to FFL)
def rooms_F13(s):
    c = {}
    # ROOM-1 (single)
    c["ROOM-1"] = [
        ("SB", 5.78, 7.05, 1.2, "+y", "latch side of F-D1", "L/F"),
        ("FAN", 5.95, 8.225, CEIL, "C", "", "L/F"), ("LT", 6.95, 8.225, CEIL, "C", "", "L/F"), ("LT", 6.60, 10.50, CEIL, "C", "front part", "L/F"),
        ("ACI", 6.60, 11.60, 2.40, "-y", "above front window", "AC"), ("ACS", 7.20, 11.60, 2.35, "-y", "", "AC"),
        ("ACO", 6.60, 11.90, 2.30, "O", "bracket outside front wall", "AC"),
    ]
    c["ROOM-1 TOILET"] = [
        ("TSW", 5.35, 9.68, 1.2, "+x", "outside toilet, room side", "L/F"),
        ("LT", 4.65, 10.20, CEIL, "C", "", "L/F"), ("EXH", 4.65, 11.60, 1.80, "-y", "in ventilator F-W7", "L/F"),
        ("GZP", 4.05, 10.25, 2.20, "+x", ">=0.6 m from shower zone", "GZ"),
        ("WC", 4.05, 10.45, 0.0, "+x", "on left wall", ""), ("HF", 4.05, 10.80, 0.45, "+x", "", ""),
        ("BAS", 4.05, 9.85, 0.80, "+x", "", ""), ("SHM", 5.25, 11.25, 1.0, "-x", "shower zone y 10.85-11.60", ""),
        ("FT", 4.65, 11.25, 0.0, "F", "shower zone", ""), ("GZ", 4.05, 10.45, 1.85, "+x", "above WC", ""),
    ]
    c["ROOM-2"] = [
        ("SB", 3.25, 7.05, 1.2, "+y", "latch side of F-D2 (just inside)", "L/F"),
        ("FAN", 2.05, 8.225, CEIL, "C", "", "L/F"), ("LT", 1.05, 8.225, CEIL, "C", "", "L/F"), ("LT", 1.40, 10.50, CEIL, "C", "front part", "L/F"),
        ("LT", 1.60, 6.55, CEIL, "C", "entry strip", "L/F"),
        ("ACI", 1.40, 11.60, 2.40, "-y", "above front window", "AC"), ("ACS", 0.80, 11.60, 2.35, "-y", "", "AC"),
        ("ACO", 1.40, 11.90, 2.30, "O", "bracket outside front wall", "AC"),
    ]
    c["ROOM-2 TOILET"] = [
        ("TSW", 2.65, 9.68, 1.2, "-x", "outside toilet, room side", "L/F"),
        ("LT", 3.35, 10.20, CEIL, "C", "", "L/F"), ("EXH", 3.35, 11.60, 1.80, "-y", "in ventilator F-W6", "L/F"),
        ("GZP", 3.95, 10.25, 2.20, "-x", "", "GZ"),
        ("WC", 3.95, 10.45, 0.0, "-x", "on right wall", ""), ("HF", 3.95, 10.80, 0.45, "-x", "", ""),
        ("BAS", 3.95, 9.85, 0.80, "-x", "", ""), ("SHM", 2.75, 11.25, 1.0, "+x", "shower zone y 10.85-11.60", ""),
        ("FT", 3.35, 11.25, 0.0, "F", "", ""), ("GZ", 3.95, 10.45, 1.85, "-x", "above WC", ""),
    ]
    c["ROOM-3"] = [
        ("SB", 3.05, 4.22, 1.2, "-x", "latch side of F-D3", "L/F"),
        ("FAN", 1.60, 4.00, CEIL, "C", "", "L/F"), ("LT", 2.40, 3.00, CEIL, "C", "", "L/F"), ("LT", 0.95, 1.10, CEIL, "C", "alcove", "L/F"),
        ("ACI", 0.95, 0.15, 2.40, "+y", "above alcove window", "AC"), ("ACS", 1.55, 0.15, 2.35, "+y", "", "AC"),
        ("ACO", 0.95, -0.25, 2.30, "O", "bracket outside rear wall", "AC"),
    ]
    c["ROOM-3 TOILET"] = [
        ("TSW", 1.75, 1.72, 1.2, "-x", "alcove side of toilet wall", "L/F"),
        ("LT", 2.45, 1.40, CEIL, "C", "", "L/F"), ("EXH", 2.50, 0.15, 1.80, "+y", "in ventilator F-W2", "L/F"),
        ("GZP", 3.05, 1.45, 2.20, "-x", "", "GZ"),
        ("WC", 3.05, 1.15, 0.0, "-x", "on right wall", ""), ("HF", 3.05, 0.88, 0.45, "-x", "", ""),
        ("BAS", 3.05, 1.72, 0.80, "-x", "compact basin near door", ""), ("SHM", 1.85, 0.48, 1.0, "+x", "shower zone y 0.15-0.80", ""),
        ("FT", 2.45, 0.45, 0.0, "F", "", ""), ("GZ", 3.05, 1.15, 1.85, "-x", "above WC", ""),
    ]
    c["ROOM-4"] = [
        ("SB", 3.15, 4.08, 1.2, "+x", "latch side of F-D4 (passage)", "L/F"),
        ("LT", 3.60, 3.30, CEIL, "C", "passage", "L/F"), ("LT", 3.80, 2.50, CEIL, "C", "entry", "L/F"),
        ("FAN", 6.15, 1.55, CEIL, "C", "", "L/F"), ("LT", 5.25, 1.55, CEIL, "C", "", "L/F"),
        ("ACI", 7.35, 0.15, 2.40, "+y", "solid wall right of window", "AC"), ("ACS", 6.80, 0.15, 2.35, "+y", "", "AC"),
        ("ACO", 7.35, -0.25, 2.30, "O", "bracket outside rear wall", "AC"),
    ]
    c["ROOM-4 TOILET"] = [
        ("TSW", 4.45, 1.78, 1.2, "+x", "room side, beyond wardrobe", "L/F"),
        ("LT", 3.75, 1.40, CEIL, "C", "", "L/F"), ("EXH", 3.75, 0.15, 1.80, "+y", "in ventilator F-W3", "L/F"),
        ("GZP", 3.15, 1.45, 2.20, "+x", "", "GZ"),
        ("WC", 3.15, 1.15, 0.0, "+x", "on left wall", ""), ("HF", 3.15, 0.88, 0.45, "+x", "", ""),
        ("BAS", 3.15, 1.72, 0.80, "+x", "compact basin near door", ""), ("SHM", 4.35, 0.48, 1.0, "-x", "shower zone y 0.15-0.80", ""),
        ("FT", 3.75, 0.45, 0.0, "F", "", ""), ("GZ", 3.15, 1.15, 1.85, "+x", "above WC", ""),
    ]
    c["LOBBY"] = [
        ("DB", 5.60, 5.07, 1.75, "-x", "on stair wall, lobby side", ""), ("RISER", 5.55, 5.50, 0.0, "-x", "full height", ""),
        ("LT", 3.85, 5.85, CEIL, "C", "motion sensor", "COMMON"), ("LT", 4.95, 5.85, CEIL, "C", "motion sensor", "COMMON"),
        ("AP", 4.40, 5.30, CEIL, "C", "", "COMMON"), ("CCTV", 3.35, 6.80, CEIL - 0.1, "C", "views lift and stair", "COMMON"),
        ("DISP", 4.255, 6.775, 0.0, "F", "floor footprint x 4.08-4.43, y 6.60-6.95 (amenity: drinking water)", "COMMON"),
        ("SKT16", 4.25, 6.95, 1.20, "-y", "for water dispenser", "COMMON"),
    ]
    c["STAIR"] = [
        ("WL", 7.85, 6.40, 2.30, "-x", "floor landing", "COMMON"), ("WL", 6.80, 3.10, 1.5 + 2.2, "+y", "mid-landing", "COMMON"),
    ]
    return c


def rooms_F4(s):
    c = {}
    c["ROOM-1"] = [
        ("SB", 5.78, 7.05, 1.2, "+y", "latch side of F4-D1", "L/F"),
        ("FAN", 5.95, 7.865, CEIL, "C", "", "L/F"), ("LT", 6.95, 7.865, CEIL, "C", "", "L/F"), ("LT", 6.60, 9.70, CEIL, "C", "front part", "L/F"),
        ("ACI", 6.60, 10.70, 2.40, "-y", "above front window", "AC"), ("ACS", 7.20, 10.70, 2.35, "-y", "", "AC"),
        ("ACO", 6.60, 11.10, 0.10, "O", "on F4 front terrace floor", "AC"),
    ]
    c["ROOM-1 TOILET"] = [
        ("TSW", 5.35, 8.95, 1.2, "+x", "", "L/F"), ("LT", 4.65, 9.40, CEIL, "C", "", "L/F"), ("EXH", 4.65, 10.70, 1.80, "-y", "in ventilator F4-W5", "L/F"),
        ("GZP", 4.05, 9.40, 2.20, "+x", "", "GZ"), ("WC", 4.05, 9.70, 0.0, "+x", "", ""), ("HF", 4.05, 9.98, 0.45, "+x", "", ""),
        ("BAS", 4.05, 9.12, 0.80, "+x", "", ""), ("SHM", 5.25, 10.40, 1.0, "-x", "shower zone y 10.05-10.70", ""),
        ("FT", 4.65, 10.40, 0.0, "F", "", ""), ("GZ", 4.05, 9.70, 1.85, "+x", "above WC", ""),
    ]
    c["ROOM-2"] = [
        ("SB", 3.25, 7.05, 1.2, "+y", "latch side of F4-D2", "L/F"),
        ("FAN", 2.05, 7.865, CEIL, "C", "", "L/F"), ("LT", 1.05, 7.865, CEIL, "C", "", "L/F"), ("LT", 1.40, 9.70, CEIL, "C", "", "L/F"),
        ("LT", 1.60, 6.55, CEIL, "C", "entry strip", "L/F"),
        ("ACI", 1.40, 10.70, 2.40, "-y", "above front window", "AC"), ("ACS", 0.80, 10.70, 2.35, "-y", "", "AC"),
        ("ACO", 1.40, 11.10, 0.10, "O", "on F4 front terrace floor", "AC"),
    ]
    c["ROOM-2 TOILET"] = [
        ("TSW", 2.65, 8.95, 1.2, "-x", "", "L/F"), ("LT", 3.35, 9.40, CEIL, "C", "", "L/F"), ("EXH", 3.35, 10.70, 1.80, "-y", "in ventilator F4-W4", "L/F"),
        ("GZP", 3.95, 9.40, 2.20, "-x", "", "GZ"), ("WC", 3.95, 9.70, 0.0, "-x", "", ""), ("HF", 3.95, 9.98, 0.45, "-x", "", ""),
        ("BAS", 3.95, 9.12, 0.80, "-x", "", ""), ("SHM", 2.75, 10.40, 1.0, "+x", "", ""),
        ("FT", 3.35, 10.40, 0.0, "F", "", ""), ("GZ", 3.95, 9.70, 1.85, "-x", "above WC", ""),
    ]
    c["ROOM-3 (suite)"] = [
        ("SB", 4.05, 4.92, 1.2, "-x", "hinge-side wall just beyond the open leaf of F4-D3 (latch-side wall holds the wardrobes)", "L/F"),
        ("FAN", 2.10, 3.05, CEIL, "C", "", "L/F"), ("LT", 2.10, 1.30, CEIL, "C", "", "L/F"), ("LT", 2.10, 4.80, CEIL, "C", "", "L/F"),
        ("LT", 4.90, 2.58, CEIL, "C", "terrace passage", "L/F"),
        ("ACI", 0.75, 0.15, 2.40, "+y", "solid wall left of window", "AC"), ("ACS", 1.27, 0.15, 2.35, "+y", "", "AC"),
        ("ACO", 7.40, 0.40, 0.10, "O", "on private terrace floor", "AC"),
        ("WL", 5.75, 1.20, 2.30, "+x", "private terrace light", "L/F"), ("WPS", 5.75, 1.60, 0.45, "+x", "private terrace", "S"),
    ]
    c["ROOM-3 TOILET"] = [
        ("TSW", 5.08, 2.20, 1.2, "+y", "passage side", "L/F"), ("LT", 4.90, 1.40, CEIL, "C", "", "L/F"),
        ("EXH", 4.90, 0.15, 1.80, "+y", "in ventilator F4-W2", "L/F"), ("GZP", 4.15, 1.15, 2.20, "+x", "", "GZ"),
        ("WC", 4.15, 0.80, 0.0, "+x", "on left wall", ""), ("HF", 4.15, 1.10, 0.45, "+x", "", ""),
        ("BAS", 5.65, 1.60, 0.80, "-x", "", ""), ("SHM", 5.65, 0.60, 1.0, "-x", "shower zone x 5.00-5.65, y 0.15-1.20", ""),
        ("FT", 5.30, 0.60, 0.0, "F", "", ""), ("GZ", 4.15, 0.80, 1.85, "+x", "above WC", ""),
    ]
    c["LOBBY"] = [
        ("DB", 5.60, 5.07, 1.75, "-x", "", ""), ("RISER", 5.55, 5.50, 0.0, "-x", "", ""),
        ("LT", 4.85, 5.40, CEIL, "C", "motion sensor", "COMMON"), ("LT", 3.70, 6.50, CEIL, "C", "motion sensor", "COMMON"),
        ("AP", 4.85, 6.30, CEIL, "C", "", "COMMON"), ("CCTV", 3.30, 6.80, CEIL - 0.1, "C", "", "COMMON"),
    ]
    c["STAIR"] = [("WL", 7.85, 6.40, 2.30, "-x", "", "COMMON"), ("WL", 6.80, 3.10, 3.70, "+y", "mid-landing", "COMMON")]
    c["FRONT TERRACE"] = [("WL", 4.00, 10.85, 2.30, "+y", "on F4 front wall", "COMMON"), ("RWO", 2.40, 11.40, 0.0, "F", "cast in F4 terrace slab", "")]
    return c


def rooms_GF():
    s = "GF"
    c = {}
    c["METER NICHE"] = [
        ("MB", 4.05, 5.30, 1.20, "-x", "in grey niche (Q9), road-accessible", ""), ("MDB", 4.05, 5.90, 1.20, "-x", "", ""),
        ("CDB", 4.05, 6.50, 1.40, "-x", "", ""),
        ("INV", 4.05, 3.60, 0.90, "-x", "wall-mounted in grey niche, ventilated (amenity: power backup)", "BACKUP"),
    ]
    c["LIFT LOBBY"] = [("RFID", 5.65, 7.05, 1.20, "+y", "stilt side, beside lobby entry (amenity: RFID access)", "BACKUP"),
                       ("MLOCK", 4.80, 7.05, 2.15, "O", "on entry door head / header (entry ASSUMED, Q8)", "BACKUP"),
                       ("RISER", 5.55, 5.50, 0.0, "-x", "riser start", ""), ("LT", 4.88, 5.90, CEIL, "C", "", "COMMON"),
                       ("CCTV", 4.30, 6.90, CEIL - 0.1, "C", "", "COMMON")]
    c["STAIR"] = [("WL", 7.85, 6.40, 2.30, "-x", "", "COMMON"), ("WL", 6.80, 3.10, 3.70, "+y", "", "COMMON")]
    c["STILT (parking)"] = [
        ("LT", 2.00, 2.00, CEIL, "C", "", "COMMON"), ("LT", 2.00, 5.50, CEIL, "C", "", "COMMON"), ("LT", 2.00, 9.00, CEIL, "C", "", "COMMON"),
        ("LT", 5.80, 9.00, CEIL, "C", "", "COMMON"), ("CCTV", 0.40, 11.40, CEIL - 0.1, "C", "covers stilt", "COMMON"),
        ("CCTV", 3.90, 0.40, CEIL - 0.1, "C", "covers rear stilt", "COMMON"),
        ("SKT16", 0.15, 6.00, 0.45, "+x", "car-wash / service socket", "COMMON"),
    ]
    c["SERVANT ROOM"] = [("SB", 6.92, 2.95, 1.2, "-y", "latch side of GF-D3", "COMMON"), ("FAN", 6.80, 2.05, CEIL, "C", "", "COMMON"),
                         ("LT", 6.25, 1.55, CEIL, "C", "", "COMMON"), ("SKT16", 5.75, 2.20, 0.40, "+x", "", "COMMON")]
    c["SERVANT VESTIBULE"] = [("LT", 7.15, 0.65, CEIL, "C", "", "COMMON"), ("BAS", 7.15, 0.15, 0.80, "+y", "under ventilator", ""),
                              ("FT", 7.15, 0.80, 0.0, "F", "", ""), ("TSW", 6.45, 0.27, 1.2, "+x", "for WC-2", "COMMON")]
    c["WC-1"] = [("TSW", 4.05, 1.30, 1.2, "-x", "outside WC-1, stilt side", "COMMON"), ("LT", 4.60, 0.60, CEIL, "C", "", "COMMON"),
                 ("EXH", 4.60, 0.15, 1.80, "+y", "in ventilator GF-W1", "COMMON"), ("WC", 4.60, 0.15, 0.0, "+y", "", ""),
                 ("HF", 4.95, 0.15, 0.45, "+y", "", ""), ("FT", 4.60, 0.90, 0.0, "F", "", "")]
    c["WC-2"] = [("LT", 5.75, 0.60, CEIL, "C", "", "COMMON"), ("EXH", 5.75, 0.15, 1.80, "+y", "in ventilator GF-W2", "COMMON"),
                 ("WC", 5.75, 0.15, 0.0, "+y", "", ""), ("HF", 6.10, 0.15, 0.45, "+y", "", ""), ("FT", 5.75, 0.90, 0.0, "F", "", "")]
    c["PANTRY"] = [("LT", 4.90, 2.05, CEIL, "C", "", "COMMON"), ("SKT16", 5.65, 1.45, 1.10, "-x", "fridge", "COMMON"),
                   ("SKT16", 5.65, 2.25, 1.10, "-x", "microwave / induction", "COMMON"), ("SINK", 5.35, 2.95, 0.85, "-y", "", ""),
                   ("FT", 5.35, 2.55, 0.0, "F", "under sink", ""), ("RO", 5.65, 2.65, 1.40, "-x", "RO drinking water (amenity)", "COMMON")]
    c["FRONT MARGIN"] = [
        ("PUMP", 6.55, 12.10, 0.0, "F", "on U.G. tank roof slab, front margin", ""), ("PUMP", 7.15, 12.10, 0.0, "F", "standby", ""),
        ("PUMPP", 7.85, 12.20, 1.20, "-x", "on compound wall", "COMMON"), ("METER", 6.00, 12.60, 0.30, "-y", "municipal inlet", ""),
        ("TCON", 6.80, 12.40, -0.15, "F", "U.G. inlet (ball valve)", ""), ("TCON", 6.55, 11.90, -0.15, "F", "U.G. pump suction", ""),
        ("TCON", 7.60, 12.40, -0.40, "F", "U.G. overflow", ""), ("IC", 4.00, 12.25, -0.30, "F", "front IC, to municipal sewer", ""),
        ("IC", 3.20, -0.30, -0.30, "F", "rear IC (rear margin)", ""),
        ("CCTV", 5.60, 12.60, 2.20, "-y", "gate camera on compound wall", "COMMON"), ("WL", 2.30, 12.60, 2.00, "-y", "gate light", "COMMON"),
        ("WL", 1.50, 11.80, 2.90, "O", "name-board / signage light under F1 slab edge", "COMMON"),
    ]
    # GF ceiling points sit at the F1 slab soffit; GF z relative to GF FFL
    return c


def rooms_TERRACE():
    c = {}
    c["TERRACE"] = [
        ("WL", 6.80, 7.05, 2.30, "+y", "on stair cabin", "COMMON"), ("WL", 4.05, 3.80, 2.30, "-x", "on lift shaft", "COMMON"),
        ("WPS", 7.30, 7.05, 0.45, "+y", "", "COMMON"), ("CCTV", 7.80, 7.05, 2.60, "+y", "terrace", "COMMON"),
        ("LIFTISO", 4.20, 4.75, 1.50, "+y", "lift machine/controller supply (MRL assumed)", "LIFT"),
        ("WL", 7.85, 6.40, 2.30, "-x", "stair cabin", "COMMON"),
        ("WM", 3.75, 0.45, 0.0, "F", "terrace laundry, against rear parapet (amenity)", ""), ("WM", 4.40, 0.45, 0.0, "F", "terrace laundry", ""),
        ("TAP", 3.75, 0.15, 0.95, "+y", "washing machine inlet", ""), ("TAP", 4.40, 0.15, 0.95, "+y", "washing machine inlet", ""),
        ("WPS", 4.08, 0.15, 1.20, "+y", "washing machines (2 x 16A)", "COMMON"), ("FT", 4.08, 0.90, 0.0, "F", "laundry floor trap -> W1 (kerbed area)", ""),
        ("SINK", 5.10, 0.15, 0.80, "+y", "cleaner's sink (IS 1172 Table 11 vi) at terrace laundry", ""), ("TAP", 5.10, 0.15, 1.05, "+y", "cleaner's sink", ""),
        ("WL", 4.00, 0.15, 2.00, "+y", "laundry light on parapet", "COMMON"),
        ("WL", 0.15, 4.50, 1.00, "+x", "terrace lounge bollard/parapet light", "COMMON"), ("WL", 0.15, 8.00, 1.00, "+x", "terrace lounge light", "COMMON"),
        ("WPS", 0.15, 6.20, 0.45, "+x", "terrace lounge (study / gaming)", "COMMON"), ("WPS", 4.05, 4.20, 0.45, "-x", "terrace lounge", "COMMON"),
        ("AP", 5.60, 5.20, 2.30, "-x", "outdoor Wi-Fi AP for terrace lounge", "COMMON"),
        ("RWO", 0.40, 0.40, 0.0, "F", "roof outlet, cast in", ""), ("RWO", 0.45, 10.40, 0.0, "F", "roof outlet, cast in", ""),
        ("RWO", 5.30, 10.40, 0.0, "F", "roof outlet, cast in", ""), ("RWO", 7.60, 0.40, -3.0, "F", "F4 private terrace outlet, cast in F4 slab", ""),
        ("TCON", 7.60, 6.85, CABIN_TOP - FFL["TERRACE"] + 1.80, "F", "O.H.T. inlet (rising main)", ""),
        ("TCON", 6.00, 4.85, CABIN_TOP - FFL["TERRACE"] + 0.20, "F", "O.H.T. outlet (down-take header)", ""),
        ("TCON", 7.75, 5.20, CABIN_TOP - FFL["TERRACE"] + 1.60, "F", "O.H.T. overflow", ""),
    ]
    return c


LAYOUT = {}
for s in ["F1", "F2", "F3"]:
    LAYOUT[s] = rooms_F13(s)
LAYOUT["F4"] = rooms_F4("F4")
LAYOUT["GF"] = rooms_GF()
LAYOUT["TERRACE"] = rooms_TERRACE()
# bedside, desk and data points follow the fitted furniture (model/furniture.json)
FWALLS = {pk: TK["floors"][pk]["walls"] for pk in ("F1-3", "F4")}


def touches(ax, c, a0, a1, ws):
    for w in ws:
        if ax == "x" and (abs(w[0] - c) < 0.011 or abs(w[2] - c) < 0.011) and w[1] <= a0 + 0.01 and w[3] >= a1 - 0.01:
            return True
        if ax == "y" and (abs(w[1] - c) < 0.011 or abs(w[3] - c) < 0.011) and w[0] <= a0 + 0.01 and w[2] >= a1 - 0.01:
            return True
    return False


for s in ["F1", "F2", "F3", "F4"]:
    pk = "F1-3" if s != "F4" else "F4"
    for room, items in FU[pk].items():
        for it in items:
            r = it["rect"]
            if it["type"].endswith("_bed"):
                long_x = (r[2] - r[0]) > (r[3] - r[1])
                ws = FWALLS[pk]
                head_x = touches("x", r[2], r[1], r[3], ws) or touches("x", r[0], r[1], r[3], ws)
                head_y = touches("y", r[3], r[0], r[2], ws) or touches("y", r[1], r[0], r[2], ws)
                if long_x and not head_x:          # long side against a wall: socket on that wall near the pillow end
                    wy, face = (r[1], "+y") if touches("y", r[1], r[0], r[2], ws) else (r[3], "-y")
                    LAYOUT[s][room].append(("BS", r[0] + 0.20, wy, 0.6, face, "bedside (long wall, above mattress)", "S"))
                elif not long_x and not head_y:
                    wx, face = (r[0], "+x") if touches("x", r[0], r[1], r[3], ws) else (r[2], "-x")
                    LAYOUT[s][room].append(("BS", wx, r[1] + 0.20, 0.6, face, "bedside (long wall, above mattress)", "S"))
                elif long_x:
                    hx, face = (r[2], "-x") if touches("x", r[2], r[1], r[3], ws) else (r[0], "+x")
                    for side in it["access"]:
                        y = r[1] - 0.15 if side == "N" else r[3] + 0.15
                        if not touches("x", hx, y - 0.05, y + 0.05, ws):          # no wall beside the bed: on head wall above mattress
                            y = r[1] + 0.12 if side == "N" else r[3] - 0.12
                        LAYOUT[s][room].append(("BS", hx, y, 0.6, face, f"bedside ({side})", "S"))
                else:
                    hy, face = (r[3], "-y") if touches("y", r[3], r[0], r[2], ws) else (r[1], "+y")
                    for side in it["access"]:
                        x = r[0] - 0.15 if side == "W" else r[2] + 0.15
                        if not touches("y", hy, x - 0.05, x + 0.05, ws):
                            x = r[0] + 0.12 if side == "W" else r[2] - 0.12
                        LAYOUT[s][room].append(("BS", x, hy, 0.6, face, f"bedside ({side})", "S"))
            if it["type"].endswith("desk"):
                side = it["access"][0]
                cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
                zd, note = 0.9, "above desk"
                if side in ("N", "S"):
                    wy, face = (r[3], "-y") if side == "N" else (r[1], "+y")
                    for wdw in TK["floors"][pk]["windows"]:
                        wyy = 0.15 if wdw["wall"] == "rear" else TK["floors"][pk]["outline"][3] - 0.15
                        if abs(wyy - wy) < 0.05 and wdw["span_x"][0] - 0.2 < cx < wdw["span_x"][1] + 0.2:
                            zd, note = 0.30, "desk under window: socket below desk + desk-top grommet power module"
                    LAYOUT[s][room] += [("DESK", cx - 0.15, wy, zd, face, note, "S"), ("DATA", cx + 0.15, wy, zd, face, note, "DATA")]
                else:
                    wx, face = (r[2], "-x") if side == "W" else (r[0], "+x")
                    LAYOUT[s][room] += [("DESK", wx, cy - 0.15, zd, face, note, "S"), ("DATA", wx, cy + 0.15, zd, face, note, "DATA")]

RLOCK = {"F1-3": {"ROOM-1": (5.45, 7.00), "ROOM-2": (3.10, 6.90), "ROOM-3": (3.10, 4.55), "ROOM-4": (3.20, 4.50)},
         "F4": {"ROOM-1": (5.45, 7.00), "ROOM-2": (3.15, 6.90), "ROOM-3 (suite)": (3.20, 6.05)}}
for s in ["F1", "F2", "F3", "F4"]:
    for room, (x, y) in RLOCK["F1-3" if s != "F4" else "F4"].items():
        LAYOUT[s][room].append(("RFIDL", x, y, 1.00, "O", "latch edge of room door (battery lock, amenity)", ""))

for s, rooms in LAYOUT.items():
    for room, items in rooms.items():
        for it in items:
            kind, x, y, z, face, note, circ = it
            P(kind, s, room, x, y, z, face, note, circ)

# ===================================================================== risers, stacks and main runs
Z = lambda s, dz=0.0: FFL[s] + dz
TOP = FFL["TERRACE"]
# electrical: service cable, MDB -> riser, riser up through every slab, feeders
R("FEED", "GF", "MSEDCL service cable (underground) road -> meter board", [[3.80, 12.75, -0.6], [3.80, 7.10, -0.6], [3.80, 5.30, -0.6], [3.80, 5.30, Z("GF", 0.9)]])
R("FEED", "GF", "MDB -> riser (GF lobby ceiling)", [[4.05, 5.90, Z("GF", 2.0)], [4.05, 5.90, Z("GF", 2.7)], [5.55, 5.90, Z("GF", 2.7)], [5.55, 5.50, Z("GF", 2.7)]])
R("FEED", "GF", "Electrical riser GF -> terrace", [[5.55, 5.50, Z("GF", 0.0)], [5.55, 5.50, TOP + 2.2]])
R("FEED", "TERRACE", "Lift supply riser -> lift isolator", [[5.55, 5.50, TOP + 1.8], [4.60, 5.50, TOP + 1.8], [4.60, 4.80, TOP + 1.8], [4.20, 4.80, TOP + 1.5]])
R("FEED", "GF", "CDB -> pump panel (underground)", [[4.05, 6.50, Z("GF", 0.9)], [3.80, 6.50, -0.5], [3.80, 12.20, -0.5], [7.80, 12.20, -0.5], [7.80, 12.20, 1.2]])

# plumbing stacks: rear S1 (x 3.10) / W1 (x 3.30) / DT-R (x 2.95); front S2 (4.00) / W2 (4.20) / DT-F (3.80) with offset at F4
YR = -0.10                       # rear stacks, outside rear wall
YF, YF4 = 11.85, 10.95           # front stacks outside F3 front wall, and outside F4 front wall
zoff = Z("F4", 0.35)             # offset level on F4 front terrace
VTOP = TOP + 2.0                 # vent termination ASSUMED 2.0 m above terrace floor (terrace is used)
R("SOIL", "GF", "Soil stack S1 (rear) + vent", [[3.10, YR, -0.3], [3.10, YR, VTOP]])
R("WASTE", "GF", "Waste stack W1 (rear) + vent", [[3.30, YR, -0.3], [3.30, YR, VTOP]])
R("SOIL", "GF", "Soil stack S2 (front) with offset at F4 + vent", [[4.00, YF, -0.3], [4.00, YF, zoff], [4.00, YF4, zoff], [4.00, YF4, VTOP]])
R("WASTE", "GF", "Waste stack W2 (front) with offset at F4 + vent", [[4.20, YF, -0.3], [4.20, YF, zoff], [4.20, YF4, zoff], [4.20, YF4, VTOP]])
R("UGD", "GF", "Underground drain rear IC -> front IC (under stilt)", [[3.20, -0.30, -0.6], [3.20, 12.25, -0.75], [4.00, 12.25, -0.75]])
R("UGD", "GF", "Front IC -> municipal sewer", [[4.00, 12.25, -0.75], [4.00, 13.50, -0.9]])
R("UGD", "GF", "GF WCs/pantry -> rear IC", [[5.75, 0.15, -0.3], [5.75, -0.30, -0.4], [3.20, -0.30, -0.6]])
# water supply
R("SUP", "GF", "Municipal supply -> U.G. tank inlet", [[6.00, 12.75, -0.3], [6.00, 12.40, -0.3], [6.80, 12.40, -0.15]])
RM = R("RM", "GF", "Rising main: pumps -> front facade -> F4 offset -> terrace -> O.H.T.",
       [[6.55, 12.10, 0.3], [7.60, 12.10, 0.3], [7.60, YF, 0.3], [7.60, YF, zoff], [7.60, YF4, zoff], [7.60, YF4, TOP + 0.3],
        [7.60, 7.15, TOP + 0.3], [7.60, 7.15, CABIN_TOP + 1.9], [7.60, 6.85, CABIN_TOP + 1.9]])
R("DT", "TERRACE", "O.H.T. outlet header on terrace -> rear and front down-takes",
  [[6.00, 4.85, CABIN_TOP + 0.2], [6.00, 4.65, CABIN_TOP + 0.2], [6.00, 4.65, TOP + 0.3], [3.80, 4.65, TOP + 0.3], [2.95, 4.65, TOP + 0.3], [2.95, 0.25, TOP + 0.3], [2.95, YR, TOP + 0.3]])
R("DT", "TERRACE", "header -> front down-take", [[3.80, 4.65, TOP + 0.3], [3.80, YF4, TOP + 0.3]])
R("DT", "F1", "Down-take DT-R (rear) F4 -> F1", [[2.95, YR, TOP + 0.3], [2.95, YR, Z("F1", 2.4)]])
R("DT", "F1", "Down-take DT-F (front) with F4 offset", [[3.80, YF4, TOP + 0.3], [3.80, YF4, Z("F4", 0.6)], [3.80, YF, Z("F4", 0.6)], [3.80, YF, Z("F1", 2.4)]])
R("WASTE", "TERRACE", "Terrace laundry floor trap + cleaner's sink -> W1 (through parapet sleeve)", [[5.10, 0.30, TOP + 0.5], [5.10, 0.30, TOP - 0.05], [4.08, 0.90, TOP - 0.05], [3.30, 0.90, TOP - 0.10], [3.30, YR, TOP - 0.15]])
R("CW", "TERRACE", "Laundry + cleaner's sink supply from O.H.T. header", [[2.95, 0.40, TOP + 0.3], [5.10, 0.40, TOP + 0.3], [5.10, 0.15, TOP + 1.05]])
R("RWP", "TERRACE", "RWP-1 rear-left corner", [[0.40, 0.40, TOP], [0.40, 0.25, TOP - 0.1], [0.08, 0.25, TOP - 0.1], [0.08, YR, TOP - 0.2], [0.08, YR, 0.0]])
R("RWP", "TERRACE", "RWP-2 front-left (offset at F4)", [[0.45, 10.40, TOP], [0.45, YF4, TOP - 0.2], [0.45, YF4, zoff], [0.45, YF, zoff], [0.45, YF, 0.0]])
R("RWP", "TERRACE", "RWP-3 roof + F4 front terrace", [[5.30, 10.40, TOP], [5.30, YF4, TOP - 0.2], [5.30, YF4, zoff + 0.2], [2.40, YF4, zoff + 0.2], [2.40, YF, zoff], [2.40, YF, 0.0]])
R("RWP", "F4", "RWP-4 private terrace", [[7.60, 0.40, Z("F4")], [7.75, 0.40, Z("F4") - 0.1], [7.75, YR, Z("F4") - 0.2], [7.75, YR, 0.0]])
R("VENT", "TERRACE", "Note: vent terminations 2.0 m above terrace floor (ASSUMED)", [[3.20, YR, VTOP], [3.20, YR, VTOP + 0.01]])

# ---- branch routes from fixtures (indicative): drainage in toilet sunk slab (ASSUMED 0.30 sunk), water at high level
SUNK = 0.30
STACKS = {"rear": {"SOIL": 3.10, "WASTE": 3.30, "DT": 2.95, "y": YR}, "front": {"SOIL": 4.00, "WASTE": 4.20, "DT": 3.80, "y": YF}}
for p in points:
    if p["sys"] != "P" or p["storey"] in ("GF", "TERRACE") or p["kind"] not in ("WC", "FT", "BAS", "SHM", "HF", "GZ"):
        continue
    s = p["storey"]
    front = p["y"] > 6
    st = dict(STACKS["front" if front else "rear"])
    if s == "F4" and front:
        st["y"] = YF4
    wall_y = (TK["floors"][PLAN_OF[s]]["outline"][3] - 0.15) if front else 0.15
    zf = FFL[s]
    if p["kind"] in ("WC", "FT"):
        sysn = "SOIL" if p["kind"] == "WC" else "WASTE"
        zr = zf - SUNK + 0.08
        R(sysn, s, f"{p['id']} branch -> {sysn} stack", [[p["x"], p["y"], zf], [p["x"], p["y"], zr], [p["x"], wall_y, zr],
                                                            [st[sysn], wall_y, zr], [st[sysn], st["y"], zr - 0.05]])
    if p["kind"] in ("WC", "BAS", "SHM", "HF", "GZ"):
        zr = zf + 2.40
        dt = st["DT"]
        R("CW", s, f"{p['id']} cold water", [[dt, st["y"], zr], [dt, wall_y, zr], [p["x"], wall_y, zr], [p["x"], p["y"], zr], [p["x"], p["y"], p["z"] + 0.1]])
    if p["kind"] == "SHM":
        g = next(q for q in points if q["storey"] == s and q["room"] == p["room"] and q["kind"] == "GZ")
        R("HW", s, f"{p['id']} hot water from geyser", [[g["x"], g["y"], g["z"]], [g["x"], g["y"], zf + 2.2], [p["x"], g["y"], zf + 2.2], [p["x"], p["y"], zf + 2.2], [p["x"], p["y"], p["z"] + 0.15]])
    if p["kind"] == "BAS":
        R("WASTE", s, f"{p['id']} basin waste -> floor trap", [[p["x"], p["y"], p["z"] - 0.3], [p["x"], p["y"], zf - 0.1]])

# ---- electrical conduits (indicative): DB -> ceiling (in slab above) -> point
for p in points:
    if p["sys"] != "E" or p["kind"] in ("MB", "MDB", "CDB", "DB", "RISER", "ACO", "PUMPP", "LIFTISO"):
        continue
    s = p["storey"]
    if s == "TERRACE" or p["room"] == "FRONT MARGIN":
        continue
    db = next(q for q in points if q["storey"] == s and q["kind"] in ("DB", "CDB"))
    zc = FFL[s] + CEIL - 0.02
    R("COND", s, f"{p['id']} conduit from {db['id']}", [[db["x"], db["y"], db["z"]], [db["x"] - 0.05, db["y"], zc], [db["x"] - 0.05, p["y"], zc],
                                                         [p["x"], p["y"], zc], [p["x"], p["y"], p["z"]]], "ASSUMED indicative route (slab-embedded)")

# ---- slab sleeves and cast-in items (must be fixed before each slab is cast)
SLEEVES = []
for s in ["F1", "F2", "F3", "F4", "TERRACE"]:
    SLEEVES.append((s, 5.52, 5.50, "Electrical riser sleeve 2 x 100 mm (or 300x150 opening) in slab", "slab"))
for s in ["F1", "F2", "F3", "F4"]:
    for t in [r for r in TK["floors"][PLAN_OF[s]]["spaces"] if "TOILET" in r["name"]]:
        r = t["rects"][0]
        SLEEVES.append((s, (r[0] + r[2]) / 2, (r[1] + r[3]) / 2, f"Toilet slab depression {SUNK*1000:.0f} mm for {t['name']} (floor trap + WC branch)", "sunk"))

NEXT = {"GF": "F1", "F1": "F2", "F2": "F3", "F3": "F4", "F4": "TERRACE"}
for p in [q for q in points if q["kind"] == "FAN"]:
    SLEEVES.append((NEXT[p["storey"]], p["x"], p["y"], f"Fan hook box for {p['storey']} {p['room']} (cast in this slab = its ceiling)", "fanbox"))
SLEEVES.append(("F4", 7.60, 0.40, "RWO in F4 private-terrace slab", "rwo"))
SLEEVES.append(("F4", 2.40, 11.40, "RWO in F4 front-terrace slab (F3 roof)", "rwo"))
for (x, y) in [(0.40, 0.40), (0.45, 10.40), (5.30, 10.40)]:
    SLEEVES.append(("TERRACE", x, y, "RWO in roof slab", "rwo"))
SLEEVES.append(("F4", 4.00, 11.70, "Parapet sleeve: soil stack S2 offset", "parapet"))
SLEEVES.append(("F4", 4.20, 11.70, "Parapet sleeve: waste stack W2 offset", "parapet"))
SLEEVES.append(("F4", 3.80, 11.70, "Parapet sleeve: down-take DT-F offset", "parapet"))
SLEEVES.append(("F4", 7.60, 11.70, "Parapet sleeve: rising main offset", "parapet"))
SLEEVES.append(("F4", 0.45, 11.70, "Parapet sleeve: RWP-2 offset", "parapet"))
SLEEVES.append(("F4", 2.40, 11.70, "Parapet sleeve: RWP-3 offset", "parapet"))
SLEEVES.append(("TERRACE", 3.30, 0.08, "Rear parapet sleeve: terrace laundry waste -> W1; kerb + slope for laundry area", "parapetT"))
SLEEVES.append(("TERRACE", 6.00, 4.85, "O.H.T. outlet puddle flange (tank base)", "tank"))
SLEEVES.append(("TERRACE", 7.60, 6.85, "O.H.T. inlet / overflow / drain puddle flanges (tank walls)", "tank"))
SLEEVES.append(("GF", 6.55, 11.90, "U.G. tank suction, inlet, overflow, manhole, puddle flanges", "tank"))
SLEEVES.append(("GF", 3.20, 6.00, "Underground drain + service cable ducts before GF slab-on-grade", "ground"))
SLEEVES.append(("GF", 4.90, 3.85, "Lift pit: sump/drain + pit light/socket conduit", "lift"))
for s, x, y, txt, cat in SLEEVES:
    z = FFL["F4"] + 0.35 if cat == "parapet" else (FFL["TERRACE"] + 0.05 if cat == "parapetT" else FFL.get(s, 0.0) - 0.075)
    P("SLV", s, cat, x, y, z - FFL.get(s, 0.0), "F", txt)

# ===================================================================== clash checks
walls = {s: TK["floors"][PLAN_OF[s]]["walls"] for s in PLAN_OF}
wins = {pk: fl.get("windows", []) for pk, fl in TK["floors"].items()}
opens = {pk: fl.get("openings", []) for pk, fl in TK["floors"].items()}
DOORS = AS["doors"]
FS = AS["furniture_sizes"]
H = AS["heights"]


def on_wall(p, ws):
    f, x, y = p["face"], p["x"], p["y"]
    for w in ws:
        if f == "+x" and abs(x - w[2]) < 0.03 and w[1] - 0.01 <= y <= w[3] + 0.01:
            return True
        if f == "-x" and abs(x - w[0]) < 0.03 and w[1] - 0.01 <= y <= w[3] + 0.01:
            return True
        if f == "+y" and abs(y - w[3]) < 0.03 and w[0] - 0.01 <= x <= w[2] + 0.01:
            return True
        if f == "-y" and abs(y - w[1]) < 0.03 and w[0] - 0.01 <= x <= w[2] + 0.01:
            return True
    return False


def window_clash(p, pk):
    out = []
    ylim = TK["floors"][pk]["outline"][3]
    for w in wins.get(pk, []):
        wy = 0.15 if w["wall"] == "rear" else ylim - 0.15
        if p["face"] in ("+y", "-y") and abs(p["y"] - wy) < 0.2:
            sill = H["ventilator_sill"] if w["width"] < H["ventilator_max_width"] else H["window_sill"]
            half = K[p["kind"]][3][0] / 2
            if w["span_x"][0] - half < p["x"] < w["span_x"][1] + half and sill - 0.05 < p["zrel"] < H["window_head"] + 0.05:
                if p["kind"] != "EXH":
                    out.append(f"inside window {w['id']}")
    return out


def door_clash(p, pk):
    out = []
    for d in DOORS.get(pk, []):
        hx, hy = d["hinge"]
        r = d["width"]
        qx, qy = d["quadrant"]
        dx, dy = p["x"] - hx, p["y"] - hy
        inq = (dx * qx >= -0.06) and (dy * qy >= -0.06)
        if inq and math.hypot(dx, dy) < r + 0.05 and p["zrel"] < H["door_head"] and p["face"] not in ("C", "F", "O"):
            out.append(f"behind/inside swing of {d['id']}")
    for o in opens.get(pk, []):
        a = o.get("span_x") or o.get("span_y")
        coord = p["x"] if "span_x" in o else p["y"]
        import re
        nums = [float(v) for v in re.findall(r"[\d.]+", o["wall"])]
        other = p["y"] if "span_x" in o else p["x"]
        if a[0] + 0.01 < coord < a[1] - 0.01 and nums and min(nums) - 0.08 <= other <= max(nums) + 0.08 and p["zrel"] < H["door_head"] and p["face"] not in ("C", "F", "O"):
            out.append(f"in door opening {o['id']}")
    return out


def furniture_clash(p, pk):
    out = []
    for room, items in FU.get(pk, {}).items():
        if room.startswith("_"):
            continue
        for it in items:
            r = it["rect"]
            hgt = FS[it["type"]][2]
            if p["kind"] in ("DESK", "DATA") and it["type"].endswith("desk") and "under window" in p["note"]:
                continue
            if r[0] - 0.05 <= p["x"] <= r[2] + 0.05 and r[1] - 0.05 <= p["y"] <= r[3] + 0.05 and p["zrel"] < hgt + 0.05 and p["face"] not in ("C",):
                out.append(f"hidden by {it['type']} in {room}")
    return out


def dist_to_walls(x, y, ws):
    best = 9
    for w in ws:
        dx = max(w[0] - x, 0, x - w[2])
        dy = max(w[1] - y, 0, y - w[3])
        best = min(best, math.hypot(dx, dy))
    return best


rows, warns, nclash = [], [], 0
for p in points:
    s, pk = p["storey"], PLAN_OF.get(p["storey"], "GF")
    issues = []
    if p["face"] in ("+x", "-x", "+y", "-y") and p["kind"] not in ("RISER",):
        ws = walls[s] if s != "GF" else walls["GF"]
        if p["room"] == "FRONT MARGIN":
            ws = ws + [[0, 11.75, 0.15, 12.75], [7.85, 11.75, 8.0, 12.75], [0, 12.6, 2.5, 12.75], [5.5, 12.6, 8.0, 12.75]]
        if not on_wall(p, ws):
            issues.append("not on a drawn wall face")
        issues += window_clash(p, pk)
        issues += door_clash(p, pk)
        issues += furniture_clash(p, pk)
    if p["face"] == "C" and p["kind"] in ("LT", "FAN", "AP", "CCTV"):
        d = dist_to_walls(p["x"], p["y"], walls[s])
        if d < 0.15:
            warns.append(f"{p['id']} ({p['room']}) ceiling point {d:.2f} m from a wall line - probable beam zone, SE to confirm")
        if p["kind"] == "FAN" and d < 0.6 + 0.15:
            issues.append(f"fan sweep (r 0.60) only {d-0.6:.2f} m from wall")
    if p["kind"] == "GZP":
        sh = next((q for q in points if q["storey"] == s and q["room"] == p["room"] and q["kind"] in ("SHM",)), None)
        ft = next((q for q in points if q["storey"] == s and q["room"] == p["room"] and q["kind"] == "FT"), None)
        if ft and math.hypot(p["x"] - ft["x"], p["y"] - ft["y"]) < 0.6:
            issues.append("geyser point < 0.6 m (plan) from shower floor trap")
    if issues:
        nclash += len(issues)
        rows.append(f"| {p['id']} | {p['room']} | {K[p['kind']][2]} | {'; '.join(issues)} |")
    p["issues"] = issues

# stacks / RWPs vs windows on facades
stack_rows = []
for nm, x, face in [("S1", 3.10, "rear"), ("W1", 3.30, "rear"), ("DT-R", 2.95, "rear"), ("RWP-1", 0.08, "rear"), ("RWP-4", 7.75, "rear"),
                    ("S2", 4.00, "front"), ("W2", 4.20, "front"), ("DT-F", 3.80, "front"), ("RM", 7.60, "front"), ("RWP-2", 0.45, "front"), ("RWP-3", 2.40, "front")]:
    hits = []
    for pk in ("GF", "F1-3", "F4"):
        for w in wins[pk]:
            if w["wall"] == face and w["span_x"][0] - 0.10 < x < w["span_x"][1] + 0.10:
                hits.append(f"{pk} {w['id']}")
    stack_rows.append(f"| {nm} | {face} | x = {x:.2f} | {'PASS' if not hits else 'CLASH with ' + ', '.join(hits)} |")
    nclash += len(hits)
# sleeves near probable beams
slv_rows = []
for p in points:
    if p["kind"] == "SLV" and p["room"] in ("slab", "rwo", "tank"):
        d = dist_to_walls(p["x"], p["y"], walls[p["storey"]])
        flag = "probable beam zone (<0.15 m from wall line) - SE to confirm" if d < 0.15 else "clear of wall lines"
        slv_rows.append(f"| {p['id']} | {p['note']} | ({p['x']:.2f}, {p['y']:.2f}) | {d:.2f} | {flag} |")

# ===================================================================== quantities, loads, water
cnt = defaultdict(Counter)
for p in points:
    cnt[p["storey"]][p["kind"]] += 1
runlen = defaultdict(float)
for r in runs:
    runlen[r["sys"]] += length(r)
WASTAGE = 1.10
water_beds = sum((3 if pk == 'F1-3' else 1) * sum(1 for it in items if it['type'].endswith('_bed')) for pk in ('F1-3', 'F4') for items in FU[pk].values())
staff = 2

# electrical connected load (ASSUMED ratings, W)
RATE = {"DISP": 500, "INV": 0, "RFID": 10, "MLOCK": 10, "WM": 0, "RO": 60, "LT": 12, "WL": 12, "FAN": 50, "EXH": 30, "AP": 15, "CCTV": 8, "DESK": 200, "BS": 100, "SKT16": 1000, "WPS": 500,
        "ACS": 1600, "GZP": 2000}
conn = Counter()
for p in points:
    if p["kind"] in RATE:
        conn[p["storey"]] += RATE[p["kind"]]
lift_kw, pump_kw = 5.5, 1.5

# ===================================================================== outputs
(ROOT / "docs/schedules").mkdir(parents=True, exist_ok=True)
with open(ROOT / "docs/schedules/points_schedule.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["point_id", "storey", "room", "system", "item", "plan_x_m", "plan_y_m", "height_above_FFL_m", "mounting", "circuit", "note", "source_tag", "clash_check"])
    for p in points:
        w.writerow([p["id"], p["storey"], p["room"], {"E": "Electrical", "P": "Plumbing", "S": "Cast-in / sleeve"}[p["sys"]], K[p["kind"]][2], p["x"], p["y"],
                    p["zrel"], {"C": "ceiling", "F": "floor/slab", "O": "outside"}.get(p["face"], "wall " + p["face"]), p["circuit"], p["note"], p["tag"],
                    "PASS" if not p["issues"] else "; ".join(p["issues"])])
kinds = sorted({k for c in cnt.values() for k in c}, key=lambda k: (K[k][0], k))
storeys = ["GF", "F1", "F2", "F3", "F4", "TERRACE"]
with open(ROOT / "docs/schedules/quantities.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["system", "item"] + storeys + ["total"])
    for k in kinds:
        row = [cnt[s][k] for s in storeys]
        w.writerow([{"E": "Electrical", "P": "Plumbing", "S": "Cast-in"}[K[k][0]], K[k][2]] + row + [sum(row)])
    w.writerow([])
    w.writerow(["run", "description", "approx length m (route x 1.10, CALCULATED from ASSUMED routes)"])
    for sysn, L in sorted(runlen.items()):
        w.writerow([sysn, PIPE[sysn][3], round(L * WASTAGE, 1)])

mep = {"points": points, "runs": runs, "kinds": {k: {"sys": v[0], "layer": v[1], "desc": v[2], "size": v[3], "ifc": v[4]} for k, v in K.items()},
       "pipes": {k: {"layer": v[0], "dia": v[1], "col": v[2], "desc": v[3]} for k, v in PIPE.items()}}
(ROOT / "model/mep.json").write_text(json.dumps(mep, separators=(",", ":")))

tot = Counter()
for s in storeys:
    tot.update(cnt[s])
md = ["# MEP checks (Phase 3, generated by tools/build_mep.py)", "",
      f"Points: {len(points)} · runs: {len(runs)} · **hard clashes: {nclash}** · probable-beam warnings: {len(warns)}", "",
      "## Point clashes (walls, windows, door openings and swings, furniture, fan sweep, geyser vs shower)", "",
      "| Point | Room | Item | Issue |", "|---|---|---|---|"] + (rows or ["| - | - | - | none |"]) + [
      "", "## Stacks, down-takes, rising main and RWPs vs facade windows (all floors)", "", "| Pipe | Facade | Position | Result |", "|---|---|---|---|"] + stack_rows + [
      "", "## Slab sleeves and cast-in items vs probable beam lines", "",
      "No beams or columns are drawn. As a coordination proxy every wall line is treated as a probable beam line.", "",
      "| Id | Item | Plan (x, y) | Distance to wall line m | Result |", "|---|---|---|---|---|"] + slv_rows + [
      "", "## Ceiling points close to wall lines (probable beam zone)", ""] + ([f"- {w}" for w in warns] or ["- none"]) + [
      "", "## Not checkable", "", "- Columns: none drawn on the AFTER O.C. sheet, so no column clash check is possible (takeoff Q1).",
      "- Beams: not drawn; wall lines used as proxy (above)."]
(ROOT / "docs/mep-checks.md").write_text("\n".join(md) + "\n")

SLABNAME = {"GF": "Ground slab-on-grade / below ground", "F1": "F1 slab (ceiling of stilt)", "F2": "F2 slab (ceiling of F1)",
            "F3": "F3 slab (ceiling of F2)", "F4": "F4 slab (ceiling of F3, F4 terraces)", "TERRACE": "Roof slab (ceiling of F4)"}
pre = ["# Pre-slab checklist (generated by tools/build_mep.py)", "",
       "Everything below must be fixed, marked or cast in **before that slab is poured**. Positions are plan X/Y (m) as in the takeoff. "
       "All items are ASSUMED proposals: the structural engineer must approve every opening, sleeve, depression and cast-in item, "
       "and licensed electrical/plumbing consultants must confirm sizes.", ""]
for st in ["GF", "F1", "F2", "F3", "F4", "TERRACE"]:
    items = [q for q in points if q["kind"] == "SLV" and q["storey"] == st]
    below = {"F1": "GF", "F2": "F1", "F3": "F2", "F4": "F3", "TERRACE": "F4"}.get(st)
    ceil_pts = [q for q in points if below and q["storey"] == below and q["face"] == "C" and q["sys"] == "E"]
    pre += [f"## {SLABNAME[st]}", "", "| # | Item | Plan X, Y (m) | Category |", "|---|---|---|---|"]
    for i, q in enumerate(items, 1):
        pre.append(f"| {i} | {q['note']} | {q['x']:.2f}, {q['y']:.2f} | {q['room']} |")
    if ceil_pts:
        kc = Counter(K[q["kind"]][2] for q in ceil_pts)
        pre.append(f"| + | Embedded conduits + junction boxes for {len(ceil_pts)} ceiling points of {below}: " +
                   ", ".join(f"{v} x {k}" for k, v in kc.items()) + " (see points_schedule.csv) | various | conduit |")
    pre.append("")
pre += ["## Also before the relevant slab or wall work", "",
        "- Sleeves through external walls for AC copper/drain lines at each AC indoor unit (masonry, can be cored later but cheaper now).",
        "- Brackets/anchors for external stacks S1/W1 (rear, x 3.10/3.30) and S2/W2 (front, x 4.00/4.20), down-takes and rising main.",
        "- Lift: pit depth, shaft size and top overrun from the chosen lift maker before the pit and shaft are built (takeoff Q3)."]
(ROOT / "docs/pre-slab-checklist.md").write_text("\n".join(pre) + "\n")

summary = {"points": len(points), "runs": len(runs), "clashes": nclash, "warnings": len(warns), "totals": dict(tot),
           "run_lengths_m": {k: round(v * WASTAGE, 1) for k, v in runlen.items()},
           "connected_load_W": dict(conn), "lift_kW": lift_kw, "pump_kW": pump_kw,
           "water_demand_L_day": water_beds * 135 + staff * 135}
(ROOT / "model/mep_summary.json").write_text(json.dumps(summary, indent=1))
print(json.dumps({k: summary[k] for k in ("points", "runs", "clashes", "warnings", "run_lengths_m", "water_demand_L_day")}, indent=1))
print("\n".join(rows[:40]))
print("\n".join(stack_rows))
print("\n".join(warns[:20]))
