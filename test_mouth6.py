from ursina import *

app = Ursina()

# 1. Load the model directly in front of the camera. 
# Using your v9 naming, change the file name if you re-exported.
character = Entity(model='anime_v9.glb', position=(0, -2, 5))

def input(key):
    # --- MOUTH CONTROLS ---
    # Press 'm' to open mouth
    if key == 'm':
        node = character.find('**/A_MouthOpen')
        if not node.is_empty():
            node.setX(1.0)
            print("Pressed M: Mouth Open (1.0)")
            
    # Press 'n' to close mouth
    if key == 'n':
        node = character.find('**/A_MouthOpen')
        if not node.is_empty():
            node.setX(0.0)
            print("Pressed N: Mouth Closed (0.0)")

    # --- BLINK CONTROLS ---
    # Press 'b' to blink
    if key == 'b':
        node = character.find('**/Blink')
        if not node.is_empty():
            node.setX(1.0)
            print("Pressed B: Eyes Closed (1.0)")

    # Press 'v' to un-blink
    if key == 'v':
        node = character.find('**/Blink')
        if not node.is_empty():
            node.setX(0.0)
            print("Pressed V: Eyes Open (0.0)")

# 2. Basic lighting to see the mesh
DirectionalLight(y=2, z=3, shadows=True)
AmbientLight(color=color.rgba(150, 150, 150, 0.1))

app.run()
