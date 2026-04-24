from ursina import *
app = Ursina()

# Test 1: Can Ursina load ANY glb?
test_library = Entity(model='library.glb', scale=1, position=(3,0,0))

# Test 2: Try your file

test_model = Entity(model='AnimeCharacter.glb', scale=1, position=(3,0,0))



EditorCamera()
app.run()
