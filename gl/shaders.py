# This file is part of COPISClient.
#
# COPISClient is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# COPISClient is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with COPISClient.  If not, see <https://www.gnu.org/licenses/>.

"""Shader program object and util functions."""

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

instanced_model_color = _Shader(
    vs=cleandoc("""
    #version 450 core

    layout (location = 0) in vec3 positions;
    layout (location = 3) in mat4 instance_model;
    layout (location = 7) in vec4 instance_color;

    out vec4 new_color;

    layout (location = 0) uniform mat4 projection;
    layout (location = 1) uniform mat4 view;

    void main() {
        gl_Position = projection * view * instance_model * vec4(positions, 1.0);
        new_color = instance_color;
    }
    """),

    fs=cleandoc("""
    #version 450 core

    in vec4 new_color;

    out vec4 color;

    void main() {
        color = new_color;
    }
    """)
)

instanced_picking = _Shader(
    vs=cleandoc("""
    #version 450 core

    layout (location = 0) in vec3 positions;
    layout (location = 3) in mat4 instance_model;
    layout (location = 8) in int id;

    out vec3 new_color;

    layout (location = 0) uniform mat4 projection;
    layout (location = 1) uniform mat4 view;
    // layout (location = 2) uniform int id_offset;

    void main() {
        gl_Position = projection * view * instance_model * vec4(positions, 1.0);
        // int id = gl_InstanceID + id_offset;
        int r = (id & (0x000000FF << 0)) << 0;
        int g = (id & (0x000000FF << 8)) >> 8;
        int b = (id & (0x000000FF << 16)) >> 16;
        new_color = vec3(float(r) / 255.0, float(g) / 255.0, float(b) / 255.0);
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

test = _Shader(
    vs=cleandoc("""
    #version 450 core

    layout (location = 0) in vec2 TexCoord;
    layout (location = 1) in vec3 Normal;
    layout (location = 2) in vec3 Vertex;

    out vec3 new_color;

    layout (location = 0) uniform mat4 projection;
    layout (location = 1) uniform mat4 modelview;
    layout (location = 2) uniform mat4 model;

    void main() {
        gl_Position = projection * modelview * model * vec4(Vertex, 1.0);
        new_color = Normal;
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
