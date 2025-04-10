import os
import re
import json
import sys
import glob
sys.path.append(os.path.dirname(__file__))

import drawing_items

def is_valid_hex_key(key:str, required_length:int=-1) -> bool:
	"""
	Returns whether the given key is a valid hex key (string of only hex digits). If required_length is specified,
	determines whether the key is of the required length.
	"""

	if len(key) < 1:
		return False
	if required_length > 0 and len(key) != required_length:
		return False
	for k in key.upper():
		if k not in '0123456789ABCDEF':
			return False
	return True


class Context:
	"""
	Represents a standard identity context
	"""
	def __init__(self):
		self.id_code:str = ""      # The ID code of the context, a 1-digit hexadecimal 
		self.names:list  = []      # The names of the context
		self.base_context:str = "" # The base context this belongs to (reality, exercise, or simulation)
		self.match_name:bool = True
		self.dashed:bool = False

	def __repr__(self):
		return f"Context {self.id_code} [{self.base_context}]: (" + ', '.join([f'\"{f}\"' for f in self.names]) + ")"

	def is_dashed(self) -> bool:
		return False

	@staticmethod
	def from_dict(id_code:str, json:dict):
		if not is_valid_hex_key(id_code, 1):
			print(f'Bad context ID {id_code}')
			return None

		context:Context = Context()
		context.id_code = id_code
		context.names = json['names']
		context.base_context = json.get('base context', id_code)
		return context


class Affiliation:
	"""
	Represents a standard identity affiliation
	"""

	def __init__(self):
		self.id_code:str = ""                 # A 1-digit hexadecimal
		self.names:list = []                  # The names of the affiliation
		self.colors:dict = {}                 # Should contain the keys ['light', 'medium', 'dark', 'unfilled']
		self.dashed:bool = False              # Whether this renders the frame dashed
		self.has_civilian_variant:bool = True # Whether this affiliation allows civilian coloring
		self.frame_id:str = ""                # The affiliation code to use the frames from. If not set this is assumed to be its own base
		self.color_id:str = ""                # The affiliation code to use the colors from. If not set this is assumed to be its own base.
		self.match_name:bool = True

	def __repr__(self):
		ret = f"Affiliation {self.id_code}: (" + ', '.join([f'\"{f}\"' for f in self.names]) + ")"
		if len(self.frame_id) > 0:
			ret += f' [Uses frame {self.frame_id}]'
		if len(self.color_id) > 0:
			ret += f' [Uses color {self.color_id}]'
		if self.has_civilian_variant:
			ret += ' +C'
		return ret

	def is_dashed(self) -> bool:
		return self.dashed

	@staticmethod
	def from_dict(id_code:str, json:dict, schema):
		if not is_valid_hex_key(id_code, 1):
			print(f'Bad affiliation ID {id_code}', file=sys.stderr)
			return None

		affiliation:Affiliation = Affiliation()
		affiliation.id_code = id_code
		affiliation.names = json["names"]
		affiliation.has_civilian_variant = bool(json.get("has civilian variant", True))
		affiliation.dashed = bool(json.get('dashed', False))
		affiliation.frame_id = json.get("frame base", "")
		affiliation.color_id = json.get("color base", "")

		if 'colors' in json:
			if len([c for c in schema.color_modes if c in json['colors']]) != len(schema.color_modes):
				print(f'Not all colors [{",".join(schema.color_modes)}] found for {affiliation.id_code}', file=sys.stderr)
				return None

			affiliation.colors = {color_id: json['colors'][color_id] for color_id in schema.color_modes}

		if not affiliation.frame_id:
			affiliation.frame_id = affiliation.id_code
		if not affiliation.color_id:
			affiliation.color_id = affiliation.id_code

		return affiliation

	def get_base_frame_affiliation(self, schema):
		if not self.frame_id or schema is None:
			return self

		if self.frame_id not in schema.affiliations:
			print(f"No base frame ID {self.frame_id} found for {self}", file=sys.stderr)
			return None

		return schema.affiliations[self.frame_id]

class FrameShape:

	DEFAULT_AMPLIFIER_OFFSETS:dict = {
		'1': {'top': [0, 0], 'bottom': [0, 0]},
		'3': {'top': [0, 0], 'bottom': [0, 0]},
		'4': {'top': [0, 0], 'bottom': [0, 0]},
		'6': {'top': [0, 0], 'bottom': [0, 0]},
	}

	KEY_TRANSLATION:dict = {
		'unknown': '1',
		'friend': '3',
		'neutral': '4',
		'hostile': '6'
	}

	def __init__(self):
		self.id_code:str = ""  # Frame shape
		self.names:list = []   # List of human-readable names
		self.frames:dict = {}  # Dictionary of frames for IDs
		self.amplifier_offsets:dict = self.DEFAULT_AMPLIFIER_OFFSETS

	def __repr__(self):
		return f'Frame shape \"{self.id_code}\" ({len(self.frames[list(self.frames.keys())[0]])} elements)'

	@classmethod
	def from_dict(cls, id_code:str, json:dict, over_dict:dict):
		frame_shape:frame_shape = cls()
		frame_shape.id_code = id_code
		frame_shape.names = json.get('names', [id_code])

		def create_base_frames(json:dict, over_dict:dict, ret:dict = {}) -> dict:
			amplifier_offsets = {}

			if 'frame base' in json:
				base_dim:str = json['frame base']
				if base_dim not in over_dict:
					raise Exception(f"No frame shape \"{base_dim}\" defined")
					return None

				ret, amplifier_offsets = create_base_frames(json=over_dict[base_dim], over_dict=over_dict)


			# Apply amplifier offsets
			if 'amplifier offsets' in json:
				amplifier_offsets = {}
				for key, value in json['amplifier offsets'].items():
					amplifier_offsets[FrameShape.KEY_TRANSLATION[key]] = value

			# Apply base frame
			for frame_key, frame_list in json.get("frames", {}).items():
				ret[FrameShape.KEY_TRANSLATION[frame_key]] = [f for f in frame_list]

			# Apply frame decorators
			for frame_key, frame_list in json.get("decorators", {}).items():
				if frame_key in ret:
					ret[FrameShape.KEY_TRANSLATION[frame_key]] = ret[FrameShape.KEY_TRANSLATION[frame_key]] + frame_list
				else:
					ret[FrameShape.KEY_TRANSLATION[frame_key]] += [f for f in frame_list]

			return ret, amplifier_offsets

		frames, amplifier_offsets = create_base_frames(json=json, over_dict=over_dict)
		
		if frames is None:
			raise Exception(f'No frames in frame set {id_code}')
			return None

		frame_shape.frames = {}
		for affil in frames:
			frame = []
			for item in frames[affil]:
				frame += drawing_items.SymbolElement.parse_from_dict(item=item, full_items={}, affiliations={})
			frame_shape.frames[affil] = frame

		frame_shape.amplifier_offsets = amplifier_offsets
		return frame_shape

class Dimension:
	""" 
	Represents a dimension, which sets the frame type
	"""

	def __init__(self):
		self.id_code:str = ""  # Human readable name for the dimension
		self.names:list = []   # Human readable names
		self.frame_shape:FrameShape = None

	def __repr__(self):
		return f'Dimension \"{self.id_code}\" {self.frame_shape}'

	@classmethod
	def from_dict(cls, id_code:str, json:dict, schema):
		dimension = cls()
		dimension.id_code = id_code
		dimension.names = json.get('names', [id_code])
		frame_shape_code:str = json.get('frame shape')
		if schema is None or frame_shape_code not in schema.frame_shapes:
			raise Exception(f"No frame shape \"{frame_shape_code}\" in schema for dimension {dimension.names[0]}")
			return None
		dimension.frame_shape = schema.frame_shapes[frame_shape_code]

		return dimension


class Status:
	"""
	Represents a status
	"""

	def __init__(self):
		self.id_code:str = ""
		self.names:list = []
		self.dashed:bool = False
		self.icon:list = []
		self.alt_icon:list = []
		self.icon_side:str = 'middle'
		self.alt_icon_side:str = 'middle'
		self.match_name:bool = True

	def __repr__(self):
		return f"Status {self.id_code} ({' / '.join(self.names)})"

		if not is_valid_hex_key(status_id, 1):
			print(f"Bad status {status_id}", file=sys.stderr)
			return None

	def is_dashed(self) -> bool:
		return self.dashed

	@staticmethod
	def from_dict(id_code:str, json:dict, affiliations:dict):
		if not is_valid_hex_key(id_code, 1):
			print(f"Bad status {id_code}", file=sys.stderr)
			return None			

		status:Status = Status()
		status.id_code = id_code
		status.names = json.get('names', [])
		status.dashed = json.get("dashed", False)

		if 'icon' in json:
			status.icon = drawing_items.SymbolElement.parse_list_from_json(json['icon'], full_items={}, affiliations=affiliations)
		if 'alt icon' in json:
			status.alt_icon = drawing_items.SymbolElement.parse_list_from_json(json['alt icon'], full_items={}, affiliations=affiliations)

		status.icon_side = json.get('icon side', 'middle')
		status.alt_icon_side = json.get('alt icon side', 'middle')

		return status

	def icon_cpp(self, schema, output_style, with_bbox=False):
		return 'SymbolLayer{{{}}}'.format(
			', '.join([cmd.cpp(output_style=output_style, schema=schema, with_bbox=with_bbox) for cmd in self.icon]),
		)

	def alt_icon_cpp(self, schema, output_style, with_bbox=False):
		return 'SymbolLayer{{{}}}'.format(
			', '.join([cmd.cpp(output_style=output_style, schema=schema, with_bbox=with_bbox) for cmd in self.alt_icon]),
		)

class HQTFD:
	"""
	Represents a HQTFD code
	"""

	def __init__(self):
		self.id_code:str = "" # 1-digit hexadecimal
		self.names:list = []
		self.dashed:bool = False
		self.headquarters:bool = False
		self.task_force:bool = False
		self.dummy:bool = False
		self.blacklist:list = []
		self.match_name:bool = True

	def __repr__(self) -> str:
		return f"HQTFD {self.id_code} ({self.names[0]})"

	def is_dashed(self) -> bool:
		return self.dashed

	def get_hqtfds(self) -> list:
		return list([item for item in ['headquarters', 'task_force', 'dummy'] if getattr(self, item)])

	def applies_to_symbol_set(self, symbol_set) -> bool:
		return symbol_set is not None and symbol_set.id_code == '10'

	def matches_blacklist(self, name_string):
		test_string = name_string.lower()
		for b in self.blacklist:
			if b.lower() in test_string:
				return True
		return False

	@staticmethod
	def from_dict(id_code:str, json:dict):
		if not is_valid_hex_key(id_code, 1):
			print(f"Bad HQTFD {id_code}", file=sys.stderr)
			return None

		hqtfd:HQTFD = HQTFD()
		hqtfd.id_code = id_code
		hqtfd.names = json.get('names', [])
		if len(hqtfd.names) < 1:
			print(f"No names for amplifier {self.id_code}")
			return None

		hqtfd.dashed = json.get("dashed", False)

		hqtfd.headquarters = 'hqtfd' in json and 'headquarters' in json['hqtfd']
		hqtfd.task_force = 'hqtfd' in json and 'task force' in json['hqtfd']
		hqtfd.dummy = 'hqtfd' in json and 'dummy' in json['hqtfd']

		hqtfd.blacklist = json.get('blacklist', [])

		return hqtfd


class Amplifier:
	"""
	Represents an amplifier
	"""

	def __init__(self):
		self.id_code:str = "" # 1-digit hexadecimal
		self.names:list = [] # Amplifier names
		self.category:str = "" # Category this applies to
		self.applies_to:list = [] # List of dimensions this applies to
		self.icon:list = []
		self.icon_side:str = 'middle' # Should be 'top' or 'bottom' or 'middle'
		self.alt_icon:list = []
		self.alt_icon_side:str = 'middle'
		self.prerun:bool = False
		self.match_name:bool = True

	def applies_to_dimension(self, dimension) -> bool:
		if dimension is None:
			return False

		if not isinstance(dimension, Dimension):
			raise Exception(f"Dimension {dimension} for amplifier {self.names} is not a Dimension object")

		return dimension.id_code in [dim.id_code for dim in self.applies_to]

	def applies_to_symbol_set(self, symbol_set) -> bool:
		if symbol_set is None:
			return False 
		if symbol_set.common:
			return True

		if symbol_set.dimension is None:
			return False
		try:
			return self.applies_to_dimension(symbol_set.dimension)
		except Exception as ex:
			raise Exception(f"Error checking dimension application of [{self}] to symbol set \"{symbol_set}\": {ex}")
			return False

	def applies_to_entity(self, entity) -> bool:
		if entity is None or entity.symbol_set is None:
			return False
		return self.applies_to_symbol_set(entity.symbol_set)

	def get_applicable_symbol_sets(self, schema) -> bool:
		return [ss for ss in schema.symbol_sets.values() if self.applies_to_symbol_set(ss)]

	@staticmethod
	def from_dict(id_code:str, json:dict, schema):
		if not is_valid_hex_key(id_code, 2):
			print(f'Bad ID code \"{id_code}\" for amplifier', file=sys.stderr)
			return None

		amplifier:Amplifier = Amplifier()
		amplifier.id_code = id_code
		amplifier.names = json.get("names", [])
		if len(amplifier.names) < 1:
			print(f"No names for amplifier {self.id_code}", file=sys.stderr)
			return None

		amplifier.category = json.get("category", "")
		amplifier.applies_to = [] 
		for apt in json.get("applies to", []):
			if apt not in schema.dimensions:
				print(f"Bad applies to dimension \"{apt}\" for amplifier {amplifier.id_code}", file=sys.stderr)
				return None

			amplifier.applies_to.append(schema.dimensions[apt])

		amplifier.icon_side = json.get('icon side', 'middle')

		amplifier.icon = []
		if 'icon' in json:
			amplifier.icon = drawing_items.SymbolElement.parse_list_from_json(item=json['icon'], full_items={}, affiliations=schema.get_base_affiliation_dict())

		amplifier.prerun = bool(json.get('prerun', False))

		return amplifier

	def applies_to_any_in_symbol_sets(self, symbol_sets) -> bool:
		for symbol_set in symbol_sets:
			if self.applies_to_symbol_set(symbol_set=symbol_set):
				return True
		return False

	def icon_cpp(self, schema, output_style, with_bbox=False):
		return 'SymbolLayer{{{}}}'.format(
			', '.join([cmd.cpp(output_style=output_style, schema=schema, with_bbox=with_bbox) for cmd in self.icon]),
		)

	def icon_svg(self, symbol, schema):
		return 


"""
A full symbol component (e.g. an entity or modifier)
"""
class SymbolLayer:
	def __init__(self, symbol_set=None):
		self.id_code:str = '' # A six (for entities) or two-digit hex code
		self.names:str = [] # Human-readable names
		self.elements:list = [] # the symbol elements
		self.civilian:bool = False # Whether this entity renders something a civilian item
		self.icon:list = []
		self.alt_icon:list = []
		self.symbol_set = symbol_set
		self.match_name:bool = True
		self.match_weight:float = None
		pass

	def get_match_weight(self) -> float:
		if self.match_weight is None:
			return self.symbol_set.match_weight if self.symbol_set is not None else 0

		return self.match_weight


	def __repr__(self):
		return '{{{}}} {} -> {}'.format(self.id_code, ' / '.join(self.names), self.elements)

	def icon_cpp(self, schema, output_style, with_bbox=False):
		return 'SymbolLayer{{{}}}{}'.format(
			', '.join([cmd.cpp(output_style=output_style, schema=schema, with_bbox=with_bbox) for cmd in self.icon]),
			'.with_civilian_override(true)' if self.civilian else ''
		)

	def alt_icon_cpp(self, schema, output_style, with_bbox=False):
		return 'SymbolLayer{{{}}}{}'.format(
			', '.join([cmd.cpp(output_style=output_style, schema=schema, with_bbox=with_bbox) for cmd in self.alt_icon]),
			'.with_civilian_override(true)' if self.civilian else ''
		)

	def is_in_any_of_symbol_sets(self, symbol_sets):
		return self.symbol_set in symbol_sets

	@classmethod
	def parse_from_dict(cls, id_code:str, json:dict, full_items:dict, schema, symbol_set = None):
		if 'icon' not in json or 'names' not in json:
			print('No keys in {}'.format(uid), file=sys.stderr)
			return None

		# if not is_valid_hex_key(id_code):
		# 	print(f'Invalid hex ID code for symbol layer \"{id_code}\"')
		# 	return None

		symbol_layer = SymbolLayer()
		symbol_layer.id_code = id_code
		symbol_layer.names = json['names'] if 'names' in json else []
		symbol_layer.civilian = json.get('civ', False)

		if 'match weight' in json:
			symbol_layer.match_weight = json['match weight']
		else:
			symbol_layer.match_weight = None

		symbol_layer.icon = drawing_items.SymbolElement.parse_list_from_json(item=json['icon'], full_items=full_items, affiliations=schema.get_base_affiliation_dict())
		symbol_layer.alt_icon = drawing_items.SymbolElement.parse_list_from_json(item=json.get('alt icon', []), full_items=full_items, affiliations=schema.get_base_affiliation_dict())
		symbol_layer.symbol_set = symbol_set
		symbol_layer.match_name = json.get('match name', True)

		return symbol_layer


class Entity(SymbolLayer):
	"""
	Represents an entity
	"""
	def __init__(self):
		super().__init__()

	@classmethod
	def parse_from_dict(cls, id_code:str, json:dict, full_items:dict, schema, symbol_set=None):
		return super().parse_from_dict(id_code=id_code, json=json, full_items=full_items, schema=schema, symbol_set=symbol_set)

class Modifier(SymbolLayer):
	"""
	Represents a modifier
	"""
	def __init__(self):
		super().__init__()


class SymbolSet:
	"""
	Represents a symbol set with entities and modifiers
	"""
	def __init__(self):
		self.id_code:str = '00' # The identifier of the symbol set
		self.names:list = []
		self.dimension = None
		self.common = False

		self.entities:dict = {} # A map of the entities in this symbol set
		self.m1:dict = {}
		self.m2:dict = {}
		self.match_name:bool = True
		self.match_weight:float = 0.0
		
	def __lt__(self, other) -> bool:
		if self.common != other.common:
			return not self.common

		return int(self.id_code) < int(other.id_code)

	def __repr__(self) -> str:
		return f'{self.names[0]} ({self.id_code})'

	@classmethod
	def parse_from_file(cls, filepath:str, schema, verbose:bool=False):
		"""
		Parse a JSON file representing a single symbol set.
		"""

		ITEM_TYPES = [("IC", Entity), ("M1", Modifier), ("M2", Modifier)]

		if not os.path.exists(filepath):
			print(f'No file "{filepath}" in parsing SymbolSet', file=sys.stderr)
			return None

		json_str:str = ''
		with open(filepath, 'r') as json_file:
			json_str = json_file.read()
			json_str = re.sub('#[.]*\n', '', json_str)

		json_dict = json.loads(json_str)

		# Parse icon sets
		ret:dict = {
			item_type: {} for item_type, ItemTypeClass in ITEM_TYPES
		}

		if not ('set' in json_dict):
			print("No set", file=sys.stderr)
			return None

		is_common = json_dict.get('common', False)

		if 'dimension' not in json_dict and not is_common:
			raise Exception(f"No dimension defined in \"{filepath}\"")
			return None

		if not is_common and json_dict['dimension'] not in schema.dimensions:
			raise Exception(f"Dimension \"{json_dict['dimension']}\" not found from \"{filepath}\"")
			return None

		icon_set:str = json_dict['set']
		ret_set = cls()

		ret_set.match_name = json_dict.get('match name', True)

		for item_type, ItemTypeClass in ITEM_TYPES:
			if not (item_type in json_dict):
				continue

			for item_code, item in json_dict[item_type].items():
				# print(f'Loading {json_dict["set"]}:{item_type}:{item_code}')
				if not(('names' in item or 'name' in item) and 'icon' in item):
					print(f'Improper indices for {json_dict["set"]}:{item_type}:{item_code}', file=sys.stderr)
					return None

				new_symbol_layer = ItemTypeClass.parse_from_dict(id_code=item_code, json=item, full_items=json_dict[item_type], schema=schema, symbol_set=ret_set)
				if new_symbol_layer is not None:
					new_symbol_layer.symbol_set = ret_set
					ret[item_type][item_code] = new_symbol_layer
				else:
					print(f'Unable to process item {json_dict["set"]}:{item_type}:{item_code}: {item["names"]}', file=sys.stderr)
					return 

		ret_set.id_code = icon_set
		ret_set.entities = {item: ret['IC'][item] for item in ret['IC'].keys() if item[0] != '.'} # Ignore utility symbols
		ret_set.m1 = ret['M1']
		ret_set.m2 = ret['M2']
		ret_set.match_weight = json_dict.get('match weight', 0.0)
		ret_set.names = json_dict['names'] if 'names' in json_dict else [json_dict['name']]
		ret_set.dimension = schema.dimensions[json_dict['dimension']] if not is_common else False
		ret_set.common = is_common
		return ret_set

class Schema:
	"""
	Represents a full symbol schema
	"""

	def __init__(self):
		## The list of color modes (icon, icon fill, etc.) this has
		self.color_modes:list = []
		## The order in which full frame symbols are expected (for C++)
		self.full_frame_ordering:list = []

		
		## The frame shapes in this schema
		self.frame_shapes:dict = {}
		## The dimensions this schema has
		self.dimensions:dict = {}
		## The contexts this schema has
		self.contexts:dict = {}
		## The affiliations this schema has
		self.affiliations:dict = {}
		## The statuses this schema has
		self.statuses:dict = {}
		## The headquarters/task force/dummy codes
		self.hqtfds:dict = {}
		## Amplifiers
		self.amplifiers:dict = {}
		## A mapping of [symbol set ID : symbol set object]
		self.symbol_sets:dict = {}

		self.templates:list = []

	def add_templates(self, templates:list):
		for temp in templates:
			if temp is not None:
				self.templates.append(temp)

		self.templates = list(set(self.templates))

	def print_constants(self):
		print("Constants set")

		for item_set in ['contexts', 'dimensions', 'color_modes', 'contexts', 'affiliations', 'statuses', 'hqtfds']:
			print(f'\t{item_set.capitalize()}:')
			if isinstance(vars(self)[item_set], list):
				for item in vars(self)[item_set]:
					print(f'\t\t{item}')
			else:
				for item in vars(self)[item_set].values():
					print(f'\t\t{item}')

	def get_base_affiliations(self) -> list:
		ret = []
		for aff in self.affiliations.values():
			if aff.get_base_frame_affiliation(schema=self) == aff:
				ret.append(aff)

		ret = sorted(ret, key=lambda x: x.id_code)
		return ret

	def get_base_affiliation_dict(self) -> list:
		return {ret: ret.get_base_frame_affiliation(schema=self) for ret in self.affiliations.values()}

	def parse_constants_from_file(self, filepath:str, verbose:bool=False):
		"""
		Parses a set of constants from a given filepath
		"""

		if not os.path.exists(filepath):
			print(f'No constant file "{filepath}"', file=sys.stderr)
			return None

		json_str:str = ''
		with open(filepath, 'r') as json_file:
			json_str = json_file.read()
			json_str = re.sub('#[.]*\n', '', json_str)

		json_dict = json.loads(json_str)

		if verbose:
			print(f'Parsing constant file \"{filepath}\"')
			
		# Validate required keys
		REQUIRED_KEYS:list = ['contexts', 'affiliations', 'color modes', 'dimensions', 'full frame ordering']
		for required_key in REQUIRED_KEYS:
			if required_key not in json_dict:
				print(f"Required key \"{required_key}\" not found in constants.json", file=sys.stderr)
				return None

		# Load contexts
		self.contexts = {}
		for context_id, context_dict in json_dict["contexts"].items():
			context = Context.from_dict(context_id, context_dict)
			self.contexts[context_id] = context

		# Load color modes
		self.color_modes = []
		for color_mode in json_dict['color modes']:
			self.color_modes.append(color_mode.lower())

		# Load affiliations
		for aff_id, aff_dict in json_dict["affiliations"].items():
			affiliation = Affiliation.from_dict(aff_id, aff_dict, schema=self)
			self.affiliations[aff_id] = affiliation

		# Load full frame ordering
		self.full_frame_ordering = []
		for item in json_dict["full frame ordering"]:
			base_affiliations = self.get_base_affiliations()
			index = [aff.names[0] for aff in base_affiliations].index(item)
			self.full_frame_ordering.append(base_affiliations[index])

		# Load frame shapes
		for frame_shape_id, frame_shape_dict in json_dict["frame shapes"].items():
			frame_shape = FrameShape.from_dict(id_code=frame_shape_id, json=frame_shape_dict, over_dict=json_dict['frame shapes'])
			if frame_shape is not None:
				self.frame_shapes[frame_shape.id_code] = frame_shape

		# Load dimension
		for dim_id, dim_dict in json_dict["dimensions"].items():
			dimension = Dimension.from_dict(id_code=dim_id, json=dim_dict, schema=self)
			if dimension is not None:
				self.dimensions[dimension.id_code] = dimension

		# Load status
		for status_id, status_dict in json_dict.get("statuses", {}).items():
			status = Status.from_dict(id_code=status_id, json=status_dict, affiliations=self.get_base_affiliation_dict())
			if status is not None:
				self.statuses[status.id_code] = status

		# Load amplifiers
		for amplifier_id, amplifier_dict in json_dict.get("amplifiers", {}).items():
			amplifier = Amplifier.from_dict(amplifier_id, amplifier_dict, schema=self)
			if amplifier is not None:
				self.amplifiers[amplifier.id_code] = amplifier

		for hqtfd_id, hqtfd_dict in json_dict.get("hqtfds", {}).items():
			hqtfd = HQTFD.from_dict(hqtfd_id, hqtfd_dict)
			if hqtfd is not None:
				self.hqtfds[hqtfd.id_code] = hqtfd

		if verbose:
			self.print_constants()
		return True

	def get_flat_entities(self) -> list:
		ret = []
		for symbol_set in self.symbol_sets.values():
			ret += list(symbol_set.entities.values())
		return ret

	@classmethod
	def load_from_directory(cls, directory:str=os.path.join(os.path.dirname(__file__), 'schema'), verbose:bool = False):
		"""
		Parses the schema from a directory of files
		"""

		schema = cls()
		files = glob.glob(os.path.join(directory, '*.json'))

		# Parse the constant file
		constant_files = [f for f in files if os.path.basename(f) == 'constants.json']
		if len(constant_files) < 1:
			print("No constant file \"constants.json\" found", file=sys.stderr)
			return None

		schema.parse_constants_from_file(filepath=constant_files[0])

		# Parse all the JSON files
		symbol_sets = []
		for filename in [f for f in files if os.path.basename(f) != 'constants.json']:
			if verbose:
				print(f'Parsing "{filename}"...')
			symbol_set:SymbolSet = SymbolSet.parse_from_file(filename, schema=schema, verbose=verbose)
			if symbol_set is None:
				print(f"Bad symbol set file \"{filename}\"", file=sys.stderr)
				continue

			schema.symbol_sets[symbol_set.id_code] = symbol_set		
		return schema

	@classmethod
	def load(cls, verbose:bool=False):
		return Schema.load_from_directory(verbose=verbose)