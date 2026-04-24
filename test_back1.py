from ursina import *
import random

app = Ursina(title="HOLO Archives", borderless=True, fullscreen=True)

# 1. THE BACKGROUND (No 3D floor cutting it off!)
# We make it large and square (50x50) so it doesn't stretch and get blurry.
# We push it far back (z=25) and shift it up slightly (y=4) to frame it perfectly.
background = Entity(
    model='quad',
    texture='library.png',
    scale=(50, 50),
    position=(0, 4, 25)
)

# 2. THE LIBRARIAN
# By setting her Y position to -2.5, we lower her so her boots 
# visually touch the wooden floor path in your background image.
librarian = Entity(
    model='AnimeCharacter.glb',
    scale=2.2,
    position=(0, -2.5, 0),
    rotation=(0, 180, 0)
)

# 3. AMBIENT HOLO PARTICLES
# Keeping the cyan particles to maintain the "AI/Hologram" vibe
for i in range(60):
    Entity(
        model='sphere',
        color=color.cyan,
        scale=random.uniform(0.03, 0.06),
        # Spread them across the screen space
        position=(random.uniform(-10, 10), random.uniform(-4, 8), random.uniform(-5, 10))
    )

# 4. CAMERA
# Pull the camera back just enough to see her full body and the library
camera.position = (0, 0, -15)

app.run()
