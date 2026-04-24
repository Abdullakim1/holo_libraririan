from ursina import *
from ursina.shaders import *
import pyttsx3
import threading
import time
import math
import random

# ========== TTS ==========
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 0.9)

# ========== APP SETUP ==========
app = Ursina(title="HOLO Professional", borderless=True, fullscreen=True)
window.color = color.black
Sky(color=color.black)

# ========== BLOOM/GLOW POST-PROCESSING ==========
class HologramShader(Shader):
    def __init__(self):
        super().__init__(
            vertex='''
            #version 130
            in vec3 p3d_Vertex;
            in vec2 p3d_MultiTexCoord0;
            out vec2 texcoord;
            uniform mat4 p3d_ModelViewProjectionMatrix;
            
            void main() {
                gl_Position = p3d_ModelViewProjectionMatrix * vec4(p3d_Vertex, 1.0);
                texcoord = p3d_MultiTexCoord0;
            }
            ''',
            fragment='''
            #version 130
            in vec2 texcoord;
            out vec4 gl_FragColor;
            uniform sampler2D p3d_Texture;
            uniform float time;
            
            void main() {
                vec4 color = texture(p3d_Texture, texcoord);
                float scanline = sin(texcoord.y * 300.0 + time * 3.0) * 0.5 + 0.5;
                float flicker = 0.85 + 0.15 * sin(time * 15.0);
                float alpha = color.a * scanline * flicker;
                gl_FragColor = vec4(0.0, 0.8, 1.0, alpha * 0.7);
            }
            '''
        )

holo_shader = HologramShader()

# Globals for facial features so the update loop can access them
mouth = None
eye_l = None
eye_r = None

# ========== LOAD 3D MODEL ==========
try:
    librarian = Entity(
        model='AnimeCharacter.glb', 
        scale=2,
        position=(0, 2, 0),
        rotation=(0, 180, 0),
        shader=holo_shader,
        double_sided=True
    )
    print("✅ Loaded 3D model successfully!")
    # NOTE: To animate a GLB face, you need a rigged model with bone control 
    # or blend shapes, which requires advanced Panda3D/Ursina Actor setups.
except:
    print("⚠️ Model not found, creating detailed figure with facial features...")
    
    # Head (sphere)
    head = Entity(model='sphere', scale=0.5, position=(0, 3.2, 0), color=color.cyan)
    
    # --- NEW: FACIAL FEATURES ---
    # We parent these to the head so they move if the head moves.
    eye_l = Entity(parent=head, model='sphere', scale=(0.2, 0.2, 0.1), position=(-0.3, 0.2, -0.45), color=color.cyan, shader=holo_shader)
    eye_r = Entity(parent=head, model='sphere', scale=(0.2, 0.2, 0.1), position=(0.3, 0.2, -0.45), color=color.cyan, shader=holo_shader)
    mouth = Entity(parent=head, model='cube', scale=(0.3, 0.05, 0.1), position=(0, -0.3, -0.45), color=color.cyan, shader=holo_shader)
    
    # Torso
    torso = Entity(model='cube', scale=(1, 1.5, 0.6), position=(0, 2, 0), color=color.cyan)
    hips = Entity(model='cube', scale=(0.9, 0.4, 0.5), position=(0, 1, 0), color=color.cyan)
    
    # Legs
    leg_l = Entity(model='cube', scale=(0.35, 1.8, 0.35), position=(-0.25, -0.1, 0), color=color.cyan)
    leg_r = Entity(model='cube', scale=(0.35, 1.8, 0.35), position=(0.25, -0.1, 0), color=color.cyan)
    
    # Arms
    arm_l_upper = Entity(model='cube', scale=(0.25, 0.7, 0.25), position=(-0.7, 2.3, 0.2), rotation=(0, 0, 20), color=color.cyan)
    arm_l_lower = Entity(model='cube', scale=(0.23, 0.7, 0.23), position=(-0.9, 1.7, 0.4), rotation=(0, 0, 40), color=color.cyan)
    
    arm_r_upper = Entity(model='cube', scale=(0.25, 0.7, 0.25), position=(0.7, 2.3, 0.2), rotation=(0, 0, -20), color=color.cyan)
    arm_r_lower = Entity(model='cube', scale=(0.23, 0.7, 0.23), position=(0.9, 1.7, 0.3), rotation=(0, 0, -30), color=color.cyan)
    
    book = Entity(model='cube', scale=(0.4, 0.5, 0.3), position=(-1.0, 1.3, 0.6), color=color.white, emissive=True)

# ========== HOLOGRAM RINGS ==========
upper_ring = Entity(model='torus', scale=(3, 0.1, 3), position=(0, 3.5, 0), rotation=(90, 0, 0), color=color.cyan, shader=holo_shader)
lower_ring = Entity(model='torus', scale=(3, 0.1, 3), position=(0, 0.1, 0), rotation=(90, 0, 0), color=color.cyan, shader=holo_shader)

# ========== LIBRARY ENVIRONMENT ==========
floor = Entity(model='plane', scale=(40, 1, 40), texture='white_cube', color=color.rgb(5, 5, 15))

for side in [-1, 1]:
    for i in range(8):
        shelf = Entity(model='cube', scale=(2, 6, 8), position=(side * 12, 1, -10 + i * 3), color=color.rgb(30, 20, 15), texture='white_cube')
        for j in range(12):
            Entity(model='cube', scale=(0.3, 1, 0.5), position=(side * 12 + (j - 5) * 0.35, 0.5, -10 + i * 3), color=color.rgb(random.randint(40, 100), random.randint(30, 80), random.randint(20, 60)))

# ========== PARTICLES ==========
particles = []
for _ in range(100):
    p = Entity(model='sphere', scale=0.05, position=(random.uniform(-5, 5), random.uniform(-1, 6), random.uniform(-3, 3)), color=color.cyan, emissive=True)
    particles.append([p, random.uniform(0.02, 0.08)])

# ========== SPEECH FUNCTION ==========
is_talking = False

def speak(text):
    global is_talking
    is_talking = True
    def _tts():
        tts.say(text)
        tts.runAndWait()
        time.sleep(0.5)
        global is_talking
        is_talking = False
    threading.Thread(target=_tts, daemon=True).start()

# ========== ANIMATION ==========
def update():
    t = time.time()
    
    upper_ring.rotation_z += time.dt * 25
    lower_ring.rotation_z -= time.dt * 20
    
    for p, speed in particles:
        p.y += speed
        if p.y > 6:
            p.y = -1
        p.x += math.sin(t + p.y * 2) * 0.01
    
    # --- NEW: FACIAL ANIMATIONS ---
    # Only run this if the primitive face was built
    if mouth and eye_l and eye_r:
        # Blinking Logic (Random chance every frame to scale eyes to 0 on Y axis)
        if random.random() < 0.015: 
            eye_l.scale_y = 0.01
            eye_r.scale_y = 0.01
        else:
            # Smoothly transition back to open eyes using lerp
            eye_l.scale_y = lerp(eye_l.scale_y, 0.2, time.dt * 15)
            eye_r.scale_y = lerp(eye_r.scale_y, 0.2, time.dt * 15)

        # Talking Logic
        if is_talking:
            # Fake lip sync: scale the mouth up and down rapidly using sine wave
            mouth.scale_y = 0.05 + abs(math.sin(t * 25)) * 0.2
            mouth.scale_x = 0.3 - abs(math.sin(t * 25)) * 0.1
            
            glow = 1.2 + abs(math.sin(t * 10)) * 0.3
            upper_ring.scale = (4 * glow, 0.1, 4 * glow)
        else:
            # Mouth rests closed
            mouth.scale_y = lerp(mouth.scale_y, 0.05, time.dt * 10)
            mouth.scale_x = lerp(mouth.scale_x, 0.3, time.dt * 10)
            upper_ring.scale = (4, 0.1, 4)

camera.position = (0, 2, 18)
camera.look_at((0, 1.5, 0))

# ========== RUN ==========
if __name__ == '__main__':
    print("🌀 Professional HOLO starting... (Press ESC to quit)")
    
    def intro():
        time.sleep(2)
        speak("Hello. I am HOLO, your advanced hologram librarian.")
        time.sleep(5)
        speak("How may I assist you today?")
    
    threading.Thread(target=intro, daemon=True).start()
    app.run()
