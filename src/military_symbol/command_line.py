import argparse
import os
import os.path
import sys

from .__init__ import *

STYLE_CHOICES = ['light', 'medium', 'dark', 'unfilled']

def main():
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
    main()