from ursina import *
from ursina.prefabs.editor_camera import EditorCamera

app = Ursina(title="Scene Inspector: Library vs Character")
window.color = color.dark_gray

# ========== 1. MARKERS FOR ORIGIN (0,0,0) ==========
# This shows where the world center is
origin_marker = Entity(
    model='sphere',
    scale=1,
    position=(0, 0, 0),
    color=color.red,
    emissive=True
)
origin_text = Text(text="ORIGIN (0,0,0)", position=(0.1, 0), scale=2, color=color.red)

# ========== 2. LOAD LIBRARY ==========
print("Loading library.glb...")
library = Entity(
    model='library.glb',
    scale=1,  # Start at normal scale to see its true size
    position=(0, 0, 0),
    color=color.white
)

# ========== 3. LOAD CHARACTER ==========
print("Loading AnimeCharacter.glb...")
character = Entity(
    model='AnimeCharacter.glb',
    scale=1,
    position=(5, 0, 0), # Place character 5 units to the right of origin
    color=color.cyan
)

# ========== 4. INSPECT LIBRARY POSITION ==========
# Get the bounding box to see where the library actually is
if library.model:
    bounds = library.bounds
    center = bounds.center
    print(f"🏛️ Library Center is at: {center}")
    print(f"📏 Library Size: {bounds.size}")
    
    # Add a marker at the library's TRUE center
    lib_center_marker = Entity(
        model='sphere',
        scale=2,
        position=center,
        color=color.yellow,
        emissive=True
    )
    print(f"💛 Yellow Marker placed at Library's True Center: {center}")

# ========== 5. CONTROLS ==========
def input(key):
    if key == 'space':
        # Move camera to look at Library's true center
        if library.model:
            cam_pos = library.bounds.center + Vec3(0, 10, -20)
            camera.position = cam_pos
            camera.look_at(library.bounds.center)
            print("📷 Camera focused on Library Center")
    
    if key == 'escape':
        application.quit()

# ========== 6. INSTRUCTIONS ==========
Text(text='''
INSPECTION MODE
----------------
Red Sphere  = World Origin (0,0,0)
Yellow Sphere = Center of Library
Cyan Figure = Character (at X=5)

Controls:
SPACE   - Focus Camera on Library
ESC     - Quit
''', position=(-0.85, 0.45), scale=1.5, color=color.lime, background=True)

EditorCamera(speed=20)
app.run()
