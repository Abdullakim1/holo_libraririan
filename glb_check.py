from ursina import *
from ursina.shaders import *
import threading
import time as time_module
import math
import subprocess

# ========== APP SETUP ==========
app = Ursina(title="HOLO Librarian", borderless=False)
window.color = color.black

# ========== SUBTLE HOLO SHADER ==========
holo_shader = Shader(language=Shader.GLSL,
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
    out vec4 fragColor;
    uniform sampler2D p3d_Texture;
    uniform float time;
    void main() {
        vec4 texColor = texture(p3d_Texture, texcoord);
        float scanline = sin(texcoord.y * 300.0 + time * 6.0) * 0.04 + 0.96;
        vec3 holoTint = vec3(0.85, 0.97, 1.0);
        vec3 finalColor = texColor.rgb * holoTint * scanline;
        fragColor = vec4(finalColor, texColor.a);
    }
    '''
)

# ========== LOAD MODEL ==========
librarian = Entity(
    model='anime.glb',
    scale=2,
    shader=holo_shader,
    double_sided=True
)

# ========== MOUTH CONTROL ==========
morph_data = None
morph_index = -1
mouth_value = 0.0

def setup_face():
    global morph_data, morph_index
    
    # Search inside the model for the geometry
    for np in librarian.model.find_all_matches('**'):
        node = np.node()
        if node.is_geom_node():
            # GeomNode contains one or more Geoms
            for i in range(node.get_num_geoms()):
                geom = node.get_geom(i)
                vdata = geom.get_vertex_data()
                
                # Check if this geometry has a Morph Table (Shape Keys)
                if vdata.has_morph():
                    morph_table = vdata.get_morph()
                    # Loop through the sliders to find 'MouthOpen'
                    for j in range(morph_table.get_num_sliders()):
                        name = morph_table.get_slider_name(j)
                        if name == 'MouthOpen':
                            morph_data = morph_table
                            morph_index = j
                            print(f"✅ Found MouthOpen! Morph Index: {j}")
                            return

    print("❌ Could not find 'MouthOpen'. Check your export settings.")

invoke(setup_face, delay=1)

# ========== SPEECH ==========
is_talking = False

def speak(text):
    global is_talking
    is_talking = True
    def _speak():
        global is_talking
        try:
            subprocess.run(['espeak', '-s', '140', '-v', 'en+f3', text],
                           capture_output=True)
        except FileNotFoundError:
            print(f"[HOLO says]: {text}")
        is_talking = False
    threading.Thread(target=_speak, daemon=True).start()

# ========== MAIN LOOP ==========
def update():
    global mouth_value
    t = time_module.time()
    delta = globalClock.getDt()

    librarian.set_shader_input('time', t)

    if morph_data is not None:
        # Calculate target (wiggle if talking, 0 if silent)
        target = (0.5 + math.sin(t * 30) * 0.5) if is_talking else 0.0
        
        # Smooth the value
        mouth_value = mouth_value + (target - mouth_value) * min(delta * 10, 1.0)
        
        # Apply to the morph slider
        morph_data.set_slider_value(morph_index, mouth_value)

# ========== CAMERA & START ==========
camera.position = (0, 2, -15)
camera.look_at((0, 1.5, 0))

def start():
    speak("Initialization successful. I am HOLO. How can I help you today?")

invoke(start, delay=2)
app.run()
