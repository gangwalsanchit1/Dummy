#!/usr/bin/env python3
"""Phase 1 takeoff helper for Bella Vita 2 (Plot C-89, Sec-12, Kharghar).

Reads the vector linework of the AFTER O.C. sheet directly from the PDF and
re-draws each floor plan in metres on a 0.5 m grid (scaled SVG overlay).

Scale is DERIVED from the drawn 8.000 m plot-width dimension: the orange plot
line and the outer wall faces span 118.022 pt  ->  14.75275 pt per metre.

Local plan coordinates (used throughout docs/drawing-takeoff.md):
  X = metres from the LEFT outer wall face (as seen on the sheet, road at bottom)
  Y = metres from the REAR outer wall face (top of sheet) towards the road.

The left half of the PDF page (x < 0, clipped off the printed page) holds a
superseded "BEFORE O.C." set; it is ignored here.

Usage: python3 tools/extract_plans.py <pdf> <out_dir>
"""
import json
from html import escape
import sys
from pathlib import Path

import pdfplumber

K = 118.022 / 8.0                      # pt per metre (CALCULATED from DRAWN 8.000)
OY = 284.193                           # pt, rear outer wall face (all plans)
PLANS = {                              # pt, left outer wall face of each plan
    "GF": (40.204, "GROUND FLOOR PLAN (STILT)"),
    "F1-3": (185.819, "FIRST, SECOND & THIRD FLOOR PLAN"),
    "F4": (331.675, "FOURTH FLOOR PLAN"),
    "TERRACE": (476.627, "TERRACE FLOOR PLAN"),
}
COLOURS = {  # pdf stroke colour -> (layer name, svg colour, width)
    (0.251, 0.251, 0.251): ("wall", "#222", 0.025),
    (1.0, 0.624, 0.251): ("plot/margin", "#f59e0b", 0.012),
    (0.8, 0.8, 0.8): ("dimension", "#888", 0.008),
    (1.0, 0.251, 0.251): ("setback line", "#ef4444", 0.012),
    (1.0, 0.718, 0.624): ("stair treads", "#f97316", 0.008),
    (0.725, 0.792, 0.522): ("window", "#16a34a", 0.02),
    (1.0, 0.624, 0.718): ("tank", "#ec4899", 0.01),
    (0.812, 0.251, 1.0): ("OHT cross", "#a855f7", 0.01),
    (0.902, 0.737, 0.251): ("opening/door", "#ca8a04", 0.015),
    (0.898, 0.898, 0.898): ("light grey", "#bbb", 0.008),
    (1.0, 0.624, 0.624): ("pink2", "#f472b6", 0.01),
    (0.6, 0.6, 0.6): ("grey", "#666", 0.012),
    (0.624, 0.718, 1.0): ("frame", "#93c5fd", 0.01),
}


def plan_of(x):
    best = None
    for k, (ox, _) in PLANS.items():
        if x >= ox - 25:
            if best is None or ox > PLANS[best][0]:
                best = k
    return best


def to_m(k, x, y):
    return (x - PLANS[k][0]) / K, (y - OY) / K


def main(pdf, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    page = pdfplumber.open(pdf).pages[0]
    geo = {k: {"segments": [], "texts": []} for k in PLANS}
    for obj in list(page.lines) + list(page.curves) + list(page.rects):
        pts = obj.get("pts")
        if not pts or min(p[0] for p in pts) < 0:
            continue                                    # BEFORE O.C. half
        k = plan_of(min(p[0] for p in pts))
        if k is None:
            continue
        col = tuple(round(v, 3) for v in (obj.get("stroking_color") or (0, 0, 0))[:3])
        layer = COLOURS.get(col, (str(col), "#000", 0.01))[0]
        mp = [to_m(k, *p) for p in pts]
        geo[k]["segments"].append({"layer": layer, "curve": obj["object_type"] == "curve",
                                   "pts": [[round(a, 3), round(b, 3)] for a, b in mp]})
    for w in page.extract_words(keep_blank_chars=False):
        if w["x0"] < 0 or w["top"] < 250:
            continue
        k = plan_of(w["x0"])
        if k is None:
            continue
        x, y = to_m(k, (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2)
        geo[k]["texts"].append({"t": w["text"], "x": round(x, 3), "y": round(y, 3),
                                "upright": bool(w.get("upright", True))})
    (out / "plan_geometry.json").write_text(json.dumps(geo, indent=0))

    colour_by_layer = {v[0]: v for v in COLOURS.values()}
    for k, (_, title) in PLANS.items():
        x0, y0, x1, y1 = -1.5, -1.5, 9.5, 15.0
        s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1-x0} {y1-y0}" '
             f'width="{(x1-x0)*100:.0f}" height="{(y1-y0)*100:.0f}" font-family="Arial">',
             f'<rect x="{x0}" y="{y0}" width="{x1-x0}" height="{y1-y0}" fill="#fff"/>']
        g = 0.0                                          # 0.5 m grid, labelled every 1 m
        while g <= 14.0001:
            w = 0.006 if abs(g - round(g)) < 1e-6 else 0.003
            s.append(f'<line x1="-0.5" y1="{g}" x2="8.5" y2="{g}" stroke="#cfe3ff" stroke-width="{w}"/>')
            if abs(g - round(g)) < 1e-6:
                s.append(f'<text x="-0.6" y="{g+0.06}" font-size="0.18" fill="#3b82f6" text-anchor="end">{g:.0f}</text>')
            g += 0.5
        g = 0.0
        while g <= 8.0001:
            w = 0.006 if abs(g - round(g)) < 1e-6 else 0.003
            s.append(f'<line x1="{g}" y1="-0.5" x2="{g}" y2="14.2" stroke="#cfe3ff" stroke-width="{w}"/>')
            if abs(g - round(g)) < 1e-6:
                s.append(f'<text x="{g}" y="-0.6" font-size="0.18" fill="#3b82f6" text-anchor="middle">{g:.0f}</text>')
            g += 0.5
        for seg in geo[k]["segments"]:
            _, colr, sw = colour_by_layer.get(seg["layer"], (None, "#000", 0.01))
            d = " ".join(f'{"M" if i == 0 else "L"}{a:.3f},{b:.3f}' for i, (a, b) in enumerate(seg["pts"]))
            s.append(f'<path d="{d}" fill="none" stroke="{colr}" stroke-width="{sw}"/>')
        for t in geo[k]["texts"]:
            if t["upright"]:
                s.append(f'<text x="{t["x"]}" y="{t["y"]+0.05}" font-size="0.16" fill="#1d4ed8" '
                         f'text-anchor="middle" opacity="0.85">{escape(t["t"])}</text>')
        s.append(f'<text x="0" y="14.75" font-size="0.3" fill="#111">{escape(title)} — scaled overlay, '
                 f'grid 0.5 m, origin = rear-left outer wall corner (X right, Y towards road)</text>')
        s.append('</svg>')
        (out / f"overlay_{k}.svg").write_text("\n".join(s))
    print("wrote", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
