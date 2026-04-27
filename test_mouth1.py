from ursina import *
from direct.actor.Actor import Actor
import math
import time

app = Ursina()

# 1. Load the model
anime_actor = Actor('anime_v1.glb')

# 2. Attach and stand her up
player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = 90

# 3. Grab ONLY the mouth control
mouth_control = anime_actor.controlJoint(None, 'modelRoot', 'A_MouthOpen')

print("\n" + "="*40)
if mouth_control:
    print("Mouth control FOUND! Starting mimic...")
else:
    print("CRITICAL ERROR: Mouth control NOT found.")
print("="*40 + "\n")

def update():
    current_time = time.time()

    # --- MOUTH LOGIC ONLY ---
    if mouth_control:
        # Smooth oscillation from 0.0 to 1.0 (NO 0.01 MULTIPLIER)
        mouth_weight = (math.sin(current_time * 8) + 1.0) / 2.0
        mouth_control.set_x(mouth_weight*0.01) 

# Add EditorCamera
EditorCamera()

app.run()
