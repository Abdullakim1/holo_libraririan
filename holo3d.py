from ursina import *
from ursina.shaders import *
import pyttsx3
import threading
import time

# ========== TTS SETUP ==========
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 0.9)

# ========== CUSTOM HOLOGRAM SHADER ==========
hologram_shader = '''
uniform float time;
uniform vec4 color;
varying vec2 vuv;
varying vec3 vpos;

void main() {
    // Scanlines
    float scan = sin(vuv.y * 200.0 + time * 5.0) * 0.5 + 0.5;
    // Flicker
    float flicker = 0.9 + 0.1 * sin(time * 13.0);
    // Transparency
    float alpha = 0.6 * scan * flicker;
    
    gl_FragColor = vec4(color.rgb, alpha);
}
'''

# ========== 3D HOLO LIBRARIAN ==========
app = Ursina(title="HOLO Librarian", borderless=True, fullscreen=True, show_ursina_splash=False)

# Dark library environment
window.color = color.rgb(5, 5, 10)
Sky(texture='sky_sunset', scale=200)

# Library floor
Entity(model='plane', scale=(40, 1, 40), texture='white_cube', color=color.gray, y=-2)

# Bookshelves (left & right)
for side in [-1, 1]:
    for i in range(5):
        shelf = Entity(
            model='cube',
            scale=(2, 8, 6),
            position=(side * 12, 2, -8 + i * 4),
            texture='white_cube',
            color=color.rgb(20, 15, 10)
        )
        # Books on shelves
        for j in range(3):
            Entity(
                model='cube',
                scale=(0.3, 1.5, 0.3),
                position=(side * 12, 2 - j * 2, -8 + i * 4),
                texture='white_cube',
                color=color.rgb(random.randint(40, 80), random.randint(30, 60), random.randint(20, 50))
            )

# Upper hologram ring
upper_ring = Entity(
    model='torus',
    scale=(4, 0.1, 4),
    position=(0, 6, 0),
    rotation=(90, 0, 0),
    color=color.azure,
    texture='white_cube',
    emissive=True,
    emissive_color=color.azure
)

# Lower platform ring
lower_ring = Entity(
    model='torus',
    scale=(3, 0.1, 3),
    position=(0, -1.5, 0),
    rotation=(90, 0, 0),
    color=color.azure,
    texture='white_cube',
    emissive=True,
    emissive_color=color.azure
)

# === HOLOGRAM LIBRARIAN FIGURE ===
# Head
holo_head = Entity(
    model='sphere',
    scale=0.8,
    position=(0, 3.5, 0),
    color=color.azure,
    texture='white_cube',
    shader=hologram_shader,
    emissive=True
)

# Body (dress/coat shape)
holo_body = Entity(
    model='cylinder',
    scale=(1.2, 3, 1.2),
    position=(0, 1, 0),
    color=color.azure,
    texture='white_cube',
    shader=hologram_shader,
    emissive=True
)

# Arms
holo_arm_l = Entity(model='cylinder', scale=(0.3, 2, 0.3), position=(-1, 1.5, 0), rotation=(0, 0, 30), color=color.azure, shader=hologram_shader)
holo_arm_r = Entity(model='cylinder', scale=(0.3, 2, 0.3), position=(1, 1.5, 0), rotation=(0, 0, -30), color=color.azure, shader=hologram_shader)

# Book in hand
holo_book = Entity(model='cube', scale=(0.5, 0.7, 0.3), position=(-1.2, 0.8, 0.5), color=color.azure, shader=hologram_shader)

# Floating particles
particles = []
for _ in range(50):
    p = Entity(
        model='sphere',
        scale=0.05,
        position=(random.uniform(-3, 3), random.uniform(-1, 5), random.uniform(-2, 2)),
        color=color.azure,
        emissive=True
    )
    particles.append(p)

# ========== HOLOGRAM LOGIC ==========
is_talking = False

def speak(text):
    global is_talking
    is_talking = True
    def _tts():
        tts.say(text)
        tts.runAndWait()
        time.sleep(0.5)
        is_talking = False
    threading.Thread(target=_tts, daemon=True).start()

# Animation update
def update():
    # Rotate rings
    upper_ring.rotation_z += time.dt * 30
    lower_ring.rotation_z -= time.dt * 20
    
    # Float hologram
    holo_head.y = 3.5 + math.sin(time.time() * 2) * 0.2
    holo_body.y = 1 + math.sin(time.time() * 2) * 0.2
    
    # Particle drift
    for p in particles:
        p.y += time.dt * 0.5
        if p.y > 5:
            p.y = -1
            
    # Talking glow pulse
    if is_talking:
        glow = 0.8 + abs(math.sin(time.time() * 10)) * 0.4
        holo_head.shader.setUniorm('color', color.rgba(0, 0.8, 1, glow))
    else:
        holo_head.shader.setUniform('color', color.rgba(0, 0.6, 1, 0.6))

# ========== RUN TEST ==========
if __name__ == '__main__':
    print("🌀 HOLO 3D Librarian starting... (Press ESC to quit)")
    
    # Initial greeting
    time.sleep(2)
    speak("Hello! I am HOLO, your hologram librarian. How can I assist you today?")
    
    app.run()
