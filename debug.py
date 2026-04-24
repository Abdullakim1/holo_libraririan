from ursina import *
import sys

app = Ursina()
model = load_model('anime.glb')

print("=== 1. FULL MODEL STRUCTURE ===")
# This prints the hierarchy of the model to the console
model.ls()

print("\n=== 2. SEARCHING FOR SHAPE KEYS / MORPHS ===")
found_anything = False

for np in model.find_all_matches('**'):
    node = np.node()
    
    # Check for ModelNode Morphs (Common for glTF exports)
    if hasattr(node, 'get_num_morphs'):
        count = node.get_num_morphs()
        if count > 0:
            print(f"✅ Found Morphs on Node: '{np.name}'")
            for i in range(count):
                morph = node.get_morph(i)
                print(f"   - Morph Name: {morph.get_name()}")
            found_anything = True

    # Check for GeomNode Vertex Morphs
    if node.is_geom_node():
        try:
            vdata = node.get_geom(0).get_vertex_data()
            if hasattr(vdata, 'get_morph'):
                morph_table = vdata.get_morph()
                if morph_table.get_num_sliders() > 0:
                    print(f"✅ Found Vertex Morphs on Node: '{np.name}'")
                    for i in range(morph_table.get_num_sliders()):
                        print(f"   - Slider Name: {morph_table.get_slider_name(i)}")
                    found_anything = True
        except:
            pass

if not found_anything:
    print("❌ NO SHAPE KEYS FOUND. The glb file might not have exported them correctly.")

input("\nPress Enter to close...")
