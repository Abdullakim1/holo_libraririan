import struct
import json
import os

def inspect_glb(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return

    print(f"Inspecting: {filepath}\n")

    try:
        with open(filepath, 'rb') as f:
            # 1. Read GLB Header (12 bytes)
            magic = f.read(4)
            if magic != b'glTF':
                print("Error: Not a valid GLB file.")
                return
            
            struct.unpack('<II', f.read(8)) # version, length
            
            # 2. Read Chunk 0 Header (8 bytes)
            chunk_length = struct.unpack('<I', f.read(4))[0]
            chunk_type = f.read(4)
            
            if chunk_type != b'JSON':
                print(f"Error: First chunk is not JSON data.")
                return
            
            # 3. Parse JSON data
            json_data = f.read(chunk_length).decode('utf-8')
            gltf_struct = json.loads(json_data)
            
            # 4. Specifically check for Morph Target Names
            print("=== Morph Target (Shape Key) Analysis ===")
            if 'meshes' in gltf_struct:
                has_morphs = False
                for i, mesh in enumerate(gltf_struct['meshes']):
                    
                    # Blender saves Shape Key names in mesh['extras']['targetNames']
                    target_names = []
                    if 'extras' in mesh and 'targetNames' in mesh['extras']:
                        target_names = mesh['extras']['targetNames']

                    for primitive in mesh.get('primitives', []):
                        if 'targets' in primitive:
                            has_morphs = True
                            print(f"Mesh {i} ('{mesh.get('name', 'unnamed')}'):")
                            
                            if target_names:
                                print(f"  * Total Keys Found: {len(target_names)}")
                                print(f"  * Available Keys: {', '.join(target_names)}")
                                
                                # Check for MouthOpen specifically
                                if "Blink" in target_names:
                                    print("\n  >> RESULT: ✅ 'MouthOpen' was found successfully!")
                                else:
                                    print("\n  >> RESULT: ❌ 'MouthOpen' was NOT found in this mesh.")
                            else:
                                print("  * Morph targets exist, but no names were saved in 'extras.targetNames'.")
                            break
                            
                if not has_morphs:
                    print("No morph targets found in any mesh.")
            else:
                print("No meshes found in file.")

    except Exception as e:
        print(f"Failed to parse GLB file: {e}")

inspect_glb("anime_v3.glb")
