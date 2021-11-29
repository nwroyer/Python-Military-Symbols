import argparse
import os
import os.path
import sys

from . import name_to_sidc
from .individual_symbol import MilitarySymbol
from .symbol_schema import SymbolSchema
from .symbol_template import SymbolTemplateSet

STYLE_CHOICES = ['light', 'medium', 'dark', 'unfilled']

# Load the symbol schema from its default location; don't
sym_schema: SymbolSchema = SymbolSchema.load_symbol_schema_from_file()
if sym_schema is None:
    print("Error loading symbol schema; exiting", file=sys.stderr)



def add_symbol_template_set(template_filename):
    """
    Add a symbol template to allow easier generation of symbols by name for specific situation.
    :param template_filename: The filename for the template file is structured as shown in the example_template.json file
    """
    symbol_temp: SymbolTemplateSet = SymbolTemplateSet(sym_schema).load_from_file(template_filename)
    sym_schema.add_template_set(symbol_temp)


def get_symbol_svg_string_from_sidc(sidc, bounding_padding=4, verbose=False, use_variants=False, style='light') -> str:
    """
    Constructs an SVG for the specified symbol, given as a SIDC, and returns it as a string for further processing.
    :param sidc: The SIDC to construct the symbol from
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    :param use_variants: Whether to use variant symbols
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    :return: A string containing the SVG for the constructed symbol.
    """
    return get_svg_string(sidc, True, pixel_padding=bounding_padding, verbose=verbose, use_variants=use_variants, style=style)


def get_symbol_svg_string_from_name(name_string:str, bounding_padding=4, verbose=False, use_variants=False, style='light') -> str:
    """
    Constructs an SVG and returns it in string form, using the best guess as to the SIDC based on the provided name.
    :param name_string: The string containing the name, i.e. "Friendly infantry platoon headquarters"
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param verbose:  Whether to print ancillary information while processing, defaulting to false.
    :param use_variants: Whether to use variant symbols
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    :return: A string containing the SVG for the constructed symbol.
    """
    return get_svg_string(name_string, False, pixel_padding=bounding_padding, verbose=verbose, use_variants=use_variants, style=style)


def get_symbol_class_from_sidc(sidc, verbose=False) -> MilitarySymbol:
    """
    Returns an individual_symbol.MilitarySymbol object representing a symbol constructed from the given SIDC
    :param sidc: The SIDC to construct the MilitarySymbol from
    :param verbose: Whether to print ancillary information
    :return: An individual_symbol.MilitarySymbol object
    """
    return MilitarySymbol(sym_schema).create_from_sidc(sidc, verbose)


def get_symbol_class_from_name(name, verbose=False) -> MilitarySymbol:
    """
    Returns an individual_symbol.MilitarySymbol object representing a symbol constructed from the given name, as a best
    guess
    :param name: The name to construct the MilitarySymbol from using a best-guess algorithm
    :param verbose: Whether to print ancillary information
    :return: An individual_symbol.MilitarySymbol object
    """
    return name_to_sidc.name_to_symbol(name, symbol_schema=sym_schema, verbose=verbose)


def get_symbol_class(originator, is_sidc=True, verbose=False) -> MilitarySymbol:
    """
    Returns an individual_symbol.MilitarySymbol object representing a symbol constructed from the given name, as a best
    guess, or SIDC, depending on inputs
    :param originator: The variable to construct from, whether name or SIDC
    :param is_sidc: Whether the originator is a SIDC (true) or name (false)
    :param verbose: Whether to print ancillary information
    :return: The generated symbol
    """
    if is_sidc:
        return get_symbol_class_from_sidc(originator, verbose)
    else:
        return get_symbol_class_from_name(originator, verbose)

def get_svg_string(creator_var, is_sidc:bool, pixel_padding=4, verbose=False, use_variants=False, style='light') -> str:
    symbol: MilitarySymbol = get_symbol_class(creator_var, is_sidc, verbose)
    if symbol is not None:
        return symbol.get_svg(style=style, pixel_padding=pixel_padding, use_variants=use_variants)


def write_symbol_svg_string(creator_var, is_sidc:bool, out_filepath, bounding_padding=4, auto_name=True, verbose=False, use_variants=False, style='light') -> None:
    """
    Internal helper function to write a symbol to the file specified.
    :param is_sidc: Whether the creator_var parameter is a SIDC or a name
    :param creator_var: The string to construct the symbol from, either a SIDC or a name
    :param out_filepath: The filepath to write to
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param auto_name: Whether to auto-name the file by SIDC in the directory specified by out_filepath, or use out_filepath directly. Defaults to true.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    :param use_variants: Whether to use variant symbols
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    """
    symbol: MilitarySymbol = get_symbol_class(creator_var, is_sidc, verbose)

    if auto_name:
        out_dir = os.path.dirname(out_filepath) if os.path.isfile(out_filepath) else out_filepath
        out_filepath = os.path.join(out_dir, f"{symbol.get_sidc()}.svg")

    with open(out_filepath, 'w') as out_file:
        out_file.write(symbol.get_svg(pixel_padding=bounding_padding, use_variants=use_variants, style=style))


def write_symbol_svg_string_from_sidc(sidc, out_filepath, bounding_padding=4, auto_name=True, verbose=False, use_variants=False, style='light') -> None:
    """
    Internal helper function to write a symbol constructed from the given SIDC to the given filepath.
    :param sidc: The SIDC to construct the symbol from
    :param out_filepath: The filepath to write to
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param auto_name: Whether to auto-name the file by SIDC in the directory specified by out_filepath, or use out_filepath directly. Defaults to true.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    :param use_variants: Whether to use variant symbol styles.
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    """
    write_symbol_svg_string(sidc, True, out_filepath, bounding_padding, auto_name, verbose, use_variants=use_variants, style=style)


def write_symbol_svg_string_from_name(name_string, out_filepath, bounding_padding=4, auto_name=True, verbose=False, use_variants=False, style='light') -> None:
    """
    Internal helper function to write a symbol constructed as a best guess from the given name to the given filepath.
    :param name_string: The name to construct the symbol from
    :param out_filepath: The filepath to write to
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param auto_name: Whether to auto-name the file by SIDC in the directory specified by out_filepath, or use out_filepath directly. Defaults to true.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    :param use_variants: Whether to use variant symbol styles. Defauls to false.
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    """
    write_symbol_svg_string(name_string, False, out_filepath, bounding_padding, auto_name, verbose, use_variants=use_variants, style=style)


def command_line_main():
    # Get current working directory
    style_choices_args = STYLE_CHOICES.copy()
    style_choices_args.extend([i[0] for i in style_choices_args])

    parser = argparse.ArgumentParser(prog='milsymbol', description="Military symbol generator per NATO APP-6D standards")
    parser.add_argument('-o', '--output-dir', dest='output_dir', default='',
                        help="Chooses an output directory (or file if not auto-naming exports)")
    parser.add_argument('-n', '--by-name', dest='by_name', action='store_const', const=True, default=False,
                        help="Indicates inputs are names, not SIDC strings")
    parser.add_argument('-a', '--auto-name', dest='auto_name', action='store_const', const=True, default=False,
                        help='Whether to auto-name outputs (only valid for one)')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_const', const=True, default=False,
                        help="Whether to print ancillary information (pollutes STDOUT if you're using a pipe)")
    parser.add_argument('-p', '--padding', dest='padding', action='store', default=4,
                        help="Select padding for output SVG; default is 4; values < 0 will not crop to fit content")
    parser.add_argument('-t', '--use-variants', dest='use_variants', action='store_const', const=True, default=False,
                        help='Whether to use variant symbols if they exist')
    parser.add_argument('-s', '--style', dest='style_name', action='store', choices=style_choices_args, default='light',
                        help='Symbol style to use to draw symbols; choices are {}'.format(', '.join(style_choices_args)))
    parser.add_argument('inputs', nargs='+', default=[])

    arguments = parser.parse_args()

    if arguments.by_name and arguments.verbose:
        print('\tParsing by name; results may not be exact', file=sys.stderr)

    use_auto_name: bool = arguments.auto_name
    if len(arguments.inputs) > 1 and not arguments.auto_name:
        print('More than one input; auto-naming anyway', file=sys.stderr)
        use_auto_name = True

    # Parse output directory
    output_dir: str = ''
    if arguments.output_dir != '':
        output_dir = os.path.realpath(arguments.output_dir)
        if os.path.isdir(output_dir):
            use_auto_name = True

    # Parse style choice to use
    style_name = arguments.style_name
    if style_name not in STYLE_CHOICES:
        style_name = [name for name in STYLE_CHOICES if name[0] == style_name[0]][0]

    # Loop through remaining inputs and process t hem
    for input_arg in arguments.inputs:
        if arguments.verbose:
            print(f'\tParsing "{input_arg}"', file=sys.stderr)
        if arguments.by_name:  # Construct from names
            if output_dir != '':
                write_symbol_svg_string_from_name(input_arg, out_filepath=output_dir, bounding_padding=arguments.padding,
                                                  auto_name=use_auto_name,
                                                  verbose=arguments.verbose,
                                                  use_variants=arguments.use_variants,
                                                  style=style_name)
            else:
                print(get_symbol_svg_string_from_name(input_arg, bounding_padding=arguments.padding,
                                                      verbose=arguments.verbose,
                                                      use_variants=arguments.use_variants,
                                                      style=style_name))
        else:  # Construct from SIDC
            if output_dir != '':
                write_symbol_svg_string_from_sidc(input_arg, out_filepath=output_dir, bounding_padding=arguments.padding,
                                                  auto_name=use_auto_name,
                                                  verbose=arguments.verbose,
                                                  use_variants=arguments.use_variants,
                                                  style=style_name)
            else:
                print(get_symbol_svg_string_from_sidc(input_arg, bounding_padding=arguments.padding,
                                                      verbose=arguments.verbose,
                                                      use_variants=arguments.use_variants,
                                                      style=style_name))

if __name__ == '__main__':
    command_line_main()