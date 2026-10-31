#!/usr/bin/env python3
"""Export model/scene.json to IFC4 (model/bella-vita-2.ifc) with IfcOpenShell.

Run with an interpreter that has ifcopenshell (pip install ifcopenshell; not committed).
World axes in the IFC: X = plan X, Y = 11.75 - plan Y (front face at Y = 0, rear at 11.75,
road towards -Y), Z = metres above road level (ASSUMED datum).
Walls that host windows are exported as one IfcWall with IfcOpeningElement voids filled by
IfcWindow, so IFC viewers cut the openings themselves.
"""
import json
import sys
from pathlib import Path

import ifcopenshell
import ifcopenshell.api as api
import ifcopenshell.api.aggregate, ifcopenshell.api.context, ifcopenshell.api.feature  # noqa: E401,F401
import ifcopenshell.api.geometry, ifcopenshell.api.project, ifcopenshell.api.pset  # noqa: E401,F401
import ifcopenshell.api.root, ifcopenshell.api.spatial, ifcopenshell.api.style, ifcopenshell.api.unit  # noqa: E401,F401
import ifcopenshell.guid

ROOT = Path(__file__).resolve().parent.parent
SC = json.loads((ROOT / "model/scene.json").read_text())
Y0 = 11.75

f = api.project.create_file(version="IFC4")
proj = api.root.create_entity(f, ifc_class="IfcProject", name="Bella Vita 2 - Plot C-89 Sec-12 Kharghar (coordination model)")
api.unit.assign_unit(f, length={"is_metric": True, "raw": "METERS"})
model_ctx = api.context.add_context(f, context_type="Model")
body = api.context.add_context(f, context_type="Model", context_identifier="Body", target_view="MODEL_VIEW", parent=model_ctx)
site = api.root.create_entity(f, ifc_class="IfcSite", name="Plot C-89, Sector 12, Kharghar, Navi Mumbai")
bldg = api.root.create_entity(f, ifc_class="IfcBuilding", name="Bella Vita 2 (student PG)")
api.aggregate.assign_object(f, relating_object=proj, products=[site])
api.aggregate.assign_object(f, relating_object=site, products=[bldg])
storeys = {}
for s in SC["storeys"]:
    st = api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=s)
    st.Elevation = SC["ffl"][s]
    api.aggregate.assign_object(f, relating_object=bldg, products=[st])
    storeys[s] = st

origin = f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.0, 0.0, 0.0)), None, None)
zdir = f.createIfcDirection((0.0, 0.0, 1.0))

COLOURS = {"wall": (0.85, 0.83, 0.78), "slab": (0.7, 0.7, 0.72), "window": (0.55, 0.75, 0.9), "door": (0.6, 0.42, 0.25),
           "stair": (0.75, 0.7, 0.62), "furniture": (0.45, 0.55, 0.8), "tank": (0.3, 0.6, 0.85), "water": (0.2, 0.5, 0.95),
           "space": (0.95, 0.9, 0.6), "site": (0.55, 0.62, 0.45), "lift": (0.9, 0.5, 0.2), "clearance": (1.0, 0.4, 0.4)}
styles = {}
for k, c in COLOURS.items():
    st = api.style.add_style(f, name=k)
    api.style.add_surface_style(f, style=st, ifc_class="IfcSurfaceStyleShading",
                                attributes={"SurfaceColour": {"Name": None, "Red": c[0], "Green": c[1], "Blue": c[2]},
                                            "Transparency": 0.6 if k in ("space", "water", "clearance", "window") else 0.0})
    styles[k] = st


def solid(b):
    x0, y0, z0, x1, y1, z1 = b
    wy0, wy1 = Y0 - y1, Y0 - y0
    cx, cy = (x0 + x1) / 2, (wy0 + wy1) / 2
    pos = f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((cx, cy, z0)), None, None)
    prof = f.createIfcRectangleProfileDef("AREA", None, f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((0.0, 0.0)), None),
                                          x1 - x0, wy1 - wy0)
    return f.createIfcExtrudedAreaSolid(prof, pos, zdir, z1 - z0)


def rep(boxes, layer):
    items = [solid(b) for b in boxes]
    r = f.createIfcShapeRepresentation(body, "Body", "SweptSolid", items)
    if layer in styles:
        for it in items:
            api.style.assign_item_style(f, item=it, style=styles[layer])
    return r


def make(cls, name, storey, boxes, layer, tag, extra=None):
    el = api.root.create_entity(f, ifc_class=cls, name=name[:255])
    api.geometry.assign_representation(f, product=el, representation=rep(boxes, layer))
    if cls == "IfcSpace":
        api.aggregate.assign_object(f, relating_object=storeys.get(storey, storeys["GF"]), products=[el])
    elif cls != "IfcSite":
        api.spatial.assign_container(f, relating_structure=storeys.get(storey, storeys["GF"]), products=[el])
    el.ObjectPlacement = f.createIfcLocalPlacement(None, origin)   # absolute; geometry is in world coords
    props = {"Source": tag, "Layer": layer}
    for k, v in (extra or {}).items():
        props[k] = v if isinstance(v, (int, float, str)) else json.dumps(v)
    ps = api.pset.add_pset(f, product=el, name="BV2_Coordination")
    api.pset.edit_pset(f, pset=ps, properties=props)
    return el


n = 0
windows_by_wall = {}
for e in SC["elements"]:
    cls = e["cls"]
    if cls == "IfcSite":
        cls = "IfcGeographicElement"
    if e["layer"] == "clearance":
        continue                                  # clearance zones stay viewer-only
    extra = {k: e[k] for k in ("label", "area", "width", "sill", "head", "volume_L", "riser", "risers") if k in e}
    if e["cls"] == "IfcWall" and "ifc_box" in e:
        w = make("IfcWall", e["name"], e["storey"], [e["ifc_box"]], "wall", e["tag"], extra)
        for v in e["voids"]:
            op = api.root.create_entity(f, ifc_class="IfcOpeningElement", name=f"Opening {v['window']}")
            op.ObjectPlacement = f.createIfcLocalPlacement(None, origin)
            api.geometry.assign_representation(f, product=op, representation=rep([v["box"]], None))
            api.feature.add_feature(f, feature=op, element=w)
            windows_by_wall.setdefault(v["window"] + e["storey"], op)
        n += 1
        continue
    if cls == "IfcWindow":
        el = make("IfcWindow", e["name"], e["storey"], e["boxes"], "window", e["tag"], extra)
        key = e["name"].split()[1] + e["storey"]
        op = windows_by_wall.get(key)
        if op is not None:
            api.feature.add_filling(f, opening=op, element=el)
        n += 1
        continue
    make(cls, e["name"], e["storey"], e["boxes"], e["layer"], e["tag"], extra)
    n += 1

out = ROOT / "model/bella-vita-2.ifc"
f.write(str(out))
print("wrote", out, "elements", n, "size", out.stat().st_size)
