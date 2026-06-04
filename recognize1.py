import sys
import os

# Completely silence TensorFlow
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from deepface import DeepFace

def main():
    if len(sys.argv) < 3:
        print("MATCH:Guest")
        return

    img_path = sys.argv[1]
    db_path = sys.argv[2]

    try:
        # We use VGG-Face with a strict cosine threshold
        results = DeepFace.find(
            img_path=img_path, 
            db_path=db_path, 
            model_name='VGG-Face', 
            distance_metric='cosine', # Cosine is usually most stable
            enforce_detection=False, 
            silent=True
        )
        
        if len(results) > 0 and not results[0].empty:
            # 1. Get the path to the matching image
            match_path = results[0].iloc[0]['identity']
            
            # 2. Get the FOLDER name (e.g., 'Kim') instead of the filename
            # Path looks like: face_known/Kim/photo.jpg
            folder_path = os.path.dirname(match_path)
            name = os.path.basename(folder_path) 
            
            # 3. Distance check (Lower is better for cosine)
            # Standard VGG-Face threshold is 0.40. 
            # If distance is higher than 0.45, it's a weak match.
            distance = results[0].iloc[0]['VGG-Face_cosine']
            
            if distance < 0.45:
                print(f"MATCH:{name}")
            else:
                print("MATCH:Guest")
        else:
            print("MATCH:Guest")
    except Exception:
        print("MATCH:Guest")

if __name__ == "__main__":
    main()
