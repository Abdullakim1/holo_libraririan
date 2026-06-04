# capture_faces.py
import cv2
import os
import sys

def capture_reference_photos(person_name="Kim", num_photos=5):
    """Capture multiple reference photos for better recognition"""
    
    # Create person folder
    person_folder = f"face_known/{person_name}"
    os.makedirs(person_folder, exist_ok=True)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print(f"📸 Capturing {num_photos} reference photos for {person_name}")
    print("Look at the camera and press SPACE to capture")
    print("Take photos with:")
    print("  - Different angles (slight left/right)")
    print("  - Different expressions (neutral, smiling)")
    print("  - Good lighting")
    
    photo_count = 0
    while photo_count < num_photos:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Show frame
        cv2.imshow('Capture Reference Photo (SPACE=Capture, Q=Quit)', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):  # Space to capture
            photo_count += 1
            filename = f"{person_folder}/{person_name}_{photo_count}.jpg"
            cv2.imwrite(filename, frame)
            print(f"✅ Saved: {filename} ({photo_count}/{num_photos})")
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"\n✅ Done! {photo_count} photos saved for {person_name}")

if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "Kim"
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    capture_reference_photos(name, count)
