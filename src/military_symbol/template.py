import os
import re
import json
import sys
import yaml
import copy

sys.path.append(os.path.dirname(__file__))
from schema import Schema
from symbol import Symbol
import name_to_sidc

class Template():
	"""
	A template for a symbol, indicating a flexible alias for a symbol
	"""

	ITEMS:list = {
		'context': (2, 1, 'contexts'), # Start, length 
		'affiliation': (3, 1, 'affiliations'),
		'symbol_set': (4, 2, 'symbol_sets'),
		'status': (6, 1, 'statuses'),
		'hqtfd': (7, 1, 'hqtfds'), 
		'amplifier': (8, 2, 'amplifiers'),

		'entity': (10, 6, 'entities'),
		'modifier_1': (16, 2, 'm1'),
		'modifier_2': (18, 2, 'm2')
	}

	SYMBOL_SET_ITEMS:list = [
		'entity', 'modifier_1', 'modifier_2'
	]

	def __init__(self):
		self.names:list = [] # A list of names for the template
		self.sidc:str = ''   # The original SIDC for the template

		for item in Template.ITEMS:
			setattr(self, f'{item}_is_flexible', True)

	def get_names(self) -> list:
		return self.names

	@classmethod 
	def load_from_sidc(cls, sidc:str, schema:Schema, names:list = [], verbose:bool=False):
		sidc = re.sub(r'\s+', '', sidc)
		if len(sidc) < 2:
			raise Exception(f'Template SIDC must be at least 20 characters (spaces don\'t count), but is "{sidc}"')

		if verbose:
			print(f'Loading {names} from SIDC "{sidc}')

		symbol_sidc:str = re.sub(r'[\*_]', '0', sidc)

		ret = cls()
		ret.sidc = sidc

		try:
			ret.symbol = Symbol.from_sidc(sidc=symbol_sidc, schema=schema)
		except ex:
			raise Exception(f'Error loading template from SIDC {sidc}: {ex}')

		for item_name, (start, length, attr) in Template.ITEMS.items():
			entry = sidc[start:(start + length)]
			if re.findall(r'[\*_]', entry):
				setattr(ret, f'{item_name}_is_flexible', True)
			else:
				setattr(ret, f'{item_name}_is_flexible', False)

		ret.names = copy.copy(names)
		return ret

	def __repr__(self) -> str:
		return f'{'/'.join([f'"{name}"' for name in self.names])}{f' [{self.sidc}]' if self.sidc else ''}{self.symbol}'

	@classmethod
	def load_from_dict(cls, data:dict, schema:Schema, names:list = [], verbose:bool=False):
		names = names + data.get('names', [])
		if 'sidc' in data:
			#raise Exception(f'Template file "{filename}" item "{name}" doesn\'t have a "sidc" entry')
			sidc = data.get('sidc', '')
			try:
				template = Template.load_from_sidc(sidc=sidc, names=names, schema=schema, verbose=verbose)
			except Exception as ex:
				print(f'Error loading template from SIDC "{sidc}"; skipping: {ex}', file=sys.stderr)
				return None

			if template is not None:
				return template

		if verbose:
			print(f'Loading template {names} from dictionary')

		temp:Template = Template()
		temp.names = names
		temp.symbol = Symbol(schema=schema)
		for item_name, (start, length, attr) in Template.ITEMS.items():
			if item_name not in data:
				if verbose:
					print(f'\t{item_name} is flexible')

				setattr(temp.symbol, f'{item_name}_is_flexible', True)
				continue

			item_code:str = re.sub(r'[\s\n]+', '', str(data[item_name]))
			if len(item_code) < length:
				item_code = item_code.rjust(length, '0')

			if len(item_code) != length and not item_name.startswith('modifier'):
				print(f'Item \"{item_name}\" for a template must be of length {length}; ignoring template item from file "{filename}"', file=sys.stderr)
				return None

			if item_name not in Template.SYMBOL_SET_ITEMS:
				choices:dict = getattr(schema, attr)
				if item_code not in choices:
					print(f'\"{item_code}\" is not a valid value for {item_name} in "{filename}"; skipping', file=sys.stderr)
					return None

				setattr(temp, f'{item_name}_is_flexible', False)
				setattr(temp.symbol, item_name, choices[item_code])
			elif temp.symbol.symbol_set is not None:
				# Symbol set

				choices:dict = getattr(temp.symbol.symbol_set, attr)
				if item_name in ['modifier_1', 'modifier_2'] and len(item_code) == 3:
					choices = getattr(schema.symbol_sets['C'], attr)

				if item_code not in choices:
					print(f'\"{item_code}\" is not a valid value for symbol set {temp.symbol.symbol_set.id_code} {item_name}; skipping', file=sys.stderr)
					return None

				setattr(temp.symbol, item_name, choices[item_code])	
				setattr(temp, f'{item_name}_is_flexible', False)
				

		if temp.symbol.context is None:
			temp.symbol.context = schema.contexts['0']
		if temp.symbol.affiliation is None:
			temp.symbol.affiliation = schema.affiliations['0']

		# print(f'Loaded template {temp}')
		return temp

	@classmethod
	def load_from_file(cls, filename:str, schema=None, verbose:bool=False) -> list:
		if not schema:
			schema = Schema.load()
		if not os.path.exists(filename):
			raise Exception(f'Template file \"{filename}\" doesn\'t exist')
		with open(filename, 'r') as in_file:
			data = yaml.safe_load(in_file)

		ret = []
		for name, data in data.items():
			template = Template.load_from_dict(names=[name], schema=schema, data=data, verbose=verbose)
			if template is not None:
				ret.append(template)

		return ret


