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
# along with COPISClient. If not, see <https://www.gnu.org/licenses/>.

"""GLCanvas3D and associated classes.

TODO: Object collisions via general 3D object class.
"""

import math
import platform as pf
import glm
import numpy as np
import wx

from glm import vec3, mat4, quat
from threading import Lock
from typing import List, NamedTuple, Dict
from wx import glcanvas
from pydispatch import dispatcher
from OpenGL.GL import (shaders,
    GL_ARRAY_BUFFER, GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW,
    GL_MULTISAMPLE, GL_FALSE, GL_UNSIGNED_BYTE, GL_FLOAT, GL_AMBIENT_AND_DIFFUSE,
    GL_BLEND, GL_COLOR_BUFFER_BIT, GL_COLOR_MATERIAL, GL_CULL_FACE,
    GL_DEPTH_BUFFER_BIT, GL_DEPTH_TEST, GL_FILL, GL_FRONT_AND_BACK, GL_LESS,
    GL_LINE_SMOOTH, GL_ONE_MINUS_SRC_ALPHA, GL_RGB, GL_SRC_ALPHA,
    glGenVertexArrays, glDeleteBuffers, glGenBuffers,
    glBindVertexArray, glEnableVertexAttribArray, glUseProgram,
    glVertexAttribPointer, glBindBuffer, glBufferData, glBlendFunc, glClear,
    glClearColor, glClearDepth, glColorMaterial, glDepthFunc, glDisable, glEnable,
    glPolygonMode, glViewport, glReadPixels)
from OpenGL.GLU import ctypes

import copis.gl.shaders as shaderlib

from copis.mathutils import arcball
from copis.globals import MAX_ID
from copis.helpers import print_error_msg
from .actionvis import GLActionVis
from .objectvis import GLObjectVis
from .chamber import GLChamber
from .viewcube import GLViewCube


class _Size(NamedTuple):
    width: int
    height: int
    scale_factor: float


class GLCanvas3D(glcanvas.GLCanvas):
    """Manage the OpenGL canvas in a wx.Window.

    Args:
        parent: Pointer to a parent wx.Window.
        build_dimensions: Optional; See GLChamber.
        axes: Optional; See GLChamber.
        bounding_box: Optional; See GLChamber.
        every: Optional; See GLChamber.
        subdivisions: Optional; See GLChamber.

    Attributes:
        orbit_control: A boolean; True: use orbit controls for rotation,
            False: arcball (trackball) controls for rotation.
        orthographic: A boolean; True: viewport uses orthographic projection,
            False: viewport uses perspective projection.
        dirty: A boolean indicating if the canvas needs updating or not.
            Avoids unnecessary work by deferring it until the result is needed.
            See https://gameprogrammingpatterns.com/dirty-flag.html.
        rot_quat: Read only; A glm quaternion representing current rotation.
            To convert to a transformation matrix, use glm.mat4_cast(rot_quat).
        chamber: Read only; A GLChamber object.
        zoom: A float representing zoom level (higher is more zoomed in).
            Zoom is achieved in projection_matrix by modifying the fov.
        build_dimensions: See Args section.
        projection_matrix: Read only; A mat4 representing the current
            projection matrix.
        modelview_matrix: Read only; A mat4 representing the current
            modelview matrix.
    """

    orbit_control = True  # True: use orbit controls, False: use arcball controls
    orthographic = False  # True: orthographic projection, False: perspective projection
    # background_color = (0.9412, 0.9412, 0.9412, 1.0)
    background_color = (1.0, 1.0, 1.0, 1.0)
    zoom_min = 0.5
    zoom_max = 6.0

    def __init__(self, parent,
                 build_dimensions: List[int] = [400, 400, 400, 200, 200, 200],
                 every: int = 100,
                 subdivisions: int = 10) -> None:
        """Initializes GLCanvas3D with constructors."""
        self.parent = parent
        self.core = self.parent.core
        display_attrs = glcanvas.GLAttributes()
        display_attrs.MinRGBA(8, 8, 8, 8).DoubleBuffer().Depth(24).EndList()
        super().__init__(self.parent, display_attrs, id=wx.ID_ANY, pos=wx.DefaultPosition,
            size=wx.DefaultSize, style=wx.BORDER_DEFAULT, name='GLCanvas', palette=wx.NullPalette)
        self._canvas = self
        self._context = glcanvas.GLContext(self._canvas)
        self._build_dimensions = build_dimensions

        # shader programs
        self._shaders = {}

        # more opengl things
        self._vaos = {}
        self._point_lines = None
        self._point_count = None
        self._num_devices: int = len(self.core.project.devices)
        self._num_objects: int = len(self.core.project.proxies)

        self._dirty = False
        self._gl_initialized = False
        self._scale_factor = None
        self._mouse_pos = None

        # other objects
        self._dist = 0.5 * (self._build_dimensions[2] +
                            max(self._build_dimensions[0], self._build_dimensions[1]))
        self._chamber = GLChamber(self, build_dimensions, every, subdivisions)
        self._viewcube = GLViewCube(self)
        self._actionvis = GLActionVis(self)
        self._objectvis = GLObjectVis(self)

        # other values
        self._zoom = 1.0
        self._hover_id = -1
        self._inside = False
        self._rot_quat = quat()
        self._rot_lock = Lock()
        self._center = vec3(0.0, 0.0, (self._build_dimensions[5] - self._build_dimensions[2]) / 2.0)
        self._object_scale = 3.0

        # Bind listeners.
        dispatcher.connect(self._update_volumes, signal='ntf_a_list_changed')
        dispatcher.connect(self._update_colors, signal='ntf_a_selected')
        dispatcher.connect(self._update_colors, signal='ntf_a_deselected')
        dispatcher.connect(self._update_devices, signal='ntf_d_list_changed')
        dispatcher.connect(self._update_objects, signal='ntf_o_list_changed')
        dispatcher.connect(self._deselect_object, signal='ntf_o_deselected')

        dispatcher.connect(self._handle_device_homed, signal='ntf_device_homed')

        # Bind events.
        self._canvas.Bind(wx.EVT_SIZE, self.on_size)
        self._canvas.Bind(wx.EVT_IDLE, self.on_idle)
        self._canvas.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        self._canvas.Bind(wx.EVT_KEY_UP, self.on_key_up)
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

        glClearColor(*self.background_color)
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

        # compile shader programs
        self._shaders['default'] = shaderlib.compile_shader(*shaderlib.default)
        self._shaders['single_color'] = shaderlib.compile_shader(*shaderlib.single_color)
        self._shaders['instanced_model_color'] = \
            shaderlib.compile_shader(*shaderlib.instanced_model_color)
        self._shaders['instanced_model_multi_colors'] = \
            shaderlib.compile_shader(*shaderlib.instanced_model_multi_colors)
        self._shaders['instanced_picking'] = shaderlib.compile_shader(*shaderlib.instanced_picking)
        self._shaders['diffuse'] = shaderlib.compile_shader(*shaderlib.diffuse)
        self._shaders['solid'] = shaderlib.compile_shader(*shaderlib.solid)

        self._gl_initialized = True
        return True

    def create_vaos(self) -> None:
        """Bind VAOs to define vertex data."""
        self._vaos['box'], self._vaos['side'], \
        self._vaos['top'] = glGenVertexArrays(3)
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
        glBindVertexArray(self._vaos['box'])

        glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # --- below are unused vaos for rendering a cylinder (for the camerae model)
        # keep them, but TODO implement general object class

        thetas = np.linspace(0, 2 * np.pi, 24, endpoint=True)
        y = np.cos(thetas) * 0.7
        z = np.sin(thetas) * 0.7
        vertices = np.zeros(6 * 24, dtype=np.float32)
        vertices[::3] = np.tile(np.array([1.0, 0.5], dtype=np.float32), 24)
        vertices[1::3] = np.repeat(y, 2)
        vertices[2::3] = np.repeat(z, 2)
        glBindVertexArray(self._vaos['side'])

        glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        # ---

        vertices = np.concatenate((np.array([1.0, 0.0, 0.0]), vertices)).astype(np.float32)
        indices = np.insert(np.arange(24) * 2 + 1, 0, 0).astype(np.uint16)
        glBindVertexArray(self._vaos['top'])

        glBindBuffer(GL_ARRAY_BUFFER, vbo[2])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, vbo[3])
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        # ---

        glBindVertexArray(0)
        glDeleteBuffers(4, vbo)

    def _handle_device_homed(self) -> None:
        wx.CallAfter(self._update_devices)

    def _update_volumes(self) -> None:
        """When action list is modified, calculate point positions.

        Handles ntf_a_list_changed signal.
        """
        self._actionvis.update_actions()
        self._dirty = True

    def _update_colors(self) -> None:
        self._actionvis.update_action_vaos()
        self._dirty = True

    def _update_devices(self) -> None:
        """When the device list has changed, update actionvis and _num_devices.

        Handles ntf_d_list_changed signal.
        """
        self._num_devices = len(self.core.project.devices)
        self._actionvis.update_devices()
        self._dirty = True

    def _update_objects(self) -> None:
        """When the proxy object list has changed, update objectvis and _num_objects.

        Handles ntf_o_list_changed signal.
        """
        self._num_objects = len(self.core.project.proxies)
        self._objectvis.update_objects()
        self._dirty = True

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

        # clear buffers and render everything normally
        self._render_background()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self._render_chamber()
        self._render_actions_and_cameras()
        self._render_objects()
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

    def on_key_down(self, event: wx.KeyEvent) -> None:
        """Handle EVT_KEY_DOWN."""
        pass

    def on_key_up(self, event: wx.KeyEvent) -> None:
        """Handle EVT_KEY_UP."""
        keycode = event.KeyCode

        if keycode == wx.WXK_ESCAPE:
            self.core.select_device(-1)
            self.core.select_point(-1, clear=True)
            self.select_object(-1)

        # delete selected proxy object if backspace
        elif keycode == wx.WXK_BACK or keycode == wx.WXK_DELETE:
            for obj in reversed(self._objectvis.objects):
                if obj.selected:
                    self.core.project.proxies.pop(obj.object_id)

        else:
            event.Skip()

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
        event.x *= scale
        event.y *= scale

        if event.Dragging():
            if event.LeftIsDown():
                self.rotate_camera(event, orbit=self.orbit_control)
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

    def on_left_dclick(self, _) -> None:
        id_ = self._hover_id

        # id_ belongs to viewcube
        if self._viewcube.hovered:
            if id_ == 0:    # front
                self._rot_quat = quat()
            elif id_ == 1:  # top
                self._rot_quat = quat(glm.radians(vec3(90, 0, 0)))
            elif id_ == 2:  # right
                self._rot_quat = quat(glm.radians(vec3(0, 0, -90)))
            elif id_ == 3:  # bottom
                self._rot_quat = quat(glm.radians(vec3(-90, 0, 0)))
            elif id_ == 4:  # left
                self._rot_quat = quat(glm.radians(vec3(0, 0, 90)))
            elif id_ == 5:  # back
                self._rot_quat = quat(glm.radians(vec3(0, 0, 180)))
            else:
                pass

        else:
            # nothing selected
            if id_ == -1:
                self.core.select_device(-1)
                self.core.select_point(-1, clear=True)
                self.select_object(-1)

            # id_ belongs to camera device
            elif -1 < id_ < self._num_devices:
                self.core.select_device(id_)

            # id_ belongs to proxy object
            elif id_ > MAX_ID - self._num_objects:
                self.select_object(MAX_ID - id_)

            # id_ belongs to action point
            else:
                # un-offset ids
                self.core.select_point(id_ - self._num_devices, clear=True)

    def select_object(self, id_: int) -> None:
        """Select proxy object given id."""
        if id_ < 0:
            if len(self._objectvis.objects) > 0 and \
                any(obj.selected for obj in self._objectvis.objects):
                dispatcher.send('ntf_o_deselected')

        elif id_ in (x.object_id for x in self._objectvis.objects):
            self.core.select_point(-1)
            self.core.select_device(-1)
            for obj in self._objectvis.objects:
                is_obj_found = obj.object_id == id_
                obj.selected = is_obj_found
                if is_obj_found:
                    self.core.select_proxy(id_)

            dispatcher.send('ntf_o_selected', object=self.core.project.proxies[id_])
            self._dirty = True

        else:
            print_error_msg(self.core.console, f'invalid proxy object id {id_}.')

    def _deselect_object(self) -> None:
        for obj in self._objectvis.objects:
            obj.selected = False
            self.core.deselect_proxy(obj.object_id)

        self._dirty = True

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
        s = self._canvas.Size
        factor = self.get_scale_factor()
        w = int(s.width * factor)
        h = int(s.height * factor)
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

        # update viewport panel zoom slider
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

        # set background to white during picking pass so it can be ignored
        # its id will be 16777215 (MAX_ID + 1)
        glClearColor(1.0, 1.0, 1.0, 1.0)

        # disable multisampling and antialiasing
        glDisable(GL_MULTISAMPLE)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

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
            id_ = (color[0]) + (color[1] << 8) + (color[2] << 16)

            # ignore background color
            if id_ == MAX_ID + 1:
                id_ = -1

        # check if mouse is inside viewcube area
        viewcube_area = self._viewcube.viewport
        if viewcube_area[0] <= mouse[0] <= viewcube_area[0] + viewcube_area[2] and \
           viewcube_area[1] <= mouse[1] <= viewcube_area[1] + viewcube_area[3]:
            self._viewcube.hover_id = id_
        else:
            self._viewcube.hover_id = -1

        self._hover_id = id_

    def _render_objects_for_picking(self) -> None:
        """Render objects with RGB color corresponding to id for picking."""
        self._objectvis.render_for_picking()
        self._actionvis.render_for_picking()
        self._viewcube.render_for_picking()

        glBindVertexArray(0)
        glUseProgram(0)

    def _render_background(self) -> None:
        """Clear the background color."""
        glClearColor(*self.background_color)

    def _render_chamber(self) -> None:
        """Render chamber."""
        if self._chamber is not None:
            self._chamber.render()

    def _render_objects(self) -> None:
        """Render proxy objects."""
        if self._objectvis is not None:
            self._objectvis.render()

    def _render_actions_and_cameras(self) -> None:
        """Render paths."""
        if self._actionvis is not None:
            self._actionvis.render()

    def _render_viewcube(self) -> None:
        """Render ViewCube."""
        if self._viewcube is not None:
            self._viewcube.render()

    # --------------------------------------------------------------------------
    # Accessor methods
    # --------------------------------------------------------------------------

    @property
    def shaders(self) -> Dict[str, shaders.ShaderProgram]:
        return self._shaders

    @property
    def rot_quat(self) -> quat:
        return self._rot_quat

    @property
    def chamber(self) -> GLChamber:
        return self._chamber

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
        self._chamber.build_dimensions = value
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
    def projection_matrix(self) -> mat4:
        """Returns a mat4 representing the current projection matrix."""
        canvas_size = self.get_canvas_size()
        if self.orthographic:
            return glm.ortho(
                -canvas_size.width / 2.0 / self._zoom, canvas_size.width / 2.0 / self._zoom,
                -canvas_size.height / 2.0 / self._zoom, canvas_size.height / 2.0 / self._zoom,
                -5.0 * self._dist, 5.0 * self._dist)
        else:
            aspect_ratio = canvas_size.width / canvas_size.height
            return glm.perspective(
                math.atan(math.tan(math.radians(45.0))),
                aspect_ratio, 0.1, 2000.0)

    @property
    def modelview_matrix(self) -> mat4:
        """Returns a mat4 representing the current modelview matrix."""
        mat = glm.lookAt(vec3(0.0, -self._dist * 2.0 / self._zoom, 0.0),  # eye
                         vec3(0.0, 0.0, 0.0),                             # center
                         vec3(0.0, 0.0, 1.0))                             # up
        return glm.translate(mat * glm.mat4_cast(self._rot_quat), self._center)

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

        with self._rot_lock:
            if orbit:
                dx = p2y - p1y
                dy = p2x - p1x

                pitch = glm.angleAxis(dx, vec3(-1.0, 0.0, 0.0))
                yaw = glm.angleAxis(dy, vec3(0.0, 0.0, 1.0))
                self._rot_quat = pitch * self._rot_quat * yaw
            else:
                quat = arcball(p1x, p1y, p2x, p2y, self._dist / 250.0)
                self._rot_quat = quat * self._rot_quat
        self._mouse_pos = cur

    def translate_camera(self, event: wx.MouseEvent) -> None:
        """Translate camera. Currently only translates along z axis.

        Args:
            event: A wx.MouseEvent representing an updated mouse position.

        TODO: Make it so you can translate freely?
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

        dy = p2y - p1y
        new_z = self._center.z + dy * self._dist / 1.5 / self._zoom
        if new_z < self._build_dimensions[5] - self._build_dimensions[2]:
            new_z = self._build_dimensions[5] - self._build_dimensions[2]
        if new_z > self._build_dimensions[5]:
            new_z = self._build_dimensions[5]
        self._center.z = new_z

        self._mouse_pos = cur

    # --------------------------------------------------------------------------
    # Misc util methods
    # --------------------------------------------------------------------------

    def get_scale_factor(self) -> float:
        """Return scale factor based on display dpi.

        Currently very rudimentary; only checks if system is MacOS or not.

        TODO: make more robust and actually detect dpi?
            - check out self.GetContentScaleFactor() and
              GetDPIScaleFactor(), might be better than this
        """
        # return self.GetContentScaleFactor()
        if self._scale_factor is None:
            if pf.system() == 'Darwin': # MacOS
                self._scale_factor = 2.0
            else:
                self._scale_factor = 1.0
        return self._scale_factor
