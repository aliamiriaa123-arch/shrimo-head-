"""
SPD V3.0 — Functional production CAD generator (Blender 4.5+ / 5.x, background mode)

Submerged Pulsed Micro-Slit Diffuser, TRL-4 test article.
Run:  "D:\\blender\\blender.exe" --background --factory-startup --python generate_functional_production_cad.py

All dimensions come from spd_design_params.py (single source of truth shared with the verifier).
Every boolean is checked (volume must change as expected) and every exported part must be a
single closed 2-manifold body; the script aborts instead of silently writing a broken STL
(the V2.2 generator printed boolean errors and continued).

Supersedes V2.2 (V2.2 files removed 2026-09-29). Why V2.2 could not work — open-top/
open-bottom air bell, blocked air path at Parts 08/09/02/05, unconnected feedback ports, 3.5 L
plenums that low-pass filtered the pulses, interferences and O-ring grooves cut by bolt holes —
is documented in CAD_V3_DESIGN_BASIS_AND_VERIFICATION.md.

Air path (V3.0):
  2" Camlock pipe stub -> Part 09 accumulator (inlet socket, hat-protected standpipe, condensate
  sump + 1/2" NPT drain) -> Part 08 duckbill check-valve spool -> Part 05 cover inlet ->
  Part 04 oscillator (supply plenum -> power nozzle -> control ports/feedback loop -> splitter)
  -> downcomers A/B -> Part 02 twin plenum ducts -> Parts 06/07 cartridge pockets ->
  11 x (1.0 x 20 mm) slits per bank, 20 deg down -> Part 01 floor deflectors (+20 deg exit lip).
"""

import bpy
import bmesh
import json
import math
import os
import sys
from mathutils import Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import spd_design_params as P  # noqa: E402

OUTPUT_DIR = os.path.join(HERE, "3D_Print_STLs")
BLEND_OUTPUT = os.path.join(HERE, "Pulsed_Diffuser_Functional_Production.blend")
GLB_OUTPUT = os.path.join(HERE, "Pulsed_Diffuser_V3_Assembly.glb")
MANIFEST = os.path.join(OUTPUT_DIR, "BUILD_MANIFEST.json")

SEG_L, SEG_M, SEG_S = 128, 64, 32
LOG = []


def log(msg):
    print(msg)
    LOG.append(msg)


# ============================================================================
# Geometry primitives (all closed, consistently oriented manifolds)
# ============================================================================
def _obj(name, bm):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def box(name, x0, x1, y0, y1, z0, z1):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(x1 - x0, y1 - y0, z1 - z0), verts=bm.verts)
    bmesh.ops.translate(bm, vec=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), verts=bm.verts)
    return _obj(name, bm)


def cyl(name, center, r, length, axis="Z", seg=SEG_M, r2=None):
    """Cylinder/frustum centred on `center`, axis X/Y/Z; r at the negative end, r2 at the positive end."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=length)
    if axis == "X":
        bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(90), 4, "Y"), verts=bm.verts)
    elif axis == "Y":
        bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(-90), 4, "X"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=center, verts=bm.verts)
    return _obj(name, bm)


def cyl_z(name, x, y, z0, z1, r, seg=SEG_M):
    return cyl(name, (x, y, (z0 + z1) / 2), r, z1 - z0, "Z", seg)


def cyl_x(name, x0, x1, y, z, r, seg=SEG_S):
    return cyl(name, ((x0 + x1) / 2, y, z), r, abs(x1 - x0), "X", seg)


def cyl_y(name, x, y0, y1, z, r, seg=SEG_S):
    return cyl(name, (x, (y0 + y1) / 2, z), r, abs(y1 - y0), "Y", seg)


def _map(plane, a, b, h):
    if plane == "XY":
        return (a, b, h)
    if plane == "XZ":
        return (a, h, b)
    if plane == "YZ":
        return (h, a, b)
    raise ValueError(plane)


def prism(name, pts, h0, h1, plane="XY"):
    """Simple polygon `pts` (2D, in `plane`) extruded between h0 and h1 along the third axis."""
    bm = bmesh.new()
    vb = [bm.verts.new(_map(plane, a, b, h0)) for a, b in pts]
    vt = [bm.verts.new(_map(plane, a, b, h1)) for a, b in pts]
    n = len(pts)
    bm.faces.new(vb[::-1])
    bm.faces.new(vt)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
    return _obj(name, bm)


def ring_prism(name, outer, inner, h0, h1, plane="XY"):
    """Closed band between two loops with equal vertex count (used for O-ring grooves)."""
    assert len(outer) == len(inner)
    bm = bmesh.new()
    ob = [bm.verts.new(_map(plane, a, b, h0)) for a, b in outer]
    ot = [bm.verts.new(_map(plane, a, b, h1)) for a, b in outer]
    ib = [bm.verts.new(_map(plane, a, b, h0)) for a, b in inner]
    it = [bm.verts.new(_map(plane, a, b, h1)) for a, b in inner]
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((ob[i], ob[j], ot[j], ot[i]))
        bm.faces.new((ib[j], ib[i], it[i], it[j]))
        bm.faces.new((ot[i], ot[j], it[j], it[i]))
        bm.faces.new((ob[j], ob[i], ib[i], ib[j]))
    return _obj(name, bm)


def rrect(cx, cy, hx, hy, r, n=10):
    """Counter-clockwise rounded rectangle."""
    pts = []
    for ox, oy, a0 in ((cx + hx - r, cy - hy + r, -90), (cx + hx - r, cy + hy - r, 0),
                       (cx - hx + r, cy + hy - r, 90), (cx - hx + r, cy - hy + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    return pts


def revolve(name, prof, seg=SEG_L):
    """Solid of revolution about Z from a closed (r, z) polygon; r == 0 vertices become poles."""
    bm = bmesh.new()
    rings = []
    for r, z in prof:
        if r < 1e-9:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * s / seg), r * math.sin(2 * math.pi * s / seg), z))
                          for s in range(seg)])
    n = len(prof)
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
        if len(a) == 1 and len(b) == 1:
            continue
        for s in range(seg):
            t = (s + 1) % seg
            if len(a) == 1:
                bm.faces.new((a[0], b[s], b[t]))
            elif len(b) == 1:
                bm.faces.new((a[s], a[t], b[0]))
            else:
                bm.faces.new((a[s], a[t], b[t], b[s]))
    return _obj(name, bm)


def annulus(name, x, y, z0, z1, ri, ro, seg=SEG_M):
    ob = revolve(name, [(ri, z0), (ro, z0), (ro, z1), (ri, z1)], seg)
    ob.data.transform(Matrix.Translation((x, y, 0.0)))
    return ob


def hexa(name, v):
    """8-vertex hexahedron: v[0..3] bottom loop, v[4..7] top loop (same order)."""
    bm = bmesh.new()
    vv = [bm.verts.new(p) for p in v]
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([vv[i] for i in f])
    return _obj(name, bm)


# ============================================================================
# Checked booleans
# ============================================================================
def mesh_volume(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    v = abs(bm.calc_volume(signed=True))
    bm.free()
    return v


def _drop(ob):
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me.users == 0:
        bpy.data.meshes.remove(me)


def boolean(target, tool, op, expect_change=True):
    v0 = mesh_volume(target.data)
    last = None
    for solver in ("MANIFOLD", "EXACT"):
        mod = target.modifiers.new("bool", "BOOLEAN")
        mod.operation = op
        mod.solver = solver
        mod.object = tool
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(target.evaluated_get(dg))
        target.modifiers.remove(mod)
        v1 = mesh_volume(me) if len(me.polygons) else 0.0
        changed = (v1 < v0 - 1e-3) if op == "DIFFERENCE" else (v1 > v0 + 1e-3)
        last = (solver, v0, v1)
        if v1 > 1e-3 and (changed or not expect_change):
            old = target.data
            target.data = me
            bpy.data.meshes.remove(old)
            _drop(tool)
            return target
        bpy.data.meshes.remove(me)
    raise RuntimeError(f"BOOLEAN {op} FAILED: target={target.name} tool={tool.name} last={last}")


def cut(target, *tools, expect=True):
    for t in tools:
        boolean(target, t, "DIFFERENCE", expect)
    return target


def add(target, *tools, expect=True):
    for t in tools:
        boolean(target, t, "UNION", expect)
    return target


# ============================================================================
# Validation & export
# ============================================================================
def finalize(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    non_manifold = sum(1 for e in bm.edges if not e.is_manifold)
    bm.verts.ensure_lookup_table()
    seen, islands = set(), 0
    for v in bm.verts:
        if v.index in seen:
            continue
        islands += 1
        stack = [v]
        seen.add(v.index)
        while stack:
            u = stack.pop()
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index)
                    stack.append(w)
    vol = abs(bm.calc_volume(signed=True))
    bm.free()
    if non_manifold or islands != 1:
        raise RuntimeError(f"{ob.name}: non-manifold edges={non_manifold}, bodies={islands}")
    xs = [v.co.x for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    return dict(volume_cm3=round(vol / 1000.0, 2), faces=len(ob.data.polygons),
                bbox=[[round(min(xs), 3), round(min(ys), 3), round(min(zs), 3)],
                      [round(max(xs), 3), round(max(ys), 3), round(max(zs), 3)]])


def export_stl(ob, path):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True, ascii_format=False,
                          apply_modifiers=True, global_scale=1.0, use_scene_unit=False)
    ob.select_set(False)


def material(name, rgb, rough=0.5, metal=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
    return m


# ============================================================================
# Part 01 — benthic chassis with pedestal, floor deflectors, ballast interface
# ============================================================================
def build_part_01():
    log("Part 01: chassis / pedestal / floor deflectors")
    hx, hy, bar = P.FRAME_HX, P.FRAME_HY, P.BAR
    z0, z1 = P.FRAME_Z
    ch = box("Part_01_Benthic_Base_Chassis", -hx, hx, -hy, hy, z0, z1)
    cut(ch, box("ring_void", -hx + bar, hx - bar, -hy + bar, hy - bar, z0 - 1, z1 + 1))
    add(ch, box("x_bar", -hx + bar - 1, hx - bar + 1, -20, 20, z0, z1))
    for (fx, fy) in P.FEET_XY:
        add(ch, cyl_z("foot", fx, fy, P.FOOT_Z[0], z0 + 1, P.FOOT_R, SEG_M))
    off, rh = P.FOOT_MUD_HOLE
    for (fx, fy) in P.FEET_XY:   # mud-suction relief through foot + bar
        for dx, dy in ((off, 0), (-off, 0), (0, off), (0, -off)):
            cut(ch, cyl_z("mud_hole", fx + dx, fy + dy, -1, z1 + 1, rh, SEG_S))
    pd = P.PEDESTAL
    add(ch, box("pedestal", -pd["hx"], pd["hx"], -pd["hy"], pd["hy"], pd["z0"] - 1, pd["z1"]))
    cut(ch, box("pedestal_void", -pd["hx"] + pd["wall"], pd["hx"] - pd["wall"], -pd["hy"] + pd["wall"],
                pd["hy"] - pd["wall"], pd["z0"] - 2, pd["z1"] - pd["top"]))
    for yc in (-50.0, 50.0):
        add(ch, box("pedestal_rib", -pd["hx"] + pd["wall"] - 0.5, pd["hx"] - pd["wall"] + 0.5, yc - 3, yc + 3,
                    pd["z0"] - 1, pd["z1"] - pd["top"] + 0.5))
    for (x, y) in P.M8_BASE_XY:
        cut(ch, cyl_z("m8_clear", x, y, pd["z1"] - pd["top"] - 1, pd["z1"] + 1, P.CLEAR["M8"], SEG_S))
    t10 = math.tan(math.radians(P.DEFL_SLOPE_DEG))
    t20 = math.tan(math.radians(P.DEFL_LIP_DEG))
    zt0 = P.DEFL_TOP_Z0
    zt1 = zt0 - (P.DEFL_X1 - P.DEFL_X0) * t10
    zt2 = zt1 + (P.DEFL_X2 - P.DEFL_X1) * t20
    for s in (-1, 1):
        top = [(P.DEFL_X0, zt0), (P.DEFL_X1, zt1), (P.DEFL_X2, zt2)]
        poly = [(x, z - P.DEFL_T) for x, z in top] + top[::-1]
        add(ch, prism("deflector", [(s * x, z) for x, z in poly], -P.DEFL_HY, P.DEFL_HY, "XZ"))
        for yc in (-P.DEFL_HY + 3, 0.0, P.DEFL_HY - 3):
            zr0 = zt0 - P.DEFL_T + 1.0
            zr1 = zt1 - P.DEFL_T + 1.0
            rib = [(50.0, z1 - 1), (P.DEFL_X1, z1 - 1), (P.DEFL_X1, zr1), (P.DEFL_X0, zr0), (50.0, zr0)]
            add(ch, prism("deflector_rib", [(s * x, z) for x, z in rib], yc - 3, yc + 3, "XZ"))
    for (x, y) in P.LIFT_HOLES_XY:
        cut(ch, cyl_z("lift_hole", x, y, z0 - 1, z1 + 1, 8.0, SEG_S))
    for s in (-1, 1):
        for x in P.CRADLE_BOLT_X:
            cut(ch, cyl_y("cradle_bolt", x, s * (hy - bar - 5), s * (hy + 5), P.CRADLE_BOLT_Z, P.CLEAR["M8"]))
    return ch


# ============================================================================
# Part 02 — twin-plenum manifold (integral divider = retired V2.2 Part 03)
# ============================================================================
def duct_profile():
    return rrect(0.0, P.DUCT_ZC, P.DUCT_HY, P.CH_H / 2.0, P.DUCT_R, 8)


def build_part_02():
    log("Part 02: twin-plenum manifold housing")
    m = box("Part_02_Twin_Plenum_Manifold", -P.M2_HX, P.M2_HX, -P.M2_HY, P.M2_HY, *P.M2_Z)
    for s in (-1, 1):
        x0, x1 = sorted((s * P.DUCT_X_IN, s * (P.M2_HX + 1.0)))
        cut(m, prism("plenum_duct", duct_profile(), x0, x1, "YZ"))
    dcx, dcy = P.DOWNCOMER_XY
    gi, go = P.groove_radii_for(P.DC_ORING)
    for s in (-1, 1):
        cut(m, cyl_z("downcomer", s * dcx, dcy, P.Z_FLOOR + P.CH_H - 1.0, P.M2_Z[1] + 1.0, P.DOWNCOMER_R))
        cut(m, annulus("dc_groove", s * dcx, dcy, P.M2_Z[1] - P.DC_ORING["depth"], P.M2_Z[1] + 1.0, gi, go))
    ri, depth = P.INSERT["M4"]
    for s in (-1, 1):
        for y in P.M4_ROW_Y:
            for z in P.M4_ROW_Z:
                x0, x1 = sorted((s * (P.M2_HX - depth), s * (P.M2_HX + 1.0)))
                cut(m, cyl_x("m4_insert", x0, x1, y, z, ri))
    ri, depth = P.INSERT["M5"]
    for (x, y) in P.M5_STACK_XY:
        cut(m, cyl_z("m5_insert", x, y, P.M2_Z[1] - depth, P.M2_Z[1] + 1.0, ri, SEG_S))
    ri, depth = P.INSERT["M8"]
    for (x, y) in P.M8_BASE_XY:
        cut(m, cyl_z("m8_insert", x, y, P.M2_Z[0] - 1.0, P.M2_Z[0] + depth, ri, SEG_S))
    ri, depth = P.INSERT["M5"]
    for s in (-1, 1):   # P_DA / P_DB pressure taps through the -Y end wall
        cut(m, cyl_y("tap_insert", s * dcx, -P.M2_HY - 1.0, -P.M2_HY + depth, P.TAP_PD_Z, ri))
        cut(m, cyl_y("tap_pilot", s * dcx, -P.M2_HY + depth - 1.0, -P.DUCT_HY + 2.0, P.TAP_PD_Z, P.TAP_M5_PILOT_R))
    return m


# ============================================================================
# Part 04 — Coanda bistable oscillator core (lid of Part 02)
# ============================================================================
def build_part_04():
    log("Part 04: oscillator core block")
    z0, z1 = P.P4_Z
    c0, c1 = P.CAV_Z[0], P.P4_Z[1] + 1.0
    blk = box("Part_04_Coanda_Oscillator_Core_Block", -P.P45_HX, P.P45_HX, P.P45_Y[0], P.P45_Y[1], z0, z1)
    b2 = P.NOZ_B / 2.0
    xw0 = b2 + P.SETBACK
    xs = P.X_WALL_AT_SPLITTER
    ys, ye = P.Y_SPLITTER, P.Y_NOZ_EXIT
    hw0 = math.sqrt(P.PLENUM_R ** 2 - P.Y_CONTRACT0 ** 2)
    cut(blk, cyl_z("supply_plenum", 0.0, 0.0, c0, c1, P.PLENUM_R, SEG_M))
    cut(blk, prism("contraction", [(-hw0, P.Y_CONTRACT0), (hw0, P.Y_CONTRACT0), (b2, P.Y_THROAT0),
                                   (-b2, P.Y_THROAT0)], c0, c1))
    cut(blk, box("throat", -b2, b2, ye, P.Y_THROAT0 + 0.5, c0, c1))
    cut(blk, box("control_ports", -P.CTRL_X_END, P.CTRL_X_END, ye - P.CTRL_W, ye, c0, c1))
    cut(blk, prism("interaction", [(-xw0, ye - P.CTRL_W + 0.5), (xw0, ye - P.CTRL_W + 0.5), (xs, ys), (-xs, ys)],
                   c0, c1))
    dcx, dcy = P.DOWNCOMER_XY
    out_b = [(0.0, ys), (xs, ys), (15.8, ys - 12.0), (dcx, dcy + 9.0), (dcx + 9.0, dcy), (dcx, dcy - 9.0),
             (dcx - 9.0, dcy), (7.0, ys - 12.0)]
    for s in (-1, 1):
        cut(blk, prism("output_channel", [(s * x, y) for x, y in out_b], c0, c1))
        cut(blk, cyl_z("downcomer_pocket", s * dcx, dcy, c0, c1, P.DC_POCKET_R))
        cut(blk, cyl_z("downcomer", s * dcx, dcy, z0 - 1.0, c0 + 1.0, P.DOWNCOMER_R))
    g = P.CAV_GROOVE_IN
    w = P.ORING_262["width"]
    inner = rrect(g["cx"], g["cy"], g["hx"], g["hy"], g["r"], 10)
    outer = rrect(g["cx"], g["cy"], g["hx"] + w, g["hy"] + w, g["r"] + w, 10)
    cut(blk, ring_prism("cavity_oring_groove", outer, inner, z1 - P.ORING_262["depth"], z1 + 1.0))
    for (x, y) in P.M5_STACK_XY:
        cut(blk, cyl_z("m5_through", x, y, z0 - 1.0, z1 + 1.0, P.CLEAR["M5"], SEG_S))
    return blk


# ============================================================================
# Part 05 — oscillator cover: supply inlet, feedback-loop hose barbs, stack mount
# ============================================================================
BARB_PROFILE = [(0.0, -1.0), (7.0, -1.0), (7.0, 4.0), (3.9, 4.0), (3.9, 6.0), (4.6, 6.0), (3.9, 11.0),
                (3.9, 13.0), (4.6, 13.0), (3.9, 18.0), (3.9, 20.0), (0.0, 20.0)]   # for PU tube ID 8 mm


def build_part_05():
    log("Part 05: oscillator cover plate")
    z0, z1 = P.P5_Z
    cv = box("Part_05_Oscillator_Top_Cover_Plate", -P.P45_HX, P.P45_HX, P.P45_Y[0], P.P45_Y[1], z0, z1)
    cut(cv, cyl_z("supply_inlet", 0.0, 0.0, z0 - 1.0, z1 + 1.0, P.INLET_R, SEG_M))
    bx, by = P.BARB_XY
    for s in (-1, 1):
        barb = revolve("feedback_barb", BARB_PROFILE, SEG_S)
        barb.data.transform(Matrix.Translation((s * bx, by, z1)))
        add(cv, barb)
        cut(cv, cyl_z("barb_bore", s * bx, by, z0 - 1.0, z1 + 21.0, 2.5, SEG_S))
    r_cb, d_cb = P.CB_M5
    for (x, y) in P.M5_STACK_XY:
        cut(cv, cyl_z("m5_clear", x, y, z0 - 1.0, z1 + 1.0, P.CLEAR["M5"], SEG_S))
        cut(cv, cyl_z("m5_cbore", x, y, z1 - d_cb, z1 + 1.0, r_cb, SEG_S))
    ri, depth = P.INSERT["M5"]
    for k in range(4):
        a = math.radians(45 + 90 * k)
        cut(cv, cyl_z("p8_insert", P.P8_BOT_BOLT_PCD_R * math.cos(a), P.P8_BOT_BOLT_PCD_R * math.sin(a),
                      z1 - depth, z1 + 1.0, ri, SEG_S))
    return cv


# ============================================================================
# Parts 06/07 — 11-slit calibrated cartridges (identical; 07 = 06 rotated 180 deg)
# ============================================================================
def build_cartridge(name):
    log(f"{name}: slit cartridge")
    x0, x1 = P.CART_X
    c = box(name, x0, x1, -P.M2_HY, P.M2_HY, *P.M2_Z)
    xp = x0 + P.POCKET_DEPTH
    cut(c, prism("pocket", duct_profile(), x0 - 1.0, xp, "YZ"))
    t = math.tan(math.radians(P.SLIT_ANGLE_DEG))
    hv = P.SLIT_GAP / math.cos(math.radians(P.SLIT_ANGLE_DEG))
    xa, xb = xp - 2.0, x1 + 2.0
    za, zb = P.Z_FLOOR - (xa - xp) * t, P.Z_FLOOR - (xb - xp) * t
    for (ya, yb) in P.slit_y_ranges():
        cut(c, hexa("slit", [(xa, ya, za), (xb, ya, zb), (xb, yb, zb), (xa, yb, za),
                             (xa, ya, za + hv), (xb, ya, zb + hv), (xb, yb, zb + hv), (xa, yb, za + hv)]))
    w, dpt, land = P.ORING_262["width"], P.ORING_262["depth"], P.MIN_LAND
    hy, hz, r = P.DUCT_HY + land, P.CH_H / 2 + land, P.DUCT_R + land
    inner = rrect(0.0, P.DUCT_ZC, hy, hz, r, 10)
    outer = rrect(0.0, P.DUCT_ZC, hy + w, hz + w, r + w, 10)
    cut(c, ring_prism("cart_oring_groove", outer, inner, x0 - 1.0, x0 + dpt, "YZ"))
    r_cb, d_cb = P.CB_M4
    for y in P.M4_ROW_Y:
        for z in P.M4_ROW_Z:
            cut(c, cyl_x("m4_clear", x0 - 1.0, x1 + 1.0, y, z, P.CLEAR["M4"]))
            cut(c, cyl_x("m4_cbore", x1 - d_cb, x1 + 1.0, y, z, r_cb))
    return c


# ============================================================================
# Part 08 — duckbill check-valve spool (between accumulator and oscillator)
# ============================================================================
def build_part_08():
    log("Part 08: duckbill check-valve spool")
    z0 = P.P8_Z0
    zt = z0 + P.P8_H
    ft = P.P8_FLANGE_T
    cbr, cbd = P.DUCKBILL_CB
    prof = [(P.INLET_R, z0), (P.P8_BOT_FLANGE_R, z0), (P.P8_BOT_FLANGE_R, z0 + ft), (P.P8_BODY_R, z0 + ft),
            (P.P8_BODY_R, zt - ft), (P.P8_TOP_FLANGE_R, zt - ft), (P.P8_TOP_FLANGE_R, zt), (cbr, zt),
            (cbr, zt - cbd), (P.DUCKBILL_BORE_R, zt - cbd), (P.DUCKBILL_BORE_R, z0 + ft), (P.INLET_R, z0 + ft)]
    sp = revolve("Part_08_Duckbill_Check_Valve_Spool", prof, SEG_L)
    gi, go = P.groove_radii_for(P.P8_ORING)
    cut(sp, annulus("p8_groove", 0.0, 0.0, z0 - 1.0, z0 + P.P8_ORING["depth"], gi, go, SEG_L))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        cut(sp, cyl_z("bot_bolt", P.P8_BOT_BOLT_PCD_R * math.cos(a), P.P8_BOT_BOLT_PCD_R * math.sin(a),
                      z0 - 1.0, z0 + ft + 1.0, P.CLEAR["M5"], SEG_S))
        b = math.radians(90 * k)
        cut(sp, cyl_z("top_bolt", P.P8_TOP_BOLT_PCD_R * math.cos(b), P.P8_TOP_BOLT_PCD_R * math.sin(b),
                      zt - ft - 1.0, zt + 1.0, P.CLEAR["M5"], SEG_S))
    return sp


# ============================================================================
# Part 09 — 4.3 L accumulator / condensate separator with hat-protected standpipe
# ============================================================================
def build_part_09():
    log("Part 09: accumulator / condensate separator")
    L = P.accumulator_levels()
    z0 = P.P9_Z0
    zfw, zfc = P.P9_Z_FLOOR_WALL, L["z_floor_centre"]
    zrs, zsh, zst, zsp = L["z_roof_start"], L["z_shoulder"], L["z_socket_top"], L["z_sp_top"]
    ro, ri = P.P9_OUT_R, P.P9_IN_R
    sr_o = P.SOCKET_R + 6.0
    k = ri + zrs                                   # interior roof: z + r = k
    ke = k + P.P9_WALL * math.sqrt(2.0)            # exterior roof, 6 mm normal offset
    prof = [(P.STANDPIPE_R[0], z0), (P.P9_BASE_R, z0), (P.P9_BASE_R, z0 + 10.0), (ro, z0 + 26.0),
            (ro, ke - ro), (sr_o, ke - sr_o), (sr_o, zst), (P.SOCKET_R, zst), (P.SOCKET_R, zsh),
            (P.SOCKET_SHOULDER_R, zsh), (ri, zrs), (ri, zfw), (P.STANDPIPE_R[1], zfc),
            (P.STANDPIPE_R[1], zsp), (P.STANDPIPE_R[0], zsp)]
    acc = revolve("Part_09_Accumulator_Condensate_Separator", prof, SEG_L)
    zh = zsp + P.HAT_GAP
    inner_apex = zh + P.HAT_R - P.HAT_T * math.sqrt(2.0)
    rh_in = inner_apex - zh
    add(acc, revolve("hat", [(0.0, zh + P.HAT_R), (P.HAT_R, zh), (rh_in, zh), (0.0, inner_apex)], SEG_L))
    for kk in range(3):
        rib = prism("hat_rib", [(17.0, zsp - 6.0), (25.0, zsp - 6.0), (25.0, zh + 10.0), (17.0, zh + 17.0)],
                    -2.0, 2.0, "XZ")
        rib.data.transform(Matrix.Rotation(math.radians(90 + 120 * kk), 4, "Z"))
        add(acc, rib)
    zd = zfw + P.DRAIN_TAP_R
    add(acc, cyl_y("drain_boss", 0.0, -(ro + 18.0), -(ri + 1.0), zd, P.DRAIN_BOSS_R, SEG_M))
    cut(acc, cyl_y("drain_tap", 0.0, -(ro + 19.0), -40.0, zd, P.DRAIN_TAP_R, SEG_M))
    zp = zrs - 30.0
    ri5, d5 = P.INSERT["M5"]
    add(acc, cyl_y("pin_boss", 0.0, ri + 1.0, ro + 10.0, zp, 8.0, SEG_S))
    cut(acc, cyl_y("pin_insert", 0.0, ro + 10.0 - d5, ro + 11.0, zp, ri5, SEG_S))
    cut(acc, cyl_y("pin_pilot", 0.0, 55.0, ro + 10.0 - d5 + 1.0, zp, P.TAP_M5_PILOT_R, SEG_S))
    gi, go = P.groove_radii_for(P.P9_ORING)
    cut(acc, annulus("p9_groove", 0.0, 0.0, z0 - 1.0, z0 + P.P9_ORING["depth"], gi, go, SEG_L))
    for kk in range(4):
        b = math.radians(90 * kk)
        cut(acc, cyl_z("p9_insert", P.P8_TOP_BOLT_PCD_R * math.cos(b), P.P8_TOP_BOLT_PCD_R * math.sin(b),
                       z0 - 1.0, z0 + d5, ri5, SEG_S))
    return acc


# ============================================================================
# Part 10 — ballast cradle (x2; -Y copy = +Y part rotated 180 deg)
# ============================================================================
def build_part_10():
    log("Part 10: ballast cradle")
    y0 = P.FRAME_HY
    bx, by, bz = P.BALLAST_BLOCK
    hx_in, y_in0, y_in1 = bx / 2 + 3.0, y0 + 6.0, y0 + 6.0 + by + 6.0
    cr = box("Part_10_Ballast_Cradle", -hx_in - 7.0, hx_in + 7.0, y0, y_in1 + 6.0, 0.0, 76.0)
    cut(cr, box("tray", -hx_in, hx_in, y_in0, y_in1, 6.0, 77.0))
    for x in (-130.0, 0.0, 130.0):
        for y in (y_in0 + 54.0, y_in1 - 52.0):
            cut(cr, cyl_z("floor_drain", x, y, -1.0, 7.0, 10.0, SEG_S))
    for x in P.CRADLE_BOLT_X:
        cut(cr, cyl_y("mount_bolt", x, y0 - 1.0, y_in0 + 1.0, P.CRADLE_BOLT_Z, P.CLEAR["M8"]))
    for s in (-1, 1):
        for yc in (y_in0 + 59.0, y_in1 - 57.0):
            xa, xb = sorted((s * (hx_in - 1.0), s * (hx_in + 8.0)))
            cut(cr, box("strap_slot", xa, xb, yc - 15.0, yc + 15.0, 62.0, 70.0))
    return cr


def rotated_copy(ob, name, deg=180.0):
    me = ob.data.copy()
    me.transform(Matrix.Rotation(math.radians(deg), 4, "Z"))
    cp = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(cp)
    return cp


# ============================================================================
# Purchased / reference parts (assembly view only — never exported for printing)
# ============================================================================
def build_reference_parts(col, mats):
    objs = []
    bx, by, bz = P.BALLAST_BLOCK
    for s in (-1, 1):
        y0 = P.FRAME_HY + 6.0 + 3.0
        ya, yb = sorted((s * y0, s * (y0 + by)))
        objs.append(("REF_Ballast_Concrete_Block_400x200x100", box("ref_ballast", -bx / 2, bx / 2, ya, yb, 6.0, 6.0 + bz),
                     mats["concrete"]))
    z_lip = P.P9_Z0 - P.DUCKBILL_CB[1]
    db = revolve("REF_Duckbill_EPDM", [(0.0, P.P9_Z0 - 0.3), (P.DUCKBILL_CB[0] - 0.3, P.P9_Z0 - 0.3),
                                        (P.DUCKBILL_CB[0] - 0.3, z_lip), (P.DUCKBILL_BORE_R - 0.4, z_lip),
                                        (P.DUCKBILL_BORE_R - 0.4, z_lip - 30.0), (6.0, z_lip - P.DUCKBILL_MAX_LEN),
                                        (0.0, z_lip - P.DUCKBILL_MAX_LEN)], SEG_M)
    objs.append(("REF_Duckbill_Check_Valve_EPDM", db, mats["epdm"]))
    L = P.accumulator_levels()
    pipe = revolve("REF_pipe", [(26.3, L["z_shoulder"]), (30.16, L["z_shoulder"]), (30.16, L["z_socket_top"] + 70.0),
                                (26.3, L["z_socket_top"] + 70.0)], SEG_M)
    objs.append(("REF_2in_Sch40_Pipe_Stub", pipe, mats["pvc"]))
    cam = revolve("REF_cam", [(26.3, L["z_socket_top"] + 55.0), (38.0, L["z_socket_top"] + 55.0),
                              (38.0, L["z_socket_top"] + 105.0), (26.3, L["z_socket_top"] + 105.0)], SEG_M)
    objs.append(("REF_2in_Camlock_Adapter", cam, mats["steel"]))
    rings = []
    gi, go = P.groove_radii_for(P.DC_ORING)
    for s in (-1, 1):
        rings.append((s * P.DOWNCOMER_XY[0], P.DOWNCOMER_XY[1], P.M2_Z[1] - 1.0, (gi + go) / 2, 1.31))
    gi, go = P.groove_radii_for(P.P8_ORING)
    rings.append((0.0, 0.0, P.P8_Z0 + 1.35, (gi + go) / 2, 1.765))
    gi, go = P.groove_radii_for(P.P9_ORING)
    rings.append((0.0, 0.0, P.P9_Z0 + 1.35, (gi + go) / 2, 1.765))
    for (x, y, z, rc, rr) in rings:
        prof = [(rc + rr * math.cos(2 * math.pi * k / 16), z + rr * math.sin(2 * math.pi * k / 16)) for k in range(16)]
        o = revolve("REF_oring", prof, SEG_M)
        o.data.transform(Matrix.Translation((x, y, 0.0)))
        objs.append(("REF_O_Ring_EPDM", o, mats["epdm"]))
    # 1.40 m PU feedback U-tube (8 x 10 mm) between the two barbs. It rises vertically on the -Y side
    # of the stack (|X| = 32 mm), i.e. OUTSIDE the bubble plume that rises above the slit lines (|X| > 72).
    bx_, by_ = P.BARB_XY
    zb = P.P5_Z[1] + 20.0
    yo = -80.0

    def u_points(ztop):
        pts_ = [(-bx_, by_, zb), (-bx_, by_, zb + 15.0), (-bx_, yo, zb + 21.0), (-bx_, yo, ztop)]
        for k in range(1, 24):
            a = math.pi - math.pi * k / 24
            pts_.append((bx_ * math.cos(a), yo, ztop + bx_ * math.sin(a)))
        return pts_ + [(bx_, yo, ztop), (bx_, yo, zb + 21.0), (bx_, by_, zb + 15.0), (bx_, by_, zb)]

    def u_len(ztop):
        p_ = u_points(ztop)
        return sum(math.dist(p_[i], p_[i + 1]) for i in range(len(p_) - 1))

    ztop = 500.0 + (1400.0 - u_len(500.0)) / 2.0     # length is linear in ztop (two vertical legs)
    pts = u_points(ztop)
    cu = bpy.data.curves.new("loop", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (*p, 1.0)
    cu.bevel_depth = 5.0
    cu.bevel_resolution = 3
    cob = bpy.data.objects.new("loop_curve", cu)
    bpy.context.scene.collection.objects.link(cob)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(cob.evaluated_get(dg))
    bpy.data.objects.remove(cob, do_unlink=True)
    tube = bpy.data.objects.new("REF_Feedback_Loop_PU_8x10", me)
    bpy.context.scene.collection.objects.link(tube)
    length = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    log(f"  reference feedback loop length drawn: {length:.0f} mm (specify 1400 mm, TRL-4 sweep 1100/1400/1900)")
    objs.append(("REF_Feedback_Loop_PU_8x10_L1400", tube, mats["pu"]))
    out = []
    for name, o, m in objs:
        o.name = name
        o.data.materials.append(m)
        for c in o.users_collection:
            c.objects.unlink(o)
        col.objects.link(o)
        out.append(o)
    return out


# ============================================================================
# Main
# ============================================================================
def main():
    fails = [r for r in P.rule_checks() if not r[3]]
    if fails:
        raise SystemExit("Design rule check failed: " + "; ".join(f"{a}={b} (req {c})" for a, b, c, _ in fails))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.length_unit = "MILLIMETERS"
    sc.unit_settings.scale_length = 0.001
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    parts = [
        ("Part_01_Benthic_Base_Chassis", build_part_01, 1, "PETG/ASA large-format FDM or MJF PA12; HDPE CNC alt."),
        ("Part_02_Twin_Plenum_Manifold", build_part_02, 1, "MJF PA12 or CF-PETG, print on +Y end face"),
        ("Part_04_Coanda_Oscillator_Core_Block", build_part_04, 1, "MJF PA12 / SLA tough, cavity face up"),
        ("Part_05_Oscillator_Top_Cover_Plate", build_part_05, 1, "PETG/PA12, bottom face on bed"),
        ("Part_06_Slit_Cartridge_BankA", lambda: None, 1, "SLA tough/MJF PA12 or wire-EDM 316L, print on Y end"),
        ("Part_07_Slit_Cartridge_BankB", lambda: build_cartridge("Part_07_Slit_Cartridge_BankB"), 1,
         "identical to Part 06 (rotated 180 deg)"),
        ("Part_08_Duckbill_Check_Valve_Spool", build_part_08, 1, "PETG/PA12 upright, support under top flange"),
        ("Part_09_Accumulator_Condensate_Separator", build_part_09, 1, "PETG/PA12 upright"),
        ("Part_10_Ballast_Cradle", build_part_10, 2, "PETG/ASA, floor on bed; 2 per module"),
    ]
    mats = {
        "Part_01": material("M_Chassis", (0.10, 0.11, 0.12), 0.6), "Part_02": material("M_Manifold", (0.16, 0.30, 0.44), 0.45),
        "Part_04": material("M_Osc", (0.08, 0.42, 0.46), 0.4), "Part_05": material("M_Cover", (0.55, 0.62, 0.68), 0.45),
        "Part_06": material("M_Cart", (0.86, 0.45, 0.10), 0.35),
        "Part_08": material("M_Spool", (0.12, 0.20, 0.34), 0.45), "Part_09": material("M_Acc", (0.72, 0.74, 0.77), 0.4),
        "Part_10": material("M_Cradle", (0.18, 0.18, 0.19), 0.7),
        "concrete": material("M_Concrete", (0.52, 0.51, 0.48), 0.9), "epdm": material("M_EPDM", (0.02, 0.02, 0.02), 0.8),
        "pvc": material("M_PVC", (0.85, 0.86, 0.88), 0.4), "steel": material("M_Steel", (0.75, 0.76, 0.78), 0.3, 0.9),
        "pu": material("M_PU", (0.25, 0.55, 0.95), 0.25, 0.0, 0.6),
    }
    mats["Part_07"] = mats["Part_06"]
    col_print = bpy.data.collections.new("SPD_V3_Printed_Parts")
    col_ref = bpy.data.collections.new("SPD_V3_Purchased_Reference")
    sc.collection.children.link(col_print)
    sc.collection.children.link(col_ref)

    manifest = {"version": P.VERSION, "units": "mm", "frame": "assembly coordinates (pond bed Z=0)", "parts": {}}
    built = {}
    cart06 = None
    for name, fn, qty, note in parts:
        if name.startswith("Part_06"):
            continue
        ob = fn()
        ob.name = name
        built[name] = ob
        if name.startswith("Part_07"):
            cart06 = rotated_copy(ob, "Part_06_Slit_Cartridge_BankA")
            built["Part_06_Slit_Cartridge_BankA"] = cart06
    for name, fn, qty, note in parts:
        ob = built[name]
        info = finalize(ob)
        info.update(qty=qty, note=note, stl=f"{name}.stl")
        manifest["parts"][name] = info
        export_stl(ob, os.path.join(OUTPUT_DIR, f"{name}.stl"))
        log(f"  [OK] {name}: {info['volume_cm3']} cm3, {info['faces']} faces, bbox {info['bbox']}")
        ob.data.materials.clear()            # booleans leave an empty slot 0 behind
        ob.data.materials.append(mats[name[:7]])
        for poly in ob.data.polygons:
            poly.material_index = 0
        for c in ob.users_collection:
            c.objects.unlink(ob)
        col_print.objects.link(ob)
    cradle_b = rotated_copy(built["Part_10_Ballast_Cradle"], "Part_10_Ballast_Cradle_(-Y_copy)")
    for c in cradle_b.users_collection:
        c.objects.unlink(cradle_b)
    col_print.objects.link(cradle_b)

    build_reference_parts(col_ref, mats)
    manifest["design_checks"] = [dict(rule=a, value=b, requirement=c, ok=d) for a, b, c, d in P.rule_checks()]
    manifest["derived"] = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in P.derived().items()}
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUTPUT)
    try:
        bpy.ops.export_scene.gltf(filepath=GLB_OUTPUT, export_format="GLB", use_selection=False)
    except Exception as e:  # visualisation only; printing uses the STLs
        log(f"  GLB export skipped: {e}")
    log(f"Saved {BLEND_OUTPUT}")
    log("SPD V3.0 CAD GENERATION COMPLETE")


if __name__ == "__main__":
    main()
