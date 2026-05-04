import threading
import time
import cv2
import numpy as np

class VisionSystem:
    """Handles camera-based detection: gestures, person type, presence"""
    
    def __init__(self):
        self.gesture_active = False
        self.person_detected = False
        self.person_type = "unknown"  # "student", "professor", "unknown"
        self.on_wave_callback = None
        self.on_person_change_callback = None
        
        # Motion detection
        self.prev_frame = None
        self.wave_count = 0
        self.last_wave_time = 0
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Initialize webcam
        self._init_webcam()
        
        if self.cap and self.cap.isOpened():
            self.gesture_active = True
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
    
    def _init_webcam(self):
        """Initialize the webcam"""
        try:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    print("✅ Vision system ready (gesture + person detection)")
                else:
                    print("⚠️ Webcam found but can't read frames")
                    self.cap = None
            else:
                print("⚠️ No webcam found")
                self.cap = None
        except Exception as e:
            print(f"⚠️ Webcam error: {e}")
            self.cap = None
    
    def set_wave_callback(self, callback):
        """Called when hand wave detected"""
        self.on_wave_callback = callback
    
    def set_person_change_callback(self, callback):
        """Called when person type changes (student/professor)"""
        self.on_person_change_callback = callback
    
    def _detection_loop(self):
        """Main detection loop - runs in background thread"""
        face_sizes = []  # Track face sizes to determine distance
        clothing_colors = []  # Track clothing for student/professor detection
        
        while self.gesture_active:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # Resize for faster processing
                frame = cv2.resize(frame, (320, 240))
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # ===== HAND WAVE DETECTION =====
                wave_detected = self._detect_wave(gray)
                
                if wave_detected and self.on_wave_callback:
                    self.on_wave_callback()
                
                # ===== PERSON DETECTION & CLASSIFICATION =====
                new_person_type = self._classify_person(gray, frame, face_sizes, clothing_colors)
                
                if new_person_type != self.person_type:
                    old_type = self.person_type
                    self.person_type = new_person_type
                    print(f"👤 Person detected: {self.person_type}")
                    
                    if self.on_person_change_callback:
                        self.on_person_change_callback(old_type, new_person_type)
                
                time.sleep(0.2)  # ~5 FPS detection
                
            except Exception as e:
                print(f"Vision error: {e}")
                time.sleep(0.5)
    
    def _detect_wave(self, gray_frame):
        """Detect hand wave using motion analysis"""
        gray = cv2.GaussianBlur(gray_frame, (21, 21), 0)
        
        if self.prev_frame is not None:
            frame_delta = cv2.absdiff(self.prev_frame, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            
            # Focus on upper portion of frame (where hands would be)
            upper_half = thresh[0:120, :]
            motion_percent = (np.sum(upper_half > 0) / upper_half.size) * 100
            
            self.prev_frame = gray.copy()
            
            # Significant motion = wave
            if motion_percent > 10:
                current_time = time.time()
                
                # Two waves within 2 seconds
                if current_time - self.last_wave_time < 2:
                    print(f"👋 Hand wave detected! ({motion_percent:.0f}% motion)")
                    self.last_wave_time = 0
                    return True
                else:
                    self.last_wave_time = current_time
            
            return False
        
        self.prev_frame = gray.copy()
        return False
    
    def _classify_person(self, gray_frame, color_frame, face_sizes, clothing_colors):
        """
        Classify person as student, professor, or unknown
        Based on face size (distance from camera) and clothing formality
        """
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) == 0:
            self.person_detected = False
            return "unknown"
        
        self.person_detected = True
        
        # Get the largest face
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = largest_face
        
        # Track face sizes
        face_sizes.append(w * h)
        if len(face_sizes) > 10:
            face_sizes.pop(0)
        
        avg_face_size = np.mean(face_sizes) if face_sizes else w * h
        
        # Analyze clothing color in torso region (below face)
        torso_y = y + h
        torso_h = min(60, gray_frame.shape[0] - torso_y)
        
        if torso_h > 0 and x > 0:
            torso_region = color_frame[torso_y:torso_y + torso_h, x:x + w]
            
            if torso_region.size > 0:
                avg_color = np.mean(torso_region, axis=(0, 1))
                clothing_colors.append(avg_color)
                if len(clothing_colors) > 10:
                    clothing_colors.pop(0)
        
        # Classification logic
        avg_color = np.mean(clothing_colors, axis=0) if clothing_colors else np.array([128, 128, 128])
        
        # Professor indicators:
        # - Larger face (closer to camera, standing at podium)
        # - Darker/more formal clothing
        # - Less movement
        
        # Student indicators:
        # - Smaller face (further away, sitting or walking)
        # - Brighter/more casual clothing
        
        is_dark_clothing = np.mean(avg_color) < 100  # Dark suit/jacket
        is_large_face = avg_face_size > 5000  # Close to camera
        
        if is_large_face and is_dark_clothing:
            return "professor"
        elif not is_large_face and not is_dark_clothing:
            return "student"
        elif is_large_face:
            return "professor"
        else:
            return "student"
    
    def get_person_type(self):
        """Get the current detected person type"""
        return self.person_type
    
    def get_greeting(self):
        """Get appropriate greeting based on person type"""
        greetings = {
            "professor": "Good day, Professor. How may I assist with your research?",
            "student": "Hey there, student! Looking for something interesting to read?",
            "unknown": "Hello! I am HOLO, your hologram librarian. How may I help you?"
        }
        return greetings.get(self.person_type, greetings["unknown"])
    
    def cleanup(self):
        """Release webcam resources"""
        self.gesture_active = False
        if self.cap:
            self.cap.release()
