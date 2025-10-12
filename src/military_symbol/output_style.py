import os


class OutputStyle:
	"""
	Class for defining an output style for the generated C++ code
	"""

	DEFAULT_STROKE_WIDTH:float = 4.0
	DEFAULT_FILL_STYLE:str = 'light'
	DEFAULT_FONT_FILE:str = os.path.join(os.path.dirname(__file__), 'Roboto.ttf')
	DEFAULT_PADDING:float = 3.0
	DEFAULT_BACKGROUND_WIDTH:float = 16.0

	def __init__(self, use_text_paths:bool = False):
		self.use_text_paths:bool = use_text_paths
		self.text_path_font:str = OutputStyle.DEFAULT_FONT_FILE
		self.use_alternate_icons:bool = False
		self.fill_style:str = OutputStyle.DEFAULT_FILL_STYLE
		self.padding:str = OutputStyle.DEFAULT_PADDING
		self.background_color:str = "#ffffff"
		self.background_width:float = 0
