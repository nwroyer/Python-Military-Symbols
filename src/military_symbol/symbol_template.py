import json

from .individual_symbol import MilitarySymbol


class SymbolTemplate:
    """
    Class representing a symbol template, to allow for easier creation of symbols by name
    """

    def __init__(self, symbol_schema):
        self.names: list = []
        self.symbol: MilitarySymbol = None
        self.template_sidc:str = ''
        self.symbol_schema = symbol_schema

        # Digits 0-1: Version code
        self.context_fixed: bool = False  # Digit 2
        self.standard_identity_fixed: bool = False  # Digit 3
        self.symbol_set_fixed: bool = False  # Digits 4-5
        self.status_fixed: bool = False  # Digit 6
        self.hqtfd_fixed: bool = False  # Digit 7
        self.amplifier_fixed: bool = False  # Digits 8-9
        self.entity_fixed: bool = False  # Digits 10-15
        self.modifiers_fixed: list = [False, False]  # Digits 16-17 and 18-19, respectively

    def get_names(self):
        return self.names

    def create_from_sidc(self, sidc):
        """
        Creates a template from a given SIDC, where asterisks indicate "free spaces" that can be modified
        :param sidc: The SIDC to create the template from
        """

        template_sidc = ''.join([c for c in sidc if c.isnumeric() or c == '*'])
        if len(template_sidc) != 20:
            print(f'Error with template SIDC "{sidc}"')

        self.template_sidc = template_sidc
        self.symbol = MilitarySymbol(self.symbol_schema)
        self.symbol.create_from_sidc(template_sidc.replace('*', '0'))
        self.names = [self.symbol.get_name()]

        # Determine whether symbol is fixed
        self.context_fixed = template_sidc[1] != '*'
        self.standard_identity_fixed = template_sidc[2] != '*'
        self.symbol_set_fixed = template_sidc[4:6] != '**'
        self.status_fixed = template_sidc[6] != '*'
        self.hqtfd_fixed = template_sidc[7] != '*'
        self.amplifier_fixed = template_sidc[8:10] != '**'
        self.entity_fixed = template_sidc[10:16] != '******'
        self.modifiers_fixed = [
            template_sidc[16:18] != '**',
            template_sidc[18:20] != '**'
        ]

        # print(f"Created template \"{self.name}\": \"{self.symbol.get_name()}\"{'' if len(self.alt_names) < 1 else ' (' + ' / '.join(self.alt_names) + ')'}")


class SymbolTemplateSet:
    """
    Class representing a set of symbol templates; can contain other SymbolTemplateSets as subsets to create "palettes"
    of symbols for better organization in human-readable files.
    """

    def __init__(self, symbol_schem):
        self.symbol_schema = symbol_schem
        self.names = ['']
        self.subsets = {}
        self.templates = {}

    def get_names(self):
        return self.names

    def load_from_dict(self, dict_val):
        """
        Loads this SymbolTemplateSet from a dictionary (typically parsed from a JSON file. Does not clear existing data
        if it already exists in the SymbolTemplateSet.
        :param dict_val: The dictionary to load values from
        """

        if 'name' in dict_val.keys():
            self.names = [dict_val['name']]
        elif 'names' in dict_val.keys():
            self.names = dict_val['names']

        # print(f'Loading template set \"{self.name}\"')

        if 'subsets' in dict_val.keys():
            for tmp_name, template in dict_val['subsets'].items():
                # print(tab_stops + f'\tSubset {self.name} >> {tmp_name}')
                subset = SymbolTemplateSet(self.symbol_schema)
                subset.names = [tmp_name]
                subset.load_from_dict(template)
                self.subsets[subset.names[0]] = subset

        if 'templates' in dict_val.keys():
            for template_name, template_sidc in dict_val['templates'].items():
                # print(f'\t{template_name} -> {template_sidc}')
                new_template = SymbolTemplate(self.symbol_schema)
                new_template.create_from_sidc(template_sidc)
                new_template.names = [template_name]
                self.templates[new_template.name] = new_template

        remaining_items = [(key, value) for (key, value) in dict_val.items() if key not in ['name', 'subsets']]
        for (template_name, template_sidc) in remaining_items:

            new_template = SymbolTemplate(self.symbol_schema)
            names = [template_name]

            if isinstance(template_sidc, str):
                new_template.create_from_sidc(template_sidc)
            elif isinstance(template_sidc, dict):
                new_template.create_from_sidc(template_sidc['sidc'])
                names.extend(template_sidc['alt names'])
            
            new_template.names = list(set(names))

            self.templates[new_template.names[0]] = new_template

    def get_template(self, template_name):
        """
        Returns a template whose primary name matches the given name exactly
        :param template_name: The name to match
        :return: The first matching template, or None if none found
        """

        if template_name in self.templates.keys():
            return self.templates[template_name]

        for subset in self.subsets:
            ret = subset.get_template(template_name)
            if ret is not None:
                return ret

        return None

    def get_template_list(self):
        """
        Returns a flat list of all the SymbolTemplates belonging to this SymbolTemplateSet and all its descendant subsets
        :return: List containing the SymbolTemplate
        """
        ret = []
        ret.extend(self.templates.values())

        for subset in self.subsets.values():
            ret.extend(subset.get_template_list())

        return ret

    def load_from_file(self, json_filepath):
        """
        Loads data into a SymbolTemplateSet from a file
        :param json_filepath: The filepath to a JSON file to load from
        :return:
        """
        with open(json_filepath, 'r') as json_file:
            json_data = json.load(json_file)  # TODO load from string instead
            self.load_from_dict(json_data)
        return self

