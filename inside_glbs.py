from ursina import *
from ursina.prefabs.editor_camera import EditorCamera

app = Ursina()

# 1. THE BUILDING
library_env = Entity(
    model='library.glb', 
    scale=20, 
    position=(0, 0, 0),
    double_sided=True # Crucial so you can see walls from inside
)

# 2. THE LIBRARIAN (Summonable)
librarian = Entity(
    model='AnimeCharacter.glb',
    parent=library_env,
    scale=0.1,         # Start small
    position=(0, 0, 0)
)

# 3. LIGHTING
sun = DirectionalLight(y=10, z=-10)
sun.look_at(Vec3(0,0,0))
AmbientLight(color=color.rgba(120, 120, 120, 1))

# 4. CAMERA
cam = EditorCamera()

def input(key):
    # TELEPORT TRIGGER
    if key == 'g':
        # This forces the character to jump to exactly where you are looking
        librarian.world_position = cam.world_position + cam.forward * 5
        print(f"Librarian summoned to: {librarian.world_position}")
    
    # SCALE CONTROLS (In case he's too small/big)
    if key == 'up arrow':
        librarian.scale *= 1.2
    if key == 'down arrow':
        librarian.scale *= 0.8

# Instructions UI
Text(text="Press 'G' to summon Librarian to your face\nUse arrows to change size", 
     position=(-0.5, 0.4), scale=1.5, color=color.yellow)

app.run()
