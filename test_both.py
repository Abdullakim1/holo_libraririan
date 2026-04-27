from ursina import *
from direct.actor.Actor import Actor
import math
import random
import time

app = Ursina()

# 1. Load your newly fixed model!
anime_actor = Actor('anime_v7.glb')

# 2. Attach it and stand her up
player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = -180

# 3. Grab the freshly made controls
mouth_control = anime_actor.controlJoint(None, 'modelRoot', 'MouthOpen')
blink_control = anime_actor.controlJoint(None, 'modelRoot', 'Blink')

# --- NEW GLB DATA INSPECTOR ---
print("\n" + "="*40)
print("INSPECTING .GLB SHAPE KEY DATA:")
if mouth_control:
    # A standard shape key should have a slider range of [0.0 to 1.0]
    print(f"MouthOpen Slider Range: {mouth_control.get_transform().get_pos()}")
else:
    print("MouthOpen: NOT FOUND in .glb")
print("="*40 + "\n")

# 4. Blink Timer Variables
next_blink_time = time.time() + 2.0
is_blinking = False
blink_start_time = 0
blink_duration = 0.2  

def update():
    global next_blink_time, is_blinking, blink_start_time
    current_time = time.time()

    # --- MOUTH LOGIC (Continuous Mimic) ---
    if mouth_control:
        # Smooth pure oscillation between 0.0 and 1.0
        mouth_weight = (math.sin(current_time * 8) + 1.0) / 2.0
        mouth_control.set_x(mouth_weight*0.01) 

    # --- EYE LOGIC (Natural Random Blinks) ---
    if blink_control:
        # Check if it is time to blink
        if not is_blinking and current_time > next_blink_time:
            is_blinking = True
            blink_start_time = current_time
            # Schedule the next blink for 2 to 6 seconds from now
            next_blink_time = current_time + random.uniform(2.0, 6.0)
        
        # Animate the blink
        if is_blinking:
            elapsed = current_time - blink_start_time
            if elapsed > blink_duration:
                is_blinking = False
                blink_control.set_x(0.0) 
            else:
                progress = elapsed / blink_duration
                blink_weight = math.sin(progress * math.pi)
                blink_control.set_x(blink_weight*0.01)

# Add EditorCamera to pan around
EditorCamera()

app.run()
