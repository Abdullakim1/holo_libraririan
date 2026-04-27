from ursina import *
from panda3d.core import *
import math

app = Ursina()

player = Entity(model='anime_v13.glb', rotation_x=-270)
panda_node = player.model

# Find the mesh geometry node
mesh_nodes = panda_node.findAllMatches('**/+GeomNode')

print(f"\n=== MORPH TARGET DEBUG ===")
print(f"Found {len(mesh_nodes)} GeomNodes\n")

target_geom_node = None
target_geom_index = 0

if len(mesh_nodes) > 0:
    geom_node = mesh_nodes[0].node()
    print(f"GeomNode name: {geom_node.getName()}")
    print(f"Number of Geoms: {geom_node.getNumGeoms()}\n")
    
    if geom_node.getNumGeoms() > 0:
        geom = geom_node.getGeom(0)
        
        # Check if this geom has morph targets
        print(f"Checking for morph/blend data...")
        print(f"Geom type: {type(geom)}")
        
        # Check the GeomNode for morph methods
        print(f"\nGeomNode methods containing 'morph':")
        for method in dir(geom_node):
            if 'morph' in method.lower():
                print(f"  - {method}")
        
        print(f"\nGeom methods containing 'morph' or 'blend':")
        for method in dir(geom):
            if 'morph' in method.lower() or 'blend' in method.lower():
                print(f"  - {method}")
        
        target_geom_node = geom_node

# The actual animation approach for glTF morph targets
def update():
    if target_geom_node:
        weight = (math.sin(time.time() * 3) + 1.0) / 2.0
        
        # For glTF morph targets, we need to modify the blend table
        # Try getting the morph through the geom's blend table
        try:
            # This is the correct way for glTF morph targets in Panda3D
            target_geom_node.setSliderValue(0, weight)  # Slider 0 = MouthOpen
            
            if held_keys['space']:
                print(f"Setting morph weight to: {weight:.2f}")
        except AttributeError as e:
            if held_keys['space']:
                print(f"setSliderValue failed: {e}")
            
            # Alternative: try through the model's controller
            try:
                # Look for animation bundle
                bundles = target_geom_node.findAllMatches('**/+PartBundle')
                if len(bundles) > 0:
                    print("Found animation bundles!")
            except:
                pass

print("\nPress SPACE to see debug output")
print("Morph target 0 should be 'MouthOpen' according to your JSON\n")

EditorCamera()
app.run()
