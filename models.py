from ursina import Entity
from direct.actor.Actor import Actor
import config

class AnimeCharacter:
    """Loads and manages the anime character with morph targets"""
    
    def __init__(self):
        # Load both models
        self.mouth_actor = Actor(config.MOUTH_MODEL)
        self.blink_actor = Actor(config.BLINK_MODEL)
        
        self.mouth_actor.stop()
        self.blink_actor.stop()
        
        # Mouth model (visible, original colors)
        self.character = Entity(
            position=config.CHARACTER_POS,
            rotation_x=-270,
            rotation_y=180,
            scale=config.CHARACTER_SCALE
        )
        self.mouth_actor.reparent_to(self.character)
        
        # Blink model (invisible, morph targets only)
        self.blink_parent = Entity(
            position=config.CHARACTER_POS,
            rotation_x=-270,
            rotation_y=180,
            scale=config.CHARACTER_SCALE
        )
        self.blink_actor.reparent_to(self.blink_parent)
        self.blink_actor.setColorScale(1, 1, 1, 0)
        
        # Get morph controls
        self.mouth_control = self.mouth_actor.controlJoint(None, 'modelRoot', 'MouthOpen')
        self.blink_control = self.blink_actor.controlJoint(None, 'modelRoot', 'Blink')
        
        print("✅ Anime character loaded with original colors!")
    
    def set_mouth(self, weight):
        """Set mouth openness (0.0 to 1.0)"""
        if self.mouth_control:
            self.mouth_control.set_x(weight * 0.01)
    
    def set_blink(self, weight):
        """Set blink amount (0.0 to 1.0)"""
        if self.blink_control:
            self.blink_control.set_x(weight * 0.01)
    
    def update_position(self):
        """Float animation - call from main update loop"""
        import math, time
        t = time.time()
        float_y = (config.CHARACTER_POS[1]+0.5) + math.sin(t * 1.5) * 0.2
        self.character.y = float_y
        self.blink_parent.y = float_y
