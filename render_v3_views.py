"""
SPD V3.0 — engineering renders straight from the generated assembly (Blender, background).
Run:  "D:\\blender\\blender.exe" --background --factory-startup --python render_v3_views.py
Then: python annotate_v3_views.py   (adds title block + leader-line labels)

Views: hero isometric, section A-A (Y = downcomer plane), section B-B (X = 0, supply stack),
section C-C (Z through the oscillator cavity, plan view). Label anchors are projected to image
coordinates and written to renders_V3/labels.json.
"""

import json
import math
import os

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
import sys  # noqa: E402
sys.path.insert(0, HERE)
import spd_design_params as P  # noqa: E402

BLEND = os.path.join(HERE, "Pulsed_Diffuser_Functional_Production.blend")
OUT = os.path.join(HERE, "renders_V3")
os.makedirs(OUT, exist_ok=True)
L = P.accumulator_levels()
DCX, DCY = P.DOWNCOMER_XY
ZS = P.SLIT_EXIT_Z_LOW

VIEWS = [
    dict(name="V3_1_Assembly_Isometric", res=(1800, 1200), persp=dict(loc=(1250, -1500, 1050), lens=44),
         target=(0, 30, 400), cut=None, hide=[],
         labels=[("09  Accumulator / condensate separator 4.3 L", (0, 68, 560)),
                 ("2in Camlock inlet (pipe stub)", (0, 0, L["z_socket_top"] + 80)),
                 ("1/2in NPT condensate drain", (0, -84, 337)),
                 ("08  Duckbill check-valve spool", (40, -30, 260)),
                 ("Feedback U-tube PU 8x10, L = 1.40 m (outside plume)", (-32, -80, 620)),
                 ("04/05  Coanda oscillator + cover", (54, -60, 190)),
                 ("02  Twin-plenum manifold", (40, -146, 150)),
                 ("07  Slit cartridge B: 11 x (1.0 x 20) mm", (72, -60, 127)),
                 ("01  Chassis + floor deflector (+20 deg lip)", (200, -60, 95)),
                 ("10  Ballast cradle + concrete block (x2)", (150, -300, 90))]),
    dict(name="V3_2_Section_AA_Downcomers", res=(1800, 1150), ortho=dict(axis="-Y", scale=560),
         target=(0, 0, 175), cut=("Y", DCY, +1), hide=["REF_Feedback", "REF_2in", "REF_Ballast"],
         labels=[("Downcomer A", (-DCX, DCY, 170)), ("Downcomer B", (DCX, DCY, 170)),
                 ("Oscillator outputs A/B (Part 04)", (-15, DCY, 186)),
                 ("Integral A/B divider", (0, DCY, 140)),
                 ("Plenum duct A (Part 02)", (-30, DCY, 138)), ("Plenum duct B", (30, DCY, 138)),
                 ("Cartridge pocket", (58, DCY, 138)),
                 ("Slit 1.0 mm, 20 deg down", (70, DCY, ZS + 0.5)),
                 ("Floor deflector, +20 deg lip", (215, DCY, 97)),
                 ("Pedestal (M8 to Part 02)", (-30, DCY, 100)),
                 ("Part 05 cover + barbs", (-32, DCY, 205))]),
    dict(name="V3_3_Section_BB_Supply_Stack", res=(1150, 1800), ortho=dict(axis="+X", scale=880),
         target=(0, -10, 450), cut=("X", 0.0, +1), hide=["REF_Feedback", "Part_10", "REF_Ballast"],
         labels=[("2in socket + Camlock", (0, 0, L["z_socket_top"] + 20)),
                 ("Inlet jet -> hat (demister)", (0, 0, L["z_sp_top"] + 30)),
                 ("Standpipe gas outlet (+120 mm)", (0, 18, L["z_sp_top"] - 40)),
                 ("P_in tap (M5)", (0, 75, L["z_roof_start"] - 30)),
                 ("Condensate sump, 5 deg floor", (0, -55, 330)),
                 ("1/2in NPT drain", (0, -80, 337)),
                 ("Duckbill (EPDM) in Part 08", (0, 0, 262)),
                 ("Supply plenum", (0, 0, 186)), ("Power nozzle b = 6 mm", (0, -33, 186)),
                 ("Splitter apex (6b)", (0, -74, 186)),
                 ("Central divider / pedestal", (0, 40, 120))]),
    dict(name="V3_4_Section_CC_Oscillator_Plan", res=(1800, 1150), ortho=dict(axis="-Z", scale=240),
         target=(0, -42, 190), cut=("Z", P.P4_Z[1] - 1.0, -1), hide=["REF_"],
         labels=[("Supply plenum (inlet dia 32 from above)", (0, 0, 193)),
                 ("Power nozzle 6 x 16 mm", (0, -33, 193)),
                 ("Control port A -> loop barb", (-30, -39, 193)),
                 ("Control port B -> loop barb", (30, -39, 193)),
                 ("Coanda attachment walls 12 deg", (-9, -58, 193)),
                 ("Splitter apex, 6 b downstream", (0, -73, 193)),
                 ("Output A -> downcomer A", (-DCX, DCY, 193)),
                 ("Output B -> downcomer B", (DCX, DCY, 193)),
                 ("O-ring groove 2.62 cord", (-39.8, -20, 193)),
                 ("M5 through-bolt to Part 02", (48, 0, 193))]),
]


def setup_scene():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 64
    sc.cycles.use_denoising = True
    sc.view_settings.view_transform = "AgX" if "AgX" in [i.identifier for i in
                                                        sc.view_settings.bl_rna.properties["view_transform"].enum_items] else "Filmic"
    w = bpy.data.worlds.new("W") if sc.world is None else sc.world
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.90, 0.92, 0.94, 1.0)
    bg.inputs["Strength"].default_value = 0.75
    for name, rot, e in (("Sun_Key", (50, 10, 35), 3.2), ("Sun_Fill", (65, -20, -140), 1.2)):
        ld = bpy.data.lights.new(name, "SUN")
        ld.energy = e
        ld.angle = math.radians(8)
        lo = bpy.data.objects.new(name, ld)
        lo.rotation_euler = [math.radians(a) for a in rot]
        sc.collection.objects.link(lo)
    cam_d = bpy.data.cameras.new("Cam")
    cam_d.clip_start, cam_d.clip_end = 5.0, 20000.0
    cam = bpy.data.objects.new("Cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    return sc, cam


def aim(cam, loc, target):
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def mesh_objects():
    return [o for o in bpy.data.objects if o.type == "MESH"]


def apply_cut(axis, value, keep):
    big = 5000.0
    lo = [-big, -big, -big]
    hi = [big, big, big]
    i = "XYZ".index(axis)
    if keep > 0:
        hi[i] = value            # remove the negative side ... keep > value
    else:
        lo[i] = value            # remove the positive side ... keep < value
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    cutter = bpy.context.active_object
    cutter.name = "SECTION_CUTTER"
    cutter.scale = [hi[k] - lo[k] for k in range(3)]
    cutter.location = [(hi[k] + lo[k]) / 2 for k in range(3)]
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    cut_mat = bpy.data.materials.get("M_SectionCut") or bpy.data.materials.new("M_SectionCut")
    bsdf = cut_mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.78, 0.20, 0.14, 1.0)   # cut faces shown in section red
    bsdf.inputs["Roughness"].default_value = 0.7
    cutter.data.materials.append(cut_mat)
    for o in mesh_objects():
        if o is cutter or o.hide_render:
            continue
        m = o.modifiers.new("SECTION", "BOOLEAN")
        m.operation = "DIFFERENCE"
        m.solver = "EXACT"
        m.material_mode = "TRANSFER"
        m.object = cutter
    return cutter


def clear_cut(cutter):
    for o in mesh_objects():
        for m in list(o.modifiers):
            if m.name == "SECTION":
                o.modifiers.remove(m)
    bpy.data.objects.remove(cutter, do_unlink=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND)
    sc, cam = setup_scene()
    labels_out = {}
    for v in VIEWS:
        sc.render.resolution_x, sc.render.resolution_y = v["res"]
        for o in mesh_objects():
            o.hide_render = any(o.name.startswith(h) for h in v["hide"])
        if "persp" in v:
            cam.data.type = "PERSP"
            cam.data.lens = v["persp"]["lens"]
            aim(cam, v["persp"]["loc"], v["target"])
        else:
            cam.data.type = "ORTHO"
            cam.data.ortho_scale = v["ortho"]["scale"]
            t = Vector(v["target"])
            ax = v["ortho"]["axis"]
            off = {"-Y": Vector((0, -2500, 0)), "+X": Vector((-2500, 0, 0)), "-Z": Vector((0, 0, 2500))}[ax]
            cam.location = t + off
            # explicit orientations: look +Y (up Z) / look +X (up Z) / look -Z (up Y)
            rot = {"-Y": (90.0, 0.0, 0.0), "+X": (90.0, 0.0, -90.0), "-Z": (0.0, 0.0, 0.0)}[ax]
            cam.rotation_euler = [math.radians(a) for a in rot]
        cutter = apply_cut(*v["cut"]) if v["cut"] else None
        bpy.context.view_layer.update()
        sc.render.filepath = os.path.join(OUT, v["name"] + "_raw.png")
        bpy.ops.render.render(write_still=True)
        rx, ry = v["res"]
        labels_out[v["name"]] = []
        for text, p in v["labels"]:
            c = world_to_camera_view(sc, cam, Vector(p))
            labels_out[v["name"]].append(dict(text=text, x=round(c.x * rx, 1), y=round((1 - c.y) * ry, 1)))
        if cutter:
            clear_cut(cutter)
        print("rendered", v["name"])
    with open(os.path.join(OUT, "labels.json"), "w", encoding="utf-8") as f:
        json.dump(labels_out, f, indent=2)


if __name__ == "__main__":
    main()
