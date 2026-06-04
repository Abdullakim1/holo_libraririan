import sys
import os

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
        results = DeepFace.find(
            img_path=img_path, 
            db_path=db_path, 
            model_name='Facenet512',
            distance_metric='cosine',
            enforce_detection=False, 
            silent=True
        )
        
        if len(results) > 0 and not results[0].empty:
            match_path = results[0].iloc[0]['identity']
            folder_path = os.path.dirname(match_path)
            name = os.path.basename(folder_path)
            
            distance = results[0].iloc[0]['distance']
            confidence = results[0].iloc[0]['confidence']
            
            if distance < 0.5 and confidence > 70:
                print(f"MATCH:{name}")
            else:
                print("MATCH:Guest")
        else:
            print("MATCH:Guest")
            
    except Exception as e:
        print("MATCH:Guest")

if __name__ == "__main__":
    main()
