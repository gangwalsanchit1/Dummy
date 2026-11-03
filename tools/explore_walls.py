"""Explore internal brick-wall / door changes on floor 1 (F1-3) and test whether each room takes the twin kit.
Usage: python3 tools/explore_walls.py <variant> <room> [<room> ...]   e.g. part6.95+d3low ROOM-3 ROOM-2
Only non-structural, non-wet changes: columns, lift walls, outer walls, windows and toilets are never touched."""
from pathlib import Path
import copy
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fit_furniture as F  # noqa: E402
import fit_floor1 as G  # noqa: E402

from takeoff import load_takeoff  # noqa: E402
TK0, AS0 = load_takeoff(raw=True), copy.deepcopy(F.AS)   # variants start from the architect's drawing (doors as in assumptions.json)
DOORS = {"ROOM-1": ("F-D1", ["F-D1T"]), "ROOM-2": ("F-D2", ["F-D2T"]), "ROOM-3": ("F-D3", ["F-D3T"]), "ROOM-4": ("F-D4", ["F-D4T"])}


def setdoor(AS, did, **kw):
    d = next(d for d in AS["doors"]["F1-3"] if d["id"] == did)
    d.update(kw)


def variant(name):
    TK, AS = copy.deepcopy(TK0), copy.deepcopy(AS0)
    fl = TK["floors"]["F1-3"]
    sp = {s["name"]: s for s in fl["spaces"]}

    def rm(*ws):
        fl["walls"] = [w for w in fl["walls"] if w not in [list(x) for x in ws]]

    for tok in name.split("+"):
        if tok == "asis":
            pass
        elif tok.startswith("part"):
            # ROOM-3/ROOM-2 partition moved towards the road to y=p; ROOM-2 door moved to the y=7.05 wall (x 3.15-3.95)
            p = float(tok[4:])
            rm([0.15, 5.95, 3.15, 6.05], [3.05, 5.4, 3.15, 6.05], [3.05, 6.95, 4.6, 7.05])
            fl["walls"] += [[0.15, p, 3.15, p + 0.10], [3.05, 5.4, 3.15, 6.95], [3.05, 6.95, 3.15, 7.05], [3.95, 6.95, 4.6, 7.05]]
            sp["ROOM-3"]["rects"] = [[0.15, 2.05, 3.05, p], [0.15, 0.15, 1.75, 2.05]]
            r2 = [r for r in sp["ROOM-2"]["rects"] if r[1] >= 7.0]
            if p + 0.10 < 7.0:
                r2.append([0.15, p + 0.10, 3.05, 7.05])
            sp["ROOM-2"]["rects"] = r2
            setdoor(AS, "F-D2", hinge=[3.15, 7.05], quadrant=[1, 1], leaf_axis="x", width=0.80)
        elif tok == "d3low":
            # ROOM-3 entry door slid to the lobby wall's far end (y 6.05-6.95), hinged at the new partition
            rm([3.05, 0.15, 3.15, 4.5], [3.05, 5.4, 3.15, 6.95])
            fl["walls"] += [[3.05, 0.15, 3.15, 6.05]]
            setdoor(AS, "F-D3", hinge=[3.05, 6.95], quadrant=[-1, -1], leaf_axis="y")
        elif tok == "t3door":
            # ROOM-3 toilet door moved from the room wall (y 2.05) to the alcove wall (x 1.75-1.85, y 1.30-1.95)
            rm([1.75, 0.15, 1.85, 2.05], [2.5, 1.95, 3.05, 2.05])
            fl["walls"] += [[1.75, 0.15, 1.85, 1.30], [1.75, 1.95, 3.05, 2.05]]
            setdoor(AS, "F-D3T", hinge=[1.85, 1.95], quadrant=[1, -1], leaf_axis="y")
        else:
            raise SystemExit("unknown variant " + tok)
    return TK, AS


def twin(room):
    beds = G.single_beds(room)
    pairs = G.twin_pairs(room, G.single_beds(room, own_table=False))
    w = G.wall_items(room, "twill_wardrobe", G.WFRONT)
    d = G.wall_items(room, "compact_desk", G.CHAIR)
    for tag, bs in (("beds apart, own Tinkers", [("bed", beds), ("bed", beds)]), ("shared Tinker", [("pair", pairs)])):
        f = G.search(room, bs + [("ward", w), ("ward", w), ("desk", d), ("desk", d)], max_walk=60000, want=6)
        if f:
            return tag, G.flatten(*max(f, key=lambda x: sum(p.get("score", 0) for p in x[0])))
    return None, None


if __name__ == "__main__":
    vname = sys.argv[1]
    TK, AS = variant(vname)
    F.TK, F.AS = TK, AS
    out = {}
    for rn in sys.argv[2:]:
        room = F.Room("F1-3", rn, *DOORS[rn])
        # a student must be able to walk up to each window of their room (target strip in front of it)
        for w in TK["floors"]["F1-3"]["windows"]:
            serves = w["serves"].split(" ")[0]
            if serves == rn and "toilet" not in w["serves"].lower():
                cx = (w["span_x"][0] + w["span_x"][1]) / 2 - 0.225
                y0 = 0.15 if w["wall"] == "rear" else 11.6 - 0.45
                room.targets_doors.append({"id": "window " + w["id"], "hinge": [cx, y0], "quadrant": [1, 1], "width": 0.45})
        tag, lay = twin(room)
        print(vname, rn, "TWIN FITS (" + tag + ")" if tag else "twin does not fit", flush=True)
        out[rn] = lay
    json.dump({"variant": vname, "TK": TK["floors"]["F1-3"], "doors": AS["doors"]["F1-3"], "layouts": out},
              open(f"var_{vname}.json", "w"))
