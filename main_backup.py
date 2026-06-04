import os
# Force TensorFlow to ignore the GPU and avoid CUDA driver conflicts
os.environ['CUDA_VISIBLE_DEVICES'] = '-1' 
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' # Disable custom CPU ops that often segfault
import time
from database import LibraryDB
from ursina import *
from vision import VisionSystem  # <--- ADD THIS LINE
import math
import time
import threading
import config
from models import AnimeCharacter
from speech import SpeechSystem
from ai import HoloAI
from environment import Environment


# ========== APP SETUP ==========
app = Ursina(title="HOLO Professional", borderless=True, fullscreen=True)
window.color = color.black
Sky(color=color.black)
db = LibraryDB()

# ========== INITIALIZE MODULES ==========
ai = HoloAI()
environment = Environment()
character = AnimeCharacter()
last_seen_time = 0

def on_user_input(text):
    """Called when user speaks or types something"""
    response = ai.get_response(text)
    speech.speak(response)

speech = SpeechSystem(on_user_input)
speech.set_status_callback(lambda t: setattr(status_text, 'text', t))

vision = VisionSystem()
has_greeted = False

# 1. Create the UI text object so it doesn't crash when updating!
person_text = Text(
    text="👤 Looking for users...",
    position=(-0.85, 0.45), # Upper left corner
    color=color.yellow, 
    size=0.03
)

def on_person_changed(old_type, new_type):
    global has_greeted
    
    # If a person is detected, run identification
    if new_type != "unknown":
        # Get the current frame from the camera to identify the user
        ret, frame = vision.cap.read()
        if ret:
            vision.identify_user(frame)
            
        user_name = vision.get_detected_name()
        age = vision.get_person_age()
        
        # Update UI text
        person_text.text = f"👤 {user_name} (Age: {age})"
        
        # Sync the identity with the AI brain
        ai.current_user_name = user_name
        ai.current_user_id = user_name.lower().replace(" ", "_")
        
        if not has_greeted and not speech.is_talking:
            # Ask the AI for a personalized greeting using the name
            greeting = ai.get_personalized_greeting(user_name)
            
            speech.start_conversation()
            threading.Thread(
                target=lambda: (time.sleep(0.5), speech.speak(greeting)),
                daemon=True
            ).start()
            has_greeted = True

# 3. CRITICAL: You must plug the function into the vision system!
vision.set_person_change_callback(on_person_changed)

# Status text
status_text = Text(
    text="Listening for 'Hey HOLO' or press SPACE/T...",
    position=(0, 0.45), color=color.cyan, size=0.03, origin=(0, 0)
)

# ========== KEYBOARD INPUT (fallback) ==========
keyboard_text = ""
input_active = False

def input(key):
    global keyboard_text, input_active
    
    if key == 'space' and not input_active and not speech.is_talking:
        speech.start_conversation()
    
    elif key == 't' and not input_active and not speech.is_talking:
        input_active = True
        keyboard_text = ""
        status_text.text = "Type message: "
    
    elif key == 'enter' and input_active and keyboard_text.strip():
        user_text = keyboard_text.strip()
        status_text.text = "You: " + user_text
        on_user_input(user_text)
        keyboard_text = ""
        input_active = False
    
    elif key == 'escape':
        vision.cleanup() # <--- ADD THIS LINE to turn off the webcam
        application.quit() # Close the app completely
        if input_active:
            keyboard_text = ""
            input_active = False
            status_text.text = "Listening for 'Hey HOLO' or press SPACE/T..."
    
    elif input_active and len(key) == 1:
        keyboard_text += key
        status_text.text = "Type: " + keyboard_text
    
    elif input_active and key == 'backspace':
        keyboard_text = keyboard_text[:-1]
        status_text.text = "Type: " + keyboard_text

def update():
    global last_seen_time
    t=time.time()
    
    # 1. Get detection data from your vision system
    is_person_present = vision.person_present  # Make sure vision.py sets this to True/False
    detected_name = vision.get_detected_name()
    
    # 2. Visual Wake-up Logic
    if is_person_present and not speech.conversation_active and not speech.is_talking:
        # Check if enough time has passed since she last "went to sleep" 
        # (e.g., 10 seconds) so she doesn't keep re-greeting you immediately
        if t - speech.last_speech_time > 15:
            print(f"👁️ Visual Wake-up: {detected_name} detected!")
            
            # Personalize the greeting
            speech.start_conversation()       
            if detected_name != "Unknown" and detected_name != "Guest":
                greeting = f"Welcome back, {detected_name}! How can I help you today?"
            else:
                greeting = "Hello! I noticed you there. I am HOLO, your librarian. How can I help you?"
            
            speech.speak(greeting)
            speech.last_speech_time = t
    character.update_position()
    
    if speech.is_talking:
        mouth_weight = 0.3 + abs(math.sin(t * 12)) * 0.7
    else:
        mouth_weight = (math.sin(t * 2) + 1.0) * 0.05
    character.set_mouth(mouth_weight)
    
    blink_cycle = math.sin(t * 1.5) * 0.5 + 0.5
    blink_weight = 1.0 if blink_cycle > 0.92 else 0.0
    character.set_blink(blink_weight)
    
    environment.update(speech.is_talking)

camera.position = config.CAMERA_POS
camera.look_at(config.CAMERA_LOOK)

if __name__ == '__main__':
    
    app.run()
