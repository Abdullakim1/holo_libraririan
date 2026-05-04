from ursina import *
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

# ========== INITIALIZE MODULES ==========
ai = HoloAI()
environment = Environment()
character = AnimeCharacter()

# Status text
status_text = Text(
    text="Listening for 'Hey HOLO' or press SPACE/T...",
    position=(0, 0.45), color=color.cyan, size=0.03, origin=(0, 0)
)

# ========== INITIALIZE SPEECH ==========
def on_user_input(text):
    """Called when user speaks or types something"""
    response = ai.get_response(text)
    speech.speak(response)

speech = SpeechSystem(on_user_input)
speech.set_status_callback(lambda t: setattr(status_text, 'text', t))

# ========== KEYBOARD INPUT (fallback) ==========
keyboard_text = ""
input_active = False

def input(key):
    global keyboard_text, input_active
    
    if key == 'space' and not input_active and not speech.is_talking:
        speech.listen()
    
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
    t = time.time()
    
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
    print("\n" + "="*50)
    print("🌀 HOLO - AI Hologram Librarian")
    print("="*50)
    print("Say 'Hey HOLO' | SPACE: Speak | T: Type | ESC: Quit")
    print("="*50 + "\n")
    
    def intro():
        time.sleep(2)
        speech.speak("Hello. I am HOLO, your advanced hologram librarian. How may I assist you today?")
    
    threading.Thread(target=intro, daemon=True).start()
    app.run()
