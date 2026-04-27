from ursina import *
from direct.actor.Actor import Actor
import sys

app = Ursina()

# Load the file
anime_actor = Actor('anime_v1.glb')

print("\n" + "="*50)
print("PANDA3D INTERNAL JOINTS AND SLIDERS:")

# This built-in Panda3D function prints the entire hierarchy to the console
anime_actor.listJoints()

print("="*50 + "\n")

# Automatically close the window after printing
sys.exit()
