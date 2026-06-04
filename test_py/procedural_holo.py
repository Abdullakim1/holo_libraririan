from ursina import *
from ursina.shaders import *
import pyttsx3
import threading
import time
import math
import random

# Force an integer win-size config to prevent that old startup error
import panda3d.core as p3d
p3d.loadPrcFileData('', 'win-size 1920 1080')

# ========== TTS SETUP ==========
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 0.9)

# ========== APP SETUP ==========
app = Ursina(title="HOLO Professional archives", borderless=True, fullscreen=True)
window.color = color.black
Sky(color=color.black) # Prevents the default sky color from leaking

# ========== HOLOGRAM SHADER ==========
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
                // High brightness cyan tint
                gl_FragColor = vec4(0.0, 0.9, 1.0, alpha * 0.8);
            }
            '''
        )

holo_shader = HologramShader()

# ========== PROCEDURAL ENVIRONMENT GENERATION ==========
# Replace your current procedural generation with this "Human-Scale" version
def generate_procedural_library():
    # 1. THE FLOOR: Let's make it a dark mahogany/wood color to ground the scene
    Entity(model='plane', scale=(100,1,100), color=color.rgb(0.1, 0.05, 0.05))

    # 2. THE WALLS: Bring them in closer (X= -10 instead of -25)
    for x_side in [-10, 10]: 
        for i in range(10):
            z_pos = -10 + (i * 5)
            
            # The Shelf Frame (Make it dark charcoal)
            Entity(
                model='cube', scale=(1.5, 10, 4), 
                position=(x_side, 5, z_pos),
                color=color.rgb(0.1, 0.1, 0.1),
                shader=holo_shader
            )
            
            # The Books (Give them subtle variety)
            for layer in range(5):
                for b in range(10):
                    Entity(
                        model='cube', scale=(0.8, 1.2, 0.2),
                        position=(x_side, 1.2 + (layer*1.8), z_pos + (b*0.4 - 2)),
                        # Only 5% glow cyan, the rest are "sleeping" dark blue
                        color=color.cyan if random.random() > 0.95 else color.rgb(0.05, 0.05, 0.2),
                        shader=holo_shader
                    )

# 3. THE CONSOLE: Make it a sleek "Glass" desk, not a solid light block
console = Entity(
    model='cube',
    scale=(4, 0.1, 1.5),
    position=(0, 1.2, 2.5), # Moved slightly further from her
    color=color.cyan,
    alpha=0.4,              # Make it semi-transparent
    shader=holo_shader
)

# 4. THE CAMERA: Move closer for an "Interview" feel
# ========== THE LIBRARIAN (FIXED LIGNMENT) ==========
try:
    librarian = Entity(
        model='AnimeCharacter.glb',
        scale=2,
        position=(0, 2.0, 0), # y=2 ensure full body on the ground
        rotation=(0, 180, 0),
        shader=holo_shader,
        double_sided=True
    )
    librarian.texture = 'white_cube' # Force the shader to use a clean texture
    print("✅ Model loaded successfully!")
except:
    librarian = Entity(model='cube', scale=(1,4,1), color=color.cyan, position=(0,2,0))

# ========== HOLOGRAM RINGS ==========
upper_ring = Entity(model='torus', scale=(3, 0.05, 3), position=(0, 4.2, 0), rotation=(90, 0, 0), color=color.cyan, shader=holo_shader, additive=True)
lower_ring = Entity(model='torus', scale=(3, 0.05, 3), position=(0, 0.1, 0), rotation=(90, 0, 0), color=color.cyan, shader=holo_shader, additive=True)

# ========== PARTICLES ==========
particles = []
for _ in range(80):
    p = Entity(model='sphere', scale=0.04, position=(random.uniform(-5, 5), random.uniform(0, 6), random.uniform(-3, 3)), color=color.cyan)
    particles.append([p, random.uniform(0.01, 0.04)])

# ========== SPEECH & ANIMATION ==========
is_talking = False

def speak(text):
    global is_talking
    is_talking = True
    def _tts():
        tts.say(text)
        tts.runAndWait()
        global is_talking
        is_talking = False
    threading.Thread(target=_tts, daemon=True).start()

ring_rotation = 0

def update():
    global ring_rotation
    t = time.time()
    
    # 1. Character Float
    librarian.y = 2.0 + (math.sin(t * 1.5) * 0.1)
    
    # 2. Rotate Rings and Console
    ring_rotation += time.dt * 20
    upper_ring.rotation_z = ring_rotation
    lower_ring.rotation_z = -ring_rotation
    
    # 3. Particles
    for p, speed in particles:
        p.y += speed
        if p.y > 6: p.y = 0
    
    # 4. Speech Reaction (Pulse)
    if is_talking:
        p_scale = 3.5 + abs(math.sin(t*15)) * 0.3
        upper_ring.scale = (p_scale, 0.05, p_scale)
        librarian.scale_x = 2.0 + abs(math.sin(t*20)) * 0.04 # Lip-sync vibration simulation
    else:
        upper_ring.scale = (3.5, 0.05, 3.5)
        librarian.scale_x = 2.0

# Camera setup (Immersive Wide Angle)
camera.position = (0, 2.5, 20)
camera.look_at((0, 2.0, 0))

# ========== RUN ==========
if __name__ == '__main__':
    def intro():
        time.sleep(2)
        speak("System online. Welcome to the archives. I am HOLO, your advanced hologram librarian.")
    threading.Thread(target=intro, daemon=True).start()
    app.run()
