from ursina import *
from direct.actor.Actor import Actor

app = Ursina()

# 1. Load the model and KILL ghost animations
anime_actor = Actor('anime_v11.glb')
anime_actor.stop() 

# 2. Attach and stand her up
player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = -270

# 3. Grab both controls
mouth_control = anime_actor.controlJoint(None, 'modelRoot', 'MouthOpen')
blink_control = anime_actor.controlJoint(None, 'modelRoot', 'Blink')

print("\n" + "="*40)
print(f"MOUTH NODE ASSIGNED TO: {mouth_control}")
print(f"BLINK NODE ASSIGNED TO: {blink_control}")
print("="*40 + "\n")

# --- MANUAL KEYBOARD OVERRIDE ---
def input(key):
    if key == '1':
        print("Pressed 1: Forcing Mouth to 1.0")
        if mouth_control: mouth_control.set_x(0.01)
    elif key == '2':
        print("Pressed 2: Forcing Mouth to 0.0")
        if mouth_control: mouth_control.set_x(0.0)
    elif key == '3':
        print("Pressed 3: Forcing Blink to 1.0")
        if blink_control: blink_control.set_x(0.01)
    elif key == '4':
        print("Pressed 4: Forcing Blink to 0.0")
        if blink_control: blink_control.set_x(0.0)

EditorCamera()
app.run()
