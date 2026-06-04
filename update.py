# deep_debug.py
import sys
import os

# Silence TensorFlow
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from deepface import DeepFace
import json

print("🔍 DeepFace Recognition Debug")
print("=" * 50)

db_path = "face_known"

# Test 1: Use a known photo from the database
test_img = os.path.join(db_path, "Kim", "Kim_1.jpg")
print(f"\n📸 Test 1: Testing {test_img} against database")

try:
    results = DeepFace.find(
        img_path=test_img,
        db_path=db_path,
        model_name='VGG-Face',
        distance_metric='cosine',
        enforce_detection=False,
        silent=True
    )
    
    print(f"Results type: {type(results)}")
    print(f"Number of results: {len(results)}")
    
    if len(results) > 0:
        df = results[0]
        print(f"DataFrame shape: {df.shape}")
        print(f"Column names: {list(df.columns)}")
        
        if not df.empty:
            print(f"\nTop matches:")
            for i in range(min(3, len(df))):
                identity = df.iloc[i]['identity']
                folder = os.path.basename(os.path.dirname(identity))
                filename = os.path.basename(identity)
                
                # Find the distance column
                distance_cols = [col for col in df.columns if 'cosine' in col.lower()]
                if distance_cols:
                    distance = df.iloc[i][distance_cols[0]]
                    print(f"  {i+1}. {folder}/{filename} - Distance: {distance:.4f}")
                else:
                    print(f"  {i+1}. {folder}/{filename} - No distance column found")
                    print(f"     All values: {df.iloc[i].to_dict()}")
        else:
            print("❌ Empty DataFrame - No faces found")
    else:
        print("❌ No results returned")
        
except Exception as e:
    print(f"❌ Error during find: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Try with face analysis first
print(f"\n📸 Test 2: Check if face can be detected in {test_img}")
try:
    analysis = DeepFace.analyze(
        img_path=test_img,
        actions=['age', 'gender', 'emotion'],
        enforce_detection=False,
        silent=True
    )
    
    if isinstance(analysis, list) and len(analysis) > 0:
        face = analysis[0]
        print(f"✅ Face detected!")
        print(f"  Age: {face.get('age', 'N/A')}")
        print(f"  Gender: {face.get('dominant_gender', 'N/A')}")
        print(f"  Emotion: {face.get('dominant_emotion', 'N/A')}")
        print(f"  Region: {face.get('region', {})}")
    else:
        print("❌ No face detected in the image")
        
except Exception as e:
    print(f"❌ Error during analysis: {e}")

# Test 3: Try different models
print(f"\n📸 Test 3: Try different recognition models")
models = ['VGG-Face', 'Facenet', 'ArcFace', 'Facenet512']

for model in models:
    try:
        print(f"\n  Trying {model}...")
        results = DeepFace.find(
            img_path=test_img,
            db_path=db_path,
            model_name=model,
            distance_metric='cosine',
            enforce_detection=False,
            silent=True
        )
        
        if len(results) > 0 and not results[0].empty:
            df = results[0]
            identity = df.iloc[0]['identity']
            folder = os.path.basename(os.path.dirname(identity))
            
            # Find distance column
            distance_cols = [col for col in df.columns if 'cosine' in col.lower() or 'distance' in col.lower()]
            if distance_cols:
                distance = df.iloc[0][distance_cols[0]]
                print(f"    ✅ Match: {folder} (distance: {distance:.4f})")
            else:
                print(f"    ✅ Match: {folder} (columns: {list(df.columns)})")
        else:
            print(f"    ❌ No match found")
            
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:100]}")
