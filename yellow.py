from ursina import *
from ursina.prefabs.editor_camera import EditorCamera

app = Ursina(title="HOLO - GUARANTEED VISIBLE", borderless=True, fullscreen=True)
window.color = color.black

# ========== LOAD LIBRARY ==========
library = Entity(model='library.glb', scale=20, position=(0, 0, 0), color=color.white)

# ========== LIGHTING ==========
AmbientLight(color=color.rgba(255, 255, 255, 1))
DirectionalLight(y=10, z=3, shadows=True, color=color.white)
PointLight(position=(0, 8, 0), color=color.white, range=50)

# ========== CHARACTER ==========
librarian = None
character_summoned = False

def summon_character():
    global librarian, character_summoned
    
    if not character_summoned:
        # Spawn at camera position
        spawn_pos = camera.position + (camera.forward * 2)
        spawn_pos.y = 0.1
        
        librarian = Entity(
            model='AnimeCharacter.glb',
            scale=10,                    # HUGE SCALE!
            position=spawn_pos,
            rotation=(0, 180, 0),
            color=color.white,
            double_sided=True,
            emissive=True                # Makes her glow
        )
        
        # Add BRIGHT CYAN LIGHT on her head
        glow_light = Entity(
            parent=librarian,
            model='sphere',
            scale=1,
            position=(0, 2, 0),
            color=color.cyan,
            emissive=True
        )
        
        # Add GIANT ARROW marker pointing to her
        marker = Entity(
            parent=librarian,
            model='cube',
            scale=(0.5, 3, 0.5),
            position=(0, 3, 0),
            color=color.yellow,
            emissive=True
        )
        
        character_summoned = True
        print(f"CHARACTER SUMMONED AT: {spawn_pos}")
        print("LOOK FOR THE YELLOW ARROW AND CYAN GLOW!")
    else:
        # Teleport to camera
        new_pos = camera.position + (camera.forward * 2)
        new_pos.y = 0.1
        librarian.position = new_pos
        print(f"Character moved to: {new_pos}")

# ========== CAMERA ==========
camera.position = (0, 2, -8)
camera.look_at((0, 2, 0))

# ========== CONTROLS ==========
def input(key):
    global character_summoned
    
    if key == 'i':
        camera.position = (0, 2, -8)
        camera.look_at((0, 2, 0))
        
    if key == 'space':
        summon_character()
        
    if key == 'f' and librarian:
        # FIND CHARACTER - Move camera to her
        camera.position = librarian.position + Vec3(0, 2, -5)
        camera.look_at(librarian)
        print("Camera focused on character!")
        
    if key == 'h' and librarian:
        librarian.enabled = not librarian.enabled
        
    if key == 'r' and librarian:
        librarian.position = (0, 0.1, 0)
        camera.position = (0, 2, -5)
        camera.look_at(librarian)
        
    if key == 'up arrow' and librarian:
        librarian.scale *= 1.5
        print(f"Scale: {librarian.scale}")
        
    if key == 'down arrow' and librarian:
        librarian.scale *= 0.8
        
    if key == 'escape':
        application.quit()

# ========== INSTRUCTIONS ==========
Text(text='''
CONTROLS:
I       - Go Inside Library
SPACE   - Summon Character (HUGE + GLOWING)
F       - FIND CHARACTER (Camera follows)
H       - Hide/Show
R       - Reset to Center
UP/DOWN - Size
''', position=(-0.85, 0.45), scale=1.5, color=color.lime, background=True)

print("\n" + "="*60)
print("INSTRUCTIONS:")
print("1. Press 'I' to enter library")
print("2. Press 'SPACE' to summon (character will be HUGE)")
print("3. Look for YELLOW ARROW and CYAN GLOW")
print("4. If still can't see, press 'F' to find her")
print("5. Keep pressing UP ARROW to make her BIGGER")
print("="*60 + "\n")

EditorCamera(speed=15)
app.run()
