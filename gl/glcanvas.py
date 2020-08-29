"""GLCanvas3D and associated classes."""

import gl.shaders as shaderlib
import math
import platform as pf
from gl.bed import GLBed
from gl.glutils import arcball
from gl.proxy3d import Proxy3D
from gl.viewcube import GLViewCube
from threading import Lock
from typing import List, NamedTuple, Optional

import numpy as np
import wx
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLU import *
from pydispatch import dispatcher
from wx import glcanvas

import glm
from utils import timing


class _Size(NamedTuple):

    width: int
    height: int
    scale_factor: float


class GLCanvas3D(glcanvas.GLCanvas):
    """Manage the OpenGL canvas in a wx.Window.

    Args:
        parent: Pointer to a parent wx.Window.
        build_dimensions: Optional; See GLBed.
        axes: Optional; See GLBed.
        bounding_box: Optional; See GLBed.
        every: Optional; See GLBed.
        subdivisions: Optional; See GLBed.

    Attributes:
        dirty: A boolean indicating if the canvas needs updating or not.
            Avoids unnecessary work by deferring it until the result is needed.
            See https://gameprogrammingpatterns.com/dirty-flag.html.
        rot_quat: Read ony; A glm quaternion representing current rotation.
            To convert to a transformation matrix, use glm.mat4_cast(rot_quat).
        bed: Read only; A GLBed object.
        proxy3d: Read only; A Proxy3D object.
        zoom: A float representing zoom level (higher is more zoomed in).
            Zoom is achieved in projection_matrix by modifying the fov.
        build_dimensions: See Args section.
        projection_matrix: Read only; A glm.mat4 representing the current
            projection matrix.
        modelview_matrix: Read only; A glm.mat4 representing the current
            modelview matrix.

    TODO: Add more documentation regarding OpenGL.
    """

    orbit_controls = True  # True: use arcball controls, False: use orbit controls
    color_background = (1.0, 1.0, 1.0, 1.0)
    zoom_min = 0.1
    zoom_max = 7.0

    def __init__(self, parent,
                 build_dimensions: List[int] = [400, 400, 400, 200, 200, 200],
                 every: int = 100,
                 subdivisions: int = 10) -> None:
        """Inits GLCanvas3D with constructors."""
        self.parent = parent
        display_attrs = glcanvas.GLAttributes()
        display_attrs.MinRGBA(8, 8, 8, 8).DoubleBuffer().Depth(24).EndList()
        super().__init__(self.parent, display_attrs, id=wx.ID_ANY, pos=wx.DefaultPosition,
                         size=wx.DefaultSize, style=wx.BORDER_DEFAULT, name='GLCanvas', palette=wx.NullPalette)
        self._canvas = self
        self._context = glcanvas.GLContext(self._canvas)
        self._build_dimensions = build_dimensions

        # shader programs
        self._default_shader = None
        self._color_shader = None
        self._instanced_color_shader = None
        self._instanced_picking_shader = None

        # gl things TODO comment/regroup
        self._vao_box = None
        self._vao_side = None
        self._vao_top = None
        self._vao_paths = None
        self._point_lines = None
        self._point_count = None
        self._id_offset = len(wx.GetApp().core.devices)

        # screen is only refreshed from the OnIdle handler if it is dirty
        self._dirty = False
        self._gl_initialized = False
        self._scale_factor = None
        self._mouse_pos = None

        # other objects
        self._dist = 0.5 * (self._build_dimensions[1] + \
                            max(self._build_dimensions[0], self._build_dimensions[2]))
        self._bed = GLBed(self, build_dimensions, every, subdivisions)
        self._viewcube = GLViewCube(self)
        self._proxy3d = Proxy3D('Sphere', [1], (0, 53, 107))

        # other values
        self._zoom = 1
        self._hover_id = -1
        self._inside = False
        self._rot_quat = glm.quat()
        self._rot_lock = Lock()
        self._object_scale = 7.5

        # bind copiscore listeners
        dispatcher.connect(self.update_volumes, signal='core_p_list_changed')
        dispatcher.connect(self.update_id_offset, signal='core_d_list_changed')

        # bind events
        self._canvas.Bind(wx.EVT_SIZE, self.on_size)
        self._canvas.Bind(wx.EVT_IDLE, self.on_idle)
        self._canvas.Bind(wx.EVT_KEY_DOWN, self.on_key)
        self._canvas.Bind(wx.EVT_KEY_UP, self.on_key)
        self._canvas.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self._canvas.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)
        self._canvas.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick)
        self._canvas.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)
        self._canvas.Bind(wx.EVT_PAINT, self.on_paint)
        self._canvas.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)

    def init_opengl(self) -> bool:
        """Initialize and set OpenGL capabilities.

        Returns:
            True if initialized without error, False otherwise.
        """
        if self._gl_initialized:
            return True

        if self._context is None:
            return False

        glClearColor(*self.color_background)
        glClearDepth(1.0)

        glDepthFunc(GL_LESS)

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # set antialiasing
        glEnable(GL_LINE_SMOOTH)

        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_MULTISAMPLE)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        self.create_vaos()
        self.update_volumes()

        # compile shader programs
        self._default_shader = shaderlib.compile_shader(*shaderlib.default)
        self._color_shader = shaderlib.compile_shader(*shaderlib.single_color)
        self._instanced_color_shader = shaderlib.compile_shader(*shaderlib.single_color_instanced)
        self._instanced_picking_shader = shaderlib.compile_shader(*shaderlib.instanced_picking)

        self._gl_initialized = True
        return True

    def create_vaos(self) -> None:
        """Bind VAOs to define vertex data."""
        self._vao_box, self._vao_side, self._vao_top = glGenVertexArrays(3)
        vbo = glGenBuffers(4)

        vertices = np.array([
            -0.5, -1.0, -1.0,  # bottom
            0.5, -1.0, -1.0,
            0.5, -1.0, 1.0,
            -0.5, -1.0, 1.0,
            -0.5, 1.0, -1.0,   # right
            0.5, 1.0, -1.0,
            0.5, -1.0, -1.0,
            -0.5, -1.0, -1.0,
            -0.5, 1.0, 1.0,    # top
            0.5, 1.0, 1.0,
            0.5, 1.0, -1.0,
            -0.5, 1.0, -1.0,
            -0.5, -1.0, 1.0,   # left
            0.5, -1.0, 1.0,
            0.5, 1.0, 1.0,
            -0.5, 1.0, 1.0,
            0.5, 1.0, -1.0,    # back
            0.5, 1.0, 1.0,
            0.5, -1.0, 1.0,
            0.5, -1.0, -1.0,
            -0.5, -1.0, -1.0,  # front
            -0.5, -1.0, 1.0,
            -0.5, 1.0, 1.0,
            -0.5, 1.0, -1.0,
        ], dtype=np.float32)
        glBindVertexArray(self._vao_box)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # ---

        thetas = np.linspace(0, 2 * np.pi, 24, endpoint=True)
        y = np.cos(thetas) * 0.7
        z = np.sin(thetas) * 0.7
        vertices = np.zeros(6 * 24, dtype=np.float32)
        vertices[::3] = np.tile(np.array([1.0, 0.5], dtype=np.float32), 24)
        vertices[1::3] = np.repeat(y, 2)
        vertices[2::3] = np.repeat(z, 2)
        glBindVertexArray(self._vao_side)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # ---

        vertices = np.concatenate((np.array([1.0, 0.0, 0.0]), vertices)).astype(np.float32)
        indices = np.insert(np.arange(24) * 2 + 1, 0, 0).astype(np.uint16)
        glBindVertexArray(self._vao_top)

        glBindBuffer(GL_ARRAY_BUFFER, vbo[2])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo[3])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        # ---

        glBindVertexArray(0)
        glDeleteBuffers(4, vbo)

    def update_volumes(self) -> None:
        """When points are modified, recalculate volumes for rendering.

        Handles core_p_list_changed signal sent by wx.GetApp().core.
        """
        points = wx.GetApp().core.points
        self._point_count = len(points)

        self._point_lines = np.array([], dtype=np.float32)
        point_mats = np.array([], dtype=np.float32)
        for id_, point in points:
            p, t = point.p, point.t
            model =  \
                glm.translate(glm.mat4(), glm.vec3(point.x, point.y, point.z)) * \
                glm.scale(glm.mat4(), glm.vec3(self._object_scale, self._object_scale, self._object_scale)) * \
                glm.mat4(math.cos(t) * math.cos(p), -math.sin(t), math.cos(t) * math.sin(p), 0.0,
                         math.sin(t) * math.cos(p), math.cos(t), math.sin(t) * math.sin(p), 0.0,
                         -math.sin(p), 0.0, math.cos(p), 0.0,
                         0.0, 0.0, 0.0, 1.0)
            # http://planning.cs.uiuc.edu/node102.html

            point_mats = np.append(point_mats, np.array(model, dtype=np.float32))
            self._point_lines = np.append(self._point_lines, np.array([point.x, point.y, point.z], dtype=np.float32))

        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, self._point_count * glm.sizeof(glm.mat4), point_mats, GL_STATIC_DRAW)

        for vao in (self._vao_box, self._vao_side, self._vao_top):
            glBindVertexArray(vao)

            # set attribute pointers for matrix (4 times vec4)
            glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(0))
            glEnableVertexAttribArray(3)
            glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(16)) # sizeof(glm::vec4)
            glEnableVertexAttribArray(4)
            glVertexAttribPointer(5, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(32)) # 2 * sizeof(glm::vec4)
            glEnableVertexAttribArray(5)
            glVertexAttribPointer(6, 4, GL_FLOAT, GL_FALSE, 64, ctypes.c_void_p(48)) # 3 * sizeof(glm::vec4)
            glEnableVertexAttribArray(6)

            glVertexAttribDivisor(3, 1)
            glVertexAttribDivisor(4, 1)
            glVertexAttribDivisor(5, 1)
            glVertexAttribDivisor(6, 1)

            glBindVertexArray(0)

        self._vao_paths = glGenVertexArrays(1)
        glBindVertexArray(self._vao_paths)

        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, self._point_lines.nbytes, self._point_lines, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        self._dirty = True

    def update_id_offset(self) -> None:
        self._id_offset = len(wx.GetApp().core.devices)

    # @timing
    def render(self):
        """Render frame.

        First runs through a picking pass, clears the buffer, and then calls all
        rendering sub-methods.
        """
        # ensure that canvas is current and initialized
        if not self._is_shown_on_screen() or not self._set_current():
            return

        # ensure that opengl is initialized
        if not self.init_opengl():
            return

        canvas_size = self.get_canvas_size()
        glViewport(0, 0, canvas_size.width, canvas_size.height)

        # run picking pass
        self._picking_pass()

        # reset viewport as _picking_pass tends to mess with it
        glViewport(0, 0, canvas_size.width, canvas_size.height)

        # clear buffers and render everything
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        self._render_background()
        self._render_bed()
        self._render_cameras()
        self._render_points_and_paths()
        self._render_viewcube()

        self._canvas.SwapBuffers()

    # --------------------------------------------------------------------------
    # Event handlers
    # --------------------------------------------------------------------------

    def on_size(self, event: wx.SizeEvent) -> None:
        """On EVT_SIZE, set dirty flag true."""
        self._dirty = True

    def on_idle(self, event: wx.IdleEvent) -> None:
        """On EVT_IDLE, render only if needed."""
        if not self._gl_initialized or self._canvas.IsFrozen():
            return

        if not self._dirty:
            return

        self._refresh_if_shown_on_screen()
        # event.RequestMore()

        self._dirty = False

    def on_key(self, event: wx.KeyEvent) -> None:
        """Handle EVT_KEY_DOWN and EVT_KEY_UP."""
        pass

    def on_mouse_wheel(self, event: wx.MouseEvent) -> None:
        """On mouse wheel change, adjust zoom accordingly."""
        if not self._gl_initialized or event.MiddleIsDown():
            return

        scale = self.get_scale_factor()
        event.x = int(event.x * scale)
        event.y = int(event.y * scale)

        self._update_camera_zoom(event.WheelRotation / event.WheelDelta)

    def on_mouse(self, event: wx.MouseEvent) -> None:
        """Handle mouse events.

        Args:
            event: A wx.MouseEvent.
                LMB drag:   move viewport
                RMB drag:   unused
                LMB/RMB up: reset position

        TODO: make this more robust, and capable of handling selection
        """
        if not self._gl_initialized or not self._set_current():
            return

        scale = self.get_scale_factor()
        event.x = int(event.x * scale)
        event.y = int(event.y * scale)

        if event.Dragging():
            if event.LeftIsDown():
                self.rotate_camera(event, orbit=self.orbit_controls)
            elif event.RightIsDown() or event.MiddleIsDown():
                self.translate_camera(event)

        elif event.LeftUp() or event.MiddleUp() or event.RightUp():
            pass

        elif event.Entering():
            self._inside = True

        elif event.Leaving():
            self._inside = False

        elif event.Moving():
            self._mouse_pos = event.Position

        else:
            event.Skip()

        self._dirty = True

    def on_left_dclick(self, event: wx.MouseEvent) -> None:
        id_ = self._hover_id
        if id_ == -1:
            return

        if self._viewcube.hovered:
            if id_ == 0:    # front
                self._rot_quat = glm.quat()
            elif id_ == 1:  # top
                self._rot_quat = glm.quat(glm.radians(glm.vec3(90, 0, 0)))
            elif id_ == 2:  # right
                self._rot_quat = glm.quat(glm.radians(glm.vec3(0, -90, 0)))
            elif id_ == 3:  # bottom
                self._rot_quat = glm.quat(glm.radians(glm.vec3(-90, 0, 0)))
            elif id_ == 4:  # left
                self._rot_quat = glm.quat(glm.radians(glm.vec3(0, 90, 0)))
            elif id_ == 5:  # back
                self._rot_quat = glm.quat(glm.radians(glm.vec3(0, 180, 0)))
            else:
                pass

        else:
            # id_ belongs to cameras or objects
            offset = len(wx.GetApp().core.devices)
            if id_ < offset:
                wx.GetApp().core.select_device_by_index(id_)
            else:
                wx.GetApp().core.select_device_by_id(-1)
                wx.GetApp().core.select_point(id_ - offset, True)

    def on_erase_background(self, event: wx.EraseEvent) -> None:
        """On EVT_ERASE_BACKGROUND, do nothing. Avoids flashing on MSW."""
        pass

    def on_paint(self, event: wx.PaintEvent) -> None:
        """On EVT_PAINT, try to refresh canvas."""
        if self._gl_initialized:
            self._dirty = True
        else:
            self.render()

    def on_set_focus(self, event: wx.FocusEvent) -> None:
        """On EVT_SET_FOCUS, try to refresh canvas."""
        self._refresh_if_shown_on_screen()

    def get_canvas_size(self) -> _Size:
        """Return canvas size as _Size based on scaling factor."""
        w, h = self._canvas.Size
        factor = self.get_scale_factor()
        w = int(w * factor)
        h = int(h * factor)
        return _Size(w, h, factor)

    # --------------------------------------------------------------------------
    # Render util methods
    # --------------------------------------------------------------------------

    def destroy(self) -> None:
        """Clean up the OpenGL context."""
        self._context.Destroy()
        glcanvas.GLCanvas.Destroy()

    @property
    def dirty(self) -> bool:
        return self._dirty

    @dirty.setter
    def dirty(self, value: bool) -> None:
        self._dirty = value

    def _is_shown_on_screen(self) -> bool:
        return self._canvas.IsShownOnScreen()

    def _set_current(self) -> bool:
        return False if self._context is None else self._canvas.SetCurrent(self._context)

    def _update_camera_zoom(self, delta_zoom: float) -> None:
        zoom = self._zoom / (1.0 - max(min(delta_zoom, 4.0), -4.0) * 0.1)
        self._zoom = max(min(zoom, self.zoom_max), self.zoom_min)
        self._dirty = True

        # update visualizer panel zoom slider
        self.parent.set_zoom_slider(self._zoom)

    def _refresh_if_shown_on_screen(self) -> None:
        if self._is_shown_on_screen():
            self._set_current()
            self.render()

    def _picking_pass(self) -> None:
        """Set _hover_id to represent what the user is currently hovering over.

        Calls _render_objects_for_picking, and reads pixels to convert the
        moused-over color to an id. Simpler than raycast intersections.
        """
        # pylint: disable=no-value-for-parameter
        if self._mouse_pos is None:
            return

        # disable multisampling and antialiasing
        glDisable(GL_MULTISAMPLE)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        self._render_objects_for_picking()

        glEnable(GL_MULTISAMPLE)
        glEnable(GL_BLEND)

        id_ = -1

        canvas_size = self.get_canvas_size()
        mouse = list(self._mouse_pos.Get())
        mouse[1] = canvas_size.height - mouse[1] - 1

        if self._inside:
            # convert rgb value back to id
            color = glReadPixels(mouse[0], mouse[1], 1, 1, GL_RGB, GL_UNSIGNED_BYTE)
            id_ = color[0] + (color[1] << 8) + (color[2] << 16)

            # ignore white (background color)
            if id_ == 16777215:
                id_ = -1

        # check if mouse is inside viewcube area
        viewcube_area = self._viewcube.get_viewport()
        if viewcube_area[0] <= mouse[0] <= viewcube_area[0] + viewcube_area[2] and \
           viewcube_area[1] <= mouse[1] <= viewcube_area[1] + viewcube_area[3]:
            self._viewcube.hover_id = id_
        else:
            self._viewcube.hover_id = -1

        self._hover_id = id_

    def _render_objects_for_picking(self) -> None:
        """Render objects with RGB color corresponding to id for picking.

        """
        glUseProgram(self._instanced_picking_shader)
        proj = self.projection_matrix
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        view = self.modelview_matrix
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))
        glUniform1i(2, self._id_offset)

        glBindVertexArray(self._vao_box)
        glDrawArraysInstanced(GL_QUADS, 0, 24, self._point_count)

        glBindVertexArray(self._vao_side)
        glDrawArraysInstanced(GL_TRIANGLE_STRIP, 0, 48, self._point_count)

        glBindVertexArray(self._vao_top)
        glDrawElementsInstanced(GL_TRIANGLE_FAN, 25, GL_UNSIGNED_SHORT, ctypes.c_void_p(0), self._point_count)

        glBindVertexArray(0)

        self._viewcube.render_for_picking()

        glBindVertexArray(0)
        glUseProgram(0)

    def _render_background(self) -> None:
        """Clear the background color."""
        glClearColor(*self.color_background)

    def _render_bed(self) -> None:
        """Render bed."""
        if self._bed is not None:
            self._bed.render()

    def _render_cameras(self) -> None:
        """Render cameras."""
        pass

    def _render_points_and_paths(self) -> None:
        """Render points and paths."""
        proj = self.projection_matrix
        view = self.modelview_matrix
        model = glm.mat4()

        glUseProgram(self._color_shader)
        color = glm.vec4(70, 70, 70, 255) / 255.0
        glUniform4fv(3, 1, glm.value_ptr(color))

        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))
        glUniformMatrix4fv(2, 1, GL_FALSE, glm.value_ptr(model))

        glBindVertexArray(self._vao_paths)
        glDrawArrays(GL_LINE_STRIP, 0, self._point_lines.size // 3)

        # ---

        glUseProgram(self._instanced_color_shader)
        glUniformMatrix4fv(0, 1, GL_FALSE, glm.value_ptr(proj))
        glUniformMatrix4fv(1, 1, GL_FALSE, glm.value_ptr(view))

        color = glm.vec4(210, 210, 210, 180) / 255.0
        glBindVertexArray(self._vao_box)
        glUniform4fv(2, 1, glm.value_ptr(color))
        glDrawArraysInstanced(GL_QUADS, 0, 24, self._point_count)

        color -= 0.05
        glUniform4fv(2, 1, glm.value_ptr(color))
        glBindVertexArray(self._vao_side)
        glDrawArraysInstanced(GL_TRIANGLE_STRIP, 0, 48, self._point_count)

        color -= 0.05
        glUniform4fv(2, 1, glm.value_ptr(color))
        glBindVertexArray(self._vao_top)
        glDrawElementsInstanced(GL_TRIANGLE_FAN, 25, GL_UNSIGNED_SHORT, ctypes.c_void_p(0), self._point_count)

        glBindVertexArray(0)

        # ---

        glBindVertexArray(0)
        glUseProgram(0)

    def _render_viewcube(self) -> None:
        """Render ViewCube."""
        if self._viewcube is not None:
            self._viewcube.render()

    # --------------------------------------------------------------------------
    # Accessor functions
    # --------------------------------------------------------------------------

    def get_shader_program(
        self, program: Optional[str] = 'default'
    ) -> Optional[shaders.ShaderProgram]:
        """Return specified shader program.

        Args:
            program: Optional; A string for selection. Defaults to 'default'.

        Returns:
            A GLuint compiled shader reference. See
            http://pyopengl.sourceforge.net/documentation/pydoc/OpenGL.GL.shaders.html
            for more info.
        """
        if program == 'color':
            return self._color_shader
        return self._default_shader # 'default'

    @property
    def rot_quat(self) -> glm.quat:
        return self._rot_quat

    @property
    def bed(self) -> GLBed:
        return self._bed

    @property
    def proxy3d(self) -> Proxy3D:
        return self._proxy3d

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        self._zoom = value
        self._dirty = True

    @property
    def build_dimensions(self) -> List[int]:
        return self._build_dimensions

    @build_dimensions.setter
    def build_dimensions(self, value: List[int]) -> None:
        self._build_dimensions = value
        self._bed.build_dimensions = value
        self._dirty = True

    @property
    def object_scale(self) -> float:
        return self._object_scale

    @object_scale.setter
    def object_scale(self, value: float) -> None:
        self._object_scale = value
        self._dirty = True

    # --------------------------------------------------------------------------
    # Matrix transformation methods
    # --------------------------------------------------------------------------

    @property
    def projection_matrix(self) -> glm.mat4:
        """Returns a glm.mat4 representing the current projection matrix."""
        canvas_size = self.get_canvas_size()
        aspect_ratio = canvas_size.width / canvas_size.height
        return glm.perspective(
            math.atan(math.tan(math.radians(45.0)) / self._zoom),
            aspect_ratio, 0.1, 2000.0)

    @property
    def modelview_matrix(self) -> glm.mat4:
        """Returns a glm.mat4 representing the current modelview matrix."""
        mat = glm.lookAt(glm.vec3(0.0, 0.0, self._dist * 1.5),  # position
                         glm.vec3(0.0, 0.0, 0.0),               # target
                         glm.vec3(0.0, 1.0, 0.0))               # up
        return mat * glm.mat4_cast(self._rot_quat)

    def rotate_camera(self, event: wx.MouseEvent, orbit: bool = True) -> None:
        """Update rotate quat to reflect rotation controls.

        Args:
            event: A wx.MouseEvent representing an updated mouse position.
            orbit: Optional; True: uses orbit controls, False: uses arcball
                controls. Defaults to True.
        """
        if self._mouse_pos is None:
            self._mouse_pos = event.Position
            return
        last = self._mouse_pos
        cur = event.Position

        canvas_size = self._canvas.get_canvas_size()
        p1x = last.x * 2.0 / canvas_size.width - 1.0
        p1y = 1 - last.y * 2.0 / canvas_size.height
        p2x = cur.x * 2.0 / canvas_size.width - 1.0
        p2y = 1 - cur.y * 2.0 / canvas_size.height

        # if p1x == p2x and p1y == p2y:
            # self._rot_quat = glm.quat()

        with self._rot_lock:
            if orbit:
                dx = p2y - p1y
                dz = p2x - p1x

                pitch = glm.angleAxis(dx, glm.vec3(-1.0, 0.0, 0.0))
                yaw = glm.angleAxis(dz, glm.vec3(0.0, 1.0, 0.0))
                self._rot_quat = pitch * self._rot_quat * yaw
            else:
                quat = arcball(p1x, p1y, p2x, p2y, self._dist / 250.0)
                self._rot_quat = quat * self._rot_quat
        self._mouse_pos = cur

    def translate_camera(self, event: wx.MouseEvent) -> None:
        """Translate camera.

        Args:
            event: A wx.MouseEvent representing an updated mouse position.

        TODO: implement this!
        """
        if self._mouse_pos is None:
            self._mouse_pos = event.Position
            return
        last = self._mouse_pos
        cur = event.Position
        # Do stuff
        self._mouse_pos = cur

    # --------------------------------------------------------------------------
    # Misc util methods
    # --------------------------------------------------------------------------

    def get_scale_factor(self) -> float:
        """Return scale factor based on display dpi.

        Currently very rudimentary; only checks if system is MacOS or not.
        TODO: make more robust and actually detect dpi?
        """
        if self._scale_factor is None:
            if pf.system() == 'Darwin': # MacOS
                self._scale_factor = 2.0
            else:
                self._scale_factor = 1.0
        return self._scale_factor
