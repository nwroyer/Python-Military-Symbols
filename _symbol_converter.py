# Utility script for converting SVGs in Inkscape-ready format to raw SVGs suitable for output

import os
import subprocess
import shutil

def main():
	current_working_directory = os.getcwd()

	clean_only = False
	subdir = 'HQTFD'

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
				inkscape_processes.append(subprocess.Popen(['inkscape', full_filename, '-o', full_filename, '-i', 'layer1',
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

if __name__ == '__main__':
	main()