import threading
import time
import cv2
import numpy as np
import os

class VisionSystem:
    """Camera-based detection: gestures, face analysis with age/gender models"""
    
    def __init__(self):
        self.gesture_active = False
        self.person_detected = False
        self.person_type = "unknown"
        self.person_age = 0
        self.person_gender = "unknown"
        self.on_wave_callback = None
        self.on_person_change_callback = None
        
        # Motion detection
        self.prev_frame = None
        self.last_wave_time = 0
        
        # Face analysis
        self.last_face_analysis = 0
        self.face_analysis_interval = 2
        self.face_history = []
        
        # Face detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Age/gender models
        self.age_net = None
        self.gender_net = None
        self.age_list = ['(0-2)', '(4-6)', '(8-12)', '(15-20)', '(25-32)', '(38-43)', '(48-53)', '(60-100)']
        self.gender_list = ['Male', 'Female']
        
        # Load models
        self._load_models()
        
        # Initialize webcam
        self._init_webcam()
        
        if self.cap and self.cap.isOpened():
            self.gesture_active = True
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
    
    def _load_models(self):
        """Load age and gender Caffe models from models/ folder"""
        models_dir = "models"
        age_proto = os.path.join(models_dir, "age_deploy.prototxt")
        age_model = os.path.join(models_dir, "age_net.caffemodel")
        gender_proto = os.path.join(models_dir, "gender_deploy.prototxt")
        gender_model = os.path.join(models_dir, "gender_net.caffemodel")
        
        if os.path.exists(age_model) and os.path.exists(gender_model):
            try:
                self.age_net = cv2.dnn.readNet(age_model, age_proto)
                self.gender_net = cv2.dnn.readNet(gender_model, gender_proto)
                print("✅ Age & gender detection models loaded!")
            except Exception as e:
                print(f"⚠️ Model loading error: {e}")
                self.age_net = None
                self.gender_net = None
        else:
            print("⚠️ Models not found in models/ folder")
            print("   Run: ./download_models.sh")
    
    def _init_webcam(self):
        """Initialize the webcam"""
        try:
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    print("✅ Vision system ready (wave + age/gender detection)")
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
        self.on_wave_callback = callback
    
    def set_person_change_callback(self, callback):
        self.on_person_change_callback = callback
    
    def _detection_loop(self):
        """Main detection loop"""
        while self.gesture_active:
            current_time = time.time()  # MOVED HERE - outside try block
        
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
            
                frame = cv2.flip(frame, 1)
                frame = cv2.resize(frame, (640, 480))
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Hand wave detection
                wave_detected = self._detect_wave(gray)
                if wave_detected and self.on_wave_callback:
                    self.on_wave_callback()
            
            # Face analysis (throttled)
                if current_time - self.last_face_analysis > self.face_analysis_interval:
                    self.last_face_analysis = current_time
                    self._analyze_face(frame, gray)
            
                time.sleep(0.1)
            
            except Exception as e:
                print(f"Vision error: {e}")
                time.sleep(0.5)

    def _detect_wave(self, gray_frame):
        """Detect hand wave using motion analysis"""
        gray = cv2.GaussianBlur(gray_frame, (21, 21), 0)
        
        if self.prev_frame is not None:
            frame_delta = cv2.absdiff(self.prev_frame, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            
            h, w = thresh.shape
            upper_region = thresh[0:h//2, :]
            motion_percent = (np.sum(upper_region > 0) / upper_region.size) * 100
            
            self.prev_frame = gray.copy()
            
            if motion_percent > 10:
                current_time = time.time()
                if current_time - self.last_wave_time < 2:
                    print(f"👋 Wave detected! ({motion_percent:.0f}% motion)")
                    self.last_wave_time = 0
                    return True
                else:
                    self.last_wave_time = current_time
            
            return False
        
        self.prev_frame = gray.copy()
        return False
    
    def _analyze_face(self, frame, gray):
        """Detect face and estimate age/gender using Caffe models"""
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
        
        if len(faces) == 0:
            if self.person_detected:
                self.person_detected = False
                old_type = self.person_type
                self.person_type = "unknown"
                self.person_age = 0
                print("👋 Person left")
                if self.on_person_change_callback:
                    self.on_person_change_callback(old_type, "unknown")
            return
        
        self.person_detected = True
        
        # Get the largest face
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = largest_face
        
        # Extract face ROI
        face_roi = frame[y:y+h, x:x+w].copy()
        
        # Estimate age and gender using models
        if self.age_net and self.gender_net:
            age, gender = self._predict_age_gender(face_roi)
        else:
            age, gender = 25, "unknown"
        
        # Add to history for smoothing
        self.face_history.append((age, gender))
        if len(self.face_history) > 10:
            self.face_history.pop(0)
        
        # Use median of recent estimates for stability
        if len(self.face_history) >= 5:
            ages = [f[0] for f in self.face_history[-5:]]
            genders = [f[1] for f in self.face_history[-5:]]
            age = int(np.median(ages))
            # Most common gender
            gender = max(set(genders), key=genders.count)
        
        # Classify
        new_type = self._classify_by_age(age)
        
        if new_type != self.person_type or age != self.person_age:
            old_type = self.person_type
            self.person_type = new_type
            self.person_age = age
            self.person_gender = gender
            
            print(f"👤 Detected: {new_type.title()} | Age: {age} | Gender: {gender}")
            
            if new_type != old_type and self.on_person_change_callback:
                self.on_person_change_callback(old_type, new_type)
    
    def _predict_age_gender(self, face_roi):
        """Use Caffe models to predict age and gender from face image"""
        try:
            # Prepare blob
            blob = cv2.dnn.blobFromImage(
                face_roi, 1.0, (227, 227),
                (78.4263377603, 87.7689143744, 114.895847746),
                swapRB=False
            )
            
            # Gender prediction
            self.gender_net.setInput(blob)
            gender_preds = self.gender_net.forward()
            gender_idx = gender_preds[0].argmax()
            gender = self.gender_list[gender_idx]
            
            # Age prediction
            self.age_net.setInput(blob)
            age_preds = self.age_net.forward()
            age_idx = age_preds[0].argmax()
            age_range = self.age_list[age_idx]
            
            # Parse age range to single number (use middle)
            age_str = age_range.strip('()')
            age_parts = age_str.split('-')
            age = (int(age_parts[0]) + int(age_parts[1])) // 2
            
            return age, gender
            
        except Exception as e:
            return 25, "unknown"
    
    def _classify_by_age(self, age):
        """Classify person based on estimated age"""
        if age >= 30:
            return "professor"
        elif age >= 14:
            return "student"
        else:
            return "unknown"
    
    def get_person_type(self):
        return self.person_type
    
    def get_person_age(self):
        return self.person_age
    
    def get_person_details(self):
        return {
            "type": self.person_type,
            "age": self.person_age,
            "gender": self.person_gender
        }
    
    def get_greeting(self):
        """Get appropriate greeting based on person type and age"""
        if self.person_type == "professor":
            if self.person_age >= 50:
                return "Good day, Professor. It's an honor to have you in the library."
            else:
                return "Hello, Professor! Ready to dive into some research?"
        elif self.person_type == "student":
            if self.person_age <= 20:
                return "Hey there, young scholar! Looking for something exciting to read?"
            else:
                return "Welcome back! What shall we explore today?"
        else:
            return "Hello! I am HOLO, your hologram librarian. How may I help you?"
    
    def cleanup(self):
        self.gesture_active = False
        if self.cap:
            self.cap.release()
