import re
import sys
import os
import copy

sys.path.append(os.path.dirname(__file__))
import font_rendering
from output_style import OutputStyle

"""
Converts a color to the appropriate C++ constant
"""
def color_type_to_cpp(color_type) -> str:
	if color_type is None:
		return 'ColorType::NONE'
	else:
		return f'ColorType::{re.sub(r'[\s-]+', '_', color_type.upper())}'

def svgify_name(text:str) -> str:
	return re.sub('_', '-', text)

"""
Acceptable values for colors in the JSON schema. Right now
yellow is only used for missile icons and chemical spills.
"""
COLORS:list = {
	'icon', 'icon_fill', 'white', 'yellow',
	"mine red", "mine dark green", "mine bright green",
	'mine yellow', 'mine orange',
	'status green', 'status yellow', 'status red', 'status blue'
}

"""
Convert color in the JSON schema to one of our
defined items from the COLORS constant
"""
def convert_color(item):
	if type(item) is bool:
		return 'icon' if item else 'none'
	elif type(item) is str:
		item = item.lower()
		if not(item in COLORS):
			print(f'Unrecognized color "{item}"', file=sys.stderr)
			return None
		return item
	else:
		print(f"Bad color: {item}", file=sys.stderr)
		return None

class BBox():
	def __init__(self, x_min:float=100, y_min:float=100, x_max:float=100, y_max:float=100):
		self.x_min = x_min
		self.y_min = y_min
		self.x_max = x_max
		self.y_max = y_max

	def __repr__(self) -> str:
		return f'BBox({self.x_min}, {self.y_min} to {self.x_max}, {self.y_max})'

	@classmethod 
	def from_list(cls, list_items):
		if len(list_items) != 4:
			raise Exception(f"Can't create BBox from value \"{list_items}\"")
		return BBox(x_min=list_items[0], y_min=list_items[1], x_max=list_items[2], y_max=list_items[3])

	def width(self):
		return abs(self.x_max - self.x_min)

	def height(self):
		return abs(self.y_max - self.y_min)

	def merge(self, other):
		self.x_min = min(self.x_min, other.x_min)
		self.y_min = min(self.y_min, other.y_min)
		self.x_max = max(self.x_max, other.x_max)
		self.y_max = max(self.y_max, other.y_max)

	@classmethod
	def merge_all(cls, box_list):
		boxes = [copy.copy(box) for box in box_list]
		if len(boxes) < 1:
			return None
		ret = boxes[0]
		for box in boxes[1:]:
			ret.merge(box)
		return ret

	def expand(self, padding:float):
		self.x_min -= padding
		self.y_min -= padding
		self.x_max += padding
		self.y_max += padding
		return self


"""
A basic symbol element
"""
class SymbolElement:

	"""
	Base class that contains styling elements
	"""
	class Base:
		def __init__(self, stroke_dashed:bool=False):
			self.fill_color:str = None
			self.stroke_color:str = "icon"
			self.stroke_width:float = OutputStyle.DEFAULT_STROKE_WIDTH
			self.stroke_dashed:bool = stroke_dashed
			self.stroke_style:str = 'round' # ['butt', 'round', 'square']

		def with_stroke(self, stroke_width=None, stroke_color=None, stroke_dashed=None, stroke_style=None):
			if stroke_width is not None:
				self.stroke_width = stroke_width
			if stroke_color is not None:
				self.stroke_color = stroke_color
			if stroke_dashed is not None:
				self.stroke_dashed = stroke_dashed
			if stroke_style is not None:
				self.stroke_style = stroke_style
			return self

		def copy_with_stroke(self, stroke_width=None, stroke_color=None, stroke_dashed=None, stroke_style=None):
			ret = copy.copy(self)
			
			if hasattr(self, 'items'):
				setattr(ret, 'items', [e.copy_with_stroke(stroke_width=stroke_width, stroke_color=stroke_color, stroke_dashed=stroke_dashed, stroke_style=stroke_style) for e in getattr(ret, 'items')])

			return ret.with_stroke(stroke_width=stroke_width, stroke_color=stroke_color, stroke_dashed=stroke_dashed, stroke_style=stroke_style)

		def with_fill(self, fill_color=None):
			self.fill_color = fill_color
			return self

		def copy_with_fill(self, fill_color=None):
			ret = copy.copy(self)
			return ret.with_fill(fill_color=fill_color)

		def base_params(self) -> str:
			return 'fill="{}" stroke="{}"{}{}{}'.format(
				self.fill_color if self.fill_color is not None and self.fill_color != '' else 'none',
				self.stroke_color if self.stroke_color is not None and self.fill_color != '' else 'none',
				f' stroke-width="{self.stroke_width}"' if self.stroke_color is not None and self.stroke_color != '' else '',
				f' stroke-dasharray="8 8"' if self.stroke_dashed and self.stroke_color is not None else '',
				f' stroke-linecap="{self.stroke_style}"' if self.stroke_style is not None else ''
			)

		def element_to_color_type(self, element):
			if type(element) not in [str, bool]:
				raise Exception(f"Non-bool or string fill color {element}")
				return None

			if type(element) == str:
				if element not in COLORS:
					raise Exception(f"Unknown fill color \"{element}\"")
					return None

				if element == 'none':
					return None

				return element

			if type(element) == bool:
				return 'icon' if element else None

			return None


		def parse_basics(self, json) -> None:
			if 'fill' in json:
				self.fill_color = self.element_to_color_type(json['fill'])

			if 'stroke' in json:
				self.stroke_color = self.element_to_color_type(json['stroke'])

			if 'strokewidth' in json:
				self.stroke_width = float(json['strokewidth'])

			if "strokedashed" in json:
				self.stroke_dashed = json['strokedashed']

	"""
	Full frame command
	"""
	class FullFrame(Base):
		def __init__(self, affiliations):
			super().__init__()
			self.elements:dict = {
				affil.id_code: [] for affil in affiliations
			}

		@classmethod
		def parse_from_dict(cls, json:dict, full_items:dict, affiliations:list):
			new_element = cls(affiliations=affiliations.values())
			affiliation_dict = {a.names[0]: a for a in affiliations}
			for type_name, type_entry in json.items():
				if not(type_name in [a.names[0] for a in affiliations]):
					print('Error: Unrecognized FF type "{}"'.format(type_name), file=sys.stderr)
					return None

				if type(type_entry) is not list:
					print(f'Bad entry for full-frame icon {type_name}', file=sys.stderr)
					return None

				for sub_entry in type_entry:
					new_subelements:list = SymbolElement.parse_from_dict(item=sub_entry, full_items=full_items, affiliations=affiliations)
					type_code = affiliation_dict[type_name].id_code
					new_element.elements[type_code].extend(new_subelements)
			new_element.parse_basics(json=json)
			return new_element

		def cpp(self, schema, output_style=OutputStyle(), with_bbox=False):
			ordering = [affiliation.id_code for affiliation in schema.full_frame_ordering]
			elements_ordered = [(item, self.elements[item]) for item in ordering]

			ret = 'DrawCommand::full_frame('

			items = []
			for affiliation in schema.full_frame_ordering:
				items.append('{' + ', '.join([e.cpp(schema=schema, output_style=output_style) for e in self.elements[affiliation.id_code]]) + '}')

			#print(constants.full_frame_ordering)

			ret += ', '.join(items)
			ret += ')'
			return ret

		def get_bbox(self, symbol, output_style=OutputStyle()) -> BBox:
			return BBox.merge_all([element.get_bbox(symbol=symbol, output_style=output_style) for element in self.elements[symbol.affiliation.frame_id]])


		def svg(self, symbol, output_style=OutputStyle()) -> str:
			assert(symbol is not None)
			assert(symbol.is_valid())
			return ''.join([element.svg(symbol=symbol, output_style=output_style) for element in self.elements[symbol.affiliation.frame_id]])

	"""
	Represents a path command
	"""
	class Path(Base):
		def __init__(self, d:str = '', bbox:BBox = BBox(), stroke_dashed:bool=False):
			super().__init__(stroke_dashed=stroke_dashed)
			self.d:str = d # The SVG path
			self.bbox:BBox = bbox
			self.fill_color = None # Default to an unfilled path
			self.stroke_color = "icon" # Default to a filled stroke

		def __repr__(self):
			return f'<path d="{self.d}" {self.base_params()} />'

		@classmethod
		def parse_from_dict(cls, json:dict):
			ret = cls()
			ret.d = json['d']
			if 'bbox' in json:
				bbox_list = list(json['bbox'])
				if len(bbox_list) != 4:
					raise Exception(f'Invalid length of BBOX: {json}')
				ret.bbox = BBox.from_list(bbox_list)
			ret.parse_basics(json=json)
			return ret

		def get_bbox(self, symbol, output_style=OutputStyle()) -> BBox:
			return copy.copy(self.bbox)

		def cpp(self, schema, output_style=OutputStyle(), with_bbox=False) -> str:
			ret:str = 'DrawCommand::path(\"{}\", BoundingBox({}, {}, {}, {}))'.format(self.d, self.bbox.x_min, self.bbox.y_min, self.bbox.x_max, self.bbox.y_max)
			if self.fill_color is not None:
				ret += '.with_fill({})'.format(color_type_to_cpp(self.fill_color))
			if self.stroke_color is None or self.stroke_color != 'icon':
				ret += '.with_stroke({})'.format(color_type_to_cpp(self.stroke_color))
			if self.stroke_width != OutputStyle.DEFAULT_STROKE_WIDTH and self.stroke_color is not None:
				ret += '.with_stroke_width({})'.format(self.stroke_width)
			if self.stroke_dashed:
				ret += '.with_stroke_style(StrokeStyle::DASHED)'

			return ret

		def svg(self, symbol, output_style=OutputStyle()) -> list:
			return self.__repr__()

	"""
	Represents a circle command
	"""
	class Circle(Base):
		def __init__(self):
			super().__init__()
			self.pos:tuple = (100, 100)
			self.radius:float = 1
			self.fill_color = None
			self.stroke_color = "icon"

		def __repr__(self):
			return f'<circle cx="{self.pos[0]}" cy="{self.pos[1]}" r="{self.radius}" {self.base_params()} />'

		def svg(self, symbol, output_style=OutputStyle()) -> list:
			return self.__repr__()

		def get_bbox(self, symbol, output_style=OutputStyle()) -> BBox:
			return BBox(
				x_min = self.pos[0] - self.radius, 
				y_min = self.pos[1] - self.radius,
				x_max = self.pos[0] + self.radius,
				y_max = self.pos[1] + self.radius
			)

		@classmethod
		def parse_from_dict(cls, json:dict):
			ret = cls()
			ret.pos = tuple(json['pos'])
			ret.radius = json['r']
			ret.parse_basics(json=json)
			return ret

		def cpp(self, schema, output_style=OutputStyle(), with_bbox=False) -> str:
			ret:str = 'DrawCommand::circle(Vector2{{{}, {}}}, {})'.format(self.pos[0], self.pos[1], self.radius)
			if self.fill_color is not None:
				ret += '.with_fill({})'.format(color_type_to_cpp(self.fill_color))
			if self.stroke_color is None or self.stroke_color != 'icon':
				ret += '.with_stroke({})'.format(color_type_to_cpp(self.stroke_color))
			if self.stroke_width != OutputStyle.DEFAULT_STROKE_WIDTH and self.stroke_color is not None:
				ret += '.with_stroke_width({})'.format(self.stroke_width)
			if self.stroke_dashed is not None:
				ret += '.with_stroke_style(StrokeStyle::DASHED)'			
			return ret


	"""
	Represents a text command
	"""
	class Text(Base):
		def __init__(self):
			super().__init__()
			self.text:str = '' # The actual rendered text
			self.pos:tuple = (100, 100) # Text origin
			self.font_size:int = 12
			self.font_family:str = 'Arial'
			self.align:str = 'middle' # Can be ['left', 'middle', 'right']
			self.text_type:str = 'auto' # ['auto', 'manual', 'm1', 'm2']
			self.fill_color = 'icon' # Default to filled text
			self.stroke_color = None # Default to no stroke
			# self.text_type = 'manual' # ['normal', 'm1', 'm2', 'manual']

		def __repr__(self):
			return f'<text x="{self.pos[0]}" y="{self.pos[1]}" font-size="{self.font_size}" text-anchor="{self.align}" {self.base_params()}>{self.text}</text>'

		def svg(self, symbol, output_style=OutputStyle()) -> list:
			if output_style.use_text_paths:
				font_face = font_rendering.Font(output_style.text_path_font, size = int(self.font_size))

				paths = font_face.render_text(
					text = self.text, 
					pos = self.pos,
					fontsize = int(self.font_size),
					align = self.align)
				
				ret_path = ' '.join(paths)
				path_el = SymbolElement.Path()
				path_el.fill_color = self.fill_color
				path_el.stroke_color = self.stroke_color
				path_el.d = ret_path
				return path_el.svg(symbol=symbol, output_style=output_style)

			return self.__repr__()

		def get_bbox(self, symbol, output_style=OutputStyle()) -> BBox:
			return BBox()

		@classmethod
		def get_used_pos_and_size(cls, text:str, text_type:str = 'normal'):
			size = 42
			pos = (100, 110)

			if text_type == 'normal':
				size = 42
				y = 115
				if len(text) == 1:
					size = 45
					y = 115
				elif len(text) == 3:
					size = 35
					y = 110
				elif len(text) >= 4:
					size = 32
					y = 110
				pos = (100, y)
			elif text_type == 'm1':
				pos = (100, 77)
				size = 30
				if len(text) == 3:
					size = 25
				elif len(text) >= 4:
					size = 22
			elif text_type == 'm2':
				y = 145
				size = 30
				if len(text) == 3:
					size = 25
					y = 140
				elif len(text) >= 4:
					size = 22
					y = 135
				pos = (100, y)

			return (pos, size)

		@classmethod
		def parse_from_dict(cls, json:dict):
			ret = cls()
			if 'textm1' in json:
				# Parse text
				ret.text = json['textm1']
				ret.pos, ret.font_size = cls.get_used_pos_and_size(text=ret.text, text_type = 'm1')
			elif 'textm2' in json:
				# Parse text
				ret.text = json['textm2']
				ret.pos, ret.font_size = cls.get_used_pos_and_size(text=ret.text, text_type = 'm2')
			else:
				ret.text = json['text']
				ret.pos, ret.font_size = cls.get_used_pos_and_size(text=ret.text, text_type = 'normal')

			if 'pos' in json:
				ret.pos = tuple(json['pos'])
			if "fontsize" in json:
				ret.font_size = float(json["fontsize"])
			elif 'size' in json:
				ret.font_size = float(json["size"])

			ret.parse_basics(json=json)
			return ret

		def cpp(self, schema, output_style=OutputStyle(), with_bbox=False) -> str:

			"""
			If we're supposed to convert text to paths, do so here and
			then return
			"""
			if output_style.use_text_paths:
				font_face = font_rendering.Font(output_style.text_path_font, size = int(self.font_size))

				paths = font_face.render_text(
					text = self.text, 
					pos = self.pos,
					fontsize = int(self.font_size),
					align = self.align)
				
				ret_path = ' '.join(paths)
				path_el = SymbolElement.Path()
				path_el.fill_color = self.fill_color
				path_el.stroke_color = self.stroke_color
				path_el.d = ret_path
				return path_el.cpp(schema=schema)

			# Default text-as-text rendition
			ret:str = ''
			# if self.text_type == 'normal':
			# 	ret = 'DrawCommand::autotext("{}")'.format(self.text)
			# elif self.text_type == 'm1':
			# 	ret = 'DrawCommand::textm1("{}")'.format(self.text)
			# elif self.text_type == 'm2':
			# 	ret = 'DrawCommand::textm2("{}")'.format(self.text)
			# else:
			ret = 'DrawCommand::text("{}", Vector2{{{}, {}}}, {})'.format(self.text, self.pos[0], self.pos[1], self.font_size)

			if self.fill_color is None or self.fill_color != 'icon':
				ret += '.with_fill({})'.format(color_type_to_cpp(self.fill_color))
			if self.stroke_color is not None:
				ret += '.with_stroke({})'.format(color_type_to_cpp(self.stroke_color))
			if self.stroke_width != OutputStyle.DEFAULT_STROKE_WIDTH and self.stroke_color is not None:
				ret += '.with_stroke_width({})'.format(self.stroke_width)
			if self.stroke_dashed is not None:
				ret += '.with_stroke_style(StrokeStyle::DASHED)'				

			return ret

	"""
	Base class for transformation
	"""
	class Transformation(Base):
		def __init__(self, items:list = []):
			super().__init__()
			self.items:list = copy.copy(items)

		def get_children_bbox(self, symbol, output_style=OutputStyle()):
			return BBox.merge_all([item.get_bbox(symbol=symbol, output_style=output_style) for item in self.items])

	"""
	Represents a translation
	"""
	class Translate(Transformation):
		def __init__(self, delta:tuple=(0, 0), items:list = []):
			super().__init__(items=items)
			self.delta:tuple = copy.copy(delta)

		def __repr__(self):
			return '<g transform=\"translate({} {})\">{}</g>'.format(
				self.delta[0],
				self.delta[1],
				' '.join([str(item) for item in self.items])
			)

		def svg(self, symbol, output_style=OutputStyle()) -> list:
			return '<g transform=\"translate({} {})\">{}</g>'.format(
				self.delta[0],
				self.delta[1],
				' '.join([item.svg(symbol=symbol, output_style=output_style) for item in self.items])
			)

		def get_bbox(self, symbol, output_style=OutputStyle()) -> BBox:
			child_box = self.get_children_bbox(symbol=symbol, output_style=output_style)
			child_box.x_min += self.delta[0]
			child_box.x_max += self.delta[0]
			child_box.y_min += self.delta[1]
			child_box.y_max += self.delta[1]
			return child_box

		def cpp(self, schema, output_style=OutputStyle(), with_bbox=False) -> str:
			return 'DrawCommand::translate(Vector2{{{}, {}}}, {})'.format(
				self.delta[0], self.delta[1],
				', '.join([x.cpp(schema=schema, output_style=output_style, with_bbox=with_bbox) for x in self.items])
			)

		@classmethod
		def parse_from_dict(cls, json:dict):
			ret = cls()
			ret.delta = tuple(json['translate'])
			ret.parse_basics(json=json)
			return ret

		def icon_list(self, symbol, output_style=OutputStyle()) -> list:
			return [self]

	"""
	Represents a scaling
	"""
	class Scale(Transformation):
		def __init__(self, scale:float = 1.0):
			super().__init__()
			self.scale:float = scale

		def __repr__(self):
			return '<g transform=\"scale({})\">{}</g>'.format(
				self.scale,
				' '.join([str(item) for item in self.items])
			)

		def svg(self, symbol, output_style=OutputStyle()) -> list:
			return '<g transform=\"translate({} {})\"><g transform=\"scale({})\">{}</g></g>'.format(
				100 - (self.scale*100),
				100 - (self.scale*100),
				self.scale,
				' '.join([item.svg(symbol=symbol, output_style=output_style) for item in self.items])
			)

		@classmethod
		def parse_from_dict(cls, json:dict):
			ret = cls()
			ret.scale = float(json['scale'])
			return ret

		def cpp(self, schema, output_style=OutputStyle(), with_bbox=False):
			return 'DrawCommand::scale({}, {})'.format(
				self.scale,
				', '.join([x.cpp(schema=schema, output_style=output_style, with_bbox=with_bbox) for x in self.items])
			)

		def get_bbox(self, symbol, output_style=OutputStyle()) -> BBox:
			child_box = self.get_children_bbox(symbol=symbol, output_style=output_style)
			child_box.x_min = 100 + ((child_box.x_min - 100) * self.scale)
			child_box.y_min = 100 + ((child_box.y_min - 100) * self.scale)
			child_box.x_max = 100 + ((child_box.x_max - 100) * self.scale)
			child_box.y_max = 100 + ((child_box.y_max - 100) * self.scale)
			return child_box


	@staticmethod
	def parse_from_dict(item:dict, full_items:dict, affiliations:dict) -> list:
		"""
		Parse a specific item from JSON as a symbol element (path, text, etc.)
		`item` is the item to be parsed; `full_items` is the dictionary
		of all items in this set, to allow for aliases for symbols (e.g. supply units
		have a similar full-frame line; aliasing allows the schema to not repeat
		the entire definition for the line every time).
		"""

		new_element = None

		if 'text' in item or 'textm1' in item or 'textm2' in item:
			# Parse text
			new_element = SymbolElement.Text.parse_from_dict(json=item)	
		elif 'd' in item:
			# Parse path
			new_element = SymbolElement.Path.parse_from_dict(json=item)
		elif 'r' in item:
			# Parse circle
			new_element = SymbolElement.Circle.parse_from_dict(json=item)
		elif 'icon' in item:
			item_name:str = item['icon']
			if not isinstance(item_name, str):
				print("Bad icon: {}".format(item_name), file=sys.stderr)
			if item_name in full_items and 'icon' in full_items[item_name]:
				original_icon = full_items[item_name]['icon']
				new_elements = []
				for subitem in original_icon:
					new_el = SymbolElement.parse_from_dict(item=subitem, full_items=full_items, affiliations=affiliations)
					if new_el is None:
						print('Bad subelement')
						return None
					new_elements.extend(new_el)

				if len(new_elements) < 1:
					print("Bad new element in icon {}".format(new_element), file=sys.stderr)
					return None
				return new_elements
			else:
				print('Unrecognized element {}'.format(item_name), file=sys.stderr)
				return None
		elif 'translate' in item:
			new_element = SymbolElement.Translate.parse_from_dict(json=item)
		elif 'scale' in item:
			new_element = SymbolElement.Scale.parse_from_dict(json=item)
		else:
			# Test for full-frame
			for affiliation in affiliations:
				if affiliations[affiliation] == affiliation and affiliation.names[0] not in item:
					print("Invalid full-frame element type {} - affiliation \"{}\" not found in {} // {}".format(item, affiliation, item, affiliations), file=sys.stderr)
					return None

			# This is a valid full-frame icon
			new_element = SymbolElement.FullFrame.parse_from_dict(json=item, full_items=full_items, affiliations=affiliations)
			if new_element is None:
				print(f'Error: Unable to parse full frame icon {item}', file=sys.stderr)
				return None

		# Parse subitems for transformation
		if isinstance(new_element, SymbolElement.Transformation):
			subitems = item['items']
			for subitem in subitems:
				new_subelements:list = SymbolElement.parse_from_dict(item=subitem, full_items=full_items, affiliations=affiliations)
				if new_subelements is None:
					print("Invalid subelements", file=sys.stderr)
					return None
				for sl in new_subelements:
					new_element.items.append(sl)

		# TODO load fill and stroke
		if new_element is None:
			return []

		if new_element.fill_color is not None and new_element.fill_color not in COLORS:
			print("Bad fill color {}".format(new_element.fill_color), file=sys.stderr)
			return None
		if new_element.stroke_color is not None and new_element.stroke_color not in COLORS:
			print("Bad stroke color {}".format(new_element.stroke_color), file=sys.stderr)
			return None

		return [new_element]

	@staticmethod
	def parse_list_from_json(item:list, full_items:dict = {}, affiliations:dict = {}) -> list:
		if type(item) != list:
			raise Exception(f'Type of icon command list \"{item}\" is not a list')
			
		ret = []
		for item_dict in item:
			ret.extend(SymbolElement.parse_from_dict(item=item_dict, full_items=full_items, affiliations=affiliations))
		return ret