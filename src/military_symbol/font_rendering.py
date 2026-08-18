import freetype

"""
Freetype helper functions for rendering text as paths.
Functions are adapted from freetype-py examples.
"""

SCALING:float = 64.0
BASE_HEIGHT:float = 1.0 # 70.0 / 64.0 #64.0 # 90.0

def move_to(a, ctx):
	scale_factor = BASE_HEIGHT # ctx[2] / BASE_HEIGHT
	ctx[0].append("M {},{}".format(
		ctx[3][0] + (ctx[1] + a.x) / SCALING * scale_factor, 
		ctx[3][1] + (-a.y / SCALING) * scale_factor))

def line_to(a, ctx):
	scale_factor = BASE_HEIGHT # ctx[2] / BASE_HEIGHT
	ctx[0].append("L {},{}".format(
		ctx[3][0] + (ctx[1] + a.x) / SCALING * scale_factor, 
		ctx[3][1] + -a.y / SCALING * scale_factor
	))

def conic_to(a, b, ctx):
	scale_factor = BASE_HEIGHT # ctx[2] / BASE_HEIGHT
	ctx[0].append("Q {},{} {},{}".format(
		ctx[3][0] + (ctx[1] + a.x) / SCALING * scale_factor, 
		ctx[3][1] + -a.y / SCALING * scale_factor, 
		ctx[3][0] + (ctx[1] + b.x) / SCALING * scale_factor, 
		ctx[3][1] + -b.y / SCALING * scale_factor
	))

def cubic_to(a, b, c, ctx):
	scale_factor = BASE_HEIGHT # ctx[2] / BASE_HEIGHT
	ctx[0].append("C {},{} {},{} {},{}".format(
		ctx[3][0] + (ctx[1] + a.x) / SCALING * scale_factor, 
		ctx[3][1] + -a.y / SCALING * scale_factor, 
		ctx[3][0] + (ctx[1] + b.x) / SCALING * scale_factor, 
		ctx[3][1] + -b.y / SCALING * scale_factor, 
		ctx[3][0] + (ctx[1] + c.x) / SCALING * scale_factor, 
		ctx[3][1] + -c.y / SCALING * scale_factor
	))

"""
Font object for rendering
"""
class Font(object):
	def __init__(self, font_file, size):
		self.face = freetype.Face(font_file)
		self.face.set_pixel_sizes(0, size)

	# Align is ['middle', 'start', 'end'].
	# Returns a list of SVG paths (but without SVG formatting or XML elements,just
	# the content of the "d" attribute)
	def render_text(self, text, pos = (0, 0), fontsize = 30, align='middle') -> str:		
		# Determine text width
		text_width = 0.0
		for char_index, char in enumerate(text):
			self.face.set_char_size(fontsize * int(SCALING)) # Freetype uses a height of 64 by default
			self.face.load_char(char, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)
			text_width += self.face.glyph.advance.x

		if align == 'start' or align == 'left':
			x_offset:float = 0.0 
		elif align == 'end' or align == 'right':
			x_offset:float = -text_width
		else:
			x_offset:float = -text_width / 2

		paths = []

		for char_index, char in enumerate(text):
			ctx = ([], x_offset, fontsize, pos)
			self.face.set_char_size(fontsize * int(SCALING)) # Freetype uses a height of 64 by default
			self.face.load_char(char, freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP)
			self.face.glyph.outline.decompose(ctx, 
				move_to=move_to, 
				line_to=line_to, 
				conic_to=conic_to, 
				cubic_to=cubic_to)
			paths.append(' '.join(ctx[0]))
			x_offset += self.face.glyph.advance.x

		return paths # ' '.join(paths)