from .widget import Widget
from .theme import Theme
from .gl_utils import draw_quad, draw_texture
from .bge_utils import get_screen_info
from Range import *

class Slider(Widget):
    def __init__(self, parent, name="", value=0.0, min_value=0.0, max_value=1.0, size=[100, 20], pos=[0, 0], sub_theme='', options=[]):
        super().__init__(parent, name, size, pos, sub_theme, options)
        
        self._value = max(min_value, min(max_value, value))
        self._min_value = min_value
        self._max_value = max_value
        self._dragging = False
        
        # Dimensões do slider
        self._slider_width = 10
        self._slider_height = size[1]
        
        # Texturas
        self._slider_texture = None
        self._track_texture = None
        
        # Callback para mudança de valor
        self._on_value_change = None
        
        # Estado do mouse
        self._mouse_over = False
        
    @property
    def value(self):
        return self._value
        
    @value.setter
    def value(self, value):
        old_value = self._value
        self._value = max(self._min_value, min(self._max_value, value))
        if self._value != old_value and self._on_value_change:
            self._on_value_change(self._value)
            
    def set_on_value_change(self, callback):
        self._on_value_change = callback
        
    def _draw(self):
        # Desenha a trilha do slider
        track_color = self.theme['slider']['track_color']
        if self._mouse_over:
            track_color = self.theme['slider']['hover_color']
        if self._dragging:
            track_color = self.theme['slider']['active_color']
            
        draw_quad(self.gl_position, self.size, track_color)
        
        # Calcula a posição do slider
        slider_pos = self.gl_position.copy()
        slider_pos[0] += (self._value - self._min_value) / (self._max_value - self._min_value) * (self.size[0] - self._slider_width)
        
        # Desenha o slider
        slider_color = self.theme['slider']['slider_color']
        if self._mouse_over:
            slider_color = self.theme['slider']['hover_color']
        if self._dragging:
            slider_color = self.theme['slider']['active_color']
            
        draw_quad(slider_pos, [self._slider_width, self._slider_height], slider_color)
        
    def _handle_mouse(self, event):
        mouse_pos = logic.mouse.position
        
        # Atualiza estado do mouse over
        self._mouse_over = self._is_inside(mouse_pos)
        
        if event == events.LEFTMOUSE:
            if self._mouse_over:
                self._dragging = True
                self._update_value_from_mouse(mouse_pos)
                return True
                
        elif event == events.LEFTMOUSEUP:
            if self._dragging:
                self._dragging = False
                return True
                
        elif event == events.MOUSEMOVE and self._dragging:
            self._update_value_from_mouse(mouse_pos)
            return True
            
        return False
        
    def _update_value_from_mouse(self, mouse_pos):
        # Converte a posição do mouse para um valor entre min_value e max_value
        relative_x = (mouse_pos[0] - self.gl_position[0]) / self.size[0]
        relative_x = max(0.0, min(1.0, relative_x))
        self.value = self._min_value + relative_x * (self._max_value - self._min_value)
        
    def _is_inside(self, pos):
        return (self.gl_position[0] <= pos[0] <= self.gl_position[0] + self.size[0] and
                self.gl_position[1] <= pos[1] <= self.gl_position[1] + self.size[1]) 