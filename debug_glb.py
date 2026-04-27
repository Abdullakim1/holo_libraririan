import struct
import json

def inspect_glb_shape_keys(filepath):
    print(f"Opening {filepath} to read raw data...\n")
    print("="*50)
    
    with open(filepath, 'rb') as f:
        # Read GLB Header
        magic = f.read(4)
        if magic != b'glTF':
            print("ERROR: Not a valid GLB file.")
            return
            
        version, length = struct.unpack('<II', f.read(8))
        
        # FIXED: Correctly unpack the byte string for the JSON chunk
        chunk0_len, = struct.unpack('<I', f.read(4))
        chunk0_type = f.read(4)
        
        if chunk0_type != b'JSON':
            print(f"ERROR: First chunk is not JSON, it is {chunk0_type}")
            return
            
        # Extract the JSON data
        json_data = f.read(chunk0_len).decode('utf-8')
        data = json.loads(json_data)

        if 'meshes' not in data:
            print("No meshes found in this file.")
            return

        for i, mesh in enumerate(data['meshes']):
            mesh_name = mesh.get('name', f'Unnamed_Mesh_{i}')
            print(f"MESH: {mesh_name}")
            
            # Get the exact names of the shape keys
            target_names = []
            if 'extras' in mesh and 'targetNames' in mesh['extras']:
                target_names = mesh['extras']['targetNames']
                print(f"SHAPE KEY NAMES FOUND: {target_names}")
            else:
                print("NO SHAPE KEY NAMES FOUND IN EXTRAS.")

            # Look at the actual data pointers
            for j, primitive in enumerate(mesh.get('primitives', [])):
                targets = primitive.get('targets', [])
                if not targets:
                    print("  -> No vertex movement data found for this primitive.")
                    continue
                    
                print(f"  -> Found {len(targets)} blocks of vertex movement data:")
                for k, target in enumerate(targets):
                    name = target_names[k] if k < len(target_names) else f"Target_{k}"
                    
                    # The POSITION number is the ID of the binary data block holding the vertices
                    position_id = target.get('POSITION', 'NONE')
                    print(f"     [{k}] {name} uses Binary Data Block ID: {position_id}")
            print("-" * 50)

inspect_glb_shape_keys('anime_v7.glb')
