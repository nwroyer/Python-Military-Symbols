# Utility script for converting SVGs in Inkscape-ready format to raw SVGs suitable for output

import os
import subprocess
from pathlib import Path

from json_filesystem import JSONFilesystem


def pack_svgs_into_json(current_working_directory:str, subdir:str = 'symbols', output_file=''):
	symbol_dir = os.path.join(current_working_directory, subdir)

	total_file_count:int = 0
	json_contents = JSONFilesystem()

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
		json_contents.dump_to_file(os.path.join(current_working_directory, output_file))
	else:
		print(json_contents.get_dump_string())

	print(f'Packing {total_file_count} SVGs into JSON')


def convert_inkscape_to_svg(current_working_directory, subdir = ''):
	clean_only = False

	svg_directory = os.path.join(current_working_directory, 'svgs')
	if subdir != '':
		svg_directory = os.path.join(svg_directory, subdir)
	symbol_dir = os.path.join(current_working_directory, 'symbols')
	if subdir != '':
		symbol_dir = os.path.join(symbol_dir, subdir)

	if not clean_only:
		try:
			subprocess.call(['rm', symbol_dir, '-r'])
		except:
			pass

	subprocess.call(['cp', '-r', svg_directory, symbol_dir])
	# export_file('/home/nick/Projects/QGIS NATO/Test converter.svg', '/home/nick/Projects/QGIS NATO/Test-processed.svg')

	total_file_count = 0
	for subdir, dirs, files in os.walk(symbol_dir):
		for filename in files:
			total_file_count += 1
	file_count = 0
	FNULL = open(os.devnull, 'w')

	# # Export from Inkscape to standard svg

	if not clean_only:
		inkscape_processes = []
		for subdir, dirs, files in os.walk(symbol_dir):
			for filename in files:
				file_count += 1
				full_filename = os.path.join(subdir, filename)
				print('[1: %4i / %4i] Exporting "%s"' % (file_count, total_file_count, full_filename))
				inkscape_processes.append(
					subprocess.Popen(['inkscape', full_filename, '-o', full_filename, '-i', 'layer1',
									  '--export-id-only', '--export-plain-svg', '--export-overwrite', '--vacuum-defs',
									  '--export-text-to-path', '--export-area-page'], stdout=FNULL, stderr=FNULL))
		exit_codes = [p.wait() for p in inkscape_processes]

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
														'--group-by-style', 'no'], stdout=FNULL))

	exit_codes = [p.wait() for p in cleaning_processes]
	FNULL.close()


def main():
	# convert_inkscape_to_svg(os.getcwd(), '')
	pack_svgs_into_json(os.getcwd(), 'symbols', 'symbols.json')


if __name__ == '__main__':
	main()