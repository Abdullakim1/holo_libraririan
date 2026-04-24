from ursina import *
from ursina.prefabs.editor_camera import EditorCamera

app = Ursina(title="HOLO - Center Spawn", borderless=True, fullscreen=True)
window.color = color.black

# ========== 1. THE LIBRARY ==========
library = Entity(
    model='library.glb',
    scale=20,
    position=(0, 0, 0),
    color=color.white
)

# ========== 2. LIGHTING ==========
AmbientLight(color=color.rgba(255, 255, 255, 1))
DirectionalLight(y=10, z=3, shadows=False, color=color.white) # Shadows off to prevent hiding
PointLight(position=(0, 10, 0), range=50, color=color.white)

# ========== 3. CHARACTER & MARKERS ==========
librarian = None
marker_head = None
marker_feet = None

def summon_character():
    global librarian, marker_head, marker_feet
    
    # Destroy old ones if they exist
    if librarian: destroy(librarian)
    if marker_head: destroy(marker_head)
    if marker_feet: destroy(marker_feet)
    
    # FIXED POSITION: Center of the room (0, 0, 0)
    center_pos = Vec3(0, 0.1, 0)
    
    print(f"📍 Summoning at CENTER: {center_pos}")
    
    # 1. GIANT RED SPHERE (Head Marker) - IMPOSSIBLE TO MISS
    marker_head = Entity(
        model='sphere',
        scale=2, # Big ball
        position=center_pos + Vec3(0, 2.5, 0), # At head height
        color=color.red,
        emissive=True
    )
    
    # 2. GIANT GREEN CUBE (Feet Marker)
    marker_feet = Entity(
        model='cube',
        scale=(1, 0.2, 1), # Flat square on floor
        position=center_pos,
        color=color.green,
        emissive=True
    )
    
    # 3. THE CHARACTER
    librarian = Entity(
        model='AnimeCharacter.glb',
        position=center_pos,
        scale=10,          # LARGE SCALE
        rotation=(0, 180, 0),
        color=color.white,
        double_sided=True,
        emissive=True      # Glow to ensure visibility
    )
    
    # 4. MOVE CAMERA TO LOOK AT THEM
    # Place camera at entrance, looking at center
    camera.position = (0, 3, -12)
    camera.look_at(center_pos + Vec3(0, 1, 0))
    
    print("✨ CHARACTER SUMMONED AT CENTER!")
    print("🔴 You should see a GIANT RED SPHERE floating in the center.")
    print("🟩 You should see a GREEN SQUARE on the floor.")
    print("👩‍💼 The Anime Character should be standing on the Green Square.")

# ========== 4. INITIAL CAMERA SETUP ==========
camera.position = (0, 5, -20) # Start outside
camera.look_at((0, 2, 0))

# ========== 5. CONTROLS ==========
def input(key):
    if key == 'i':
        # Teleport inside
        camera.position = (0, 3, -12)
        camera.look_at((0, 1, 0))
        print("📍 Moved inside library")
        
    if key == 'space':
        summon_character()
        
    if key == 'up arrow' and librarian:
        librarian.scale *= 1.5
        print(f"📏 Character Scale: {librarian.scale}")
        
    if key == 'escape':
        application.quit()

# ========== 6. INSTRUCTIONS ==========
Text(text='''
CONTROLS:
I       - Go Inside
SPACE   - Spawn Character at CENTER (Look for Red Sphere!)
UP      - Grow Character
ESC     - Quit
''', position=(-0.85, 0.45), scale=1.5, color=color.lime, background=True)

print("\n" + "="*60)
print("🎯 CENTER SPAWN MODE")
print("Press 'SPACE' to spawn everything in the CENTER of the room.")
print("Camera will auto-aim at the center.")
print("Look for the RED SPHERE.")
print("="*60 + "\n")

EditorCamera(speed=20)
app.run()
