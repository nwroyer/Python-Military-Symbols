from symbol_schema import SymbolSchema
from nato_symbol import NATOSymbol
import os
import subprocess
import xml.etree.ElementTree as ET


master_json_location = '/home/nick/Projects/QGIS NATO/QGIS-APP-6D-Renderer-Plugin/NATO symbols.json'

if __name__ == '__main__':
    symbol_schema = SymbolSchema.load_symbol_schema_from_file(master_json_location)

    test_symbol = NATOSymbol(symbol_schema)
    #test_symbol.create_from_sidc('12-34-56-7-8-90-123456-78-90')

    # Status flag then HQTFD flag
    test_symbol.create_from_sidc('10-03-10-0-1-14-121800-01-42')
    # 10041012141211019800
    # test_symbol.create_from_sidc('10-04-01-0-0-14-120000-98-00')

    svg_output = test_symbol.get_svg(fill_type='light')
    # print(svg_output)

    with open(os.path.join('/home/nick/Projects/QGIS NATO', 'test' + '.svg'), 'w') as out_file:
        out_file.write(svg_output)

    filename = test_symbol.get_name() + ' [%s]' % test_symbol.get_sidc()
    filename = filename if len(filename) < 250 else filename[:250]
    print(filename)


    # Export all possible entities
    base_path = '/home/nick/Projects/QGIS NATO/images'

    total_file_count = 0
    # Export to SVGs
    for si in symbol_schema.standard_identities.values():
        si_dir = os.path.join(base_path, si.name.title())
        os.makedirs(si_dir, exist_ok=True)
        

        for sym_set in symbol_schema.symbol_sets.values():
            sym_set_dir = os.path.join(si_dir, sym_set.name.title())
            os.makedirs(sym_set_dir, exist_ok=True)
            os.makedirs(os.path.join(sym_set_dir, 'Modifiers'), exist_ok=True)

            entities = sym_set.get_flat_entities()

            for amp in symbol_schema.amplifiers.values():
                if not amp.applies_to(sym_set.id_code):
                    continue
                os.makedirs(os.path.join(sym_set_dir, 'Amplifiers'), exist_ok=True)

                amp_svg = symbol_schema.get_svg_by_code('A-%s' % amp.id_code, si)
                filename = '%s amplifier - %s (%s).svg' % (sym_set.name.title(), amp.name.title(), amp.id_code)
                filename = filename.replace('/', ' or ').replace('  ', ' ')
                filepath = os.path.join(sym_set_dir, 'Amplifiers', filename)
                if amp_svg is None:
                    continue

                with open(filepath, 'w') as out_file:
                    out_file.write(ET.tostring(amp_svg, encoding='utf8', method='xml').decode('utf-8'))

            modifiers = list(sym_set.modifiers[1].values()) + list(sym_set.modifiers[2].values())

            for mod in modifiers:
                if mod.type == 'nn':
                    continue

                if mod.type == 'ff':
                    pass

                mod_svg = symbol_schema.get_svg_by_code('M-%s-%s-%s' % (sym_set.id_code,
                    mod.modifier_set, mod.id_code), si)
                filename = '%s modifier %s - %s (%s).svg' % (sym_set.name.title(), mod.modifier_set, mod.name.title(), mod.id_code)
                filename = filename.replace('/', ' or ').replace('  ', ' ')
                filepath = os.path.join(sym_set_dir, 'Modifiers', filename)
                if mod_svg is None:
                    continue

                with open(filepath, 'w') as out_file:
                    out_file.write(ET.tostring(mod_svg, encoding='utf8', method='xml').decode('utf-8'))

            for ent in entities:
                if ent.icon_type == 'nn':
                    continue

                new_symbol = NATOSymbol(symbol_schema)
                new_symbol.create_from_sidc('10-0%s-%s-0-0-00-%s-00-00' % (si.id_code, sym_set.id_code, ent.id_code))

                filename = new_symbol.get_name() + ' [%s]' % new_symbol.get_sidc()
                filename = filename if len(filename) < 250 else filename[:250]
                filename = filename.replace('/', ' or ').replace('  ', ' ')
                print(filename)
                total_file_count += 1

                filepath = os.path.join(sym_set_dir, filename + '.svg')
                symbol_svg = new_symbol.get_svg()

                with open(filepath, 'w') as out_file:
                    out_file.write(symbol_svg)

    # Use SVGcleaner to reduce cruft
    # file_count = 0
    # cleaning_processes = []
    # FNULL = open(os.devnull, 'w')

    # for subdir, dirs, files in os.walk(base_path):
    #     for filename in files:
    #         full_filename = os.path.join(subdir, filename)
    #         print('[2: %4i / %4i] Cleaning "%s"' % (file_count, total_file_count, full_filename))
    #         cleaning_processes.append(subprocess.Popen(['svgcleaner', full_filename, full_filename, '--indent', '4',
    #             '--trim-colors', 'no', '--remove-default-attributes', 'no',
    #             '--apply-transform-to-paths', 'yes',
    #             '--join-style-attributes', 'no',
    #             '--group-by-style', 'no'], stdout=FNULL))
    #         file_count += 1

    # exit_codes = [p.wait() for p in cleaning_processes]

    # # Export pngs
    # total_file_count = 0
    # for subdir, dirs, files in os.walk(base_path):
    #     for filename in files:
    #         total_file_count += 1
    # file_count = 0
    # FNULL = open(os.devnull, 'w')

    # inkscape_processes = []
    # for subdir, dirs, files in os.walk(base_path):
    #     for filename in files:
    #         if '.png' in filename:
    #             continue

    #         file_count += 1
    #         full_filename = os.path.join(subdir, filename)
    #         out_filename = full_filename.replace('.svg', '.png')
    #         print('[1: %4i / %4i] Converting "%s" to "%s"' % (file_count, total_file_count, full_filename, out_filename))
    #         inkscape_processes.append(subprocess.Popen(['inkscape', full_filename, '-o', out_filename, 
    #             '--export-type=png', '--export-area-page', '-w', '256', '-h', '256'], stdout=FNULL, stderr=FNULL))


    # exit_codes = [p.wait() for p in inkscape_processes]

