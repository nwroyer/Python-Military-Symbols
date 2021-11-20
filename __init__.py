# test
from name_to_sidc import name_to_symbol
from nato_symbol import NATOSymbol
from symbol_schema import SymbolSchema
from symbol_template import SymbolTemplateSet

if __name__ == '__main__':
    # Get current working directory
    import os
    working_dir = os.getcwd()

    symbol_schema:SymbolSchema = SymbolSchema.load_symbol_schema_from_file(os.path.join(working_dir, 'NATO symbols.json'))

    symbol_temp:SymbolTemplateSet = SymbolTemplateSet(symbol_schema)
    symbol_temp.load_from_file(os.path.join(working_dir, 'templates.json'))
    symbol_schema.add_template_set(symbol_temp)

    test_lines = [
        "friendly airborne infantry platoon headquarters",
        "HIMARS battery",
        "suspected enemy PSYOP company",
        "friendly VTOL rotary-wing squadron"
    ]

    for symbol_name in test_lines:
        # print(symbol_name)
        symbol:NATOSymbol = name_to_symbol(symbol_name, symbol_schema, verbose=False)
        if symbol is not None:
            svg_text = symbol.get_svg(expand_to_fit=True, pixel_padding=4)
            svg_filename = os.path.join(working_dir, 'examples', f'{symbol.get_name()} ({symbol.get_sidc()}).svg')
            with open(svg_filename, 'w') as output:
                output.write(svg_text)


