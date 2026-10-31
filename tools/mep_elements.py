"""Shared: convert model/mep.json into viewer/IFC elements."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def mep_elements():
    """Convert model/mep.json into viewer elements (points -> boxes, runs -> lines)."""
    mp = ROOT / "model/mep.json"
    if not mp.exists():
        return []
    M = json.loads(mp.read_text())
    out = []
    for p in M["points"]:
        k = M["kinds"][p["kind"]]
        w, d, h = k["size"]
        x, y, z, f = p["x"], p["y"], p["z"], p["face"]
        if f in ("+x", "-x"):
            b = [x, y - w / 2, z - h / 2, x + d, y + w / 2, z + h / 2] if f == "+x" else [x - d, y - w / 2, z - h / 2, x, y + w / 2, z + h / 2]
        elif f in ("+y", "-y"):
            b = [x - w / 2, y, z - h / 2, x + w / 2, y + d, z + h / 2] if f == "+y" else [x - w / 2, y - d, z - h / 2, x + w / 2, y, z + h / 2]
        elif f == "C":
            b = [x - w / 2, y - d / 2, z - h, x + w / 2, y + d / 2, z]
        elif f == "F":
            b = [x - w / 2, y - d / 2, z, x + w / 2, y + d / 2, z + max(h, 0.03)]
        else:
            b = [x - w / 2, y - d / 2, z - h / 2, x + w / 2, y + d / 2, z + h / 2]
        if p["kind"] == "RISER":
            b = [x - 0.05, y - 0.10, z, x + 0.05, y + 0.10, z + 2.85]
        layer = {"E": "elec", "P": "plumb", "S": "sleeve"}[p["sys"]]
        out.append({"cls": k["ifc"], "name": f"{p['id']} {k['desc']}" + (f" - {p['note']}" if p["note"] else ""), "storey": p["storey"],
                    "layer": layer, "boxes": [b], "tag": p["tag"] + (" | circuit " + p["circuit"] if p["circuit"] else "") +
                    (" | check: PASS" if not p.get("issues") else " | check: " + "; ".join(p["issues"])), "room": p["room"]})
    lay = {"SOIL": "drainL", "WASTE": "drainL", "VENT": "drainL", "RWP": "drainL", "UGD": "drainL", "CW": "waterL", "HW": "waterL",
           "DT": "waterL", "RM": "waterL", "SUP": "waterL", "FEED": "feedL", "COND": "condL"}
    col = {"SOIL": "8b4513", "WASTE": "d97706", "VENT": "9ca3af", "RWP": "16a34a", "UGD": "78350f", "CW": "2563eb", "HW": "dc2626",
           "DT": "1d4ed8", "RM": "7c3aed", "SUP": "0891b2", "FEED": "eab308", "COND": "fb923c"}
    for r in M["runs"]:
        out.append({"cls": "IfcPipeSegment" if r["sys"] not in ("FEED", "COND") else "IfcCableCarrierSegment",
                    "name": f"{M['pipes'][r['sys']]['desc']}: {r['name']}", "storey": r["storey"], "layer": lay[r["sys"]],
                    "line": r["pts"], "col": col[r["sys"]], "tag": r["tag"], "boxes": [], "dia": M["pipes"][r["sys"]]["dia"],
                    "span": any(k in r["name"] for k in ("stack", "riser", "Down-take", "Rising main", "RWP", "header"))})
    return out
