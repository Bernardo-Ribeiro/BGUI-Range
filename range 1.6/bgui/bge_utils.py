# bge_utils.py
# Standard BGUI and utility imports
from .widget import Widget, BGUI_MOUSE_NONE, BGUI_MOUSE_CLICK, BGUI_MOUSE_RELEASE, BGUI_MOUSE_ACTIVE, BGUI_NO_NORMALIZE, BGUI_NO_THEME
from .text.blf import BlfTextLibrary
from .theme import Theme
from . import key_defs
import collections
import bgui
import os
import weakref

# Attempt to import essential Range Engine modules at the module level.
# These will be validated and used by the System class.
# This approach aims to capture the modules once when this script is first loaded,
# hoping to get the correct versions before potential engine state changes affect re-imports.
try:
    from Range import logic as module_level_logic
    from Range import events as module_level_events
    from Range import render as module_level_render
    # Import Range.types specifically for comparison to detect incorrect module loading
    from Range import types as range_engine_types_module
except Exception as e:
    # If initial imports fail catastrophically, set them to None.
    # The System class __init__ will then raise an error.
    print(f"CRITICAL ERROR during initial Range Engine module imports: {e}")
    module_level_logic, module_level_events, module_level_render, range_engine_types_module = None, None, None, None

def get_screen_info():
    """
    Retorna informações sobre a tela atual.
    :return: Uma tupla contendo (largura, altura) da janela em pixels
    """
    try:
        from Range import render
        return (render.getWindowWidth(), render.getWindowHeight())
    except Exception as e:
        print(f"Erro ao obter informações da tela: {e}")
        return (800, 600)

def flatten_status_list(lst):
    """Achata listas aninhadas de qualquer profundidade em uma lista plana."""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten_status_list(item))
        else:
            result.append(item)
    return result

class Layout(Widget):
    """The base layout class to be used with the BGESystem"""

    def __init__(self, sys, data):
        """
        :param sys: The BGUI system
        :param data: User data
        """
        super().__init__(sys, size=[1, 1])
        self.data = data

    def update(self):
        """A function that is called by the system to update the widget (subclasses should override this)"""
        pass


class System(Widget):
    """
    Sistema BGUI unificado para uso com a Range Engine.
    Gerencia elementos de UI, renderização e integrações específicas da Range.
    """
    normalize_text = True

    def __init__(self, theme_name=None):
        # --- Inicialização específica da Range Engine ---
        try:
            from Range import logic as module_level_logic
            from Range import events as module_level_events
            from Range import render as module_level_render
            from Range import types as range_engine_types_module
        except Exception as e:
            print(f"CRITICAL ERROR during initial Range Engine module imports: {e}")
            module_level_logic = module_level_events = module_level_render = range_engine_types_module = None

        if not module_level_logic or not module_level_events or not module_level_render or not range_engine_types_module:
            raise ImportError("CRITICAL: Essential Range Engine modules (logic, events, render, types) were not loaded correctly.")

        # Workaround para inconsistências de importação
        logic_candidate = module_level_logic
        if logic_candidate is range_engine_types_module or \
           ('KX_PythonComponent' in dir(logic_candidate) and not hasattr(logic_candidate, 'expandPath')):
            if 'GameLogic' in globals() and hasattr(globals()['GameLogic'], 'expandPath'):
                self.logic = globals()['GameLogic']
            else:
                raise ImportError("CRITICAL: Range.logic resolved to Range.types and no suitable fallback found.")
        else:
            self.logic = logic_candidate

        render_candidate = module_level_render
        if render_candidate is range_engine_types_module or \
           (hasattr(render_candidate, '__name__') and render_candidate.__name__ == 'types' and not hasattr(render_candidate, 'getWindowWidth')):
            raise ImportError(f"CRITICAL: Range.render resolved to Range.types and not the expected render module.")
        else:
            self.render = render_candidate

        self.events = module_level_events
        # --- Fim do workaround ---

        # Caminho do tema
        if theme_name is None:
            theme_name = "default"
        
        theme_path = self.logic.expandPath(f"//bgui/themes/{theme_name}")
        if not os.path.exists(theme_path):
            print(f"BGUI WARNING: Theme '{theme_name}' not found. Using default theme at '//bgui/themes/default'.")
            theme_path = self.logic.expandPath("//bgui/themes/default")

        # --- Inicialização base do antigo System (system.py) ---
        # Viewport
        view = self.render.getWindowWidth(), self.render.getWindowHeight()
        self.textlib = BlfTextLibrary()
        self._system = weakref.ref(self)
        self.theme = Theme(theme_path)
        Widget.__init__(self, None, "<System>", size=[view[0], view[1]], pos=[0, 0], options=BGUI_NO_NORMALIZE|BGUI_NO_THEME)
        self._focused_widget = weakref.ref(self)
        self.lock_focus = False
        self.mouse = self.logic.mouse
        self.layout = None
        self.overlays = collections.OrderedDict()
        self.keymap = {getattr(self.events, val): getattr(key_defs, val) for val in dir(self.events) if val.endswith('KEY') or val.startswith('PAD')}
        self.main_frame = bgui.Frame(self, "main_frame", border=0)
        self.main_frame.colors = [(0, 0, 0, 0) for _ in range(4)]
        self.elements = {}

        # Callback de renderização pós-draw
        try:
            current_scene = self.logic.getCurrentScene()
            if current_scene:
                current_scene.post_draw.append(self._render)
            else:
                print("BGUI ERROR: Could not get current scene to add post_draw callback.")
        except Exception as e:
            print(f"BGUI ERROR: Failed to add post_draw callback: {e}")

    @property
    def focused_widget(self):
        return self._focused_widget()

    @focused_widget.setter
    def focused_widget(self, value):
        self._focused_widget = weakref.ref(value)

    def update_mouse(self, pos, click_state=BGUI_MOUSE_NONE):
        self.cursor_pos = pos
        Widget._handle_mouse(self, pos, click_state)

    def update_keyboard(self, key, is_shifted):
        Widget._handle_key(self, key, is_shifted)

    def _attach_widget(self, widget):
        if widget == self:
            return
        Widget._attach_widget(self, widget)

    def render(self):
        from .gl_utils import (
            glGetIntegerv, GL_VIEWPORT, glPushAttrib, GL_ALL_ATTRIB_BITS,
            glDisable, GL_DEPTH_TEST, GL_LIGHTING, glBindTexture, GL_TEXTURE_2D,
            glShadeModel, GL_SMOOTH, glMatrixMode, GL_TEXTURE, GL_PROJECTION,
            glPushMatrix, glLoadIdentity, gluOrtho2D, GL_MODELVIEW, glPopMatrix, glPopAttrib
        )

        view = glGetIntegerv(GL_VIEWPORT)
        if self.size != [view[2], view[3]]:
            self.size = [view[2], view[3]]

        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glBindTexture(GL_TEXTURE_2D, 0)
        glShadeModel(GL_SMOOTH)

        glMatrixMode(GL_TEXTURE)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, view[2], 0, view[3])
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        Widget._update_anims(self)
        Widget._draw(self)

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_TEXTURE)
        glPopMatrix()
        glPopAttrib()

    def _render(self):
        try:
            System.render(self)
        except Exception:
            import traceback
            traceback.print_exc()
            try:
                if hasattr(self, 'logic') and self.logic:
                    current_scene = self.logic.getCurrentScene()
                    if current_scene and self._render in current_scene.post_draw:
                        current_scene.post_draw.remove(self._render)
            except Exception as e_rem:
                print(f"BGUI Error: Could not remove _render from post_draw during exception handling: {e_rem}")

        for widget in self.elements.values():
            if hasattr(widget, '_mouse_over'):
                widget._mouse_over = widget._is_inside(self.cursor_pos)

    def run(self):
        if not hasattr(self, 'render') or not hasattr(self.render, 'getWindowWidth'):
            print(f"BGUI CRITICAL ERROR in run(): self.render (repr: {repr(getattr(self, 'render', 'N/A'))}) is not the expected render module or lacks getWindowWidth. System may not have initialized correctly.")
            return
        mouse_obj = self.mouse
        mouse_events = mouse_obj.inputs
        pos = list(mouse_obj.position[:])
        left_mouse_key = getattr(self.events, 'LEFTMOUSE', None)
        final_mouse_status_int = self.logic.KX_INPUT_NONE
        if left_mouse_key is not None and left_mouse_key in mouse_events:
            raw_status_from_engine = mouse_events[left_mouse_key].status
            status_list = raw_status_from_engine if not isinstance(raw_status_from_engine, list) else [raw_status_from_engine]
            if any(s == self.logic.KX_INPUT_JUST_ACTIVATED for s in status_list):
                final_mouse_status_int = self.logic.KX_INPUT_JUST_ACTIVATED
            elif any(s == self.logic.KX_INPUT_JUST_RELEASED for s in status_list):
                final_mouse_status_int = self.logic.KX_INPUT_JUST_RELEASED
            elif any(s == self.logic.KX_INPUT_ACTIVE for s in status_list):
                final_mouse_status_int = self.logic.KX_INPUT_ACTIVE
            else:
                final_mouse_status_int = self.logic.KX_INPUT_NONE
        pos[0] *= self.render.getWindowWidth()
        pos[1] = self.render.getWindowHeight() - (self.render.getWindowHeight() * pos[1])
        if final_mouse_status_int == self.logic.KX_INPUT_JUST_ACTIVATED:
            mouse_state = BGUI_MOUSE_CLICK
        elif final_mouse_status_int == self.logic.KX_INPUT_JUST_RELEASED:
            mouse_state = BGUI_MOUSE_RELEASE
        elif final_mouse_status_int == self.logic.KX_INPUT_ACTIVE:
            mouse_state = BGUI_MOUSE_ACTIVE
        else:
            mouse_state = BGUI_MOUSE_NONE
        self.update_mouse(pos, mouse_state)
        keyboard = self.logic.keyboard
        key_events = keyboard.inputs
        left_shift_key_event = getattr(self.events, 'LEFTSHIFTKEY', None)
        right_shift_key_event = getattr(self.events, 'RIGHTSHIFTKEY', None)
        is_shifted = False
        if left_shift_key_event is not None and left_shift_key_event in key_events:
            shift_status = key_events[left_shift_key_event].status
            if isinstance(shift_status, list) and shift_status: shift_status = shift_status[-1]
            if shift_status == self.logic.KX_INPUT_ACTIVE: is_shifted = True
        if not is_shifted and right_shift_key_event is not None and right_shift_key_event in key_events:
            shift_status = key_events[right_shift_key_event].status
            if isinstance(shift_status, list) and shift_status: shift_status = shift_status[-1]
            if shift_status == self.logic.KX_INPUT_ACTIVE: is_shifted = True
        for key, state in keyboard.inputs.items():
            if state == self.logic.KX_INPUT_JUST_ACTIVATED:
                if key in self.keymap:
                    self.update_keyboard(self.keymap[key], is_shifted)

    # Métodos de gerenciamento de elementos
    def add_element(self, element_class, name, **kwargs):
        parent = kwargs.pop('parent', self.main_frame)
        widget = element_class(parent, name, **kwargs)
        self.elements[name] = widget
        return widget

    def get_element(self, name):
        return self.elements.get(name)

    def remove_element(self, name):
        if name in self.elements:
            element = self.elements[name]
            if element.parent:
                try:
                    element.parent.remove_widget(element)
                except Exception as e:
                    print(f"BGUI Error: Failed to remove widget {name} from parent: {e}")
            del self.elements[name]

    def load_layout(self, layout, data=None):
        if self.layout:
            self._remove_widget(self.layout)
        # Aqui você pode adicionar lógica para carregar layouts, se necessário

    def cleanup(self):
        self.elements.clear()
        self.overlays.clear()
        self.layout = None
