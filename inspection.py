import panda3d.core as p3d
from direct.showbase.ShowBase import ShowBase
import sys

class GLBInspector(ShowBase):
    def __init__(self, glb_path):
        super().__init__()
        
        # Load the GLB file
        try:
            self.model = self.loader.load_model(glb_path)
            print(f"\n=== Successfully loaded: {glb_path} ===")
        except Exception as e:
            print(f"Failed to load: {e}")
            sys.exit(1)
        
        # Inspect the model structure
        self.inspect_model(self.model, 0)
        
        # Look for morph targets/blend shapes
        self.find_morph_targets(self.model)
        
    def inspect_model(self, np, depth):
        """Recursively inspect node structure"""
        indent = "  " * depth
        print(f"{indent}Node: {np.name} (Type: {np.type})")
        
        # Check for GeomNodes
        if isinstance(np, p3d.GeomNode):
            print(f"{indent}  GeomNode with {np.get_num_geoms()} geometries")
            for i in range(np.get_num_geoms()):
                geom = np.get_geom(i)
                vdata = geom.get_vertex_data()
                if vdata:
                    self.inspect_vertex_data(vdata, indent + "    ")
        
        # Recursively inspect children
        for child in np.get_children():
            self.inspect_model(child, depth + 1)
    
    def inspect_vertex_data(self, vdata, indent):
        """Inspect vertex data arrays"""
        print(f"{indent}Vertex Data:")
        
        # List all arrays
        for i in range(vdata.get_num_arrays()):
            array = vdata.get_array(i)
            name = array.get_name()
            num_rows = array.get_num_rows()
            num_cols = array.get_num_columns() if hasattr(array, 'get_num_columns') else 0
            print(f"{indent}  Array {i}: {name} ({num_rows} rows, {num_cols} columns)")
        
        # Check for morph-related data
        print(f"{indent}  Data columns:")
        for i in range(vdata.get_num_columns()):
            col = vdata.get_column(i)
            print(f"{indent}    Column {i}: {col.get_name()} (Data type: {col.get_data_type()})")
    
    def find_morph_targets(self, np):
        """Look specifically for morph target/blend shape data"""
        print("\n=== Searching for Morph Targets/Blend Shapes ===")
        
        # Check for MorphVertexSlider or similar
        slider_attrs = np.find_all_matches('**/+MorphVertexSlider')
        if slider_attrs:
            print(f"Found {len(slider_attrs)} MorphVertexSlider attributes")
            for attr in slider_attrs:
                print(f"  - {attr}")
        
        # Check for blend shapes in node names
        morph_nodes = np.find_all_matches('**/*morph*')
        morph_nodes += np.find_all_matches('**/*blend*')
        morph_nodes += np.find_all_matches('**/*shape*')
        
        if morph_nodes:
            print(f"Found {len(morph_nodes)} nodes with morph/blend/shape in name:")
            for node in morph_nodes:
                print(f"  - {node.name}")
        
        # Try to access sliders
        sliders = self.morph.get_sliders() if hasattr(self, 'morph') else None
        if sliders:
            print(f"\nMorph sliders found: {sliders}")
        else:
            print("\nNo morph sliders detected via standard methods")
        
        print("\nFor GLB blend shapes, you typically need to:")
        print("1. Access via: model.get_geom(0).get_vertex_data().get_morph_list()")
        print("2. Or use: p3d.MorphVertexSlider objects attached to the model")
        print("3. Or access via: model.get_blend_shapes() if available")

# Usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_glb.py <path_to_glb_file>")
        sys.exit(1)
    
    app = GLBInspector(sys.argv[1])
    app.run()
