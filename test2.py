from ursina import *
from direct.actor.Actor import Actor
import sys

app = Ursina()

# Load the file
anime_actor = Actor('anime_v8.glb')

print("\n" + "="*50)
print("DEEP ENGINE DEBUG: RAW C++ CHARACTER SLIDERS")

# Search the 3D model for the core Panda3D Character node
character_nodes = anime_actor.findAllMatches('**/+Character')

if character_nodes.getNumPaths() == 0:
    print("CRITICAL: No Character nodes found. Model loaded as static mesh!")
else:
    for char_np in character_nodes:
        char_node = char_np.node()
        bundles = char_node.getBundles()
        
        for bundle in bundles:
            print(f"\nFound Bundle: {bundle.getName()}")
            num_sliders = bundle.getNumNodes()
            print(f"Total Raw Sliders Registered: {num_sliders}")
            
            for i in range(num_sliders):
                slider = bundle.getSlider(i)
                print(f" -> Raw Slider [{i}]: '{slider.getName()}'")

print("="*50 + "\n")
sys.exit()
