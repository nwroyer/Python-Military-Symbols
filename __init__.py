# test
from name_to_sidc import name_to_symbol
from nato_symbol import NATOSymbol
from symbol_schema import SymbolSchema

if __name__ == '__main__':
    # Get current working directory
    import os
    working_dir = os.getcwd()

    symbol_schema = SymbolSchema.load_symbol_schema_from_file(os.path.join(working_dir, 'NATO symbols.json'))
    symbol = NATOSymbol(symbol_schema)

    TEST_SIDC = '10061000141100000508'
    new_sidc = TEST_SIDC

    symbol.create_from_sidc(new_sidc)

    test_lines = [
        "friendly infantry platoon headquarters",
        "friendly infantry squad",
        "enemy self-propelled howitzer",
        "friendly forward observer theater"
    ]
    for symbol_name in test_lines:
        print(symbol_name)
        symbol = name_to_symbol(symbol_name, symbol_schema, verbose=True)
        if symbol is not None:
            svg_text = symbol.get_svg(expand_to_fit=True, pixel_padding=4)
            svg_filename = os.path.join(working_dir, 'examples', f'{symbol.get_name()} ({symbol.get_sidc()}).svg')
            with open(svg_filename, 'w') as output:
                output.write(svg_text)


