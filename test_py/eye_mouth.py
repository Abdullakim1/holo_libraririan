from ursina import *
from direct.actor.Actor import Actor
import math

app = Ursina()

# Load both models
mouth_actor = Actor('anime_v1.glb')  # Vertical, has mouth + colors
blink_actor = Actor('anime_v7.glb')  # Horizontal, has blink

mouth_actor.stop()
blink_actor.stop()

# Create separate parents so we can rotate them independently
mouth_parent = Entity()
blink_parent = Entity()

mouth_actor.reparent_to(mouth_parent)
blink_actor.reparent_to(blink_parent)

# Rotate each model to their correct orientation
mouth_parent.rotation_x = -270  # v1's correct rotation
blink_parent.rotation_x = 180   # v7's correct rotation

# Make blink model invisible
blink_actor.setColorScale(1, 1, 1, 0)

# Get controls
mouth_control = mouth_actor.controlJoint(None, 'modelRoot', 'MouthOpen')
blink_control = blink_actor.controlJoint(None, 'modelRoot', 'Blink')

def update():
    # Mouth animation
    if mouth_control:
        mouth_weight = (math.sin(time.time() * 8) + 1.0) / 2.0
        mouth_control.set_x(mouth_weight * 0.01)
    
    # Blink animation
    if blink_control:
        blink_weight = 1.0 if (math.sin(time.time() * 3.14) > 0.95) else 0.0
        blink_control.set_x(blink_weight * 0.01)

EditorCamera()

app.run()
