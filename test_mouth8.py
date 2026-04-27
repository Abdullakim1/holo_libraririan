from ursina import *
from direct.actor.Actor import Actor
import math

app = Ursina()

# Load the model
anime_actor = Actor('anime_v7.glb')
anime_actor.stop()

# Attach to scene
player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = 180

# IMPORTANT: Only control the joint ONCE
# This gives you access to the ENTIRE slider array
control = anime_actor.controlJoint(None, 'modelRoot', 'MouthOpen')  
# Note: 'MouthOpen' here is just used to find the joint - 
# it doesn't matter which morph you specify as long as it exists

# Now we need to figure out which POSITION in the joint corresponds to which morph target
# Typically, Panda3D stores morph targets in the order they appear in the glTF file
# Position X is the first morph target, Y is second, Z is third, etc.

# Let's check which component controls which morph
print("\n" + "="*40)
print("Testing morph target order...")
print("Setting X=0.01 to test MouthOpen...")
control.set_x(0.01)  # This likely controls MouthOpen (first morph target)
print("="*40 + "\n")

def input(key):
    if key == '1':
        # Mouth open - X position
        print("Mouth Open: 1.0")
        control.set_x(0.01)
    elif key == '2':
        # Mouth closed - X position
        print("Mouth Open: 0.0")
        control.set_x(0.0)
    elif key == '3':
        # Blink - Y position (second morph target)
        print("Blink: 1.0")
        control.set_y(0.01)  # Note: using Y instead of X!
    elif key == '4':
        # Blink off
        print("Blink: 0.0")
        control.set_y(0.0)  # Note: using Y instead of X!
    elif key == '5':
        # Both at 1.0 simultaneously
        print("Both: 1.0")
        control.set_x(0.01)
        control.set_y(0.01)
    elif key == '6':
        # Both at 0.0 simultaneously  
        print("Both: 0.0")
        control.set_x(0.0)
        control.set_y(0.0)

# For the oscillating demo with both working:
def update():
    # Mouth oscillates
    mouth_weight = (math.sin(time.time() * 4) + 1.0) / 2.0
    control.set_x(mouth_weight * 0.01)
    
    # Blink oscillates at a different rate
    blink_weight = (math.sin(time.time() * 2 + 1) + 1.0) / 2.0
    control.set_y(blink_weight * 0.01)

EditorCamera()
app.run()
