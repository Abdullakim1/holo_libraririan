from ursina import *
from ursina.shaders import *
from direct.actor.Actor import Actor
import threading
import time
import math
import random
import asyncio
import edge_tts
import subprocess
import tempfile
import os

# ========== SPEECH FUNCTION ==========
is_talking = False

VOICE = "en-US-JennyNeural"  # Natural American female voice

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

# ========== LOAD ANIME CHARACTER ==========
mouth_actor = Actor('anime_v1.glb')
blink_actor = Actor('anime_v7.glb')

mouth_actor.stop()
blink_actor.stop()

# MAIN CHARACTER - v1 (mouth + body)
# v1 needs rotation_x=-270 to stand upright facing camera
character = Entity(
    position=(0, 1.5, 0),
    rotation_x=-270,  # Stand upright
    rotation_y=180,
    scale=1.5,
    shader=holo_shader
)
mouth_actor.reparent_to(character)

# BLINK LAYER - v7 (blink only)
# v7 needs rotation_x=180 to stand upright facing same direction as v1
blink_parent = Entity(
    position=(0, 1.5, 0),
    rotation_x=180,  # Stand upright
    rotation_y=180,
    scale=1.5,
    shader=holo_shader
)
blink_actor.reparent_to(blink_parent)
blink_actor.setColorScale(1, 1, 1, 0)

# Get controls
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
    shader=holo_shader,
    thickness=3
)

lower_ring = Entity(
    model='circle',
    scale=(3, 3, 1),
    position=(0, 0.2, 0),
    rotation=(90, 0, 0),
    color=color.cyan,
    shader=holo_shader,
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

# ========== SPEECH =========
is_talking = False

def speak(text):
    global is_talking
    is_talking = True
    
    def _tts():
        async def run_tts():
            communicate = edge_tts.Communicate(text, VOICE)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                tmp_path = tmp.name
            await communicate.save(tmp_path)
            
            # Play the audio
            subprocess.run(['mpv', '--no-video', '--really-quiet', tmp_path], 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.unlink(tmp_path)
            
            global is_talking
            is_talking = False
        
        asyncio.run(run_tts())
    
    threading.Thread(target=_tts, daemon=True).start()

# ========== ANIMATION ==========
def update():
    t = time.time()
    
    upper_ring.rotation_z += time.dt * 25
    lower_ring.rotation_z -= time.dt * 20
    
    # Float both parents together
    float_y = 1.5 + math.sin(t * 1.5) * 0.2
    character.y = float_y
    blink_parent.y = float_y
    
    if mouth_control:
        if is_talking:
            mouth_weight = 0.3 + abs(math.sin(t * 12)) * 0.7
        else:
            mouth_weight = (math.sin(t * 2) + 1.0) * 0.1
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

if __name__ == '__main__':
    print("🌀 Professional HOLO starting... (Press ESC to quit)")
    
    def intro():
        time.sleep(2)
        speak("Hello. I am HOLO, your advanced hologram librarian.")
        time.sleep(5)
        speak("How may I assist you today?")
    
    threading.Thread(target=intro, daemon=True).start()
    app.run()
