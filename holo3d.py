from ursina import *
import pyttsx3
import threading
import time
import math

# ========== TTS SETUP ==========
tts = pyttsx3.init()
tts.setProperty('rate', 150)
tts.setProperty('volume', 0.9)

# ========== 3D HOLO LIBRARIAN ==========
app = Ursina(title="HOLO 3D Librarian", borderless=True, fullscreen=True)

# Dark environment
window.color = color.rgb(0, 0, 5)

# Floor with grid
Entity(model='plane', scale=(50, 1, 50), texture='white_cube', color=color.rgb(10, 10, 20))

# === UPPER HOLOGRAM RINGS (using circle of cubes) ===
upper_rings = []
for i in range(36):
    angle = i * 10
    ring = Entity(
        model='cube',
        scale=(0.3, 0.05, 0.3),
        position=(math.cos(math.radians(angle)) * 4, 6, math.sin(math.radians(angle)) * 4),
        rotation=(0, angle, 0),
        color=color.azure,
        emissive=True
    )
    upper_rings.append(ring)

# === LOWER PLATFORM RINGS ===
lower_rings = []
for i in range(32):
    angle = i * 11.25
    ring = Entity(
        model='cube',
        scale=(0.25, 0.05, 0.25),
        position=(math.cos(math.radians(angle)) * 3, -1, math.sin(math.radians(angle)) * 3),
        rotation=(0, angle, 0),
        color=color.azure,
        emissive=True
    )
    lower_rings.append(ring)

# === HOLOGRAM LIBRARIAN FIGURE ===
# Head
holo_head = Entity(
    model='sphere',
    scale=0.6,
    position=(0, 3.5, 0),
    color=color.azure,
    emissive=True
)

# Body (elegant dress shape - tapered cylinder using scaled cubes)
body_parts = []
for i in range(12):
    y_pos = 2.8 - (i * 0.25)
    scale_factor = 0.8 - (i * 0.03)
    part = Entity(
        model='cube',
        scale=(scale_factor, 0.22, scale_factor),
        position=(0, y_pos, 0),
        color=color.azure,
        emissive=True
    )
    body_parts.append(part)

# Arms (holding book gesture)
arm_l_parts = []
for i in range(6):
    part = Entity(
        model='cube',
        scale=(0.15, 0.25, 0.15),
        position=(-0.6 - (i * 0.08), 2.2 - (i * 0.2), 0.3),
        color=color.azure,
        emissive=True
    )
    arm_l_parts.append(part)

arm_r_parts = []
for i in range(5):
    part = Entity(
        model='cube',
        scale=(0.15, 0.25, 0.15),
        position=(0.6 + (i * 0.08), 2.2 - (i * 0.2), 0.2),
        color=color.azure,
        emissive=True
    )
    arm_r_parts.append(part)

# Book in left hand
holo_book = Entity(
    model='cube',
    scale=(0.4, 0.5, 0.3),
    position=(-1.1, 0.8, 0.4),
    color=color.cyan,
    emissive=True
)

# Glasses on face
glasses_l = Entity(model='sphere', scale=0.12, position=(-0.15, 3.5, 0.35), color=color.white, emissive=True)
glasses_r = Entity(model='sphere', scale=0.12, position=(0.15, 3.5, 0.35), color=color.white, emissive=True)

# === BOOKSHELVES ===
for side in [-1, 1]:
    for shelf in range(6):
        shelf_entity = Entity(
            model='cube',
            scale=(1.5, 0.1, 5),
            position=(side * 10, -1 + shelf * 1.2, 0),
            color=color.rgb(40, 30, 20),
            emissive=False
        )
        # Books on shelf
        for book in range(8):
            b = Entity(
                model='cube',
                scale=(0.25, 0.8, 0.4),
                position=(side * 10 + (book - 3.5) * 0.28, -0.5 + shelf * 1.2, 0),
                color=color.rgb(
                    random.randint(30, 80),
                    random.randint(20, 60),
                    random.randint(10, 50)
                ),
                emissive=False
            )

# === FLOATING PARTICLES ===
particles = []
for _ in range(80):
    p = Entity(
        model='sphere',
        scale=0.04,
        position=(
            random.uniform(-4, 4),
            random.uniform(-1, 5),
            random.uniform(-2, 2)
        ),
        color=color.azure,
        emissive=True
    )
    particles.append([p, random.uniform(0.01, 0.05)])

# ========== ANIMATION & LOGIC ==========
is_talking = False
float_base = 0

def speak(text):
    global is_talking
    is_talking = True
    def _tts():
        tts.say(text)
        tts.runAndWait()
        time.sleep(0.5)
        global i_talking
        is_talking = False
    threading.Thread(target=_tts, daemon=True).start()

def update():
    global float_base
    
    # Gentle floating motion
    float_base = math.sin(time.time() * 1.5) * 0.15
    
    # Rotate upper rings
    for i, ring in enumerate(upper_rings):
        angle = (i * 10 + time.time() * 20) % 360
        ring.position = (
            math.cos(math.radians(angle)) * 4,
            6 + float_base * 0.5,
            math.sin(math.radians(angle)) * 4
        )
    
    # Rotate lower rings (opposite direction)
    for i, ring in enumerate(lower_rings):
        angle = (i * 11.25 - time.time() * 15) % 360
        ring.position = (
            math.cos(math.radians(angle)) * 3,
            -1 + float_base * 0.3,
            math.sin(math.radians(angle)) * 3
        )
    
    # Float hologram figure
    holo_head.y = 3.5 + float_base
    for i, part in enumerate(body_parts):
        part.y = (2.8 - (i * 0.25)) + float_base
    for i, part in enumerate(arm_l_parts):
        part.y = (2.2 - (i * 0.2)) + float_base
    for i, part in enumerate(arm_r_parts):
        part.y = (2.2 - (i * 0.2)) + float_base
    holo_book.y = 0.8 + float_base
    glasses_l.y = 3.5 + float_base
    glasses_r.y = 3.5 + float_base
    
    # Animate particles
    for p, speed in particles:
        p.y += speed
        if p.y > 5:
            p.y = -1
        p.x += math.sin(time.time() + p.y) * 0.005
    
    # Talking effect - pulse brightness
    if is_talking:
        pulse = 1.0 + abs(math.sin(time.time() * 8)) * 0.3
        holo_head.scale = (0.6 * pulse, 0.6 * pulse, 0.6 * pulse)
    else:
        holo_head.scale = (0.6, 0.6, 0.6)

# Camera position
camera.position = (0, 2, 12)
camera.look_at((0, 2, 0))

# ========== RUN ==========
if __name__ == '__main__':
    print("🌀 HOLO 3D Librarian starting... (Press ESC to quit)")
    
    def run_tests():
        time.sleep(2.5)
        tests = [
            "Hello! I am HOLO, your hologram librarian.",
            "I can help you find books, check availability, or check out titles.",
            "What book would you like to explore today?"
        ]
        for msg in tests:
            speak(msg)
            time.sleep(4)
    
    threading.Thread(target=run_tests, daemon=True).start()
    app.run()
