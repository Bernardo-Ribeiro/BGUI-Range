# This file handles differences between BGL and PyOpenGL, and provides various
# utility functions for OpenGL

try:
	from bgl import *
	USING_BGL = True
except ImportError:
	from OpenGL.GL import *
	from OpenGL.GLU import *
	from PyQt4 import QtOpenGL  # Make sure we have PyQt4 available, otherwise PyOpenGL is too slow
	USING_BGL = False


if USING_BGL:
	# The following line is to make ReadTheDocs happy
	from bgl import glGenTextures, glDeleteTextures, glGetIntegerv, GL_NEAREST, GL_LINEAR

	_glGenTextures = glGenTextures
	def glGenTextures(n, textures=None):
		id_buf = Buffer(GL_INT, n)
		_glGenTextures(n, id_buf)

		if textures:
			textures.extend(id_buf.to_list())

		return id_buf.to_list()[0] if n == 1 else id_buf.to_list()


	_glDeleteTextures = glDeleteTextures
	def glDeleteTextures(textures):
		n = len(textures)
		id_buf = Buffer(GL_INT, n, textures)
		_glDeleteTextures(n, id_buf)


	_glGetIntegerv = glGetIntegerv
	def glGetIntegerv(pname):
		# Only used for GL_VIEWPORT right now, so assume we want a size 4 Buffer
		buf = Buffer(GL_INT, 4)
		_glGetIntegerv(pname, buf)
		return buf.to_list()

else:
	# The following line is to make ReadTheDocs happy
	from OpenGL.GL import glTexImage2D, GL_NEAREST, GL_LINEAR

def draw_quad(position, size, color):
	"""Desenha um quadrado preenchido com a cor especificada"""
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	
	glBegin(GL_QUADS)
	glColor4f(*color)
	glVertex2f(position[0], position[1])
	glVertex2f(position[0] + size[0], position[1])
	glVertex2f(position[0] + size[0], position[1] + size[1])
	glVertex2f(position[0], position[1] + size[1])
	glEnd()
	
	glDisable(GL_BLEND)

def draw_texture(position, size, texture_id, color=(1, 1, 1, 1)):
	"""Desenha uma textura na posição e tamanho especificados"""
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	glEnable(GL_TEXTURE_2D)
	
	glBindTexture(GL_TEXTURE_2D, texture_id)
	glColor4f(*color)
	
	glBegin(GL_QUADS)
	glTexCoord2f(0, 0)
	glVertex2f(position[0], position[1])
	glTexCoord2f(1, 0)
	glVertex2f(position[0] + size[0], position[1])
	glTexCoord2f(1, 1)
	glVertex2f(position[0] + size[0], position[1] + size[1])
	glTexCoord2f(0, 1)
	glVertex2f(position[0], position[1] + size[1])
	glEnd()
	
	glDisable(GL_TEXTURE_2D)
	glDisable(GL_BLEND)

