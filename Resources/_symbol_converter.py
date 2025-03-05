"""
Utility script for converting SVGs in Inkscape-ready format to raw SVGs suitable for output
"""

import json
import os, sys
import subprocess
from pathlib import Path

if __name__ == '__main__':
    sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '../src')))
    print(sys.path)

from military_symbol import _json_filesystem

def pack_svgs_into_json(current_working_directory: str, subdir: str = 'symbols', existing_input_file='',
                        output_file=''):
    """
    Packs the SVGs in the symbol directory into a single .json file
    :param current_working_directory: The current working directory
    :param subdir: The subdirectory of the current working directory containing the processed symbol folder
    :param existing_input_file: The location of the input file (to allow for adding symbols); defaults to empty
    :param output_file: The output file; defaults to an empty string.
    """

    symbol_dir = os.path.join(current_working_directory, subdir)
    print(f'Symbol dir: {symbol_dir}')

    total_file_count: int = 0
    json_contents = _json_filesystem.JSONFilesystem()

    for subdir, dirs, files in os.walk(symbol_dir):
        for filename in files:
            if os.path.splitext(filename)[1] != '.svg':
                # Skip non-SVG files
                continue

            file_text = Path(os.path.join(subdir, filename)).read_text()
            file_path_rel = os.path.relpath(os.path.join(subdir, filename), symbol_dir)
            json_contents.set_contents_at_path(file_path_rel, file_text, create_if_nonexistent=True)
            total_file_count += 1

    if output_file != '':
        outfile_existing_dict = {}
        if existing_input_file != '':
            with open(os.path.join(os.path.dirname(__file__), existing_input_file), 'r') as json_file:
                outfile_existing_dict = json.load(json_file)

        outfile_existing_dict['SVGs'] = json_contents.json

        with open(os.path.join(current_working_directory, output_file), 'w') as output_file_obj:
            json.dump(outfile_existing_dict, output_file_obj, indent=True)

    else:
        print(json_contents.get_dump_string())

    print(f'Packed {total_file_count} SVGs into JSON')

    new_json_file = _json_filesystem.JSONFilesystem()
    new_json_file.read_from_file(os.path.join(current_working_directory, output_file))


def convert_inkscape_to_svg(current_working_directory, subdir='', clean_only=False):
    """
    Converts a folder full of Inkscape SVG files into cleaned-up, minimal SVG files suitable for other programs
    and easy processing
    :param current_working_directory: The current working directory containing the folder with the SVG files
    :param subdir: The subdirectory of current_working_directory containing the SVG files
    """

    # Input directory
    svg_directory = os.path.join(current_working_directory, 'svgs')
    if subdir != '':
        svg_directory = os.path.join(svg_directory, subdir)

    # Output directory
    symbol_dir = os.path.join(current_working_directory, 'symbols')
    if subdir != '':
        symbol_dir = os.path.join(symbol_dir, subdir)

    if not clean_only:
        try:
            subprocess.call(['rm', symbol_dir, '-r'])
        except:
            pass

    subprocess.call(['cp', '-r', svg_directory, symbol_dir])

    total_file_count = 0
    for subdir, dirs, files in os.walk(symbol_dir):
        for filename in files:
            total_file_count += 1
    file_count = 0
    f_null = open(os.devnull, 'w')

    # Export from Inkscape to standard svg
    if not clean_only:
        inkscape_processes = []
        for subdir, dirs, files in os.walk(symbol_dir):
            for filename in files:
                file_count += 1
                full_filename = os.path.join(subdir, filename)

                print('[1: %4i / %4i] Exporting "%s"' % (file_count, total_file_count, full_filename))
                inkscape_processes.append(
                    subprocess.run(['inkscape', full_filename, '-o', full_filename, '-i', 'layer1',
                                      '--export-id-only', '--export-plain-svg', '--export-overwrite', '--vacuum-defs',
                                      '--export-text-to-path', '--export-area-page']))
        # exit_codes = [p.wait() for p in inkscape_processes]

    # Use SVGcleaner to reduce cruft
    cleaning_processes = []
    for subdir, dirs, files in os.walk(symbol_dir):
        for filename in files:
            full_filename = os.path.join(subdir, filename)
            print('[2: %4i / %4i] Cleaning "%s"' % (file_count, total_file_count, full_filename))
            cleaning_processes.append(subprocess.Popen(['svgcleaner', full_filename, full_filename, '--indent', '4',
                                                        '--trim-colors', 'no', '--remove-default-attributes', 'no',
                                                        '--apply-transform-to-paths', 'yes',
                                                        '--join-style-attributes', 'no',
                                                        '--group-by-style', 'no'], stdout=f_null))

    exit_codes = [p.wait() for p in cleaning_processes]
    f_null.close()


def main():
    """
    Main function that processes everything
    """

    subdirs = ['Frames', 'Amplifiers', 'HQTFD', 'Statuses'] 

    working_dir = os.path.dirname(os.path.realpath(__file__))
    print(working_dir)
    convert_inkscape_to_svg(os.getcwd(), '', clean_only=True)

    pack_svgs_into_json(working_dir, 'symbols', output_file=os.path.join(working_dir,
                        '../src/military_symbol/symbols.json'),
                        existing_input_file=os.path.join(working_dir, 'Symbol schema.json'))


if __name__ == '__main__':
    main()
