# Python military symbols

This is a lightweight Python module, including a command-line script, to generate NATO APP-6(D) compliant military symbol icons in SVG format. These SVGs can be generated from inputs formatted as NATO SIDCs (Symbol identification codes) or as natural-language names for symbols, i.e. "friendly infantry platoon" or "enemy mortar section." Features supported include:

- Headquarters, task force, mobility, and echelon indicators
- Automatic checking of modifier and entity types for congruence
- Symbol sets to indicate land units and installations, air, space, sea surface, subsurface, signals intelligence, and cyber units, tracks, and activities
- Status indicators in both standard and alternate forms
- Construction of SVGs in light, medium, dark, and unfilled styles

Control measure graphics are not yet implemented.

Available as a [Python package](https://pypi.org/project/military-symbol/1.0.0/). 

### Usage

Command line usage examples:

```bash
# Create a set of symbols by name, using variant symbols if available, in the current directory
military_symbol --use-variants --by-name -o . "Friendly artillery company" "Destroyed Enemy PSYOP section"

# Create a single symbol at the designated path by name
military_symbol -o platoon.svg -n "Friendly infantry platoon"

# Print a set of symbols by name, in unfilled style, to STDOUT
military_symbol -s unfilled -n "Friendly infantry platoon" "Enemy anti-air battery"

# Create the same set of symbols as above, but by SIDC
military_symbol -o .  -n 10031000141211000000 10041000141211000000
```

Python module usage:

```Python
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

    shapes = [
        'friendly infantry',
        'friendly cavalry',
        'friendly artillery'
    ]
    for shape in shapes:
        military_symbol.write_symbol_svg_string_from_name(shape, out_filepath=example_template_directory)

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
            output_file.write(example_symbol.get_svg(style=example_style, pixel_padding=4, use_variants=True))
```

## License

This project is licensed under the MIT license. 
 