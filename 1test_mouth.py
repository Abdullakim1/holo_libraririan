from ursina import *
from direct.actor.Actor import Actor
import math

app = Ursina()

# 1. Load the model as a Panda3D Actor
# This gives us access to animations and morph targets/sliders
anime_actor = Actor('anime_v3.glb')

# 2. Attach it to an Ursina Entity
# This allows it to exist and be moved around in the Ursina 3D scene
player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = -270

# 3. Take control of the Morph Target
# We ask Panda3D to give us control over the 'MouthOpen' shape key
mouth_control = anime_actor.controlJoint(None, 'modelRoot', 'MouthOpen')

def update():
    if mouth_control:
        # Create a smooth oscillation between 0.0 (closed) and 1.0 (open)
        weight = (math.sin(time.time() * 8) + 1.0) / 2.0
        
        # In Panda3D, morph target weights are controlled via the X position
        mouth_control.set_x(weight*0.01)

# Add an EditorCamera so you can easily pan around and zoom in on the face
EditorCamera()

app.run()
