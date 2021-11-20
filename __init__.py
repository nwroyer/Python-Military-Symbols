# test
from name_to_sidc import name_to_symbol
from nato_symbol import NATOSymbol
from symbol_schema import SymbolSchema
from symbol_template import SymbolTemplateSet

if __name__ == '__main__':
    # Get current working directory
    import os
    working_dir = os.getcwd()

    symbol_schema = SymbolSchema.load_symbol_schema_from_file(os.path.join(working_dir, 'NATO symbols.json'))

    symbol_temp:SymbolTemplateSet = SymbolTemplateSet(symbol_schema)
    symbol_temp.load_from_file(os.path.join(working_dir, 'templates.json'))

    test_lines = [
        "friendly infantry platoon headquarters",
        "friendly infantry squad",
        "enemy self-propelled artillery battery",
        "friendly forward observer section",
        "friendly class I",
        "friendly amphibious infantry company",
        "friendly combat camera section",
        "enemy PSYOP company",
        "enemy HIMARS",
        "friendly comm battalion"
    ]

    for symbol_name in test_lines:
        # print(symbol_name)
        symbol:NATOSymbol = name_to_symbol(symbol_name, symbol_schema, verbose=False)
        if symbol is not None:
            svg_text = symbol.get_svg(expand_to_fit=True, pixel_padding=4)
            svg_filename = os.path.join(working_dir, 'examples', f'{symbol.get_name()} ({symbol.get_sidc()}).svg')
            with open(svg_filename, 'w') as output:
                output.write(svg_text)


