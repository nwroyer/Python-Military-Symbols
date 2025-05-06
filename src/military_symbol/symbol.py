from schema import *
from output_style import OutputStyle
import re
import os
from drawing_items import BBox
import math

class Symbol():
	def __init__(self, schema=None):
		self.schema = schema
		self.context:Context = None
		self.affiliation:Affiliation = None
		self.status:Status = None
		self.hqtfd:HQTFD = None
		self.amplifier:Amplifier = None
		self.symbol_set:SymbolSet = None
		self.entity:Entity = None
		self.modifier_1:Modifier = None
		self.modifier_2:Modifier = None

		self.frame_shape_override = None

	def is_valid(self) -> bool:
		return self.schema is not None

	def is_headquarters(self) -> bool:
		return self.hqtfd is not None and self.hqtfd.headquarters

	def is_task_force(self) -> bool:
		return self.hqtfd is not None and self.hqtfd.task_force

	def is_dummy(self) -> bool:
		return self.hqtfd is not None and self.hqtfd.dummy

	def is_frame_dashed(self) -> bool:
		return (self.affiliation is not None and self.affiliation.is_dashed()) or (self.status is not None and self.status.is_dashed()) or (self.context is not None and self.context.is_dashed())

	def __repr__(self):
		ret = ', '.join([
			'Symbol',
			f'context = {self.context.names[0]}',
			f'affiliation = {self.affiliation.names[0] if self.affiliation else 'none'} [{self.affiliation.id_code if self.affiliation else 'none'}]',
			f'symbol set = {self.symbol_set.names[0] if self.symbol_set else 'none'} [{self.symbol_set.id_code if self.symbol_set else 'none'}]',
			
			f'dimension = {self.symbol_set.dimension.names[0] if self.symbol_set and self.symbol_set.dimension else 'none'} [{self.symbol_set.dimension.id_code if self.symbol_set and self.symbol_set.dimension else 'none'}]',
			f'frame shape = {self.symbol_set.dimension.frame_shape.names[0] if self.symbol_set else 'none'} [{self.symbol_set.dimension.frame_shape.id_code if self.symbol_set else 'none'}]',
			f'entity = {self.entity.names[0]} [{self.entity.id_code}]' if self.entity is not None else 'entity = none',
		] 
			+ ([] if self.frame_shape_override is None else [f'frame shape override = {self.frame_shape_override.names[0]}'])
			+ ([] if self.modifier_1 is None else [f'm1 = {self.modifier_1.names[0]}'])
			+ ([] if self.modifier_2 is None else [f'm2 = {self.modifier_2.names[0]}'])
			+ ([f'status = {self.status.names[0]} [{self.status.id_code}]'] if self.status is not None else [])
			+ ([f'HQTFD = {self.hqtfd.names[0]} [{self.hqtfd.id_code}]'] if self.hqtfd is not None else [])
			+ ([f'amplifier = {self.amplifier.names[0]} [{self.amplifier.id_code}]'] if self.amplifier is not None else [])
		)
		return ret

	def to_sidc(self) -> str:
		return f'13{self.context.id_code if self.context else "0"}{self.affiliation.id_code if self.affiliation else '0'}' + \
			f'{self.status.id_code if self.status else '0'}' + \
			f'{self.hqtfd.id_code if self.hqtfd else '0'}' + \
			f'{self.amplifier.id_code if self.amplifier else '00'}' + \
			f'{self.symbol_set.id_code if self.symbol_set else '00'}' + \
			f'{self.entity.id_code if self.entity else '000000'}' + \
			f'{self.modifier_1.id_code if self.modifier_1 else '00'}' + \
			f'{self.modifier_2.id_code if self.modifier_2 else '00'}' + \
			f'{self.modifier_1.id_code[0] if self.modifier_1 and len(self.modifier_1.id_code) > 2 else '0'}' + \
			f'{self.modifier_2.id_code[0] if self.modifier_2 and len(self.modifier_2.id_code) > 2 else '0'}' + \
			'0000000'

	def get_sidc(self) -> str:
		return self.to_sidc()

	def get_name(self) -> str:
		return self.__repr__()

	@classmethod
	def from_sidc(cls, sidc:str, schema:Schema):
		sidc = re.sub(r'\s+', '', sidc)

		if len(sidc) < 20:
			raise Exception(f'SIDC "{sidc}" must be at least 20 characters')
		if schema is None:
			raise Exception('No schema supplied')

		ret = cls()
		ret.schema = schema
		
		# Digits 0,1 are version
		
		# Digit 2 is the context
		ret.context = schema.contexts.get(sidc[2], schema.contexts['0'])

		# Digit 3 is the affiliation
		ret.affiliation = schema.affiliations.get(sidc[3], schema.affiliations['0'])

		# Digit 6 is the status
		ret.status = schema.statuses.get(sidc[6], schema.statuses['0'])

		# Digit 7 is the HQTFD code
		ret.hqtfd = schema.hqtfds.get(sidc[7], schema.hqtfds['0'])

		# Digits 8-9 are the amplifier
		ret.amplifier = schema.amplifiers.get(sidc[8:10], schema.amplifiers['00'])

		# Digits 4-5 are the symbol set
		ret.symbol_set = schema.symbol_sets.get(sidc[4:6], None)
		if ret.symbol_set is None:
			print(f'Unknown symbol set \"{sidc[4:6]}\"', file=sys.stderr)
			return ret

		# Digits 10-15 are the 
		entity_code:str = sidc[10:16]
		fallbacks:list = [entity_code, f'{entity_code[0:4]}00', f'{entity_code[0:2]}0000']
		for code_index, code in enumerate(fallbacks):
			if code in ret.symbol_set.entities:
				ret.entity = ret.symbol_set.entities[code]
				break

			print(f'Entity "{entity_code}" not found in symbol set "{ret.symbol_set.names[0]}"; falling back to {fallbacks[code_index + 1] if code_index < 2 else '000000'}', file=sys.stderr)			

		mod_1_prefix, mod_2_prefix = '', ''
		mod_1_set:SymbolSet = ret.symbol_set
		mod_2_set:SymbolSet = ret.symbol_set

		if len(sidc) >= 22:
			if bool(int(sidc[20])): # Digit 20 indicates the sector 1 modifier is common
				mod_1_set = schema.symbol_sets.get('C', mod_1_set)
				mod_1_prefix += sidc[20]
			if bool(int(sidc[21])): # Digit 21 indicates the sector 2 modifier is common
				mod_2_set = schema.symbol_sets.get('C', mod_2_set)
				mod_2_prefix += sidc[21]

		if len(sidc) >= 23:
			ret.frame_shape_override = schema.frame_shapes.get(sidc[22], None) # Digit 22 is the frame shape override
			if ret.frame_shape_override is not None and ret.frame_shape_override.id_code == '0':
				ret.frame_shape_override = None

		ret.modifier_1 = mod_1_set.m1.get(mod_1_prefix + sidc[16:18], None)
		ret.modifier_2 = mod_2_set.m2.get(mod_2_prefix + sidc[18:20], None)

		return ret

	def get_svg(self, output_style=OutputStyle()) -> str:
		if not self.is_valid():
			return None

		# Assemble elements
		elements:list = []
		ret_bbox = BBox()

		# Add frame base
		frame_to_use = self.frame_shape_override if self.frame_shape_override is not None else self.symbol_set.dimension.frame_shape

		frame_commands = []

		SVG_NAMESPACE:str = "http://www.w3.org/2000/svg";

		if self.is_frame_dashed():
			base_frame = frame_to_use.frames[self.affiliation.frame_id]
			if output_style.fill_style != 'unfilled':
				elements += [base_frame[0].copy_with_stroke(stroke_color='white').svg(symbol=self, output_style=output_style)]

			elements += [base_frame[0].copy_with_stroke(stroke_color='icon', stroke_dashed=True).with_fill(fill_color=None).svg(symbol=self, output_style=output_style)]

			elements += [
				e.svg(symbol=self, output_style=output_style) for e in base_frame[1:]
			]
		else:
			if output_style.fill_style != 'unfilled':
				elements += [e.svg(symbol=self, output_style=output_style) for e in frame_to_use.frames[self.affiliation.frame_id]]
			else:
				base_frame = frame_to_use.frames[self.affiliation.frame_id]
				elements += [base_frame[0].copy_with_fill(fill_color=None).svg(symbol=self, output_style=output_style)]
				elements += [e.svg(symbol=self, output_style=output_style) for e in base_frame[1:]]
		
		frame_commands += [c for c in frame_to_use.frames[self.affiliation.frame_id]]

		frame_bbox = BBox.merge_all([e.get_bbox(symbol=self, output_style=output_style) for e in frame_to_use.frames[self.affiliation.frame_id]])
		ret_bbox.merge(frame_bbox)

		# Handle headquarters
		if self.is_headquarters():
			cmd = drawing_items.SymbolElement.Path(d=f"m {ret_bbox.x_min},100 l 0,100", bbox=BBox(ret_bbox.x_min, 100, ret_bbox.x_min, 200))
			frame_commands += [cmd]
			elements += [cmd.svg(symbol=self, output_style=output_style)]
			ret_bbox.merge(cmd.get_bbox(symbol=self, output_style=output_style))

		# Add amplfiiers
		amplifier_bbox = BBox()
		has_amps:bool = self.amplifier is not None and self.amplifier.icon and self.amplifier.icon_side == 'top'
		if self.amplifier is not None and self.amplifier.icon:
			if self.amplifier.icon_side != 'middle':
				amplifier_offset = tuple(frame_to_use.amplifier_offsets[self.affiliation.frame_id][self.amplifier.icon_side])

				command = drawing_items.SymbolElement.Translate(delta=amplifier_offset, items=self.amplifier.icon)
				frame_commands += [command]
				elements += [command.svg(symbol=self, output_style=output_style)]
				ret_bbox.merge(command.get_bbox(symbol=self, output_style=output_style))
				amplifier_bbox.merge(command.get_bbox(symbol=self, output_style=output_style))
			else:
				elements += [e.svg(symbol=self, output_style=output_style) for e in self.amplifier.icon]
				frame_commands += [e for e in self.amplifier.icon]
				amp_bbox = BBox.merge_all([e.get_bbox(symbol=self, output_style=output_style) for e in self.amplifier.icon])
				ret_bbox.merge(amp_bbox)
				amplifier_bbox.merge(amp_bbox)

		if self.is_task_force():
			pass
			tf_width = 100 if not has_amps else (amplifier_bbox.width() + 20)

			bounds = BBox(
				x_min = 100 - (tf_width / 2), 
				x_max = 100 + (tf_width / 2), 
				y_min = amplifier_bbox.y_min - (5 if has_amps else 20), 
				y_max = frame_bbox.y_min)

			bounds.y_min = bounds.y_min - 5
			bounds.y_max = frame_bbox.y_min

			cmd = drawing_items.SymbolElement.Path(d=f"M {bounds.x_min},{bounds.y_max} l 0,-{bounds.height()} l {tf_width},0 l 0,{bounds.height()}", bbox=bounds)
			frame_commands += [cmd]
			ret_bbox.merge(bounds)
			amplifier_bbox.merge(bounds)
			elements += [cmd.svg(symbol=self, output_style=output_style)]
			
		if self.is_dummy():
			half_width = frame_bbox.width() * 0.5
			height = round(half_width * math.tan(math.pi / 4), 6)
			origin = (frame_bbox.x_min, amplifier_bbox.y_min - 3 if has_amps else frame_bbox.y_min - 3)
			cmd = drawing_items.SymbolElement.Path(d=f"M {origin[0]},{origin[1]} l {half_width},-{height} L {frame_bbox.x_max},{origin[1]}", 
				bbox=BBox(x_min=origin[0], y_min=origin[1] - height, x_max = origin[1] + (2*half_width), y_max = origin[1]),
				stroke_dashed=True)

			frame_commands += [cmd]
			ret_bbox.merge(cmd.get_bbox(symbol=self, output_style=output_style))
			amplifier_bbox.merge(cmd.get_bbox(symbol=self, output_style=output_style))
			elements += [cmd.svg(symbol=self, output_style=output_style)]

		# Add status
		if self.status and self.status.icon:
			use_alt:bool = output_style.use_alternate_icons and self.status.alt_icon
			icon_to_use = self.status.alt_icon if use_alt else self.status.icon
			icon_side = self.status.alt_icon_side if use_alt else self.status.icon_side

			if icon_to_use:
				if icon_side != 'middle':
					amplifier_offset = tuple(frame_to_use.amplifier_offsets[self.affiliation.frame_id][icon_side])
					command = drawing_items.SymbolElement.Translate(delta=amplifier_offset, items=icon_to_use)
					frame_commands += [command]
					elements += [command.svg(symbol=self, output_style=output_style)]
					ret_bbox.merge(command.get_bbox(symbol=self, output_style=output_style))
				else:
					elements += [e.svg(symbol=self, output_style=output_style) for e in icon_to_use]
					frame_commands += [e for e in icon_to_use]
					status_bbox = BBox.merge_all([e.get_bbox(symbol=self, output_style=output_style) for e in icon_to_use])
					ret_bbox.merge(status_bbox)

		if output_style.background_width > 0.01:
			bg_color = output_style.background_color
			if not bg_color.startswith('#'):
				bg_color = f'#{bg_color}'

			elements = [cmd.copy_with_stroke(stroke_color=f'{bg_color}', stroke_width=output_style.background_width*2, stroke_style='round').svg(symbol=self, output_style=output_style) for cmd in frame_commands] + elements

		# Handle entities and modifiers
		for entmod in [self.entity, self.modifier_1, self.modifier_2]:
			if not entmod:
				continue
			icon_to_use = entmod.alt_icon if output_style.use_alternate_icons and entmod.alt_icon else entmod.icon
			#print(f'{type(entmod).__name__} {entmod.names[0]}: {entmod.icon}')
			elements += [e.svg(symbol=self, output_style=output_style) for e in icon_to_use]

		# Create the SVGs
		ret_bbox.expand(padding=output_style.padding)

		if output_style.background_width > 0.01:
			ret_bbox.expand(padding=output_style.background_width)

		svg_content = f'<svg xmlns="{SVG_NAMESPACE}" width="{ret_bbox.width()}" height="{ret_bbox.height()}" ' + \
			f'viewBox="{ret_bbox.x_min} {ret_bbox.y_min} {ret_bbox.width()} {ret_bbox.height()}">\n' + \
			('\n'.join(elements) if elements is not None else '') + \
			'\n</svg>'

		# Determine proper coloration
		icon_fill_color = self.schema.affiliations[self.affiliation.color_id].colors.get(output_style.fill_style, OutputStyle.DEFAULT_FILL_STYLE)

		COLOR_DICT = {
			'icon': (0, 0, 0) if output_style.fill_style != 'unfilled' else icon_fill_color,
			'icon_fill': icon_fill_color if output_style.fill_style != 'unfilled' else None,
			'status yellow': (255, 255, 0),
			'status red': (255, 0, 0),
			'status blue': (0, 180, 240),
			'status green': (0, 255, 0),
			'mine yellow': (255, 255, 0),
			'mine orange': (255, 141, 42),
			'mine bright green': (0, 255, 0),
			'mine dark green': (0, 130, 24),
			'mine dark green': (0, 130, 24),
			'mine red': (255, 0, 0),
			'white': (255, 255, 255) if output_style.fill_style != 'unfilled' else None,
			'yellow': (255, 255, 128)
		}

		for color_type in ['stroke', 'fill']:
			for key, replacement in COLOR_DICT.items():
				svg_content = re.sub(f'{color_type}="{key}"', f'{color_type}="rgb({replacement[0]}, {replacement[1]}, {replacement[2]})"' if replacement is not None else 'none', svg_content)
			pass

		return svg_content


if __name__ == '__main__':
	TEST_SIDCS:list = [
		'130310001411060000600000000000',
		'130310000011092000600000000000',
		'130560000011020008101100000000',
		'130310021316040007891000000000',
		'130515003211010300000000000000',
		'130310071213010300000000000000',
		'130310072313010300000000000000',
		'130320400011030007201100000000'
	]

	schema = Schema.load_from_directory()

	test_dir = os.path.join(os.path.dirname(__file__), '..', 'test')
	os.makedirs(test_dir, exist_ok=True)

	output_style=OutputStyle()
	output_style.use_text_paths = True
	output_style.use_alternate_icons = True

	for sidc_raw in TEST_SIDCS:
		for affil in ['1', '3', '4', '5', '6']:
			sidc = sidc_raw[:3] + affil + sidc_raw[4:]
			symbol = Symbol.from_sidc(sidc=sidc, schema=schema)
			# print(symbol)
			svg = symbol.get_svg(output_style=output_style)
			with open(os.path.join(test_dir, f'{sidc}.svg'), 'w') as out_file:
				out_file.write(svg)
			#print(svg)
		


