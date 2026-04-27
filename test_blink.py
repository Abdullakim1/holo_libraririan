from ursina import *
from direct.actor.Actor import Actor
import math
import time

app = Ursina()

anime_actor = Actor('anime_v5.glb')
player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = -180

mouth_control = anime_actor.controlJoint(None, 'modelRoot', 'MouthOpen')
blink_control = anime_actor.controlJoint(None, 'modelRoot', 'Blink')

# Variable to track what we are testing
current_test = None

def input(key):
    global current_test
    if key == '1':
        current_test = 'mouth'
        print("\n--- TESTING MOUTH ONLY ---")
        if blink_control: blink_control.set_x(0.0) # Force eyes to stay still
        
    elif key == '2':
        current_test = 'blink'
        print("\n--- TESTING EYES ONLY ---")
        if mouth_control: mouth_control.set_x(0.0) # Force mouth to stay still
        
    elif key == '0':
        current_test = None
        print("\n--- STOPPED ---")
        if mouth_control: mouth_control.set_x(0.0)
        if blink_control: blink_control.set_x(0.0)

def update():
    current_time = time.time()

    # ONLY run if we pressed '1'
    if current_test == 'mouth' and mouth_control:
        mouth_weight = (math.sin(current_time * 8) + 1.0) / 2.0
        # Testing full strength without the 0.01 multiplier
        mouth_control.set_x(mouth_weight * 0.01) 

    # ONLY run if we pressed '2'
    if current_test == 'blink' and blink_control:
        blink_weight = (math.sin(current_time * 8) + 1.0) / 2.0
        # Testing full strength without the 0.01 multiplier
        blink_control.set_x(blink_weight * 0.01)

EditorCamera()
app.run()
