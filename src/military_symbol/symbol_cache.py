
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
        self.sidc_to_symbol_map:dict = {}  # Map of SIDCs + options to SVG string
        self.name_to_sidc_string_map:dict = {}  # Map of names to (symbol, SIDC) pairs
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

    def _get_symbol_cache_from_sidc(self, sidc, create_if_missing:bool=True) -> tuple:
        symbol_cache_entry:tuple = self.sidc_to_symbol_map.get(sidc, ())
        if len(symbol_cache_entry) < 0:
            # Entry doesn't exist
            if create_if_missing:
                # Tuple doesn't exist
                symbol: MilitarySymbol = MilitarySymbol(symbol_schema=self.symbol_schema)
                symbol.create_from_sidc(sidc)
                symbol_cache_entry = (symbol, {})
                self.sidc_to_symbol_map[sidc] = symbol_cache_entry
            else:
                return None
        else:
            # print('Symbol cache hit')
            return symbol_cache_entry

    def get_symbol_from_sidc(self, sidc:str, create_if_missing:bool=True) -> MilitarySymbol:
        cache_entry:tuple = self._get_symbol_cache_from_sidc(sidc, create_if_missing)
        return cache_entry[0] if cache_entry is not None else None

    def _get_symbol_cache_from_name(self, name, create_if_missing:bool=True) -> tuple:
        sidc:str = self.name_to_sidc_string_map.get(name, '')
        if sidc == '':
            if create_if_missing:
                symbol:MilitarySymbol = name_to_sidc.name_to_symbol(name, self.symbol_schema)
                sidc = symbol.get_sidc()
                cache_entry:tuple = (symbol, {})
                self.sidc_to_symbol_map[sidc] = cache_entry
                self.name_to_sidc_string_map[name] = sidc
                return cache_entry
            else:
                return None
        else:
            # print('Cache hit on symbol cache to name')
            return self.sidc_to_symbol_map[sidc]

    def get_symbol_from_name(self, name, create_if_missing:bool=True) -> MilitarySymbol:
        cache_entry:tuple = self._get_symbol_cache_from_name(name, create_if_missing)
        return cache_entry[0] if cache_entry is not None else None

    def get_symbol(self, creator_var:str, is_sidc:bool, create_if_missing:bool=True):
        if is_sidc:
            return self.get_symbol_from_sidc(creator_var, create_if_missing)
        else:
            return self.get_symbol_from_name(creator_var, create_if_missing)

    def get_symbol_and_svg_string(self, creator_val:str, is_sidc:bool, padding:int, style:str, use_variants:bool, create_if_missing:bool=True) -> tuple:
        cache_entry_tuple: tuple = self._get_symbol_cache_from_sidc(creator_val,
                                                                    create_if_missing) if is_sidc else self._get_symbol_cache_from_name(
            creator_val, create_if_missing)

        if cache_entry_tuple is None:
            return None, ''

        symbol: MilitarySymbol = cache_entry_tuple[0]
        svg_map: dict = cache_entry_tuple[1]

        key_string: str = self.options_string_encode(padding, style, use_variants)
        svg_string: str = svg_map.get(key_string, '')
        if svg_string == '':
            if create_if_missing:
                svg_string = symbol.get_svg(style=style, pixel_padding=padding, use_variants=use_variants)
                svg_map[key_string] = svg_string
                return symbol, svg_string
            else:
                return symbol, ''
        else:
            return symbol, svg_string

    def get_svg_string(self, creator_val:str, is_sidc:bool, padding:int, style:str, use_variants:bool, create_if_missing:bool=True):
        return self.get_symbol_and_svg_string(creator_val, is_sidc, padding, style, use_variants, create_if_missing)[1]

    def get_svg_string_from_name(self, name, padding:int, style:str, use_variants:bool=False, create_if_missing:bool=True):
        return self.get_svg_string(name, False, padding, style, use_variants, create_if_missing)

    def get_svg_string_from_sidc(self, sidc, padding:int, style:str, use_variants:bool=False, create_if_missing:bool=True):
        return self.get_svg_string(sidc, True, padding, style, use_variants, create_if_missing)