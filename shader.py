from ursina import Shader

# Fixed shader: added vertex shader output for texcoord
holo_shader = Shader(
    vertex='''
    #version 140
    uniform mat4 p3d_ModelViewProjectionMatrix;
    in vec4 p3d_Vertex;
    in vec2 p3d_MultiTexCoord0;
    out vec2 texcoord;  // This was missing!

    void main() {
        gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
        texcoord = p3d_MultiTexCoord0;
    }
    ''',
    fragment='''
    #version 140
    uniform sampler2D p3d_Texture;
    in vec2 texcoord;
    out vec4 fragColor;

    void main() {
        vec4 color = texture(p3d_Texture, texcoord);
        float scanline = sin(texcoord.y * 300.0) * 0.3 + 0.7;
        float alpha = color.a * scanline;
        fragColor = vec4(0.0, 0.8, 1.0, alpha * 0.8);
    }
    '''
)
