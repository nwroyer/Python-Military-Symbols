import os

import military_symbol

if __name__ == '__main__':
    # Print symbol generated from a name to STDOUT
    print(military_symbol.get_symbol_svg_string_from_name("enemy infantry platoon"))

    # Add a symbol template and write it to a file adjacent to this script
    example_template_directory = os.path.dirname(__file__)
    military_symbol.add_symbol_template_set(os.path.join(example_template_directory, 'example_template.json'))
    military_symbol.write_symbol_svg_string_from_name("T-82", out_filepath=os.path.join(example_template_directory,
                                                                                        'T-82.svg'), auto_name=False)

    # Generate a list of symbols from names and write them as SVG files in specific
    # styles, named according to a user-defined pattern and using variant symbols where available
    examples = [
        ('Enemy armor company', 'light'),
        ("Dummy damaged neutral hospital", 'medium'),
        ("Friendly fighter", 'dark'),
        ("Destroyed neutral artillery task force headquarters", 'unfilled'),
        ("Suspected CBRN section", 'light')
    ]

    for example_name, example_style in examples:
        example_symbol: military_symbol.individual_symbol.MilitarySymbol = military_symbol.get_symbol_class_from_name(example_name)
        print('Exporting symbol "{}"'.format(example_symbol.get_name()))

        output_filename = '{} ({}).svg'.format(example_symbol.get_sidc(), example_style)
        with open(output_filename, 'w') as output_file:
            output_file.write(example_symbol.get_svg(fill_type=example_style, pixel_padding=4, use_variants=True))
