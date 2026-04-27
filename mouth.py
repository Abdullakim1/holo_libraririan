from ursina import *
from direct.actor.Actor import Actor

app = Ursina()

anime_actor = Actor('anime_v7.glb')
player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = -180

# Grab BOTH controls directly by their raw names, no mapping.
control_mouth = anime_actor.controlJoint(None, 'modelRoot', 'MouthOpen')
control_blink = anime_actor.controlJoint(None, 'modelRoot', 'Blink')

def update():
    # Press and hold '1' to test 'MouthOpen'
    if control_mouth:
        if held_keys['1']:
            control_mouth.set_x(0.01) # Max strength
        else:
            control_mouth.set_x(0)    # Zero strength
            
    # Press and hold '2' to test 'Blink'
    if control_blink:
        if held_keys['2']:
            control_blink.set_x(0.01) # Max strength
        else:
            control_blink.set_x(0)    # Zero strength

EditorCamera()
app.run()
