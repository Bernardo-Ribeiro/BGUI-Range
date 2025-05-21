import os
import sys

# Add BGUI to the path - adjust based on your installation
bgui_path = os.path.join(os.path.dirname(__file__), 'bgui')
if bgui_path not in sys.path:
    sys.path.append(bgui_path)

import Range as rg
import bgl
import bgui
from bgui import System
from bgui.text.blf import BlfTextLibrary

class RangeBGUI:
    def __init__(self, range_scene, theme_path=None):
        self.scene = range_scene
        self.textlib = BlfTextLibrary()

        self.system = System(self.textlib, theme_path)

        self.frame = bgui.Frame(self.system, "main_frame", border=1)
        self.frame.colors = [(0, 0, 0, 0) for _ in range(4)]

        self.elements = {}
        self.scene.post_draw.append(self._render_ui)

    def load_theme(self, theme_path):
        self.system.load_theme(theme_path)

    def _setup_callbacks(self):
        self.scene.post_draw.append(self._render_ui)
        self.scene.add_input_callback(self._handle_input)

    def _render_ui(self):
        bgl.glPushAttrib(bgl.GL_ALL_ATTRIB_BITS)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBlendFunc(bgl.GL_SRC_ALPHA, bgl.GL_ONE_MINUS_SRC_ALPHA)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        bgl.glHint(bgl.GL_LINE_SMOOTH_HINT, bgl.GL_NICEST)
        bgl.glEnable(bgl.GL_POLYGON_SMOOTH)

        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_NEAREST)
        bgl.glTexParameteri(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_NEAREST)

        self.system.render()

        bgl.glPopAttrib()



    def _handle_input(self, event):
        if event.type == rg.EVENT_MOUSE_MOVE:
            self.system.update_mouse(event.mouse_x, event.mouse_y)
        elif event.type == rg.EVENT_MOUSE_PRESS:
            self.system.update_mouse(event.mouse_x, event.mouse_y)
            self.system.activate_mouse_button(event.button)
        elif event.type == rg.EVENT_MOUSE_RELEASE:
            self.system.update_mouse(event.mouse_x, event.mouse_y)
            self.system.deactivate_mouse_button(event.button)
        elif event.type == rg.EVENT_KEY_PRESS:
            self.system.activate_key(event.key)
        elif event.type == rg.EVENT_KEY_RELEASE:
            self.system.deactivate_key(event.key)

    def add_element(self, element_class, name, **kwargs):
        parent = kwargs.pop('parent', self.frame)
        widget = element_class(parent, name, **kwargs)

        self.elements[name] = widget
        return widget


    def get_element(self, name):
        return self.elements.get(name)

    def remove_element(self, name):
        if name in self.elements:
            element = self.elements[name]
            element.parent.remove_widget(element)
            del self.elements[name]
    
    @property
    def theme(self):
        return self.system.theme
    
    def cleanup(self):
        self.scene.remove_post_draw_callback(self._render_ui)
        self.scene.remove_input_callback(self._handle_input)
        self.system = None
        self.elements = {}
