from ursina import *
from direct.actor.Actor import Actor
import math
import random
import time

app = Ursina()

# 1. Load Actor and set up Entity
anime_actor = Actor('anime_v3.glb')
player = Entity()
anime_actor.reparent_to(player)

# Keep her standing upright
player.rotation_x = -90  

# 2. Grab control of BOTH morph targets
mouth_control = anime_actor.controlJoint(None, 'modelRoot', 'MouthOpen')
# CHANGE 'Blink' TO YOUR ACTUAL SHAPE KEY NAME (e.g., 'EyeClose')
eye_control = anime_actor.controlJoint(None, 'modelRoot', 'Blink') 

# 3. Blinking Variables
next_blink_time = time.time() + 2.0
is_blinking = False
blink_start_time = 0
blink_duration = 0.2  # A natural blink takes about 0.2 seconds

def update():
    global next_blink_time, is_blinking, blink_start_time
    current_time = time.time()

    # --- MOUTH LOGIC ---
    if mouth_control:
        # Smooth oscillation for testing
        weight = (math.sin(current_time * 8) + 1.0) / 2.0
        mouth_control.set_x(weight)

    # --- EYE BLINK LOGIC ---
    if eye_control:
        # Check if it's time to trigger a new blink
        if not is_blinking and current_time > next_blink_time:
            is_blinking = True
            blink_start_time = current_time
            # Schedule the next blink randomly between 2 and 6 seconds from now
            next_blink_time = current_time + random.uniform(2.0, 6.0)
        
        # If a blink is currently happening, animate it
        if is_blinking:
            elapsed = current_time - blink_start_time
            
            if elapsed > blink_duration:
                # Blink is finished
                is_blinking = False
                eye_control.set_x(0.0) # Ensure eyes are fully open
            else:
                # Calculate the blink animation (0.0 -> 1.0 -> 0.0)
                # Using a sine wave over the duration of the blink makes it smooth
                progress = elapsed / blink_duration
                blink_weight = math.sin(progress * math.pi)
                eye_control.set_x(blink_weight)

EditorCamera()
app.run()
