
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
    def options_string_encode(cls, padding:int, style:str, use_variants:bool, use_background:bool, background_color:str):
        """
        Encodes options into a three-character string for string caching, with character 1 indicating padding as
        an int (X for values less than 0), one-character indicating style from options ['light', 'medium', 'dark',
        unfilled'], and a 0/1 Boolean value indicating whether to use variant symbols if available
        :param padding: An integer for padding SVGs
        :param style: String indicating style from ['light', 'medium', 'dark', 'unfilled']
        :param use_variants: Boolean indicating whether to use variant symbols if they exist
        :param use_background: Boolean indicating whether to use the background "halo"
        :param background_color: Background color
        :return: Three-character string of encoded options
        """
        return '{}{}{}{}{}'.format(
            'X' if padding < 0 else padding,
            style[0].lower(),
            '1' if use_variants else '0',
            '1' if use_background else '0',
            background_color
        )

    def _get_symbol_cache_from_sidc(self, sidc, create_if_missing:bool=True, verbose:bool=False) -> tuple:
        symbol_cache_entry:tuple = self.sidc_to_symbol_map.get(sidc, ())
        if len(symbol_cache_entry) < 1:
            # Entry doesn't exist
            if create_if_missing:
                # Tuple doesn't exist
                symbol: MilitarySymbol = MilitarySymbol(symbol_schema=self.symbol_schema)
                symbol.create_from_sidc(sidc)
                symbol_cache_entry = (symbol, {})
                self.sidc_to_symbol_map[sidc] = symbol_cache_entry

                return symbol_cache_entry
            else:
                return None
        else:
            # print('Symbol cache hit')
            return symbol_cache_entry

    def get_symbol_from_sidc(self, sidc:str, create_if_missing:bool=True, verbose:bool=False) -> MilitarySymbol:
        ret = self._get_symbol_cache_from_sidc(sidc, create_if_missing, verbose=verbose)
        return ret[0] if ret is not None else None

    def _get_symbol_cache_from_name(self, name, create_if_missing:bool=True, verbose:bool=False, limit_to_symbol_sets=None) -> tuple:
        sidc:str = self.name_to_sidc_string_map.get(name, '')
        if sidc == '':
            if create_if_missing:
                symbol:MilitarySymbol = name_to_sidc.name_to_symbol(name, self.symbol_schema, verbose=verbose, limit_to_symbol_sets=limit_to_symbol_sets)
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

    def get_symbol_from_name(self, name, create_if_missing:bool=True, verbose:bool=False, limit_to_symbol_sets=None) -> MilitarySymbol:
        cache_entry:tuple = self._get_symbol_cache_from_name(name, create_if_missing, verbose=verbose, limit_to_symbol_sets=limit_to_symbol_sets)
        return cache_entry[0] if cache_entry is not None else None

    def get_symbol(self, creator_var:str, is_sidc:bool, create_if_missing:bool=True, verbose:bool=False, limit_to_symbol_sets=None):
        if is_sidc:
            return self.get_symbol_from_sidc(creator_var, create_if_missing, verbose=verbose)
        else:
            return self.get_symbol_from_name(creator_var, create_if_missing, verbose=verbose, limit_to_symbol_sets=limit_to_symbol_sets)

    def get_symbol_and_svg_string(self, creator_val:str, is_sidc:bool, padding:int, style:str, use_variants:bool, 
        use_background:bool=True, background_color:str='#ffffff', create_if_missing:bool=True, verbose:bool=False, force_all_elements:bool=False,
        limit_to_symbol_sets=None) -> tuple:

        cache_entry_tuple: tuple = self._get_symbol_cache_from_sidc(creator_val,
                                                                    create_if_missing) if is_sidc else self._get_symbol_cache_from_name(
            creator_val, create_if_missing, verbose=verbose, limit_to_symbol_sets=limit_to_symbol_sets)

        if cache_entry_tuple is None:
            return None, ''

        symbol: MilitarySymbol = cache_entry_tuple[0]
        svg_map: dict = cache_entry_tuple[1]

        key_string: str = self.options_string_encode(padding, style, use_variants, use_background, background_color)
        svg_string: str = svg_map.get(key_string, '')
        if svg_string == '':
            if create_if_missing:
                svg_string = symbol.get_svg(style=style, pixel_padding=padding, use_variants=use_variants, use_background=use_background, 
                    background_color=background_color, force_all_elements=force_all_elements)
                svg_map[key_string] = svg_string
                return symbol, svg_string
            else:
                return symbol, ''
        else:
            return symbol, svg_string

    def get_svg_string(self, creator_val:str, is_sidc:bool, padding:int, style:str, use_variants:bool, use_background:bool=True, 
        background_color:str='#ffffff', create_if_missing:bool=True, verbose:bool=False, force_all_elements:bool=False,
        limit_to_symbol_sets=None):

        return self.get_symbol_and_svg_string(creator_val, is_sidc, padding, style, use_variants, use_background, 
            background_color, create_if_missing, verbose=verbose, force_all_elements=force_all_elements)[1]

    def get_svg_string_from_name(self, name, padding:int, style:str, use_variants:bool=False, use_background:bool=True, 
        background_color:str='#ffffff', create_if_missing:bool=True, verbose:bool=False, force_all_elements:bool=False,
        limit_to_symbol_sets=None):

        return self.get_svg_string(name, False, padding, style, use_variants, use_background, background_color, create_if_missing, 
            verbose=verbose, force_all_elements=force_all_elements)

    def get_svg_string_from_sidc(self, sidc, padding:int, style:str, use_variants:bool=False, use_background:bool=True, 
        background_color:str='#ffffff', create_if_missing:bool=True, verbose:bool=False, force_all_elements:bool=False):

        return self.get_svg_string(sidc, True, padding, style, use_variants, use_background, background_color, create_if_missing, 
            verbose=verbose, force_all_elements=force_all_elements)