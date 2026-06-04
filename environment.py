from ursina import Entity, color
from shader import holo_shader
import random
import math

class Environment:
    """Creates the hologram rings, library, and particles"""
    
    def __init__(self):
        # Hologram rings
        self.upper_ring = Entity(
            model='circle', scale=(3, 3, 1), position=(0, 3, 0),
            rotation=(90, 0, 0), color=color.cyan, shader=holo_shader, thickness=3
        )
        self.lower_ring = Entity(
            model='circle', scale=(3, 3, 1), position=(0, 0.2, 0),
            rotation=(90, 0, 0), color=color.cyan, shader=holo_shader, thickness=3
        )
        
        # Floor
        Entity(model='plane', scale=(40, 1, 40), texture='white_cube', color=color.rgb(5, 5, 15))
        
        # Bookshelves
        self._create_bookshelves()
        
        # Particles
        self.particles = self._create_particles()
        
        print("✅ Environment loaded!")
    
    def _create_bookshelves(self):
        for side in [-1, 1]:
            for i in range(8):
                Entity(
                    model='cube', scale=(2, 6, 8),
                    position=(side * 12, 1, -10 + i * 3),
                    color=color.rgb(30, 20, 15), texture='white_cube'
                )
                for j in range(12):
                    Entity(
                        model='cube', scale=(0.3, 1, 0.5),
                        position=(side * 12 + (j - 5) * 0.35, 0.5, -10 + i * 3),
                        color=color.rgb(
                            random.randint(40, 100),
                            random.randint(30, 80),
                            random.randint(20, 60)
                        )
                    )
    
    def _create_particles(self):
        particles = []
        for _ in range(100):
            p = Entity(
                model='sphere', scale=0.05,
                position=(
                    random.uniform(-5, 5),
                    random.uniform(-1, 6),
                    random.uniform(-3, 3)
                ),
                color=color.cyan, emissive=True
            )
            particles.append([p, random.uniform(0.02, 0.08)])
        return particles
    
    def update(self, is_talking):
        """Update rings and particles"""
        import time
        t = time.time()
        
        self.upper_ring.rotation_z += time.dt * 25
        self.lower_ring.rotation_z -= time.dt * 20
        
        # Particles
        for p, speed in self.particles:
            p.y += speed
            if p.y > 6:
                p.y = -1
            p.x += math.sin(t + p.y * 2) * 0.01
        
        # Ring pulse when talking
        if is_talking:
            glow = 1.2 + abs(math.sin(t * 10)) * 0.3
            self.upper_ring.scale = (3 * glow, 3 * glow, 1)
            self.lower_ring.scale = (3 * glow, 3 * glow, 1)
        else:
            self.upper_ring.scale = (3, 3, 1)
            self.lower_ring.scale = (3, 3, 1)
