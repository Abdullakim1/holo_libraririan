from ursina import *
from direct.actor.Actor import Actor
import math
import time # Added time import since your script uses time.time()

app = Ursina()

# 1. Load the new model that has the Blink key
anime_actor = Actor('anime_v7.glb')

# 2. Attach it to an Ursina Entity
player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = -180

# 3. Take control of the Blink Morph Target instead of the mouth
# Make sure the name matches EXACTLY what the file check script output
blink_control = anime_actor.controlJoint(None, 'modelRoot', 'Blink')

def update():
    if blink_control:
        # Create a smooth oscillation between 0.0 and 1.0
        weight = (math.sin(time.time() * 8) + 1.0) / 2.0
        
        # Apply the weight (keeping your 0.01 multiplier!)
        blink_control.set_x(weight * 0.01)

# Add an EditorCamera so you can easily pan around
EditorCamera()

app.run()
