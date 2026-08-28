import json
from pathlib import Path
import textwrap

# Generates Blender Python scripts that can be executed headless: blender -b -P <script>

TEMPLATE_BUILD = r'''
import bpy
import json
import math
from pathlib import Path

# Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# --- Config from factory ---
film_dir = Path(r"__FILM_DIR__")
shots_path = film_dir / "shots.json"
style = "__STYLE__"
engine = "__ENGINE__"

# Load shots
shots = []
if shots_path.exists():
    shots = json.loads(shots_path.read_text(encoding="utf-8")).get("shots", [])

# Render settings (EEVEE tuned for old NVIDIA like GTX 650 Ti 1GB)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = __RES_X__
scene.render.resolution_y = __RES_Y__
scene.render.resolution_percentage = 100
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_depth = '8'
scene.render.filepath = str(film_dir / "render" / "frames" / "frame_####")
scene.render.fps = __FPS__
# EEVEE settings
if hasattr(scene, "eevee"):
    ee = scene.eevee
    # Blender 3.x vs 4.x API compat
    for attr, val in [("use_gtao", True), ("use_bloom", True), ("use_ssr", False)]:
        if hasattr(ee, attr):
            setattr(ee, attr, val)
    if hasattr(ee, "taa_render_samples"):
        ee.taa_render_samples = __SAMPLES__
    if hasattr(ee, "taa_samples"):
        ee.taa_samples = __SAMPLES__

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
'''

TEMPLATE_ANIMATE = r'''
import bpy
import json
from pathlib import Path
from math import sin, cos

film_dir = Path(r"__FILM_DIR__")
shots_path = film_dir / "shots.json"
blend_path = film_dir / "scenes" / "shot_master.blend"

if blend_path.exists():
    bpy.ops.wm.open_mainfile(filepath=str(blend_path))
else:
    print(f"WARNING: master blend not found at {blend_path}, using current scene")

scene = bpy.context.scene
shots = []
if shots_path.exists():
    shots = json.loads(shots_path.read_text(encoding="utf-8")).get("shots", [])

fps = scene.render.fps
frame = 1
scene.frame_start = 1

# Find hero head for simple bob animation
hero = bpy.data.objects.get("Hero_Head") or bpy.data.objects.get("Hero_Body")

# Animate per shot: camera switch + hero bob
for shot in shots:
    dur = float(shot.get("duration_sec", 5.0))
    frames = int(dur * fps)
    cam_type = shot.get("camera", "medium")
    # Simple camera positions per type
    cam_positions = {
        "wide": (7, -7, 5),
        "medium": (4, -5, 2.5),
        "closeup": (1.5, -2.5, 1.8),
        "over_shoulder": (1, -3, 1.7),
        "dutch": (5, -5, 4)
    }
    pos = cam_positions.get(cam_type, (4, -5, 2.5))
    if scene.camera:
        scene.camera.location = pos
        scene.camera.keyframe_insert(data_path="location", frame=frame)
        # slight rotation jitter for life
        scene.camera.rotation_euler[2] = 0.78 + 0.05 * sin(frame * 0.05)
        scene.camera.keyframe_insert(data_path="rotation_euler", frame=frame)
    # Hero bob
    if hero:
        hero.location.z = 1.6 + 0.12 * sin(frame * 0.2)
        hero.keyframe_insert(data_path="location", frame=frame)
        hero.keyframe_insert(data_path="location", frame=frame + frames // 2)
    frame += frames

scene.frame_end = max(frame - 1, 24)
print(f"Animated {len(shots)} shots, total frames: {scene.frame_end}")

# Save animated blend
out = film_dir / "scenes" / "shot_animated.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print(f"Saved animated blend to {out}")
'''

def run(film_dir: Path, config: dict, dry_run: bool = False, mode="build"):
    film_dir = Path(film_dir)
    render_cfg = config.get("render", {})
    res = render_cfg.get("resolution", [1920, 1080])
    if isinstance(res, list) and len(res) == 2:
        res_x, res_y = res
    else:
        res_x, res_y = 1920, 1080
    fps = render_cfg.get("fps", 24) if isinstance(render_cfg, dict) else 24
    samples = render_cfg.get("samples", 16) if isinstance(render_cfg, dict) else 16
    engine = render_cfg.get("engine", "BLENDER_EEVEE")
    style = config.get("preset", config.get("style", "pixar"))

    scenes_dir = film_dir / "scenes"
    scenes_dir.mkdir(parents=True, exist_ok=True)
    (film_dir / "render" / "frames").mkdir(parents=True, exist_ok=True)

    if mode == "build":
        script_path = film_dir / "scripts" / "build_scene.py"
        content = TEMPLATE_BUILD.replace("__FILM_DIR__", str(film_dir).replace("\\", "\\\\")).replace("__STYLE__", style).replace("__ENGINE__", engine).replace("__RES_X__", str(res_x)).replace("__RES_Y__", str(res_y)).replace("__FPS__", str(fps)).replace("__SAMPLES__", str(samples))
    else:
        script_path = film_dir / "scripts" / "animate.py"
        content = TEMPLATE_ANIMATE.replace("__FILM_DIR__", str(film_dir).replace("\\", "\\\\"))

    script_path.parent.mkdir(parents=True, exist_ok=True)
    if dry_run:
        print(f"[dry-run] would write {script_path} ({len(content)} bytes) mode={mode}")
        # also preview first 20 lines
        print("\n".join(content.splitlines()[:12]))
        return {"script": str(script_path), "dry_run": True, "mode": mode}

    script_path.write_text(content, encoding="utf-8")
    print(f"Wrote Blender script: {script_path} (mode={mode})")
    # Try to hint execution
    print(f"To execute: blender -b -P \"{script_path}\"")
    return {"script": str(script_path), "mode": mode}
