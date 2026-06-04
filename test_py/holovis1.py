from ursina.prefabs.editor_camera import EditorCamera
from ursina import *
from ursina.shaders import *
import pyttsx3
import threading
import time
import math
import random

# ========== TTS SETUP ==========
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 0.9)

app = Ursina(title="HOLO Professional", borderless=True, fullscreen=True)
window.color = color.black

# ========== HOLOGRAM SHADER ==========
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
            out vec4 frag_color; // <--- Changed this name to fix your error
            uniform sampler2D p3d_Texture;
            uniform float time;
            void main() {
                vec4 color = texture(p3d_Texture, texcoord);
                float scanline = sin(texcoord.y * 300.0 + time * 3.0) * 0.5 + 0.5;
                float flicker = 0.85 + 0.15 * sin(time * 15.0);
                float alpha = color.a * scanline * flicker;
                frag_color = vec4(0.0, 0.8, 1.0, alpha * 0.7); // <--- Changed this to match
            }
            ''',
            default_input={'time': 0.0} # <--- ADD THIS LINE HERE
        )

holo_shader = HologramShader()

# ========== CINEMATIC BACKGROUND ==========
# ========== 3D LIBRARY ENVIRONMENT ==========
# Load your newly converted .glb file
library_env = Entity(
    model='library.glb',  # Make sure the name matches your downloaded file exactly
    scale=20,              # We will likely need to adjust this!
    position=(0, 0, 0)
)

# ========== 3D LIGHTING (CRUCIAL) ==========
# 3D rooms are pitch black without lights. This adds a sun and soft ambient room light.
sun = DirectionalLight(y=2, z=3, shadows=True, color=color.white)
sun.look_at(Vec3(0, -1, 1))
AmbientLight(color=color.rgba(150, 150, 150, 0.5))

# ========== THE LIBRARIAN ==========
librarian = Entity(
    model='AnimeCharacter.glb',
    scale=1.5,
    position=(0, 0, 0), # y=2 ensures feet are visible on the floor
    rotation=(0, 180, 0),
    double_sided=True
)

# ========== HOLOGRAM RINGS ==========
upper_ring = Entity(model='cylinder', scale=(3, 0.1, 3), position=(0, 4, 0), rotation=(90, 0, 0), color=color.cyan, shader=holo_shader)
lower_ring = Entity(model='cylinder', scale=(3, 0.1, 3), position=(0, 0.1, 0), rotation=(90, 0, 0), color=color.cyan, shader=holo_shader)

# ========== PARTICLES ==========
particles = []
for _ in range(70):
    p = Entity(model='sphere', scale=0.04, position=(random.uniform(-4, 4), random.uniform(0, 5), random.uniform(-2, 2)), color=color.cyan)
    particles.append([p, random.uniform(0.01, 0.05)])

# ========== SPEECH & UPDATE ==========
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

def update():
    t = time.time()
    upper_ring.rotation_z += time.dt * 20
    lower_ring.rotation_z -= time.dt * 15
    
    for p, speed in particles:
        p.y += speed
        if p.y > 5: p.y = 0
    
    if is_talking:
        upper_ring.scale = (3.5 + math.sin(t*10)*0.2, 0.1, 3.5 + math.sin(t*10)*0.2)

# Camera setup
camera.position = (0, 5, -10)
camera.look_at(librarian)

# ========== DEBUG: SUMMON CHARACTER ==========
def input(key):
    if key == 'space':
        # Teleport her 5 units in front of exactly where you are looking
        librarian.position = camera.position + (camera.forward * 5)
        
        # This will print her new coordinates in your terminal
        # so you can permanently save them later!
        print(f"HOLO summoned to: X:{librarian.x}, Y:{librarian.y}, Z:{librarian.z}")

if __name__ == '__main__':
    def intro():
        time.sleep(2)
        speak("System online. Welcome to the archives. I am HOLO.")
    threading.Thread(target=intro, daemon=True).start()
    EditorCamera()
    app.run()

