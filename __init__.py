# test
from symbol_schema import  SymbolSchema
from nato_symbol import NATOSymbol
from name_to_sidc import name_to_symbol

if __name__ == '__main__':
    # Get current working directory
    import os
    working_dir = os.getcwd()

    symbol_schema = SymbolSchema.load_symbol_schema_from_file(os.path.join(working_dir, 'NATO symbols.json'))
    symbol = NATOSymbol(symbol_schema)

    TEST_SIDC = '10061000141100000508'
    new_sidc = TEST_SIDC

    symbol.create_from_sidc(new_sidc)

    symbol = name_to_symbol("friendly infantry platoon headquarters", symbol_schema)
    if symbol is not None:
        with open(os.path.join(working_dir, 'examples', f'{symbol.get_name()} ({symbol.get_sidc()}).svg'), 'w') as output:
            output.write(symbol.get_svg(expand_to_fit=False, pixel_padding=4))
