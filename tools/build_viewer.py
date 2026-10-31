#!/usr/bin/env python3
"""Assemble the single-file offline viewer viewer/bella-vita-2.html.

Inlines three.js (r160, MIT licence) and its OrbitControls, plus model/scene.json.
Usage: python3 tools/build_viewer.py <path-to-three-package-dir>
       (the 'package' folder of `npm pack three@0.160.0`; not committed)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
pkg = Path(sys.argv[1])
three = (pkg / "build/three.module.min.js").read_text()
orbit = (pkg / "examples/jsm/controls/OrbitControls.js").read_text()
# rewrite the ES-module import/export of OrbitControls into plain code using a THREE object
m = re.search(r"import\s*\{([^}]*)\}\s*from\s*'three';", orbit)
orbit = orbit.replace(m.group(0), "const {" + m.group(1) + "} = THREE;")
orbit = re.sub(r"export\s*\{\s*OrbitControls\s*\};?", "", orbit)
import json
sys.path.insert(0, str(ROOT / "tools"))
from mep_elements import mep_elements  # noqa: E402

SC = json.loads((ROOT / "model/scene.json").read_text())
SC["elements"] = SC["elements"] + mep_elements()
scene = json.dumps(SC, separators=(",", ":"))
for name, txt in (("three", three), ("orbit", orbit), ("scene", scene)):
    assert "</script" not in txt.lower(), name
html = (ROOT / "tools/viewer_template.html").read_text()
html = html.replace("__THREE__", three).replace("__ORBIT__", orbit).replace("__SCENE__", scene)
out = ROOT / "viewer/bella-vita-2.html"
out.parent.mkdir(exist_ok=True)
out.write_text(html)
print("wrote", out, f"{out.stat().st_size/1024:.0f} KB")
