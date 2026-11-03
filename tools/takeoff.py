"""Load the drawing takeoff (model/takeoff.json, DRAWN) with the family-approved internal brick changes
(model/changes.json) applied. Every tool reads the plan through load_takeoff(); raw=True gives the
architect's drawing exactly as taken off (used to show what changed)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_takeoff(raw=False):
    tk = json.loads((ROOT / "model/takeoff.json").read_text())
    cf = ROOT / "model/changes.json"
    if raw or not cf.exists():
        return tk
    ch = json.loads(cf.read_text())
    for pk, c in ch.get("floors", {}).items():
        fl = tk["floors"][pk]
        rm = [list(w) for w in c.get("walls_remove", [])]
        fl["walls"] = [w for w in fl["walls"] if list(w) not in rm] + [list(w) for w in c.get("walls_add", [])]
        for sp in fl["spaces"]:
            if sp["name"] in c.get("spaces", {}):
                sp["rects"] = c["spaces"][sp["name"]]
        for op in fl.get("openings", []):
            new = c.get("openings", {}).get(op["id"])
            if new:
                op.clear()
                op.update(new)
    return tk
