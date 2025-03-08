import argparse
import os
import os.path
import sys

from . import name_to_sidc

from .individual_symbol import MilitarySymbol
from .symbol_schema import SymbolSchema
from .symbol_template import SymbolTemplateSet
from .symbol_cache import SymbolCache

STYLE_CHOICES = ['light', 'medium', 'dark', 'unfilled']

# Load the symbol schema from its default location; don't
sym_schema: SymbolSchema = SymbolSchema.load_symbol_schema_from_file()
if sym_schema is None:
    print("Error loading symbol schema; exiting", file=sys.stderr)

symbol_cache: SymbolCache = SymbolCache(sym_schema)

def add_symbol_template_set(template_filename):
    """
    Add a symbol template to allow easier generation of symbols by name for specific situation.
    :param template_filename: The filename for the template file is structured as shown in the example_template.json file
    """
    symbol_temp: SymbolTemplateSet = SymbolTemplateSet(sym_schema).load_from_file(template_filename)
    sym_schema.add_template_set(symbol_temp)


def get_symbol_svg_string_from_sidc(sidc, bounding_padding=4, verbose=False, use_variants=False, style='light', 
                                    use_background=False, background_color='#ffffff', force_all_elements=False) -> str:
    """
    Constructs an SVG for the specified symbol, given as a SIDC, and returns it as a string for further processing.
    :param sidc: The SIDC to construct the symbol from
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    :param use_variants: Whether to use variant symbols
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    :param use_background: Whether to use a colored background around the symbol
    :param background_color: Background color to use, if it's used
    :return: A string containing the SVG for the constructed symbol.
    """
    return get_svg_string(sidc, True, pixel_padding=bounding_padding, verbose=verbose, use_variants=use_variants,
                          style=style, use_background=use_background, background_color=background_color, force_all_elements=force_all_elements)


def get_symbol_svg_string_from_name(name_string:str, bounding_padding=4, verbose=False, use_variants=False, style='light',
                                    use_background:bool=True, background_color:str='#ffffff', force_all_elements=False,
                                    limit_to_symbol_sets=None) -> str:
    """
    Constructs an SVG and returns it in string form, using the best guess as to the SIDC based on the provided name.
    :param name_string: The string containing the name, i.e. "Friendly infantry platoon headquarters"
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param verbose:  Whether to print ancillary information while processing, defaulting to false.
    :param use_variants: Whether to use variant symbols
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    :param use_background: Whether to use a colored background around the symbol
    :param background_color: Background color to use, if it's used
    :return: A string containing the SVG for the constructed symbol.
    """
    return get_svg_string(name_string, False, pixel_padding=bounding_padding, verbose=verbose, use_variants=use_variants, style=style,
                          use_background=use_background, background_color=background_color, force_all_elements=force_all_elements,
                          limit_to_symbol_sets=limit_to_symbol_sets)


def get_symbol_class(originator, is_sidc=True, verbose=False, limit_to_symbol_sets=None) -> MilitarySymbol:
    """
    Returns an individual_symbol.MilitarySymbol object representing a symbol constructed from the given name, as a best
    guess, or SIDC, depending on inputs
    :param originator: The variable to construct from, whether name or SIDC
    :param is_sidc: Whether the originator is a SIDC (true) or name (false)
    :param verbose: Whether to print ancillary information
    :return: The generated symbol
    """
    return symbol_cache.get_symbol(originator, is_sidc=is_sidc, verbose=verbose, limit_to_symbol_sets=limit_to_symbol_sets)


def get_symbol_class_from_name(name, verbose=False, limit_to_symbol_sets=None) -> MilitarySymbol:
    """
    Returns an individual_symbol.MilitarySymbol object representing a symbol constructed from the given name, as a best
    guess
    :param name: The name to construct the MilitarySymbol from using a best-guess algorithm
    :param verbose: Whether to print ancillary information
    :return: An individual_symbol.MilitarySymbol object
    """
    return get_symbol_class(name, is_sidc=False, verbose=verbose, limit_to_symbol_sets=limit_to_symbol_sets)


def get_symbol_class_from_sidc(sidc, verbose=False) -> MilitarySymbol:
    """
    Returns an individual_symbol.MilitarySymbol object representing a symbol constructed from the given SIDC
    :param sidc: The SIDC to construct the MilitarySymbol from
    :param verbose: Whether to print ancillary information
    :return: An individual_symbol.MilitarySymbol object
    """
    return get_symbol_class(sidc, is_sidc=True, verbose=verbose)


def get_svg_string(creator_var:str, is_sidc:bool, pixel_padding=4, use_variants=False, style='light', use_background=False, 
                   background_color='#ffffff', verbose=False, force_all_elements=False, limit_to_symbol_sets=None) -> str:
    """
    Constructs an SVG for the specified symbol, given as a SIDC or name, and returns it as a string for further processing.
    :param creator_var: The SIDC or name to construct the symbol from
    :param is_sidc: Whether the creator value is a SIDC (true) or name (false)
    :param pixel_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    :param use_variants: Whether to use variant symbols
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    :param use_background: Whether to use a colored background around the symbol
    :param background_color: Background color to use, if it's used
    :return: A string containing the SVG for the constructed symbol.
    """
    return symbol_cache.get_svg_string(creator_var, is_sidc, padding=pixel_padding, style=style,
                                       use_variants=use_variants, use_background=use_background,
                                       background_color=background_color, create_if_missing=True, verbose=verbose,
                                       force_all_elements=force_all_elements, 
                                       limit_to_symbol_sets=limit_to_symbol_sets)


def get_symbol_and_svg_string(creator_var:str, is_sidc:bool, padding:int=4, style:str='light', use_variants:bool=False, use_background=False, background_color='#ffffff',
                              verbose=False, force_all_elements=False, limit_to_symbol_sets=None) -> tuple:
    """
    Returns a (MilitarySymbol, str) tuple containing the symbol and SVG string for the given creator value and style elements
    :param creator_var: The SIDC or name to construct the symbol from
    :param is_sidc: Whether the creator value is a SIDC (true) or name (false)
    :param padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    :param use_variants: Whether to use variant symbols
    :param use_background: Whether to use a colored background around the symbol
    :param background_color: Background color to use, if it's used
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    :return: A (MilitarySymbol, str) tuple containing the symbol and SVG for the constructed symbol.
    """
    return symbol_cache.get_symbol_and_svg_string(creator_var, is_sidc, padding, style, use_variants, use_background=use_background, 
        background_color=background_color, verbose=verbose, force_all_elements=force_all_elements, limit_to_symbol_sets=limit_to_symbol_sets)


def write_symbol_svg_string(creator_var, is_sidc:bool, out_filepath, bounding_padding=4, auto_name=True, use_variants=False, style='light', 
                            use_background=False, background_color='#ffffff', verbose=False, force_all_elements=False,
                            limit_to_symbol_sets=None) -> None:
    """
    Internal helper function to write a symbol to the file specified.
    :param is_sidc: Whether the creator_var parameter is a SIDC or a name
    :param creator_var: The string to construct the symbol from, either a SIDC or a name
    :param out_filepath: The filepath to write to
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param auto_name: Whether to auto-name the file by SIDC in the directory specified by out_filepath, or use out_filepath directly. Defaults to true.
    :param use_variants: Whether to use variant symbols
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    :param use_background: Whether to use a colored background around the symbol
    :param background_color: Background color to use, if it's used
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    """
    symbol, svg_string = symbol_cache.get_symbol_and_svg_string(creator_var, is_sidc,
                                                                padding=bounding_padding, style=style,
                                                                use_variants=use_variants,
                                                                use_background=use_background,
                                                                background_color=background_color,
                                                                verbose=verbose,
                                                                force_all_elements=force_all_elements,
                                                                limit_to_symbol_sets=limit_to_symbol_sets)

    if auto_name:
        out_dir = os.path.dirname(out_filepath) if os.path.isfile(out_filepath) else out_filepath
        out_filepath = os.path.join(out_dir, f"{symbol.get_sidc()}.svg")

    with open(out_filepath, 'w') as out_file:
        out_file.write(svg_string)


def write_symbol_svg_string_from_sidc(sidc, out_filepath, bounding_padding=4, auto_name=True, verbose=False, use_variants=False, style='light', 
                                      use_background=False, background_color='#ffffff', force_all_elements=False) -> None:
    """
    Internal helper function to write a symbol constructed from the given SIDC to the given filepath.
    :param sidc: The SIDC to construct the symbol from
    :param out_filepath: The filepath to write to
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param auto_name: Whether to auto-name the file by SIDC in the directory specified by out_filepath, or use out_filepath directly. Defaults to true.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    :param use_variants: Whether to use variant symbol styles.
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    :param use_background: Whether to use a colored background around the symbol
    :param background_color: Background color to use, if it's used
    """
    write_symbol_svg_string(sidc, True, out_filepath, bounding_padding, auto_name, use_variants=use_variants, style=style, 
        use_background=use_background, background_color=background_color, verbose=verbose, force_all_elements=force_all_elements)


def write_symbol_svg_string_from_name(name_string, out_filepath, bounding_padding=4, auto_name=True, verbose=False, use_variants=False, 
                                      style='light', use_background=False, background_color='#ffffff', force_all_elements=False,
                                      limit_to_symbol_sets=None) -> None:
    """
    Internal helper function to write a symbol constructed as a best guess from the given name to the given filepath.
    :param name_string: The name to construct the symbol from
    :param out_filepath: The filepath to write to
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param auto_name: Whether to auto-name the file by SIDC in the directory specified by out_filepath, or use out_filepath directly. Defaults to true.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    :param use_variants: Whether to use variant symbol styles. Defaults to false.
    :param style: Style to use, between 'light', 'dark', 'medium', and 'unfilled'
    :param use_background: Whether to use a colored background around the symbol
    :param background_color: Background color to use, if it's used
    """
    write_symbol_svg_string(name_string, False, out_filepath, bounding_padding, auto_name, use_variants=use_variants, style=style, 
        use_background=use_background, background_color=background_color, verbose=verbose, force_all_elements=force_all_elements,
        limit_to_symbol_sets=limit_to_symbol_sets)


def command_line_main():
    # Get current working directory
    style_choices_args = STYLE_CHOICES.copy()
    style_choices_args.extend([i[0] for i in style_choices_args])

    parser = argparse.ArgumentParser(prog='milsymbol', description="Military symbol generator per NATO APP-6D standards, v1.2.2")
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
    parser.add_argument('-b', '--use-background', dest='use_background', action='store_const', const=True, default=False,
                        help='Whether to draw a background halo around the symbol')
    parser.add_argument('-c', '--background-color', dest='background_color', action='store', default='#ffffff',
                        help='Background color to use, if it\'s used')
    parser.add_argument('-d', '--sidc-only', dest='sidc_only', action='store_const', const=True, default=False,
                        help='Whether to only return the SIDC from the name')
    parser.add_argument('-l', '--force-all-elements', dest='force_all_elements', action='store_const', const=True, default=False,
                        help='Whether to force using all elements even if they would overlap in a way that conflicts with the standard')
    parser.add_argument('-m', '--template', dest='template_filename', action='store', default='',
                        help='A template JSON file; see example folder for details')
    parser.add_argument('-e', '--limit-to', dest='limit_to_symbol_sets', action='append', default=[],
                        help='Limits to a specific symbol set for name guessing, like air, ground, surface, etc. Has no effect when using SIDCs. ' + 
                             'Multiple symbol sets to choose from can be specified.')
    parser.add_argument('inputs', nargs='+', default=[])

    arguments = parser.parse_args()

    if arguments.by_name and arguments.verbose:
        print('\tParsing by name; results may not be exact', file=sys.stderr)

    use_auto_name: bool = arguments.auto_name
    if len(arguments.inputs) > 1 and not arguments.auto_name and not arguments.sidc_only:
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

    if arguments.template_filename != '':
        add_symbol_template_set(arguments.template_filename)

    # Handle limiting to symbol sets
    limit_to_symbol_sets = []
    # Add limited symbol sets
    if arguments.verbose:
        print('\tLimiting to symbol sets [' + ', '.join(arguments.limit_to_symbol_sets) + ']')

    for limit in arguments.limit_to_symbol_sets:
        limit_to_symbol_sets.append(limit)
    if len(limit_to_symbol_sets) < 1:
        limit_to_symbol_sets = None


    # Loop through remaining inputs and process t hem
    for input_arg in arguments.inputs:
        if arguments.verbose:
            print(f'\tParsing "{input_arg}": {arguments.verbose}', file=sys.stderr)

        if arguments.by_name:  # Construct from names
            if arguments.sidc_only:
                # Print SIDCs only
                symbol_class = get_symbol_class_from_name(input_arg, verbose=arguments.verbose)
                if symbol_class is None:
                    print(f'No symbol creatable for name \"{input_arg}\"; skipping', file=sys.stderr)
                else:
                    print(f'{input_arg} -> {symbol_class.get_sidc()}' if arguments.verbose else f'{symbol_class.get_sidc()}')

            elif output_dir:
                # Write to an output directory
                write_symbol_svg_string_from_name(input_arg, 
                                                  out_filepath=output_dir, 
                                                  bounding_padding=arguments.padding,
                                                  auto_name=use_auto_name,
                                                  verbose=arguments.verbose,
                                                  use_variants=arguments.use_variants,
                                                  style=style_name,
                                                  use_background=arguments.use_background,
                                                  background_color=arguments.background_color,
                                                  force_all_elements=arguments.force_all_elements,
                                                  limit_to_symbol_sets=limit_to_symbol_sets)
            else:
                # Write SVG strings to stdout
                print(get_symbol_svg_string_from_name(input_arg, 
                                                      bounding_padding=arguments.padding,
                                                      verbose=arguments.verbose,
                                                      use_variants=arguments.use_variants,
                                                      style=style_name,
                                                      use_background=arguments.use_background,
                                                      background_color=arguments.background_color,
                                                      force_all_elements=arguments.force_all_elements,
                                                      limit_to_symbol_sets=limit_to_symbol_sets))
        else:  # Construct from SIDC
            if output_dir != '':
                write_symbol_svg_string_from_sidc(input_arg, 
                                                  out_filepath=output_dir, 
                                                  bounding_padding=arguments.padding,
                                                  auto_name=use_auto_name,
                                                  verbose=arguments.verbose,
                                                  use_variants=arguments.use_variants,
                                                  style=style_name,
                                                  use_background=arguments.use_background,
                                                  background_color=arguments.background_color,
                                                  force_all_elements=arguments.force_all_elements)
            else:
                print(get_symbol_svg_string_from_sidc(input_arg, bounding_padding=arguments.padding,
                                                      verbose=arguments.verbose,
                                                      use_variants=arguments.use_variants,
                                                      style=style_name,
                                                      use_background=arguments.use_background,
                                                      background_color=arguments.background_color,
                                                      force_all_elements=arguments.force_all_elements))

if __name__ == '__main__':
    command_line_main()