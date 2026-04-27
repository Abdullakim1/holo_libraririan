from ursina import *
from direct.actor.Actor import Actor

app = Ursina()

# 1. Load the brand new .bam file!
anime_actor = Actor('anime_v7.bam')

player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = 270

# 2. Grab the controls using their REAL names (no mapping needed)
control_mouth = anime_actor.controlJoint(None, 'modelRoot', 'MouthOpen')
control_blink = anime_actor.controlJoint(None, 'modelRoot', 'Blink')

def update():
    # Press and hold '1' for Mouth
    if control_mouth:
        if held_keys['1']:
            control_mouth.set_x(0.01) # Max open
        else:
            control_mouth.set_x(0)    # Closed
            
    # Press and hold '2' for Eyes
    if control_blink:
        if held_keys['2']:
            control_blink.set_x(0.01) # Max blink
        else:
            control_blink.set_x(0)    # Open

EditorCamera()
app.run()
