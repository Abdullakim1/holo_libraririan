from ursina import *
from ursina.shaders import *
from direct.actor.Actor import Actor
import pyttsx3
import threading
import time
import math
import random
import asyncio
import edge_tts
import subprocess
import tempfile
import os
import speech_recognition as sr
import requests

# ========== CONFIGURATION ==========
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"
VOICE = "en-US-JennyNeural"

# ========== TTS ==========
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 0.9)

# ========== APP SETUP ==========
app = Ursina(title="HOLO Professional", borderless=True, fullscreen=True)
window.color = color.black
Sky(color=color.black)

# ========== SIMPLE HOLOGRAM SHADER (no time uniform) ==========
holo_shader = Shader(
    vertex='''
    #version 140
    uniform mat4 p3d_ModelViewProjectionMatrix;
    in vec4 p3d_Vertex;
    in vec2 p3d_MultiTexCoord0;
    out vec2 texcoord;
    
    void main() {
        gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        texcoord = p3d_MultiTexCoord0;
    }
    ''',
    fragment='''
    #version 140
    uniform sampler2D p3d_Texture;
    in vec2 texcoord;
    out vec4 fragColor;
    
    void main() {
        vec4 color = texture(p3d_Texture, texcoord);
        float scanline = sin(texcoord.y * 300.0) * 0.3 + 0.7;
        float alpha = color.a * scanline;
        // Cyan hologram tint
        fragColor = vec4(color.r * 0.3, color.g * 0.8, color.b * 1.0, alpha * 0.8);
    }
    '''
)

# ========== LOAD ANIME CHARACTER ==========
mouth_actor = Actor('anime_v1.glb')
blink_actor = Actor('anime_v7.glb')

mouth_actor.stop()
blink_actor.stop()

character = Entity(
    position=(0, 1.5, 0),
    rotation_x=-270,
    rotation_y=180,
    scale=1.5,
    shader=holo_shader
)
mouth_actor.reparent_to(character)

blink_parent = Entity(
    position=(0, 1.5, 0),
    rotation_x=180,
    rotation_y=180,
    scale=1.5,
    shader=holo_shader
)
blink_actor.reparent_to(blink_parent)
blink_actor.setColorScale(1, 1, 1, 0)

mouth_control = mouth_actor.controlJoint(None, 'modelRoot', 'MouthOpen')
blink_control = blink_actor.controlJoint(None, 'modelRoot', 'Blink')

print("✅ Anime character loaded!")

# ========== HOLOGRAM RINGS ==========
upper_ring = Entity(
    model='circle',
    scale=(3, 3, 1),
    position=(0, 3, 0),
    rotation=(90, 0, 0),
    color=color.cyan,
    thickness=3
)

lower_ring = Entity(
    model='circle',
    scale=(3, 3, 1),
    position=(0, 0.2, 0),
    rotation=(90, 0, 0),
    color=color.cyan,
    thickness=3
)

# ========== LIBRARY ENVIRONMENT ==========
floor = Entity(model='plane', scale=(40, 1, 40), texture='white_cube', color=color.rgb(5, 5, 15))

for side in [-1, 1]:
    for i in range(8):
        shelf = Entity(
            model='cube',
            scale=(2, 6, 8),
            position=(side * 12, 1, -10 + i * 3),
            color=color.rgb(30, 20, 15),
            texture='white_cube'
        )
        for j in range(12):
            Entity(
                model='cube',
                scale=(0.3, 1, 0.5),
                position=(side * 12 + (j - 5) * 0.35, 0.5, -10 + i * 3),
                color=color.rgb(
                    random.randint(40, 100),
                    random.randint(30, 80),
                    random.randint(20, 60)
                )
            )

# ========== PARTICLES ==========
particles = []
for _ in range(100):
    p = Entity(
        model='sphere',
        scale=0.05,
        position=(
            random.uniform(-5, 5),
            random.uniform(-1, 6),
            random.uniform(-3, 3)
        ),
        color=color.cyan,
        emissive=True
    )
    particles.append([p, random.uniform(0.02, 0.08)])

# ========== STATUS TEXT ==========
status_text = Text(
    text="Press SPACE to talk or T to type",
    position=(0, 0.45),
    color=color.cyan,
    size=0.03,
    origin=(0, 0)
)

# ========== SPEECH FUNCTION ==========
is_talking = False

def speak(text):
    global is_talking
    is_talking = True
    status_text.text = "HOLO: " + text[:60] + "..."
    
    def _tts():
        async def run_tts():
            try:
                communicate = edge_tts.Communicate(text, VOICE)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                    tmp_path = tmp.name
                await communicate.save(tmp_path)
                
                subprocess.run(['mpv', '--no-video', '--really-quiet', tmp_path], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.unlink(tmp_path)
            except Exception as e:
                print(f"TTS Error: {e}")
            
            global is_talking
            is_talking = False
            status_text.text = "Press SPACE to talk or T to type"
        
        asyncio.run(run_tts())
    
    threading.Thread(target=_tts, daemon=True).start()

# ========== AI RESPONSE (OLLAMA) ==========
conversation_history = []

def get_ollama_response(user_input):
    print(f"\n📝 User: {user_input}")
    
    system_prompt = """You are HOLO, a female hologram librarian. 
Be friendly and helpful. Keep responses SHORT (1 sentence max).
No special characters or formatting."""
    
    prompt = f"{system_prompt}\n"
    for msg in conversation_history[-4:]:
        prompt += f"{msg['role']}: {msg['content']}\n"
    prompt += f"User: {user_input}\nHOLO:"

    try:
        print("🤔 Asking Ollama...")
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.8, "max_tokens": 80, "stop": ["\n", "User:"]}
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '').strip()
            ai_response = ai_response.replace('*', '').replace('#', '').strip()
            print(f"🤖 HOLO: {ai_response}")
            return ai_response if ai_response else "I'm not sure what to say."
        else:
            print(f"❌ Ollama error: {response.status_code}")
            return "I'm having trouble thinking right now."
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return "I can't reach my brain right now."

# ========== SPEECH RECOGNITION ==========
recognizer = sr.Recognizer()
is_listening = False

try:
    microphone = sr.Microphone()
    print("✅ Microphone found!")
except Exception as e:
    print(f"⚠️ No microphone: {e}")
    microphone = None

def listen_and_respond():
    global is_listening
    
    if is_listening or is_talking:
        return
    
    if microphone is None:
        status_text.text = "No microphone! Press T to type."
        return
    
    is_listening = True
    status_text.text = "🎤 Listening..."
    print("🎤 Listening...")
    
    def _listen():
        global is_listening
        
        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                status_text.text = "💭 Thinking..."
                
                user_text = recognizer.recognize_google(audio)
                print(f"  Recognized: {user_text}")
                status_text.text = "You: " + user_text
                
                conversation_history.append({"role": "User", "content": user_text})
                response = get_ollama_response(user_text)
                if response:
                    conversation_history.append({"role": "HOLO", "content": response})
                    speak(response)
                
        except sr.WaitTimeoutError:
            print("  ⏰ No speech heard")
            status_text.text = "Didn't hear anything. Try again."
            time.sleep(2)
            status_text.text = "Press SPACE to talk or T to type"
        except sr.UnknownValueError:
            print("  ❓ Couldn't understand")
            status_text.text = "Couldn't understand. Try again."
            time.sleep(2)
            status_text.text = "Press SPACE to talk or T to type"
        except Exception as e:
            print(f"  ❌ Error: {e}")
            status_text.text = "Error. Try again."
            time.sleep(2)
            status_text.text = "Press SPACE to talk or T to type"
        
        is_listening = False
    
    threading.Thread(target=_listen, daemon=True).start()

# ========== KEYBOARD INPUT ==========
keyboard_text = ""
input_active = False

def input(key):
    global keyboard_text, input_active
    
    if key == 'space' and not input_active and not is_talking:
        print("\n🎙️ SPACE pressed")
        listen_and_respond()
    
    elif key == 't' and not input_active and not is_talking:
        input_active = True
        keyboard_text = ""
        status_text.text = "✏️ "
    
    elif key == 'enter' and input_active and keyboard_text.strip():
        user_text = keyboard_text.strip()
        status_text.text = "You: " + user_text
        print(f"\n⌨️ Typed: {user_text}")
        
        conversation_history.append({"role": "User", "content": user_text})
        response = get_ollama_response(user_text)
        if response:
            conversation_history.append({"role": "HOLO", "content": response})
            speak(response)
        
        keyboard_text = ""
        input_active = False
    
    elif key == 'escape':
        if input_active:
            keyboard_text = ""
            input_active = False
            status_text.text = "Press SPACE to talk or T to type"
    
    elif input_active and len(key) == 1:
        keyboard_text += key
        status_text.text = "✏️ " + keyboard_text
    
    elif input_active and key == 'backspace':
        keyboard_text = keyboard_text[:-1]
        status_text.text = "✏️ " + keyboard_text

# ========== ANIMATION ==========
def update():
    t = time.time()
    
    upper_ring.rotation_z += time.dt * 25
    lower_ring.rotation_z -= time.dt * 20
    
    float_y = 1.5 + math.sin(t * 1.5) * 0.2
    character.y = float_y
    blink_parent.y = float_y
    
    if mouth_control:
        if is_talking:
            mouth_weight = 0.3 + abs(math.sin(t * 12)) * 0.7
        else:
            mouth_weight = (math.sin(t * 2) + 1.0) * 0.05
        mouth_control.set_x(mouth_weight * 0.01)
    
    if blink_control:
        blink_cycle = math.sin(t * 1.5) * 0.5 + 0.5
        blink_weight = 1.0 if blink_cycle > 0.92 else 0.0
        blink_control.set_x(blink_weight * 0.01)
    
    for p, speed in particles:
        p.y += speed
        if p.y > 6:
            p.y = -1
        p.x += math.sin(t + p.y * 2) * 0.01
    
    if is_talking:
        glow = 1.2 + abs(math.sin(t * 10)) * 0.3
        upper_ring.scale = (3 * glow, 3 * glow, 1)
        lower_ring.scale = (3 * glow, 3 * glow, 1)
    else:
        upper_ring.scale = (3, 3, 1)
        lower_ring.scale = (3, 3, 1)

# Camera
camera.position = (0, 2.5, 15)
camera.look_at((0, 1.5, 0))

# ========== RUN ==========
if __name__ == '__main__':
    print("\n" + "="*50)
    print("🌀 HOLO - AI Hologram Librarian")
    print("="*50)
    print("SPACE: Speak | T: Type | ESC: Quit")
    print("="*50 + "\n")
    
    # Test Ollama
    try:
        test = requests.post(OLLAMA_URL, 
            json={"model": OLLAMA_MODEL, "prompt": "Say hi", "stream": False, "options": {"max_tokens": 10}}, 
            timeout=10)
        if test.status_code == 200:
            print("✅ Ollama connected!")
    except:
        print("⚠️ Ollama not reachable")
    
    def intro():
        time.sleep(2)
        speak("Hello. I am HOLO, your advanced hologram librarian. How may I assist you today?")
    
    threading.Thread(target=intro, daemon=True).start()
    app.run() 
