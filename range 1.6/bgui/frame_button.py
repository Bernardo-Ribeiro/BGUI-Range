from .widget import Widget, BGUI_DEFAULT, BGUI_NO_THEME, BGUI_CENTERED
from .frame import Frame
from .label import Label


class FrameButton(Widget):
    """A clickable frame-based button."""
    theme_section = 'FrameButton'
    theme_options = {
        'Color': None,
        'BorderSize': 0,
        'BorderColor': (0, 0, 0, 1),
        'LabelSubTheme': '',
    }

    def __init__(self, parent, name=None, base_color=None, text="", font=None,
             pt_size=None, aspect=None, size=[1, 1], pos=[0, 0], sub_theme='', options=BGUI_DEFAULT,
             solid_color=False):
        """
        :param parent: the widget's parent
        :param name: the name of the widget
        :param base_color: the color of the button
        :param text: the text to display (this can be changed later via the text property)
        :param font: the font to use
        :param pt_size: the point size of the text to draw (defaults to 30 if None)
        :param aspect: constrain the widget size to a specified aspect ratio
        :param size: a tuple containing the width and height
        :param pos: a tuple containing the x and y position
        :param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
        :param solid_color: bool - if True, the button uses a solid color (no gradient)
        :param options: various other options
        """

        Widget.__init__(self, parent, name, aspect, size, pos, sub_theme, options)

        self.frame = Frame(self, size=[1, 1], pos=[0, 0], options=BGUI_NO_THEME)
        self.label = Label(self, text=text, font=font, pt_size=pt_size, pos=[0, 0],
                           sub_theme=self.theme['LabelSubTheme'], options=BGUI_DEFAULT | BGUI_CENTERED)

        if not base_color:
            base_color = self.theme.get('BGColor1', (0.4, 0.4, 0.4, 1))
            
        self.base_color = base_color
        self.frame.border = self.theme['BorderSize']
        self.frame.border_color = self.theme['BorderColor']

        self.solid_color = solid_color

        self._update_colors()

    def _update_colors(self):
        if self.solid_color:
            # Solid color: use the same color for all four corners
            self.frame.colors = [self.base_color] * 4
        else:
            # Gradient: create light and dark colors for the gradient
            self.light = [
                min(self.base_color[0] + 0.15, 1.0),
                min(self.base_color[1] + 0.15, 1.0),
                min(self.base_color[2] + 0.15, 1.0),
                self.base_color[3]
            ]
            self.dark = [
                max(self.base_color[0] - 0.15, 0.0),
                max(self.base_color[1] - 0.15, 0.0),
                max(self.base_color[2] - 0.15, 0.0),
                self.base_color[3]
            ]
            self.frame.colors = [self.dark, self.dark, self.light, self.light]

    @property
    def text(self):
        return self.label.text

    @text.setter
    def text(self, value):
        self.label.text = value

    @property
    def color(self):
        return self.base_color

    @color.setter
    def color(self, value):
        self.base_color = value
        self._update_colors()

    def _handle_hover(self):
        light = self.light[:] if not self.solid_color else self.base_color[:]
        dark = self.dark[:] if not self.solid_color else self.base_color[:]

        # Lighten button when hovered over.
        if self.solid_color:
            # For solid color, lighten base color a bit
            light = [min(c + 0.1, 1.0) for c in self.base_color[:3]] + [self.base_color[3]]
            dark = light[:]
            self.frame.colors = [dark] * 4
        else:
            for n in range(3):
                light[n] += 0.1
                dark[n] += 0.1
            self.frame.colors = [dark, dark, light, light]

    def _handle_active(self):
        light = self.light[:] if not self.solid_color else self.base_color[:]
        dark = self.dark[:] if not self.solid_color else self.base_color[:]

        # Darken button when clicked.
        if self.solid_color:
            # For solid color, darken base color a bit
            light = [max(c - 0.1, 0.0) for c in self.base_color[:3]] + [self.base_color[3]]
            dark = light[:]
            self.frame.colors = [dark] * 4
        else:
            for n in range(3):
                light[n] -= 0.1
                dark[n] -= 0.1
            self.frame.colors = [light, light, dark, dark]

    def _draw(self):
        """Draw the button"""

        # Draw the children before drawing an additional outline
        Widget._draw(self)

        # Reset the button's color
        self._update_colors()
