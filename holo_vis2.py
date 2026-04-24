from ursina import *
from ursina.prefabs.editor_camera import EditorCamera

app = Ursina(title="GLB Import Test")

# Add a ground grid so you can see exactly where the center of the world (0,0,0) is.
Entity(model='grid_20x20', color=color.gray, rotation_x=90)

# 1. LOAD THE LIBRARY
library_env = Entity(
    model='library.glb',
    scale=20,           # Scaled up
    double_sided=True,  # Prevents walls from turning invisible
    color=color.light_gray # Fallback color in case textures fail
)

# 2. LOAD THE CHARACTER (Parented to Library)
librarian = Entity(
    model='AnimeCharacter.glb',
    parent=library_env,
    scale=0.05,         # Try to normalize scale relative to the library
    position=(0, 0, 0), # Dead center of the library's local space
    color=color.red     # Tinted RED so you cannot miss them!
)

# 3. LIGHTING (Crucial for seeing models properly)
sun = DirectionalLight(y=10, z=-10, shadows=True)
sun.look_at(Vec3(0, 0, 0))
AmbientLight(color=color.rgba(150, 150, 150, 1))

# 4. CAMERA
EditorCamera() # Use Right-Click + WASD to fly around the scene

# 5. DEBUG TOOLS
def input(key):
    # Press SPACEBAR in the game window to print their exact coordinates to your terminal
    if key == 'space':
        print(f"--- DEBUG INFO ---")
        print(f"Library World Position: {library_env.world_position}")
        print(f"Librarian World Position: {librarian.world_position}")
        print(f"Librarian World Scale: {librarian.world_scale}")

app.run()
