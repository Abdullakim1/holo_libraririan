from ursina import *

app = Ursina()

# 1. Add the free-fly camera so we can look around
EditorCamera()

# 2. Load your character (Let's also force a scale just in case she's tiny)
character = Entity(model='anime_v9.glb', position=(0, 0, 0), scale=1)

# 3. Define what happens when the sliders move
def update_mouth():
    mouth_node = character.find('**/A_MouthOpen')
    if not mouth_node.is_empty():
        mouth_node.setX(mouth_slider.value)

def update_blink():
    blink_node = character.find('**/Blink')
    if not blink_node.is_empty():
        blink_node.setX(blink_slider.value)

# 4. Create on-screen sliders
mouth_slider = Slider(min=0, max=1, default=0, text='Mouth', y=-0.3, dynamic=True)
mouth_slider.on_value_changed = update_mouth

blink_slider = Slider(min=0, max=1, default=0, text='Blink', y=-0.4, dynamic=True)
blink_slider.on_value_changed = update_blink

# 5. Lighting
DirectionalLight(y=2, z=3, shadows=True)
AmbientLight(color=color.rgba(100, 100, 100, 0.1))

app.run()
