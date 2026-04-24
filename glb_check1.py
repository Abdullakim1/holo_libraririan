from ursina import *
import sys

app = Ursina()
model = load_model('anime_v2.glb')

print("=== DEEP SEARCH FOR MOUTH ===")

# We know from ls() that there is a Character node. Let's find it.
for np in model.find_all_matches('**/+Character'):
    char_node = np.node()
    print(f"✅ Found Character Node: {np.name}")
    
    # Method 1: Check if the Character node has morphs directly
    # (Some glTF loaders put them here)
    if hasattr(char_node, 'get_num_morphs'):
        count = char_node.get_num_morphs()
        if count > 0:
            print(f"   -> Found {count} morphs on Character Node!")
            for i in range(count):
                morph = char_node.get_morph(i)
                print(f"   -> Morph Name: {morph.get_name()}")
                if morph.get_name() == 'MouthOpen':
                    print("🎉 SUCCESS! Found MouthOpen on Character Node!")

    # Method 2: Check the GeomNode inside the Character
    # The Character contains the actual mesh (GeomNode)
    for child in np.get_children():
        if child.node().is_geom_node():
            geom_node = child.node()
            print(f"   -> Found GeomNode inside: {child.name}")
            
            # Try to get the vertex data morph
            try:
                geom = geom_node.get_geom(0)
                vdata = geom.get_vertex_data()
                
                # In Panda3D, morphs are often accessed via get_morph()
                morph_table = vdata.get_morph()
                if morph_table and morph_table.get_num_sliders() > 0:
                    print(f"   -> Found Morph Table on Geom Vertex Data!")
                    for i in range(morph_table.get_num_sliders()):
                        name = morph_table.get_slider_name(i)
                        print(f"      -> Slider: {name}")
                        if name == 'MouthOpen':
                            print("🎉 SUCCESS! Found MouthOpen on Geom Vertex Data!")
                            
            except Exception as e:
                print(f"   -> Error checking Geom: {e}")

input("Press Enter to close...")
