#!/usr/bin/env python3
"""Build the hosted (claude.ai artifact) version of the viewer.

Differences from viewer/bella-vita-2.html: no document wrapper (the host adds it), three.js r128
UMD + OrbitControls inlined as classic scripts (no blob/module import), errors shown on the page,
and the 2D plan fallback when the browser has no WebGL.
Usage: python3 tools/build_viewer_hosted.py <three@0.128.0 package dir> <output.html>
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from mep_elements import mep_elements  # noqa: E402

pkg, out = Path(sys.argv[1]), Path(sys.argv[2])
three = (pkg / "build/three.min.js").read_text()
orbit = (pkg / "examples/js/controls/OrbitControls.js").read_text()
SC = json.loads((ROOT / "model/scene.json").read_text())
SC["elements"] += mep_elements()
scene = json.dumps(SC, separators=(",", ":"))
for x in (three, orbit, scene):
    assert "</script" not in x.lower()
t = (ROOT / "tools/viewer_template.html").read_text()
for tag in ("<!doctype html>\n", '<html lang="en">\n', "<head>\n", "</head>\n", "<body>\n", "</body>\n", "</html>\n"):
    t = t.replace(tag, "")
t = re.sub(r'<meta charset="utf-8">\n<meta name="viewport"[^>]*>\n', "", t)
t = t.replace("#panel { position:fixed; top:10px; left:10px;",
              "#panel { position:fixed; top:calc(10px + env(safe-area-inset-top, 0px)); left:calc(10px + env(safe-area-inset-left, 0px));")
t = t.replace("#info { position:fixed; right:10px; bottom:10px;",
              "#info { position:fixed; right:calc(10px + env(safe-area-inset-right, 0px)); bottom:calc(10px + env(safe-area-inset-bottom, 0px));")
t = t.replace('<script type="text/plain" id="three-src">__THREE__</script>\n<script type="text/plain" id="orbit-src">__ORBIT__</script>\n',
              "<script>\n" + three + "\n</script>\n<script>\n" + orbit + "\n</script>\n")
a = t.index("const THREE = await import(")
b = min(i for i in (t.find("const FTIN"), t.index("const SC = JSON.parse(")) if i >= 0)
t = t[:a] + "const OrbitControls = THREE.OrbitControls;\n" + t[b:]
t = t.replace("new THREE.HemisphereLight(0xffffff, 0x8a8f99, 1.6)", "new THREE.HemisphereLight(0xffffff, 0x8a8f99, 0.85)")
t = t.replace("new THREE.DirectionalLight(0xffffff, 1.4)", "new THREE.DirectionalLight(0xffffff, 0.7)")
m = t.index('<script type="module">')
t = (t[:m] + "<script>\nwindow.addEventListener('error', function (e) { var d = document.getElementById('info'); if (d) d.innerHTML = '<b>Viewer could not start</b><br>' + String(e.message || e).replace(/</g, '&lt;'); });\n</script>\n"
     + "<script>\n(function () {\ntry {\n" + t[m + len('<script type="module">'):])
e = t.rindex("</script>")
t = (t[:e] + "} catch (err) { var d = document.getElementById('info'); if (d) d.innerHTML = '<b>Viewer could not start</b><br>' + String(err && (err.stack || err.message) || err).replace(/</g, '&lt;').slice(0, 600); }\n})();\n" + t[e:])
t = t.replace("__SCENE__", scene)
assert "await import(URL" not in t and "id=\"three-src\"" not in t
out.write_text(t)
print("wrote", out, f"{len(t) // 1024} KB")
