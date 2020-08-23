"""TODO"""

from inspect import cleandoc
from typing import NamedTuple

from OpenGL.GL import GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, shaders


def compile_shader(vs: str, fs: str) -> shaders.ShaderProgram:
    """Compile and return shader given vertex and fragment shaders.

    Args:
        vs: A string which represents the vertex shader.
        fs: A string which represents the fragment shader.
    """
    return shaders.compileProgram(
        shaders.compileShader(vs, GL_VERTEX_SHADER),
        shaders.compileShader(fs, GL_FRAGMENT_SHADER))


class _Shader(NamedTuple):
    """Stores a vertex and fragment shader."""
    vs: str
    fs: str


default = _Shader(
    vs=cleandoc("""
    #version 450 core

    layout (location = 0) in vec3 positions;
    layout (location = 1) in vec3 colors;

    out vec3 new_color;

    layout (location = 0) uniform mat4 projection;
    layout (location = 1) uniform mat4 modelview;

    void main() {
        gl_Position = projection * modelview * vec4(positions, 1.0);
        new_color = colors;
    }
    """),

    fs=cleandoc("""
    #version 450 core

    in vec3 new_color;
    out vec4 color;

    void main() {
        color = vec4(new_color, 1.0);
    }
    """)
)

single_color = _Shader(
    vs=cleandoc("""
    #version 450 core

    layout (location = 0) in vec3 positions;

    layout (location = 0) uniform mat4 projection;
    layout (location = 1) uniform mat4 view;
    layout (location = 2) uniform mat4 model;

    void main() {
        gl_Position = projection * view * model * vec4(positions, 1.0);
    }
    """),

    fs=cleandoc("""
    #version 450 core

    out vec4 color;

    layout (location = 3) uniform vec4 new_color;

    void main() {
        color = new_color;
    }
    """)
)

single_color_instanced = _Shader(
    vs=cleandoc("""
    #version 450 core

    layout (location = 0) in vec3 positions;
    layout (location = 3) in mat4 instance_model;

    layout (location = 0) uniform mat4 projection;
    layout (location = 1) uniform mat4 view;

    void main() {
        gl_Position = projection * view * instance_model * vec4(positions, 1.0);
    }
    """),

    fs=cleandoc("""
    #version 450 core

    out vec4 color;

    layout (location = 2) uniform vec4 new_color;

    void main() {
        color = new_color;
    }
    """)
)
