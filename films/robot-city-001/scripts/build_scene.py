
import bpy
import json
import math
from pathlib import Path

# Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# --- Config from factory ---
film_dir = Path(r"C:\\Users\\Long\\Documents\\animation-factory\\films\\robot-city-001")
shots_path = film_dir / "shots.json"
style = "pixar"
engine = "BLENDER_EEVEE"

# Load shots
shots = []
if shots_path.exists():
    shots = json.loads(shots_path.read_text(encoding="utf-8")).get("shots", [])

# Render settings (EEVEE tuned for old NVIDIA like GTX 650 Ti 1GB)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_depth = '8'
scene.render.filepath = str(film_dir / "render" / "frames" / "frame_####")
scene.render.fps = 24
# EEVEE settings
if hasattr(scene, "eevee"):
    ee = scene.eevee
    # Blender 3.x vs 4.x API compat
    for attr, val in [("use_gtao", True), ("use_bloom", True), ("use_ssr", False)]:
        if hasattr(ee, attr):
            setattr(ee, attr, val)
    if hasattr(ee, "taa_render_samples"):
        ee.taa_render_samples = 16
    if hasattr(ee, "taa_samples"):
        ee.taa_samples = 16

# --- World / HDRI fallback (simple studio) ---
world = bpy.data.worlds.new("FactoryWorld")
bpy.context.scene.world = world
world.use_nodes = True
# Keep default nodes for now

# --- Camera (safe frame for multi-aspect) ---
bpy.ops.object.camera_add(location=(7, -7, 5), rotation=(1.1, 0, 0.785))
cam = bpy.context.object
cam.name = "FactoryCamera"
scene.camera = cam
cam.data.lens = 50
# Safe area visualization is manual in Blender, we ensure framing is centered

# --- Lights (Pixar 3-point) ---
bpy.ops.object.light_add(type='SUN', location=(5, -5, 8))
key = bpy.context.object
key.name = "KeyLight"
key.data.energy = 1000
bpy.ops.object.light_add(type='SUN', location=(-5, -3, 6))
fill = bpy.context.object
fill.name = "FillLight"
fill.data.energy = 500
fill.data.color = (0.8, 0.9, 1.0)
bpy.ops.object.light_add(type='POINT', location=(0, 0, 3))
rim = bpy.context.object
rim.name = "RimLight"
rim.data.energy = 800
rim.data.color = (0.6, 0.8, 1.0)

# --- Ground ---
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,0))
ground = bpy.context.object
ground.name = "Ground"
mat = bpy.data.materials.new("GroundMat")
mat.use_nodes = True
ground.data.materials.append(mat)

# --- Pixar-style character proxy (chibi) ---
def create_pixar_character(name="Hero"):
    # Simple proxy: sphere head + capsule body — replaceable with rigged asset
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(0,0,1.6))
    head = bpy.context.object
    head.name = f"{name}_Head"
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=1.0, location=(0,0,0.8))
    body = bpy.context.object
    body.name = f"{name}_Body"
    # Pixar shader
    mat = bpy.data.materials.new(f"{name}_Mat")
    mat.use_nodes = True
    nodes = mat.node_graph if hasattr(mat, "node_graph") else mat.node_tree
    # Use node_tree compat
    nt = mat.node_tree
    principled = nt.nodes.get("Principled BSDF")
    if principled:
        principled.inputs["Base Color"].default_value = (0.95, 0.82, 0.65, 1)
        if "Subsurface Weight" in principled.inputs:
            principled.inputs["Subsurface Weight"].default_value = 0.12
        elif "Subsurface" in principled.inputs:
            principled.inputs["Subsurface"].default_value = 0.12
        principled.inputs["Roughness"].default_value = 0.45
        if "Specular IOR Level" in principled.inputs:
            principled.inputs["Specular IOR Level"].default_value = 0.5
    for obj in [head, body]:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
    return head, body

create_pixar_character("Hero")

# --- Simple set piece ---
bpy.ops.mesh.primitive_cube_add(size=1.5, location=(2,0,0.75))
prop = bpy.context.object
prop.name = "PropBox"

# Save blend
blend_path = film_dir / "scenes" / "shot_master.blend"
blend_path.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
print(f"Saved master blend to {blend_path}")
print(f"Shots loaded: {len(shots)}")
