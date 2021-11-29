
from .individual_symbol import MilitarySymbol
from . import name_to_sidc
from .symbol_schema import SymbolSchema

class SymbolCache:

    STYLE_OPTIONS = [
        'light',
        'medium',
        'dark',
        'unfilled'
    ]

    def __init__(self, symbol_schema):
        self.sidc_to_svg_string_map:dict = {}
        self.name_to_sidc_string_map:dict = {}
        self.symbol_schema = symbol_schema

    @classmethod
    def options_string_decode(cls, options_string:str):
        """
        Decodes options from a string to allow caching by string SIDC with options (since different options
        result in different SVGs even for the same symbol (denoted with SIDC).
        :param options_string: A three-character string for caching options
        :return: A tuple of (padding:int, style:str, use_variants:bool)
        """
        # Options are formatted as [XSV], where X is padding (X for none), S is style code (See above constants),
        # and V is use variants [0, 1]

        return (
            options_string[0] if options_string[0].isnumeric() else -1,
            [style for style in SymbolCache.STYLE_OPTIONS if style[0].lower() == options_string[1].lower()][0],
            bool(options_string[0])
        )

    @classmethod
    def options_string_encode(cls, padding:int, style:str, use_variants:bool):
        """
        Encodes options into a three-character string for string caching, with character 1 indicating padding as
        an int (X for values less than 0), one-character indicating style from options ['light', 'medium', 'dark',
        unfilled'], and a 0/1 Boolean value indicating whether to use variant symbols if available
        :param padding: An integer for padding SVGs
        :param style: String indicating style from ['light', 'medium', 'dark', 'unfilled']
        :param use_variants: Boolean indicating whether to use variant symbols if they exist
        :return: Three-character string of encoded options
        """
        return '{}{}{}'.format(
            'X' if padding < 0 else padding,
            style[0].lower(),
            '1' if use_variants else '0'
        )

    def get_svg_string_from_sidc(self, sidc:str, padding:int, style:str, use_variants:bool, create_if_missing:bool=True) -> str:
        key_string:str = sidc + SymbolCache.options_string_encode(padding, style, use_variants)
        svg_string:str =  self.sidc_to_svg_string_map.get(key=key_string, default='')

        if svg_string == '' and create_if_missing:
            symbol:MilitarySymbol = MilitarySymbol(symbol_schema=self.symbol_schema)
            symbol.create_from_sidc(sidc)
            svg_string = symbol.get_svg(style, padding, use_variants)
            self.sidc_to_svg_string_map[key_string] = svg_string
            return svg_string
        else:
            return svg_string

    def get_svg_string_from_name(self, name:str, padding:int, style:str, use_variants:bool, create_if_missing:bool=True) -> str:
        sidc_string = self.name_to_sidc_string_map.get(name, defualt='')

        if sidc_string == '':
            if create_if_missing:
                symbol:MilitarySymbol = name_to_sidc.name_to_symbol(name, self.symbol_schema)
                sidc_string = symbol.get_sidc()
                self.name_to_sidc_string_map[name] = sidc_string

                # Add to name -> SIDC map
                key_string = sidc_string + self.options_string_encode(padding, style, use_variants)
                svg_string:str = symbol.get_svg(style, padding, use_variants)
                self.sidc_to_svg_string_map[key_string] = svg_string
                return svg_string
            else:
                return ''

        return self.get_svg_string_from_sidc(sidc_string, padding, style, use_variants, create_if_missing)

