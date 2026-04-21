from ursina import *
from ursina.shaders import *
import pyttsx3
import threading
import time
import math

# ========== TTS ==========
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 0.9)

# ========== APP SETUP ==========
app = Ursina(title="HOLO Professional", borderless=True, fullscreen=True)
window.color = color.rgb(0, 2, 10)

# ========== BLOOM/GLOW POST-PROCESSING ==========
# Simple bloom using camera filter
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
                
                // Hologram scanlines
                float scanline = sin(texcoord.y * 300.0 + time * 3.0) * 0.5 + 0.5;
                // Flicker
                float flicker = 0.85 + 0.15 * sin(time * 15.0);
                // Fade edges
                float alpha = color.a * scanline * flicker;
                
                // Cyan tint
                gl_FragColor = vec4(0.0, 0.8, 1.0, alpha * 0.7);
            }
            '''
        )

holo_shader = HologramShader()

# ========== LOAD 3D MODEL ==========
try:
    # Try loading FBX model
    librarian = Entity(
        model='AnimeCharacter.glb',  # Will look for librarian.fbx or librarian.obj
        scale=2,
        position=(0, 0, 0),
        rotation=(0, 180, 0),
        shader=holo_shader,
        double_sided=True
    )
    print("✅ Loaded 3D model successfully!")
except:
    # Fallback: create better humanoid from primitives
    print("⚠️ Model not found, creating detailed figure...")
    
    # Head (sphere)
    head = Entity(model='sphere', scale=0.5, position=(0, 3.2, 0), color=color.cyan)
    
    # Torso (better proportions)
    torso = Entity(model='cube', scale=(1, 1.5, 0.6), position=(0, 2, 0), color=color.cyan)
    
    # Hips/waist
    hips = Entity(model='cube', scale=(0.9, 0.4, 0.5), position=(0, 1, 0), color=color.cyan)
    
    # Legs
    leg_l = Entity(model='cube', scale=(0.35, 1.8, 0.35), position=(-0.25, -0.1, 0), color=color.cyan)
    leg_r = Entity(model='cube', scale=(0.35, 1.8, 0.35), position=(0.25, -0.1, 0), color=color.cyan)
    
    # Arms (bent at elbows)
    arm_l_upper = Entity(model='cube', scale=(0.25, 0.7, 0.25), position=(-0.7, 2.3, 0.2), rotation=(0, 0, 20), color=color.cyan)
    arm_l_lower = Entity(model='cube', scale=(0.23, 0.7, 0.23), position=(-0.9, 1.7, 0.4), rotation=(0, 0, 40), color=color.cyan)
    
    arm_r_upper = Entity(model='cube', scale=(0.25, 0.7, 0.25), position=(0.7, 2.3, 0.2), rotation=(0, 0, -20), color=color.cyan)
    arm_r_lower = Entity(model='cube', scale=(0.23, 0.7, 0.23), position=(0.9, 1.7, 0.3), rotation=(0, 0, -30), color=color.cyan)
    
    # Book in hand
    book = Entity(model='cube', scale=(0.4, 0.5, 0.3), position=(-1.0, 1.3, 0.6), color=color.white, emissive=True)

# ========== HOLOGRAM RINGS ==========
upper_ring = Entity(
    model='torus',
    scale=(4, 0.1, 4),
    position=(0, 5, 0),
    rotation=(90, 0, 0),
    color=color.cyan,
    emissive=True
)

lower_ring = Entity(
    model='torus',
    scale=(3, 0.1, 3),
    position=(0, -1, 0),
    rotation=(90, 0, 0),
    color=color.cyan,
    emissive=True
)

# ========== LIBRARY ENVIRONMENT ==========
# Floor with grid
floor = Entity(model='plane', scale=(40, 1, 40), texture='white_cube', color=color.rgb(5, 5, 15))

# Bookshelves (left & right)
for side in [-1, 1]:
    for i in range(8):
        shelf = Entity(
            model='cube',
            scale=(2, 6, 8),
            position=(side * 12, 1, -10 + i * 3),
            color=color.rgb(30, 20, 15),
            texture='white_cube'
        )
        # Books
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
    
    # Rotate rings
    upper_ring.rotation_z += time.dt * 25
    lower_ring.rotation_z -= time.dt * 20
    
    # Float everything
    float_y = math.sin(t * 1.5) * 0.2
    
    # Animate particles
    for p, speed in particles:
        p.y += speed
        if p.y > 6:
            p.y = -1
        p.x += math.sin(t + p.y * 2) * 0.01
    
    # Talking pulse
    if is_talking:
        glow = 1.2 + abs(math.sin(t * 10)) * 0.3
        upper_ring.scale = (4 * glow, 0.1, 4 * glow)
    else:
        upper_ring.scale = (4, 0.1, 4)

# Camera setup
camera.position = (0, 2, 10)
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
