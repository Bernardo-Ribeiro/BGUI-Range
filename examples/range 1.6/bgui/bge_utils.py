from .system import System as BguiSystem  # Imports the base BGUI System
from .widget import Widget, BGUI_MOUSE_NONE, BGUI_MOUSE_CLICK, BGUI_MOUSE_RELEASE, BGUI_MOUSE_ACTIVE
from .text.blf import BlfTextLibrary
from . import key_defs
from Range import logic, events, render
import collections
import bgui


class Layout(Widget):
    """The base layout class to be used with the BGESystem"""

    def __init__(self, sys, data):
        """
        :param sys: The BGUI system
        :param data: User data
        """
        super().__init__(sys, size=[1,1])
        self.data = data

    def update(self):
        """A function that is called by the system to update the widget (subclasses should override this)"""
        pass


class System(BguiSystem):
    """A system intended for use with BGE games.
    It also acts as the UI element manager.
    """

    def __init__(self, theme=None):
        """
        :param theme: the path to a theme directory
        """
        super().__init__(BlfTextLibrary(), theme)

        self.mouse = logic.mouse

        # All layouts are subclasses of Widget, so we can just track one widget
        self.layout = None

        # We can also add 'overlay' layouts
        self.overlays = collections.OrderedDict()

        # Create a dict to map BGE keys to BGUI keys
        self.keymap = {getattr(events, val): getattr(key_defs, val) for val in dir(events) if val.endswith('KEY') or val.startswith('PAD')}

        # Set up the scene callback so we can draw
        logic.getCurrentScene().post_draw.append(self._render)

        # --- NEW ADDITIONS FOR ELEMENT MANAGEMENT ---
        # A base frame for the elements, like in RangeBGUI
        self.main_frame = bgui.Frame(self, "main_frame", border=0)
        self.main_frame.colors = [(0, 0, 0, 0) for _ in range(4)]  # Transparent background

        # Dictionary to store added elements
        self.elements = {}
        # --- END OF NEW ADDITIONS ---

    def load_layout(self, layout, data=None):
        """Load a layout and replace any previously loaded layout

        :param layout: The layout to load (None to unload all layouts)
        :param data: User data passed to the layout constructor
        """
        if self.layout:
            self._remove_widget(self.layout)

        if layout:
            self.layout = layout(self, data)
        else:
            self.layout = None

    def add_overlay(self, overlay, data=None):
        """Add an overlay layout, which sits on top of the currently loaded layout

        :param overlay: The layout to add as an overlay
        :param data: User data passed to the overlay constructor
        """
        name = overlay.__class__.__name__

        if name in self.overlays:
            print("Overlay: %s is already added" % name)
            return

        self.overlays[name] = overlay(self, data)

    def remove_overlay(self, overlay):
        """Remove an overlay layout by name

        :param overlay: The class name of the overlay to remove (same as used when adding it)
        """
        name = overlay.__class__.__name__

        if name in self.overlays:
            self._remove_widget(self.overlays[name])
            del self.overlays[name]
        else:
            print("WARNING: Overlay: %s was not found, nothing was removed" % name)

    def toggle_overlay(self, overlay, data=None):
        """Toggle an overlay (remove if active, otherwise add)

        :param overlay: The class name of the layout to toggle
        :param data: User data passed to the overlay constructor
        """
        if overlay.__class__.__name__ in self.overlays:
            self.remove_overlay(overlay)
        else:
            self.add_overlay(overlay, data)

    def _render(self):
        try:
            # Note: No need to manually set GL_BLEND, GL_LINE_SMOOTH, etc. here,
            # as super().render() from bgui.System already handles most of that.
            # If you have additional GL configs, you may keep them here.
            super().render()
        except:
            # If a rendering error occurs, stop to avoid spamming the console
            import traceback
            traceback.print_exc()
            logic.getCurrentScene().post_draw.remove(self._render)

    def run(self):
        """A high-level method to be run every frame"""

        # The run method also updates elements managed directly by this system.
        # Do not remove self.layout.update() as it handles full layouts.
        # If your elements are added directly to the System, they are updated
        # through the _draw in the superclass, which iterates through children.

        # Handle mouse input
        mouse = self.mouse
        mouse_events = mouse.inputs

        pos = list(mouse.position[:])
        pos[0] *= render.getWindowWidth()
        pos[1] = render.getWindowHeight() - (render.getWindowHeight() * pos[1])

        if mouse_events[events.LEFTMOUSE] == logic.KX_INPUT_JUST_ACTIVATED:
            mouse_state = BGUI_MOUSE_CLICK
        elif mouse_events[events.LEFTMOUSE] == logic.KX_INPUT_JUST_RELEASED:
            mouse_state = BGUI_MOUSE_RELEASE
        elif mouse_events[events.LEFTMOUSE] == logic.KX_INPUT_ACTIVE:
            mouse_state = BGUI_MOUSE_ACTIVE
        else:
            mouse_state = BGUI_MOUSE_NONE

        self.update_mouse(pos, mouse_state)

        # Handle keyboard input
        keyboard = logic.keyboard
        key_events = keyboard.inputs

        is_shifted = key_events[events.LEFTSHIFTKEY] == logic.KX_INPUT_ACTIVE or \
                     key_events[events.RIGHTSHIFTKEY] == logic.KX_INPUT_ACTIVE

        for key, state in keyboard.inputs.items():
            if state == logic.KX_INPUT_JUST_ACTIVATED:
                self.update_keyboard(self.keymap[key], is_shifted)

    # --- ELEMENT MANAGEMENT METHODS TRANSFERRED FROM RangeBGUI ---
    def add_element(self, element_class, name, **kwargs):
        """Adds a BGUI element to the system.

        :param element_class: The BGUI widget class to add (e.g. bgui.FrameButton).
        :param name: A unique name for the element.
        :param kwargs: Additional arguments for the widget constructor.
        :return: The instance of the created widget.
        """
        # Set the default parent as main_frame, or use a custom one
        parent = kwargs.pop('parent', self.main_frame)
        widget = element_class(parent, name, **kwargs)

        self.elements[name] = widget
        return widget

    def get_element(self, name):
        """Retrieves a BGUI element by name.

        :param name: The name of the element.
        :return: The widget instance or None if not found.
        """
        return self.elements.get(name)

    def remove_element(self, name):
        """Removes a BGUI element by name.

        :param name: The name of the element to remove.
        """
        if name in self.elements:
            element = self.elements[name]
            # Remove the widget from its parent
            element.parent.remove_widget(element)
            del self.elements[name]
    # --- END OF ELEMENT MANAGEMENT METHODS ---

    def cleanup(self):
        """Cleans up scene callbacks and elements on shutdown."""
        logic.getCurrentScene().post_draw.remove(self._render)
        # If your System had an input_callback registered to the scene,
        # you would remove it here. But since we use .run(), there's nothing extra to remove.
        self.elements = {}
        self.layout = None
        self.overlays.clear()
        # Do not set self.system = None here, as this is the System instance
        # that other parts of your game might still reference.
