# bge_utils.py
# Standard BGUI and utility imports
from .system import System as BGUISystem
from .widget import Widget, BGUI_MOUSE_NONE, BGUI_MOUSE_CLICK, BGUI_MOUSE_RELEASE, BGUI_MOUSE_ACTIVE
from .text.blf import BlfTextLibrary
from . import key_defs
import collections
import bgui
import os

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


class System(BGUISystem):
    """
    A BGUI system adapted for use with Range Engine games.
    It handles UI element management and rendering, with workarounds for
    potential inconsistencies in Range Engine's Python module loading.
    """

    def __init__(self, theme_name=None):
        """
        Initializes the BGUI System.
        :param theme_name: The name of the theme directory to use.
        """
        # Check if the module-level imports were successful
        if not module_level_logic or not module_level_events or not module_level_render or not range_engine_types_module:
            raise ImportError("CRITICAL: Essential Range Engine modules (logic, events, render, types) "
                              "were not loaded correctly at the module level of bge_utils.py.")

        # --- Workaround for Range Engine module loading inconsistency ---
        # 1. Validate and assign self.logic
        logic_candidate = module_level_logic
        # Check if the imported 'logic' is actually the 'Range.types' module or similar
        if logic_candidate is range_engine_types_module or \
           ('KX_PythonComponent' in dir(logic_candidate) and not hasattr(logic_candidate, 'expandPath')):
            # If so, this indicates the engine provided Range.types instead of Range.logic.
            # Try a fallback: check if a 'GameLogic' module is available in the global scope.
            # This is a guess that 'GameLogic' might be the actual correct module and globally accessible.
            if 'GameLogic' in globals() and hasattr(globals()['GameLogic'], 'expandPath'):
                self.logic = globals()['GameLogic']
                # This warning can be enabled for debugging if issues persist
                # print("WARNING BGUI __init__: Range.logic resolved to Range.types. Using global 'GameLogic' as a fallback.")
            else:
                raise ImportError("CRITICAL BGUI __init__: Range.logic resolved to Range.types "
                                  "and no suitable fallback (like a global 'GameLogic') was found.")
        else:
            # The imported module_level_logic seems to be the correct game logic module
            self.logic = logic_candidate

        # 2. Validate and assign self.render
        render_candidate = module_level_render
        # Check if the imported 'render' is actually the 'Range.types' module
        if render_candidate is range_engine_types_module or \
           (hasattr(render_candidate, '__name__') and render_candidate.__name__ == 'types' 
            and not hasattr(render_candidate, 'getWindowWidth')):
            # This warning can be enabled for debugging
            # print(f"WARNING BGUI __init__: Range.render (repr: {repr(render_candidate)}) "
            #       "appears to be Range.types or similar!")
            # No standard fallback for 'render' is implemented here; an error is raised if it's incorrect.
            # If a reliable way to get the 'Rasterizer' or equivalent render module exists as a fallback,
            # it could be implemented similarly to the 'GameLogic' fallback.
            raise ImportError(f"CRITICAL BGUI __init__: Range.render (repr: {repr(render_candidate)}) "
                              "resolved to Range.types and not the expected render module (e.g., Rasterizer).")
        else:
            # The imported module_level_render seems to be the correct render module
            self.render = render_candidate
        
        # 3. Assign self.events (assuming it's less prone to this issue, or validate similarly if needed)
        self.events = module_level_events
        # --- End of Workaround ---

        # Proceed with BGUI system initialization using the validated modules
        theme_path = self.logic.expandPath(f"//bgui/themes/{theme_name}")
        if not os.path.exists(theme_path):
            # This warning is useful for users, not a debug print
            print(f"BGUI WARNING: Theme '{theme_name}' not found. Using default theme at '//bgui/themes/default'.")
            theme_path = self.logic.expandPath("//bgui/themes/default")

        super().__init__(BlfTextLibrary(), theme_path)

        self.mouse = self.logic.mouse
        self.layout = None
        self.overlays = collections.OrderedDict()
        self.keymap = {getattr(self.events, val): getattr(key_defs, val) for val in dir(self.events) if val.endswith('KEY') or val.startswith('PAD')}
        
        # Safely add post_draw callback
        try:
            current_scene = self.logic.getCurrentScene()
            if current_scene:
                current_scene.post_draw.append(self._render)
            else:
                print("BGUI ERROR: Could not get current scene to add post_draw callback.")
        except Exception as e:
            print(f"BGUI ERROR: Failed to add post_draw callback: {e}")

        self.main_frame = bgui.Frame(self, "main_frame", border=0)
        self.main_frame.colors = [(0, 0, 0, 0) for _ in range(4)]
        self.elements = {}

    def _render(self):
        try:
            super().render()
        except Exception:
            import traceback # Keep for runtime error diagnosis
            traceback.print_exc()
            try:
                if hasattr(self, 'logic') and self.logic:
                    current_scene = self.logic.getCurrentScene()
                    if current_scene and self._render in current_scene.post_draw:
                        current_scene.post_draw.remove(self._render)
            except Exception as e_rem:
                print(f"BGUI Error: Could not remove _render from post_draw during exception handling: {e_rem}")

    def run(self):
        if not hasattr(self, 'render') or not hasattr(self.render, 'getWindowWidth'):
            # This error indicates a critical failure in __init__ if render wasn't set up correctly
            print(f"BGUI CRITICAL ERROR in run(): self.render (repr: {repr(getattr(self, 'render', 'N/A'))}) "
                  "is not the expected render module or lacks getWindowWidth. System may not have initialized correctly.")
            return 

        mouse_obj = self.mouse
        mouse_events = mouse_obj.inputs
        pos = list(mouse_obj.position[:])

        pos[0] *= self.render.getWindowWidth()
        pos[1] = self.render.getWindowHeight() - (self.render.getWindowHeight() * pos[1])

        if mouse_events[self.events.LEFTMOUSE] == self.logic.KX_INPUT_JUST_ACTIVATED:
            mouse_state = BGUI_MOUSE_CLICK
        elif mouse_events[self.events.LEFTMOUSE] == self.logic.KX_INPUT_JUST_RELEASED:
            mouse_state = BGUI_MOUSE_RELEASE
        elif mouse_events[self.events.LEFTMOUSE] == self.logic.KX_INPUT_ACTIVE:
            mouse_state = BGUI_MOUSE_ACTIVE
        else:
            mouse_state = BGUI_MOUSE_NONE
        self.update_mouse(pos, mouse_state)

        keyboard = self.logic.keyboard
        key_events = keyboard.inputs
        
        # Ensure events module is valid for key constants
        left_shift_key_event = getattr(self.events, 'LEFTSHIFTKEY', None)
        right_shift_key_event = getattr(self.events, 'RIGHTSHIFTKEY', None)

        is_shifted = (left_shift_key_event is not None and key_events[left_shift_key_event] == self.logic.KX_INPUT_ACTIVE) or \
                     (right_shift_key_event is not None and key_events[right_shift_key_event] == self.logic.KX_INPUT_ACTIVE)

        for key, state in keyboard.inputs.items():
            if state == self.logic.KX_INPUT_JUST_ACTIVATED:
                if key in self.keymap:
                    self.update_keyboard(self.keymap[key], is_shifted)

    # --- Element Management Methods (ensure these are present) ---
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
        if layout:
            self.layout = layout(self, data)
        else:
            self.layout = None

    def add_overlay(self, overlay, data=None):
        name = overlay.__class__.__name__
        if name in self.overlays:
            # print(f"BGUI Info: Overlay '{name}' is already added.") # Optional info
            return
        self.overlays[name] = overlay(self, data)

    def remove_overlay(self, overlay):
        name = overlay.__class__.__name__
        if name in self.overlays:
            self._remove_widget(self.overlays[name])
            del self.overlays[name]
        else:
            # print(f"BGUI Warning: Overlay '{name}' was not found, nothing was removed.") # Optional warning
            pass
            
    def toggle_overlay(self, overlay, data=None):
        if overlay.__class__.__name__ in self.overlays:
            self.remove_overlay(overlay)
        else:
            self.add_overlay(overlay, data)
    # --- End Element Management Methods ---

    def cleanup(self):
        try:
            if hasattr(self, 'logic') and self.logic:
                current_scene = self.logic.getCurrentScene()
                if current_scene and self._render in current_scene.post_draw:
                    current_scene.post_draw.remove(self._render)
        except Exception as e:
            print(f"BGUI Error: Could not remove _render from post_draw during cleanup: {e}")
        self.elements = {}
        self.layout = None
        self.overlays.clear()