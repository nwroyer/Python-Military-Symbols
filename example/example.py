"""
Minimal example class demonstrating usage as a Python module, including use of templates, writing to files, and to the
command line
"""

import os
import inspect

import military_symbol

if __name__ == '__main__':
    # Print symbol genera/home/nick/Projects/Python-Military-Symbols/Resources/_symbol_converter.pyted from a name to STDOUT
    # print(military_symbol.get_symbol_svg_string_from_name("enemy infantry platoon"))

    # Add a symbol template and write it to a file adjacent to this script
    military_symbol.add_templates_from_file('example_template.yml')

    test_dir = os.path.join(os.path.dirname(__file__), '..', 'test')
    os.makedirs(test_dir, exist_ok=True)

    # Generate a list of symbols from names and write them as SVG files in specific
    # styles, named according to a user-defined pattern and using variant symbols where available
    examples = [
        ('hostile armor company', 'light'),
        ("Dummy damaged neutral hospital", 'medium'),
        ("Friendly fighter", 'dark'),
        ("Destroyed neutral artillery task force headquarters", 'unfilled'),
        ("Suspected CBRN section", 'light'),
        ('hostile TOS-1 battery', 'unfilled'),
        ('friendly amphibious HIMARS battery', 'light'),
        ('friendly amphibious HIMARS battery', 'medium')
    ]

    for example_name, example_style in examples:
        example_symbol, svg_string = military_symbol.get_symbol_and_svg_string(example_name, 
                                                                               is_sidc=False,
                                                                               style=example_style,
                                                                               padding=4,
                                                                               use_variants=True,
                                                                               use_background=True)

        # print('\tExporting symbol "{}"'.format(example_symbol.get_name()))

        output_filename = os.path.join(os.getcwd(), '{} {} ({}).svg'.format(example_name, example_symbol.get_sidc(), example_style))
        with open(output_filename, 'w') as output_file:
            output_file.write(svg_string)
