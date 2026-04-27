from ursina import *
from direct.actor.Actor import Actor
import math
import time

app = Ursina()

anime_actor = Actor('anime_v12.glb')

player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = 90

# We are asking for BLINK. If the theory is right, this will move the MOUTH.
test_control = anime_actor.controlJoint(None, 'modelRoot', '02_Blink')

print("\n" + "="*40)
print("TESTING ENGINE NAME SWAP BUG...")
print("="*40 + "\n")

def update():
    current_time = time.time()
    if test_control:
        # Full 1.0 strength oscillation
        weight = (math.sin(current_time * 8) + 1.0) / 2.0
        test_control.set_x(weight*0.01) 

EditorCamera()
app.run()
