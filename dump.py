import json
import struct

filename = 'anime_v13.glb'

print(f"Cracking open {filename}...")

with open(filename, 'rb') as f:
    # Read the 12-byte GLB header
    magic, version, length = struct.unpack('<4sII', f.read(12))
    
    if magic != b'glTF':
        print("Not a valid GLB file!")
        exit()

    # FIX: Unpack as an Unsigned Int (length) and a 4-byte string (type)
    chunk_len, chunk_type = struct.unpack('<I4s', f.read(8))
    
    if chunk_type == b'JSON':
        # Decode the raw bytes into a readable JSON string
        json_data = f.read(chunk_len).decode('utf-8')
        parsed = json.loads(json_data)
        
        # Save it out to a readable text file
        output_name = 'blueprint.json'
        with open(output_name, 'w') as out:
            json.dump(parsed, out, indent=4)
            
        print(f"SUCCESS! The internal blueprint has been extracted to {output_name}")
    else:
        print(f"Failed to find JSON. Found {chunk_type} instead.")
