
import bpy
import json
from pathlib import Path
from math import sin, cos

film_dir = Path(r"C:\\Users\\Long\\Documents\\animation-factory\\films\\demo-001")
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
