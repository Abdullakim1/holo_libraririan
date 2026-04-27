from ursina import *
from direct.actor.Actor import Actor
import math

app = Ursina()

# Load the model
anime_actor = Actor('anime_v7.glb')
anime_actor.stop()

player = Entity()
anime_actor.reparent_to(player)
player.rotation_x = 180

# --- DISCOVERY PHASE: Find all morph targets ---
print("\n" + "="*60)
print("DISCOVERING MORPH TARGETS ON YOUR MODEL")
print("="*60)

# Method 1: Try to list all available blend shapes
model_node = anime_actor.getChild(0)  # Get the actual geometry node

# Let's check what blend shapes exist
if hasattr(model_node, 'getNumSliders'):
    print(f"Number of sliders: {model_node.getNumSliders()}")

# Try to access the actual mesh geometry
for child in anime_actor.findAllMatches('**'):
    if hasattr(child, 'getBlendShape'):
        print(f"Found node with blendshape: {child}")
        # Try to list blend shapes
        if hasattr(child, 'getBlendShape'):
            try:
                # Different Panda3D methods to list blend shapes
                print(f"Node type: {type(child)}")
                print(f"Node name: {child.getName()}")
                
                # Try to get tags that might indicate morph targets
                if hasattr(child, 'getTags'):
                    tags = child.getTags()
                    for tag in tags:
                        print(f"Tag: {tag}")
            except Exception as e:
                print(f"Error accessing node: {e}")

# Method 2: Try ALL possible joint names combination
print("\n" + "="*60)
print("TESTING DIFFERENT JOINT NAMES")
print("="*60)

# Let's try to control using different approaches
test_names = ['MouthOpen', 'Blink', None]  # None will look for any joint

for test_name in test_names:
    print(f"\nTrying to control joint with name: {test_name}")
    try:
        # Temporarily try to get control
        test_control = anime_actor.controlJoint(None, 'modelRoot', test_name)
        if test_control:
            print(f"✓ SUCCESS with name: {test_name}")
            # Test all components to see which one controls mouth vs blink
            print("  Testing X component...")
            test_control.set_x(0.01)
            # (You'll visually check which morph activates)
        else:
            print(f"✗ FAILED with name: {test_name}")
    except Exception as e:
        print(f"✗ ERROR with name {test_name}: {e}")

# Method 3: The nuclear option - list everything
print("\n" + "="*60)
print("LISTING ALL CHILDREN AND THEIR PROPERTIES")
print("="*60)

def print_node_tree(node, indent=0):
    """Recursively print the node tree"""
    prefix = "  " * indent
    print(f"{prefix}Node: {node.getName()} (Type: {type(node).__name__})")
    
    # Print available methods that might be relevant
    if hasattr(node, 'getNumChildren'):
        print(f"{prefix}  Children: {node.getNumChildren()}")
    
    # Check for blend shapes
    for attr in ['getBlendShape', 'setBlendShape', 'getNumSliders', 'getSliderName']:
        if hasattr(node, attr):
            print(f"{prefix}  Has method: {attr}")
    
    # Recurse into children
    if hasattr(node, 'getChildren'):
        for child in node.getChildren():
            print_node_tree(child, indent + 1)

print_node_tree(anime_actor)

# --- NOW THE ACTUAL CONTROL ATTEMPT ---
# Once we know the structure, we'll control differently

# Try this alternative approach that sometimes works with glTF:
print("\n" + "="*60)
print("ATTEMPTING DIRECT NODE CONTROL")
print("="*60)

# Search for the mesh node that actually has the blend shapes
for node in anime_actor.findAllMatches('**/+GeomNode'):
    print(f"\nFound GeomNode: {node.getName()}")
    
    # Try to access blend shapes directly
    if hasattr(node, 'getBlendShape'):
        print(f"  BlendShape names available:")
        # The blend shapes might be accessible this way
        try:
            # Try to get the number of blend shapes
            # This varies by Panda3D version
            print(f"  Node type details: {dir(node)}")
        except:
            pass

# Human-readable keyboard controls for testing
print("\n" + "="*60)
print("KEYBOARD CONTROLS:")
print("  1/2: Toggle mouth (working?)")
print("  3/4: Toggle blink (working?)")
print("  5: Try to set BOTH at once")
print("  D: Dump all node info to console")
print("="*60 + "\n")

# We'll set up controls AFTER we know the structure
# For now, let's try this dirty trick:
def input(key):
    if key == 'd':
        # Dump detailed info about every single node
        print("\n" + "="*40)
        print("FULL NODE DUMP")
        print("="*40)
        for i, child in enumerate(anime_actor.getChildren()):
            print(f"\nChild {i}: {child}")
            try:
                # Try to get the node's type and all its attributes
                for attr in dir(child):
                    if not attr.startswith('_'):
                        try:
                            val = getattr(child, attr)
                            if not callable(val):
                                print(f"  {attr}: {val}")
                        except:
                            pass
            except Exception as e:
                print(f"  Error dumping child: {e}")
    
    elif key == '5':
        # Try setting the weight directly without joint control
        print("\nTrying direct blend shape control...")
        # This is the most direct method
        try:
            # Search through all nodes for blend shape capability
            for node in anime_actor.findAllMatches('**'):
                if hasattr(node, 'setBlendShape') and callable(node.setBlendShape):
                    print(f"Setting blend shape on {node.getName()}")
                    node.setBlendShape('MouthOpen', 1.0)
                    node.setBlendShape('Blink', 1.0)
                    return
            print("No node with setBlendShape found!")
        except Exception as e:
            print(f"Error: {e}")

EditorCamera()
app.run()
