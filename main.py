import os
import urllib.request
import re
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
from intent_handler import IntentHandler

# ========== APP SETUP ==========
app = Ursina(title="HOLO Professional", borderless=True, fullscreen=True)
window.color = color.black
Sky(color=color.black)
db = LibraryDB()

# ========== INITIALIZE MODULES ==========
ai = HoloAI()
intent_handler = IntentHandler(db, ai)
environment = Environment()
character = AnimeCharacter()
last_seen_time = 0
last_greeted_name = None
greeting_in_progress = False

vision = VisionSystem()

pending_cover_loads = []
book_cover_uis = []
positions = [(0.4, 0.1), (0.6, 0.1), (0.8, 0.1)]
# 🔥 NEW: CREATE THE BOOK COVER DISPLAY PANEL IN URSINA
for pos in positions:
    book_cover_uis.append(Entity(
        parent=camera.ui, 
        model='quad', 
        texture=None, 
        scale=(0.18, 0.26),    # Slightly smaller so 3 can fit
        position=pos, 
        enabled=False          
    ))
# 🔥 NEW: ASYNC DOWNLOADER FUNCTION
def download_and_show_covers(urls):
    """Downloads up to 3 cover images asynchronously and sends them to the UI all at once."""
    global pending_cover_loads
    import glob
    
    # 🧹 NEW: Clean up old temporary files from previous searches to save disk space
    for old_file in glob.glob("temp_cover_*.jpg"):
        try: os.remove(old_file)
        except: pass

    batch_ready_images = [] 
    unique_stamp = int(time.time() * 1000) # 🔥 NEW: Unique ID to bypass Ursina cache
    
    for i, url in enumerate(urls):
        if i >= 3: break # Max 3 covers
        try:
            # 🔥 NEW: Make the filename unique so Ursina realizes it's a new image!
            local_filename = f"temp_cover_{i}_{unique_stamp}.jpg"
            urllib.request.urlretrieve(url, local_filename)
            
            if os.path.exists(local_filename) and os.path.getsize(local_filename) > 0:
                with open(local_filename, "rb") as f:
                    header = f.read(3)
                
                # Check for blank GIF placeholder
                if header.startswith(b'GIF'):
                    if os.path.exists("no_cover.jpg"):
                        batch_ready_images.append((i, "no_cover.jpg"))
                    continue
                
                batch_ready_images.append((i, local_filename))
        except Exception as e:
            print(f"⚠️ Failed to download cover {i}: {e}")
            
    if batch_ready_images:
        pending_cover_loads = batch_ready_images

def on_user_input(text):
    def think_and_speak():
            # 🛑 Shut off the microphone
            speech.is_thinking = True  
            setattr(status_text, 'text', "HOLO is thinking...")
            
            print(f"\n⏱️ [TIMER] STT Finished. Sending to Brain: '{text}'")
            start_time = time.time()
            
            # 🔥 1 SINGLE CALL TO LLAMA (This handles both Intent AND Chatting)
            response = intent_handler.classify_and_execute(text)
            
            # 🔥 NEW: VISUAL IMAGE INJECTION PIPELINE
            if hasattr(ai, 'current_book_images') and ai.current_book_images:
                print(f"🖼️ Displaying Cover UI for: {ai.current_book_image}")
                # Use a daemon thread to load images seamlessly without stopping animations
                threading.Thread(target=download_and_show_covers, args=(ai.current_book_images,), daemon=True).start()
            else:
                # If the current interaction didn't trigger a book image, hide the viewport asset
                for ui in book_cover_uis:
                    ui.enabled = False
            
            # Fallback if Llama completely fails to return JSON
            if not response:
                response = "I had a bit of trouble understanding that. Could you repeat?"
            print(f"🤖 HOLO: {response}")
            print(f"⏱️  [LOG] Response time: {time.time() - start_time:.2f}s")
            print("="*30 + "\n")
            
            speech.speak(response)
            speech.is_thinking = False

    threading.Thread(target=think_and_speak, daemon=True).start()
speech = SpeechSystem(on_user_input)


def clean_text_for_ursina(text):
    # This removes emojis and weird symbols that Ursina hates
    return re.sub(r'[^\x00-\x7f]', r'', text)

# Update your status callback
speech.set_status_callback(lambda t: setattr(status_text, 'text', clean_text_for_ursina(t)))


def on_user_waved():
    if not speech.conversation_active and not speech.is_talking:
        print("👁️ Visual Wake-up Triggered by Wave!")
        
        speech.start_conversation()
        
        # Get the smart greeting
        detected_name = vision.get_detected_name()
        if detected_name != "Unknown" and detected_name != "Guest":
            greeting = f"Welcome back, {detected_name}! How can I help you today?"
        else:
            greeting = vision.get_greeting() 
            
        # Hide any leftover book image when conversational context resets via wave
        for ui in book_cover_uis:
                ui.enabled = False
        speech.speak(greeting)
        
        # Reset the 15-second cooldown timer
        speech.last_speech_time = time.time()

# 🔥 2. Link it to the vision system
vision.set_wave_callback(on_user_waved)

# 1. Create the UI text object so it doesn't crash when updating!
person_text = Text(
    text="👤 Looking for users...",
    position=(-0.85, 0.45), # Upper left corner
    color=color.yellow, 
    size=0.03
)

def on_person_changed(old_type, new_type):
    global last_greeted_name, greeting_in_progress
    
    # 1. Reset memory when person leaves
    if new_type == "unknown":
        last_greeted_name = None
        greeting_in_progress = False
        person_text.text = "👤 Looking for users..."
        for ui in book_cover_uis:
                ui.enabled = False
        return
        
    # 2. Database Sync Logic (Keep this as is)
    current_name = vision.get_detected_name()
    if current_name not in ["Unknown", "Guest"]:
        face_id = current_name.lower().replace(" ", "_")
        db.cursor.execute("SELECT user_id, name, role FROM users WHERE face_id = %s", (face_id,))
        user = db.cursor.fetchone()
        if user:
            ai.current_user_name = user[1]
            ai.current_user_id = user[0]
            person_text.text = f"👤 {user[1]} ({user[2]})"
    else:
        person_text.text = f"👤 {new_type.title()} (Age: {vision.get_person_age()})"

    # 3. THE REFINED GREETING TRIGGER
    # If we are already talking or already greeted this session, stop.
    if greeting_in_progress:
        return

    def strip_emojis(text):
        return "".join(c for c in text if c.isascii())

    def wait_and_greet():
        global last_greeted_name, greeting_in_progress
        greeting_in_progress = True
        
        # 🔥 THE "WAITER" LOGIC:
        # If the scanner is running, we just hang out here until it's done
        wait_start = time.time()
        while vision.is_identifying:
            time.sleep(0.2)
            # Safety timeout: if it takes > 10 seconds, just proceed as Guest
            if time.time() - wait_start > 10:
                break
        
        # NOW re-fetch the name (it's likely changed from Unknown to Alfred)
        final_name = vision.get_detected_name()
        
        # Don't double-greet the same person
        if final_name == last_greeted_name:
            greeting_in_progress = False
            return

        if final_name not in ["Unknown", "Guest"]:
            print(f"✨ Generating AI greeting for: {final_name}")
            msg = ai.generate_face_recognition_greeting(ai.current_user_name)
        else:
            msg = "Hello! I am HOLO, your librarian. How can I help you?"
            
        for ui in book_cover_uis:
                ui.enabled = False    
        speech.speak(msg)
        last_greeted_name = final_name
        greeting_in_progress = False

    # Start the "Waiter" thread
    if not speech.is_talking:
        speech.start_conversation()
        threading.Thread(target=wait_and_greet, daemon=True).start()

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
    global last_seen_time, has_greeted, pending_cover_loads
    t=time.time()
    
    # 🔥 SAFE TEXTURE LOADING PIPELINE FOR MULTIPLE IMAGES
    if pending_cover_loads:
        for ui in book_cover_uis:
            ui.enabled = False # Hide old ones first
            
        for index, filename in pending_cover_loads:
            try:
                book_cover_uis[index].texture = filename
                book_cover_uis[index].enabled = True
            except Exception as e:
                print(f"❌ Error rendering texture {index}: {e}")
        pending_cover_loads = [] # Clear the queue

    # 🔥 ADD THIS: Check for text file input (temporary testing)
    if os.path.exists("user_text_input.txt"):
        try:
            with open("user_text_input.txt", "r") as f:
                text = f.read().strip()
            if text:
                # Clear the file after reading
                with open("user_text_input.txt", "w") as f:
                    f.write("")
                
                # 🔥 SYNC IDENTITY BEFORE PROCESSING
                detected = vision.get_detected_name()
                if detected not in ["Unknown", "Guest"]:
                    face_id = detected.lower().replace(" ", "_")
                    db.cursor.execute("SELECT user_id, name FROM users WHERE face_id = %s", (face_id,))
                    user = db.cursor.fetchone()
                    if user:
                        ai.identify_user(user[1])
                        ai.current_user_id = user[0]
                        print(f"⚡ Pre-text sync: Face '{detected}' → DB '{user[1]}'")
                
                # Process the input
                print(f"📝 Text input: {text}")
                status_text.text = "You: " + text
                on_user_input(text)
        except Exception as e:
            print(f"Text input error: {e}")
    # 1. Get detection data from your vision system
    is_person_present = vision.person_present
    detected_name = vision.get_detected_name()
    
    # 2. Visual Wake-up Logic
    if is_person_present and not speech.conversation_active and not speech.is_talking:
        # Add "and not vision.is_identifying" so she doesn't interrupt the scanner!
        if (t - speech.last_speech_time > 15) and not vision.is_identifying:
            detected_name = vision.get_detected_name()
            speech.start_conversation()
            
            if detected_name not in ["Unknown", "Guest"]:
                greeting = ai.generate_face_recognition_greeting(detected_name)
            else:
                greeting = "Hello! I noticed you there. How can I help you today?"
                
            for ui in book_cover_uis:
                ui.enabled = False    
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
