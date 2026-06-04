from deepface import DeepFace
import cv2
import numpy as np

# This will force DeepFace to download its models and initialize 
# without the Ursina 3D engine running.
print("Downloading/Loading models... please wait.")
dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
try:
    DeepFace.find(img_path=dummy_img, db_path="face_known", enforce_detection=False)
    print("✅ DeepFace initialized successfully!")
except Exception as e:
    print(f"Error: {e}")
