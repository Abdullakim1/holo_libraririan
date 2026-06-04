from ursina import *
from direct.actor.Actor import Actor

app = Ursina()

anime_actor = Actor('anime_v12.glb') 

# Tell Panda3D to print out EVERY joint and morph target it sees
print("\n--- INTERNAL JOINT REGISTRY ---")
anime_actor.listJoints()
print("-------------------------------\n")

player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = -180

EditorCamera()
app.run()
