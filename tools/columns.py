"""Columns from the structural sheet (model/structure.json) for one floor, snapped to that floor's wall faces.

Positions were scaled off an undimensioned layout (about +/-0.02 m), so any column edge within 0.015 m of a
drawn wall face is snapped to it; otherwise the scaled value is kept. Floors F1 and up use the 230-wide size;
GF uses the 300-wide plinth-to-first-floor size.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAP = 0.015


def columns(pk):
    st = json.loads((ROOT / "model/structure.json").read_text())
    walls = json.loads((ROOT / "model/takeoff.json").read_text())["floors"][pk]["walls"]
    fx = sorted({w[i] for w in walls for i in (0, 2)})
    fy = sorted({w[i] for w in walls for i in (1, 3)})

    def snap(v, faces):
        f = min(faces, key=lambda q: abs(q - v))
        return f if abs(f - v) <= SNAP else round(v, 3)

    out = []
    for c in st["columns"]:
        r = c["plinth_to_F1_rect"] if pk == "GF" else c["upper_rect"]
        out.append({"name": c["name"], "size": c["size_below_F1"] if pk == "GF" else c["size_F1_up"],
                    "rect": [snap(r[0], fx), snap(r[1], fy), snap(r[2], fx), snap(r[3], fy)]})
    return out
