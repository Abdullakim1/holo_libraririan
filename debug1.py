from ursina import *
from panda3d.core import *

app = Ursina()

player = Entity(model='anime_v13.glb', rotation_x=-270)

# Deep inspection
def inspect_node(node, depth=0):
    indent = "  " * depth
    print(f"{indent}{node.getName()} - {node.__class__.__name__}")
    
    if isinstance(node, GeomNode):
        gn = node
        for i in range(gn.getNumGeoms()):
            print(f"{indent}  Geom {i}: {gn.getGeom(i)}")
    
    for i in range(node.getNumChildren()):
        inspect_node(node.getChild(i), depth + 1)

print("=== MODEL STRUCTURE ===")
inspect_node(player.model.node())

EditorCamera()
app.run()
