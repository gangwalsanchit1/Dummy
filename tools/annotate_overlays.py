#!/usr/bin/env python3
"""Draw the Phase-1 takeoff (model/takeoff.json) on top of the PDF linework
(docs/overlays/plan_geometry.json) so every takeoff wall/room/opening can be
checked visually against the architect's lines.

Output: docs/overlays/takeoff_<FLOOR>.svg  and prints room areas (CALCULATED).
Usage: python3 tools/annotate_overlays.py
"""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TK = json.loads((ROOT / "model/takeoff.json").read_text())
GEO = json.loads((ROOT / "docs/overlays/plan_geometry.json").read_text())
PAL = ["#fde68a", "#bfdbfe", "#bbf7d0", "#fecaca", "#ddd6fe", "#fbcfe8", "#a5f3fc", "#fed7aa", "#d9f99d", "#e9d5ff"]
SRC = {"wall": "#222", "window": "#16a34a", "opening/door": "#ca8a04", "stair treads": "#f97316",
       "tank": "#ec4899", "OHT cross": "#a855f7", "grey": "#666", "pink2": "#f472b6"}


def area(rects):
    return sum((r[2] - r[0]) * (r[3] - r[1]) for r in rects)


def main():
    out = []
    for fk, fl in TK["floors"].items():
        x0, y0, w, h = -0.8, -1.0, 9.6, 14.6
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {w} {h}" width="{w*110:.0f}" '
             f'height="{h*110:.0f}" font-family="Arial"><rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#fff"/>']
        for g in range(0, 14):
            s.append(f'<line x1="-0.3" y1="{g}" x2="8.3" y2="{g}" stroke="#e0ecff" stroke-width="0.006"/>'
                     f'<text x="-0.35" y="{g+0.05}" font-size="0.15" fill="#60a5fa" text-anchor="end">{g}</text>')
        for g in range(0, 9):
            s.append(f'<line x1="{g}" y1="-0.3" x2="{g}" y2="13.0" stroke="#e0ecff" stroke-width="0.006"/>'
                     f'<text x="{g}" y="-0.4" font-size="0.15" fill="#60a5fa" text-anchor="middle">{g}</text>')
        # rooms (tinted)
        for i, sp in enumerate(fl.get("spaces", [])):
            for r in sp["rects"]:
                s.append(f'<rect x="{r[0]}" y="{r[1]}" width="{r[2]-r[0]:.3f}" height="{r[3]-r[1]:.3f}" '
                         f'fill="{PAL[i % len(PAL)]}" opacity="0.55"/>')
        # takeoff walls (translucent red fill) under the source linework
        for r in fl["walls"] + fl.get("railings", []):
            s.append(f'<rect x="{r[0]}" y="{r[1]}" width="{r[2]-r[0]:.3f}" height="{r[3]-r[1]:.3f}" fill="#ef4444" opacity="0.45"/>')
        for g in fl.get("grey_items", []):
            r = g["rect"]
            s.append(f'<rect x="{r[0]}" y="{r[1]}" width="{r[2]-r[0]:.3f}" height="{r[3]-r[1]:.3f}" fill="none" '
                     f'stroke="#6b7280" stroke-width="0.02" stroke-dasharray="0.08 0.05"/>')
        # source PDF linework
        for seg in GEO[fk]["segments"]:
            col = SRC.get(seg["layer"])
            if not col:
                continue
            d = " ".join(f'{"M" if i == 0 else "L"}{a:.3f},{b:.3f}' for i, (a, b) in enumerate(seg["pts"]))
            s.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="0.012"/>')
        # openings / windows markers
        for o in fl.get("openings", []) + fl.get("windows", []):
            is_win = "serves" in o
            if "span_x" in o:
                a, b = o["span_x"]
                wy = 0.075 if o.get("wall") == "rear" else None
                if wy is None:
                    import re
                    m = re.findall(r"[\d.]+", o["wall"])
                    wy = (sum(map(float, m)) / len(m)) if m else (fl["outline"][3] - 0.075)
                    if o.get("wall") == "front":
                        wy = fl["outline"][3] - 0.075
                s.append(f'<line x1="{a}" y1="{wy}" x2="{b}" y2="{wy}" stroke="{"#16a34a" if is_win else "#2563eb"}" stroke-width="0.07" opacity="0.8"/>')
                tx, ty = (a + b) / 2, wy
            else:
                a, b = o["span_y"]
                import re
                m = re.findall(r"[\d.]+", o["wall"])
                wx = sum(map(float, m)) / len(m)
                s.append(f'<line x1="{wx}" y1="{a}" x2="{wx}" y2="{b}" stroke="#2563eb" stroke-width="0.07" opacity="0.8"/>')
                tx, ty = wx, (a + b) / 2
            s.append(f'<text x="{tx}" y="{ty-0.09}" font-size="0.12" fill="{"#166534" if is_win else "#1e3a8a"}" '
                     f'text-anchor="middle" font-weight="bold">{escape(o["id"])} {o["width"]:.2f}</text>')
        # room names + measured sizes
        print(f"== {fk}")
        for sp in fl.get("spaces", []):
            r = max(sp["rects"], key=lambda q: (q[2]-q[0])*(q[3]-q[1]))
            cx, cy = (r[0]+r[2])/2, (r[1]+r[3])/2
            A = area(sp["rects"])
            main = f'{r[2]-r[0]:.2f} x {r[3]-r[1]:.2f}'
            s.append(f'<text x="{cx}" y="{cy+0.25}" font-size="0.15" fill="#7f1d1d" text-anchor="middle">'
                     f'<tspan x="{cx}" font-weight="bold">{escape(sp["name"])}</tspan>'
                     f'<tspan x="{cx}" dy="0.19">main {main} m</tspan><tspan x="{cx}" dy="0.19">area {A:.2f} m²</tspan></text>')
            print(f'  {sp["name"]:<48} main {main:<13} area {A:6.2f} m2   label {sp.get("label")}')
        s.append(f'<text x="0" y="13.4" font-size="0.22">{escape(fl["label"])} — TAKEOFF CHECK: red fill = takeoff walls, '
                 f'black = PDF lines, blue = door/opening, green = window (width m)</text></svg>')
        (ROOT / f"docs/overlays/takeoff_{fk}.svg").write_text("\n".join(s))


if __name__ == "__main__":
    main()
