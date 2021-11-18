# test
from symbol_schema import  SymbolSchema
from nato_symbol import NATOSymbol
from name_to_sidc import name_to_sidc

if __name__ == '__main__':
    # Get current working directory
    import os
    working_dir = os.getcwd()

    symbol_schema = SymbolSchema.load_symbol_schema_from_file(os.path.join(working_dir, 'NATO symbols.json'))
    symbol = NATOSymbol(symbol_schema)

    TEST_SIDC = '10061000141100000508'

    symbol.create_from_sidc(TEST_SIDC)
    new_sidc = name_to_sidc("friendly   infantry platoon", symbol_schema)

    with open(os.path.join(working_dir, f'{symbol.get_name()} ({symbol.get_sidc()}).svg'), 'w') as output:
        output.write(symbol.get_svg(expand_to_fit=True, pixel_padding=4))
