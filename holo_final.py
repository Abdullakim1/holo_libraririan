from ursina import *
import pyttsx3
import threading
import time
import math

# ========== TTS ==========
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 0.9)

# ========== APP SETUP ==========
app = Ursina(title="HOLO Librarian", borderless=True, fullscreen=True)

# Force dark background
window.color = color.rgb(0, 0, 5)
scene.bg_color = color.rgb(0, 0, 5)

# ========== CREATE TORUS FROM CUBES ==========
def create_ring(radius, y_pos, num_segments=36):
    """Create a ring from individual cubes"""
    parts = []
    for i in range(num_segments):
        angle = (i / num_segments) * 2 * math.pi
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius
        part = Entity(
            model='cube',
            scale=(0.2, 0.08, 0.2),
            position=(x, y_pos, z),
            color=color.cyan,
            emissive=True
        )
        parts.append(part)
    return parts

# ========== LIBRARY ENVIRONMENT ==========
# Dark floor
Entity(model='plane', scale=(50, 1, 50), color=color.rgb(5, 5, 10))

# Bookshelves
for side in [-1, 1]:
    for i in range(10):
        Entity(
            model='cube',
            scale=(2, 8, 6),
            position=(side * 12, 3, -15 + i * 3.5),
            color=color.rgb(30, 20, 15)
        )
        for j in range(15):
            Entity(
                model='cube',
                scale=(0.3, 1.2, 0.5),
                position=(side * 12 + (j - 7) * 0.35, 1.5, -15 + i * 3.5),
                color=color.rgb(
                    random.randint(40, 100),
                    random.randint(20, 60),
                    random.randint(10, 50)
                )
            )

# Lighting
AmbientLight(color=color.rgb(30, 30, 50))

# ========== LOAD MODEL ==========
try:
    librarian = Entity(
        model='AnimeCharacter.glb',
        scale=1.8,
        position=(0, 0, 0),
        rotation=(0, 180, 0),
        color=color.cyan,
        emissive=True  # Makes it glow cyan
    )
    print("✅ Model loaded!")
except Exception as e:
    print(f"⚠️ Error: {e}")
    librarian = Entity(model='cube', scale=1, position=(0, 1, 0), color=color.cyan)

# ========== HOLOGRAM RINGS ==========
upper_ring = create_ring(radius=3.5, y_pos=4.5)
lower_ring = create_ring(radius=2.5, y_pos=-0.5)

# ========== PARTICLES ==========
particles = []
for _ in range(80):
    p = Entity(
        model='sphere',
        scale=0.05,
        position=(random.uniform(-5, 5), random.uniform(0, 5), random.uniform(-3, 3)),
        color=color.cyan,
        emissive=True
    )
    particles.append(p)

# ========== CAMERA ==========
camera.position = (0, 2.5, 9)
camera.look_at((0, 1.5, 0))

# ========== SPEECH ==========
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
ring_rotation = 0

def update():
    global ring_rotation
    t = time.time()
    
    # Float character
    librarian.y = math.sin(t * 1.5) * 0.15
    
    # Rotate rings
    ring_rotation += time.dt * 30
    for i, part in enumerate(upper_ring):
        angle = (i / len(upper_ring)) * 2 * math.pi + ring_rotation * 0.017
        part.x = math.cos(angle) * 3.5
        part.z = math.sin(angle) * 3.5
        
    for i, part in enumerate(lower_ring):
        angle = (i / len(lower_ring)) * 2 * math.pi - ring_rotation * 0.015
        part.x = math.cos(angle) * 2.5
        part.z = math.sin(angle) * 2.5
    
    # Animate particles
    for p in particles:
        p.y += time.dt * 0.4
        if p.y > 5:
            p.y = 0

# ========== RUN ==========
if __name__ == '__main__':
    print("🌀 Starting HOLO... (ESC to quit)")
    
    def intro():
        time.sleep(2)
        speak("Hello. I am HOLO, your hologram librarian.")
        
    threading.Thread(target=intro, daemon=True).start()
    app.run()
