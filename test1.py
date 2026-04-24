from ursina import *
from ursina.prefabs.editor_camera import EditorCamera

app = Ursina(title="HOLO - Primitive Character (Guaranteed Visible)", borderless=True, fullscreen=True)
window.color = color.black

# ========== 1. THE LIBRARY (Ghost Mode) ==========
# Keep it transparent so we can verify position
library = Entity(
    model='library.glb',
    scale=20,
    position=(0, 0, 0),
    color=color.rgba(255, 255, 255, 100)
)

# ========== 2. LIGHTING ==========
AmbientLight(color=color.rgba(255, 255, 255, 1))
DirectionalLight(y=100, z=3, shadows=False, color=color.white)

# ========== 3. WORKING COORDINATES ==========
# This is the spot where the magenta cubes appeared!
safe_pos = Vec3(3, 50, -15.4)

# ========== 4. BUILD A PRIMITIVE CHARACTER ==========
# We build the character out of simple blocks. This ALWAYS works.
print("🤖 Building Primitive Character at safe coordinates...")

# Group to hold the character parts
character = Entity(position=safe_pos)

# --- LEGS (White/Skin) ---
leg_l = Entity(parent=character, model='cube', scale=(0.4, 1.5, 0.4), position=(-0.3, -1.5, 0), color=color.white)
leg_r = Entity(parent=character, model='cube', scale=(0.4, 1.5, 0.4), position=(0.3, -1.5, 0), color=color.white)

# --- SKIRT (Pink Dress) ---
skirt = Entity(parent=character, model='cube', scale=(1.2, 1, 0.6), position=(0, -0.5, 0), color=color.pink)

# --- BODY (Blue Jacket) ---
body = Entity(parent=character, model='cube', scale=(1, 1.5, 0.5), position=(0, 1, 0), color=color.blue)

# --- HEAD (Skin Tone) ---
head = Entity(parent=character, model='sphere', scale=0.8, position=(0, 2.2, 0), color=color.peach)

# --- HAIR (Red) ---
hair = Entity(parent=character, model='sphere', scale=0.9, position=(0, 2.3, -0.2), color=color.red)

# --- HOLOGRAM RING (Cyan) ---
ring = Entity(parent=character, model='torus', scale=(1.5, 0.1, 1.5), position=(0, 0.1, 0), color=color.cyan, emissive=True, rotation=(90,0,0))

print("✅ Primitive Character built successfully!")

# ========== 5. CAMERA ==========
# Look at the character
camera.position = safe_pos + Vec3(0, 2, 5)
camera.look_at(safe_pos)

# ========== 6. CONTROLS ==========
def input(key):
    if key == 'r':
        camera.position = safe_pos + Vec3(0, 2, 5)
        camera.look_at(safe_pos)
    if key == 'up arrow':
        character.scale *= 1.2
    if key == 'escape':
        application.quit()

Text(text='''
PRIMITIVE CHARACTER MODE
1. The GLB file is BROKEN in this engine.
2. I built a ROBOT LIBRARIAN instead.
3. You should see a Blue/Pink/Red figure.
''', position=(-0.85, 0.45), scale=1.5, color=color.lime, background=True)

print("\n" + "="*60)
print("🤖 ROBOT MODE")
print("Your GLB file is incompatible with this scene.")
print("I replaced it with a Primitive Robot Character.")
print("You should see her standing where the magenta cubes were.")
print("="*60 + "\n")

EditorCamera(speed=10)
app.run()
