import json

from nato_symbol import NATOSymbol
from symbol_schema import SymbolSchema


class SymbolTemplate:

    def __init__(self, symbol_schema:SymbolSchema):
        self.name: str = ''
        self.alt_names: list = []
        self.symbol: NATOSymbol = None
        self.template_sidc:str = ''
        self.symbol_schema:SymbolSchema = symbol_schema

        # Digits 0-1: Version code
        self.context_fixed: bool = False  # Digit 2
        self.standard_identity_fixed: bool = False  # Digit 3
        self.symbol_set_fixed: bool = False  # Digits 4-5
        self.status_fixed: bool = False  # Digit 6
        self.hqtfd_fixed: bool = False  # Digit 7
        self.amplifier_fixed: bool = False  # Digits 8-9
        self.entity_fixed: bool = False  # Digits 10-15
        self.modifiers_fixed: list = [False, False]  # Digits 16-17 and 18-19, respectively

    def create_from_sidc(self, sidc):

        template_sidc = ''.join([c for c in sidc if c.isnumeric() or c == '*'])
        if len(template_sidc) != 20:
            print(f'Error with template SIDC "{sidc}"')

        self.template_sidc = template_sidc
        self.symbol = NATOSymbol(self.symbol_schema)
        self.symbol.create_from_sidc(template_sidc.replace('*', '0'))

        # Determine whether symbol is fixed
        self.context_fixed = template_sidc[2] != '*'
        self.standard_identity_fixed = template_sidc[3] != '*'
        self.symbol_set_fixed = template_sidc[4:6] != '**'
        self.status_fixed = template_sidc[6] != '*'
        self.hqtfd_fixed = template_sidc[7] != '*'
        self.amplifier_fixed = template_sidc[8:10] != '**'
        self.entity_fixed = template_sidc[10:16] != '******'
        self.modifiers_fixed = [
            template_sidc[16:18] != '**',
            template_sidc[18:20] != '**'
        ]

        print(f"Created template \"{self.name}\": \"{self.symbol.get_name()}\"{'' if len(self.alt_names) < 1 else ' (' + ' / '.join(self.alt_names) + ')'}")


class SymbolTemplateSet:

    def __init__(self, symbol_schema):
        self.symbol_schema:SymbolSchema = symbol_schema
        self.name = ''
        self.subsets = {}
        self.templates = {}

    def load_from_dict(self, dict_val):
        tab_stops = ''
        template_list:dict = None

        if 'name' in dict_val.keys():
            self.name = dict_val['name']

        print(f'Loading template set \"{self.name}\"')

        if 'subsets' in dict_val.keys():
            for tmp_name, template in dict_val['subsets'].items():
                print(tab_stops + f'\tSubset {self.name} >> {tmp_name}')
                subset = SymbolTemplateSet(self.symbol_schema)
                subset.name = tmp_name
                subset.load_from_dict(template)
                self.subsets[subset.name] = subset

        if 'templates' in dict_val.keys():
            for template_name, template_sidc in dict_val['templates'].items():
                print(f'\t{template_name} -> {template_sidc}')
                new_template = SymbolTemplate(self.symbol_schema)
                new_template.name = template_name
                new_template.create_from_sidc(template_sidc)
                self.templates[new_template.name] = new_template

        remaining_items = [(key, value) for (key, value) in dict_val.items() if key not in ['name', 'subsets']]
        for (template_name, template_sidc) in remaining_items:

            new_template = SymbolTemplate(self.symbol_schema)
            new_template.name = template_name

            if isinstance(template_sidc, str):
                new_template.create_from_sidc(template_sidc)
            elif isinstance(template_sidc, dict):
                new_template.alt_names = template_sidc['alt names']
                new_template.create_from_sidc(template_sidc['sidc'])

            self.templates[new_template.name] = new_template

    def get_template(self, template_name):
        if template_name in self.templates.keys():
            return self.templates[template_name]

    def load_from_file(self, json_filepath):
        json_data = {}
        with open(json_filepath, 'r') as json_file:
            json_data = json.load(json_file)  # TODO load from string instead
            self.load_from_dict(json_data)

