from ursina import *
from direct.actor.Actor import Actor

app = Ursina()

# 1. Load the model and KILL ghost animations
anime_actor = Actor('anime_v9.glb')
anime_actor.stop() 

# 2. Attach and stand her up (Moved forward to z=5 so she stays visible!)
player = Entity(position=(0, -2, 5))
anime_actor.reparent_to(player)
player.rotation_x = -270

# 3. Grab both controls
mouth_control = anime_actor.controlJoint(None, 'modelRoot', '01_MouthOpen')
blink_control = anime_actor.controlJoint(None, 'modelRoot', '02_Blink')

print("\n" + "="*40)
print(f"MOUTH NODE ASSIGNED TO: {mouth_control}")
print(f"BLINK NODE ASSIGNED TO: {blink_control}")
print("="*40 + "\n")

# Variables to track current blend weights
mouth_weight = 0.0
blink_weight = 0.0

# --- MANUAL KEYBOARD OVERRIDE ---
def input(key):
    global mouth_weight, blink_weight
    
    # --- MOUTH CONTROLS ---
    if key == '1':
        mouth_weight = min(1.0, mouth_weight + 0.1) # Increase by 0.1
        if mouth_control: mouth_control.set_x(mouth_weight)
        print(f"Pressed 1: Mouth is now at {mouth_weight:.1f}")
        
    elif key == '2':
        mouth_weight = max(0.0, mouth_weight - 0.1) # Decrease by 0.1
        if mouth_control: mouth_control.set_x(mouth_weight)
        print(f"Pressed 2: Mouth is now at {mouth_weight:.1f}")

    # --- BLINK CONTROLS ---
    elif key == '3':
        blink_weight = min(1.0, blink_weight + 0.1) # Increase by 0.1
        if blink_control: blink_control.set_x(blink_weight)
        print(f"Pressed 3: Blink is now at {blink_weight:.1f}")
        
    elif key == '4':
        blink_weight = max(0.0, blink_weight - 0.1) # Decrease by 0.1
        if blink_control: blink_control.set_x(blink_weight)
        print(f"Pressed 4: Blink is now at {blink_weight:.1f}")

EditorCamera()

# Lighting to see the mesh
DirectionalLight(y=2, z=3, shadows=True)
AmbientLight(color=color.rgba(150, 150, 150, 0.1))

app.run()
