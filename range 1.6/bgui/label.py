from .gl_utils import *
from .widget import Widget, BGUI_DEFAULT, BGUI_NO_NORMALIZE


class Label(Widget):
	"""Widget for displaying text"""
	theme_section = 'Label'
	theme_options = {
				'Font': '',
				'Color': (1, 1, 1, 1),
				'OutlineColor': (0, 0, 0, 1),
				'OutlineSize': 0,
				'OutlineSmoothing': False,
				'Size': 20,
				'CenterText': True,
				}

	def __init__(self, parent, name=None, text="", font=None, pt_size=None, color=None,
				outline_color=None, outline_size=None, outline_smoothing=None, pos=[0, 0], sub_theme='', options=BGUI_DEFAULT, center_text=None):
		"""
		:param parent: the widget's parent
		:param name: the name of the widget
		:param text: the text to display (this can be changed later via the text property)
		:param font: the font to use
		:param pt_size: the point size of the text to draw (defaults to 30 if None)
		:param color: the color to use when rendering the font
		:param pos: a tuple containing the x and y position (normalized 0-1 if BGUI_NORMALIZE is set, pixels otherwise)
		:param sub_theme: name of a sub_theme defined in the theme file (similar to CSS classes)
		:param options: various other options
		:param center_text: whether to center the text at the given position (defaults to theme setting)

		"""
		is_normalized = all(0 <= p <= 1 for p in pos)
		if not is_normalized:
			options &= ~BGUI_DEFAULT
			options |= BGUI_NO_NORMALIZE

		Widget.__init__(self, parent, name, None, [0, 0], pos, sub_theme, options)

		if font:
			self.fontid = self.system.textlib.load(font)
		else:
			font = self.theme['Font']
			self.fontid = self.system.textlib.load(font) if font else 0

		if pt_size:
			self.pt_size = pt_size
		else:
			self.pt_size = self.theme['Size']

		if color:
			self.color = color
		else:
			self.color = self.theme['Color']

		if outline_color:
			self.outline_color = outline_color
		else:
			self.outline_color = self.theme['OutlineColor']

		if outline_size is not None:
			self.outline_size = outline_size
		else:
			self.outline_size = self.theme['OutlineSize']
		self.outline_size = int(self.outline_size)

		if outline_smoothing is not None:
			self.outline_smoothing = outline_smoothing
		else:
			self.outline_smoothing = self.theme['OutlineSmoothing']
			
		if center_text is not None:
			self.center_text = center_text
		else:
			self.center_text = self.theme['CenterText']

		self.text = text

	@property
	def text(self):
		"""The text to display"""
		return self._text

	@text.setter
	def text(self, value):
		
		self.system.textlib.size(self.fontid, self.pt_size, 72)
		
		width = self.system.textlib.dimensions(self.fontid, value)[0]
		height = self.system.textlib.dimensions(self.fontid, 'Mj')[0]
		
		self._original_size = [width, height]
		
		if not (self.options & BGUI_NO_NORMALIZE):
			size = [width / self.parent.size[0], height / self.parent.size[1]]
		else:
			size = [width, height]

		base_pos = list(self._base_pos)
		if not (self.options & BGUI_NO_NORMALIZE) and (base_pos[0] > 1 or base_pos[1] > 1):
			base_pos = [base_pos[0] / self.parent.size[0], base_pos[1] / self.parent.size[1]]

		self._update_position(size, base_pos)

		self._text = value

	@property
	def pt_size(self):
		"""The point size of the label's font"""
		return self._pt_size

	@pt_size.setter
	def pt_size(self, value):
		if self.system.normalize_text:
			self._pt_size = int(value * (self.system.size[1] / 1000))
		else:
			self._pt_size = value

	def _draw_text(self, x, y):
		lines = [i for i in self._text.split('\n')]
		for i, txt in enumerate(lines):
			
			if self.center_text:
				if not (self.options & BGUI_NO_NORMALIZE):
					if x > 1:
						x = x / self.parent.size[0]
					
					half_width_norm = (self._original_size[0] / 2) / self.parent.size[0]
					
					x_centered_norm = x - half_width_norm
					
					adjusted_x = x_centered_norm * self.parent.size[0]
				else:
					half_width = self._original_size[0] / 2
					adjusted_x = x - half_width
			else:
				adjusted_x = x
			
			final_y = y - (self.size[1] * i)
			
			self.system.textlib.position(self.fontid, adjusted_x, final_y, 0)
			self.system.textlib.draw(self.fontid, txt.replace('\t', '    '))

	def _draw(self):
		"""Display the text"""

		self.system.textlib.size(self.fontid, self.pt_size, 72)

		if self.outline_size:
			glColor4f(*self.outline_color)
			if self.outline_smoothing:
				steps = range(-self.outline_size, self.outline_size + 1)
			else:
				steps = (-self.outline_size, 0, self.outline_size)

			for x in steps:
				for y in steps:
					self._draw_text(self.position[0] + x, self.position[1] + y)

		glColor4f(*self.color)
		self._draw_text(*self.position)

		Widget._draw(self)

