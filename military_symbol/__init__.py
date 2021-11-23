# test
import os
import sys

from military_symbol import name_to_sidc
from military_symbol.individual_symbol import MilitarySymbol
from military_symbol.symbol_schema import SymbolSchema
from military_symbol.symbol_template import SymbolTemplateSet

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


def get_symbol_svg_string_from_sidc(sidc, bounding_padding=4, verbose=False) -> str:
    """
    Constructs an SVG for the specified symbol, given as a SIDC, and returns it as a string for further processing.
    :param sidc: The SIDC to construct the symbol from
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    :return: A string containing the SVG for the constructed symbol.
    """
    symbol: MilitarySymbol = MilitarySymbol(sym_schema).create_from_sidc(sidc, verbose)
    return symbol.get_svg(pixel_padding=bounding_padding) if symbol is not None else ''


def get_symbol_svg_string_from_name(name_string:str, bounding_padding=4, verbose=False) -> str:
    """
    Constructs an SVG and returns it in string form, using the best guess as to the SIDC based on the provided name.
    :param name_string: The string containing the name, i.e. "Friendly infantry platoon headquarters"
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param verbose:  Whether to print ancillary information while processing, defaulting to false.
    :return: A string containing the SVG for the constructed symbol.
    """
    symbol: MilitarySymbol = name_to_sidc.name_to_symbol(name_string, sym_schema, verbose)
    return symbol.get_svg(pixel_padding=bounding_padding) if symbol is not None else ''


def _write_symbol(is_sidc, creator_var, out_filepath, bounding_padding=4, auto_name=True, verbose=False) -> None:
    """
    Internal helper function to write a symbol to the file specified.
    :param is_sidc: Whether the creator_var parameter is a SIDC or a name
    :param creator_var: The string to construct the symbol from, either a SIDC or a name
    :param out_filepath: The filepath to write to
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param auto_name: Whether to auto-name the file by SIDC in the directory specified by out_filepath, or use out_filepath directly. Defaults to true.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    """
    symbol: MilitarySymbol = get_symbol_class_from_sidc(creator_var, verbose) if is_sidc else get_symbol_class_from_name(creator_var, verbose)

    if auto_name:
        out_dir = os.path.dirname(out_filepath) if os.path.isfile(out_filepath) else out_filepath
        out_filepath = os.path.join(out_dir, f"{symbol.get_sidc()}.svg")

    with open(out_filepath, 'w') as out_file:
        out_file.write(symbol.get_svg(pixel_padding=bounding_padding))


def get_symbol_class_from_sidc(sidc, verbose=False) -> individual_symbol.MilitarySymbol:
    """
    Returns an individual_symbol.MilitarySymbol object representing a symbol constructed from the given SIDC
    :param sidc: The SIDC to construct the MilitarySymbol from
    :param verbose: Whether to print ancillary information
    :return: An individual_symbol.MilitarySymbol object
    """
    symbol: MilitarySymbol = MilitarySymbol(sym_schema).create_from_sidc(sidc, verbose)
    return symbol


def get_symbol_class_from_name(name, verbose=False) -> individual_symbol.MilitarySymbol:
    """
    Returns an individual_symbol.MilitarySymbol object representing a symbol constructed from the given name, as a best
    guess
    :param name: The name to construct the MilitarySymbol from using a best-guess algorithm
    :param verbose: Whether to print ancillary information
    :return: An individual_symbol.MilitarySymbol object
    """
    symbol: MilitarySymbol = name_to_sidc.name_to_symbol(name, symbol_schema=sym_schema, verbose=verbose)
    return symbol


def write_symbol_svg_string_from_sidc(sidc, out_filepath, bounding_padding=4, auto_name=True, verbose=False) -> None:
    """
    Internal helper function to write a symbol constructed from the given SIDC to the given filepath.
    :param sidc: The SIDC to construct the symbol from
    :param out_filepath: The filepath to write to
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param auto_name: Whether to auto-name the file by SIDC in the directory specified by out_filepath, or use out_filepath directly. Defaults to true.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    """
    _write_symbol(True, sidc, out_filepath, bounding_padding, auto_name, verbose)


def write_symbol_svg_string_from_name(name_string, out_filepath, bounding_padding=4, auto_name=True, verbose=False) -> None:
    """
    Internal helper function to write a symbol constructed as a best guess from the given name to the given filepath.
    :param name_string: The name to construct the symbol from
    :param out_filepath: The filepath to write to
    :param bounding_padding: The padding around the symbol, in pixels, to maintain when cropping. Values less than 0 will result in no cropping being performed. The default value is 4 pixels.
    :param auto_name: Whether to auto-name the file by SIDC in the directory specified by out_filepath, or use out_filepath directly. Defaults to true.
    :param verbose: Whether to print ancillary information while processing, defaulting to false.
    """
    _write_symbol(False, name_string, out_filepath, bounding_padding, auto_name, verbose)

if __name__ == '__main__':
    # Get current working directory

    module_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep

    add_symbol_template_set(os.path.join(module_dir, '../Examples/example_template.json'))

    test_lines = [
        "friendly airborne infantry platoon headquarters",
        "HIMARS battery",
        "suspected enemy airborne PSYOP company",
        "friendly VTOL rotary-wing squadron",
        "friendly Javelin",
        "neutral civilian pickup truck",
        "T-82"
    ]

    out_dir = os.path.join(os.getcwd(), '../Examples')

    for symbol_name in test_lines:
        write_symbol_svg_string_from_name(symbol_name, out_dir)
