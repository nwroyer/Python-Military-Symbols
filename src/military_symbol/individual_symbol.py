

import os
import sys

import svgpathtools

from ._svg_tools import *


class MilitarySymbol:
    """
    A class representing a given NATO symbol
    """
    def __init__(self, symbol_schema):
        if symbol_schema is None:
            print('ERROR: symbol schema must not be None for NATO symbol creation', file=sys.stderr)

        self.version_code = '10'
        self.symbol_schema = symbol_schema

        # SIDC component codes
        self.context = None
        self.standard_identity = None
        self.symbol_set = None
        self.status = None
        self.hqtfd = None
        self.entity = None

        self.amplifier = None
        self.modifiers = {1: None, 2: None}

        self.extra_ten_digits = ''  # Ignored for the purposes of this application

    def get_sidc(self) -> str:
        """
        Returns the SIDC of the symbol.
        :return: A string containing the SICC of the symbol
        """
        return ''.join([
            self.version_code,
            self.context.id_code if self.context is not None else '0',
            self.standard_identity.id_code if self.standard_identity is not None else '0',
            self.symbol_set.id_code if self.symbol_set is not None else '00',
            self.status.id_code if self.status is not None else '0',
            self.hqtfd.id_code if self.hqtfd is not None else '0',
            self.amplifier.id_code if self.amplifier is not None else '00',
            self.entity.id_code if self.entity is not None else '000000',
            self.modifiers[1].id_code if self.modifiers[1] is not None else '00',
            self.modifiers[2].id_code if self.modifiers[2] is not None else '00'
        ])

    def get_name(self):
        """
        Returns the name of the symbol in the format "[symbol set] - [standard identity]
        [mod1] [mod2] [entity] [amplifier] ([HQTFD])"
        :return:
        """
        ret = ''
        ret += self.symbol_set.name.capitalize() + ' - ' if self.symbol_set is not None else ''
        ret += self.standard_identity.name + ' ' if self.standard_identity is not None else ''
        ret += self.modifiers[1].name + ' ' if self.modifiers[1] is not None else ''
        ret += self.modifiers[2].name + ' ' if self.modifiers[2] is not None else ''
        ret += self.entity.name + ' ' if self.entity is not None else ''
        ret += self.amplifier.names[0] + ' ' if self.amplifier is not None else ''
        ret += '(%s) ' % self.hqtfd.names[0] if self.hqtfd is not None else ''

        ret = ret.replace('/', ' or ')

        return ret.strip()

    def create_from_sidc(self, sidc_raw, verbose=False):
        """
        Initializes the SIC from the given symbol
        :param sidc_raw: The string containing the SIDC to initialize from
        :param verbose: Whether to print ancillary information
        :return: Whether initialization was successful
        """
        # Strip all non-digit characters
        sidc = ''.join(c for c in sidc_raw if c.isnumeric())
        if len(sidc) < 20:
            print('SIDCs must be at least 20 digits', file=sys.stderr)
            return None
        elif len(sidc) > 20:
            if len(sidc) >= 30:
                self.extra_ten_digits = sidc[20:30]
            print('Ignoring extra digits from SIDC; only using first 20')

        # TODO handle special entity subtypes

        # Sanity check SIDC code
        self.version_code = sidc[0:2]
        if int(self.version_code) > int(self.symbol_schema.version):
            print('This SIDC is for an APP-6 standard greater than this program is intended for;" + \
                  output may be unexpected',
                  file=sys.stderr)

        # Load symbol components - necessary (non-default)
        context_code = sidc[2]
        if context_code not in self.symbol_schema.contexts.keys():
            print('Context "%s" not recognized; aborting' % context_code, file=sys.stderr)
            return None
        self.context = self.symbol_schema.contexts[context_code]

        symbol_set_code = sidc[4:6]
        if symbol_set_code not in self.symbol_schema.symbol_sets.keys():
            print('Symbol set "%s" not recognized; aborting' % symbol_set_code, file=sys.stderr)
            return None
        self.symbol_set = self.symbol_schema.symbol_sets[symbol_set_code]

        standard_identity_code = sidc[3]
        if standard_identity_code not in self.symbol_schema.standard_identities.keys():
            print('SI %s not recognized; defaulting to 0' % standard_identity_code, file=sys.stderr)
            self.standard_identity = None
        self.standard_identity = self.symbol_schema.standard_identities[standard_identity_code]

        status_code = sidc[6]
        if status_code == '0':
            self.status = None
        elif status_code not in self.symbol_schema.statuses.keys():
            print("Status %s not recognized; defaulting to 0" % status_code, file=sys.stderr)
            self.status = None
        else:
            self.status = self.symbol_schema.statuses[status_code]

        hqtfd_code = sidc[7]
        if hqtfd_code == '0':
            self.hqtfd = None
        elif hqtfd_code not in self.symbol_schema.hqtfd_codes.keys():
            print("HQTFD code %s not recognized; defaulting to 0" % hqtfd_code, file=sys.stderr)
            self.hqtfd = None
        else:
            new_hqtfd = self.symbol_schema.hqtfd_codes[hqtfd_code]
            if new_hqtfd.applies_to_symbol_set(self.symbol_set):
                self.hqtfd = new_hqtfd
            else:
                print('HQTFD code "%s" doesn\'t apply to symbol set %s; ignoring' %
                      (hqtfd_code, self.symbol_set.id_code))
                self.hqtfd = None

        amplifier_code = sidc[8:10]
        if amplifier_code == '00':
            self.amplifier = None
        elif amplifier_code not in self.symbol_schema.amplifiers:
            print('Amplifier "%s" not recognized; defaulting to 00' % amplifier_code, file=sys.stderr)
            self.amplifier = None

        # Check that amplifier applies to symbol set
        elif not self.symbol_schema.amplifiers[amplifier_code].applies_to(symbol_set_code):
            print('Amplifier "%s" doesn\'t apply to symbol set "%s"; defaulting to 0' %
                  (amplifier_code, symbol_set_code))
            self.amplifier = None
        else:
            self.amplifier = self.symbol_schema.amplifiers[amplifier_code]

        entity_id_code = sidc[10:16]
        test_entity = self.symbol_schema.get_entity(symbol_set_code, entity_id_code)
        if test_entity is None:
            print('Entity "%s" does not exist in symbol set "%s"; defaulting to 000000' %
                  (entity_id_code, symbol_set_code), file=sys.stderr)
            self.entity = None
        else:
            self.entity = test_entity

        modifier_codes = {
            1: sidc[16:18],
            2: sidc[18:20]
        }

        for mod_set in [1, 2]:
            if modifier_codes[mod_set] == '00':
                continue

            test_mod = modifier_codes[mod_set]
            new_mod = self.symbol_schema.get_modifier(symbol_set_code, mod_set, test_mod)
            if self.entity is None:
                self.modifiers[mod_set] = None
            if new_mod is None:
                print('Modifier "%s" not recognized in %s-%s' % (test_mod, self.symbol_set.id_code, mod_set))
                self.modifiers[mod_set] = None
            else:
                self.modifiers[mod_set] = new_mod

        # Sanity check complete; pointers to all the relevant information have been loaded in
        return self

    def uses_civilian_coloring(self):
        if self.entity.uses_civilian_coloring:
            return True
        for mod in [mod for mod in self.modifiers.values() if mod is not None]:
            if mod.has_civilian_coloring_override and mod.civilian_coloring_override_value:
                return True
        return False

    def get_svg(self, style='light', pixel_padding=-1, use_variants=False):
        """
        Gets an SVG as a string representing this object
        :param style: Can be "light" (default), "medium", "dark", or 'unfilled'
        :param pixel_padding: The padding around the symbol to use when cropping to fit. Values less than 0 will lead to no cropping. Defaults to -1.
        :param use_variants: Whether to use the variant type of symbol element if they exist (primarily for statuses and sea mine symbols).
        :return: A string containing the SVG of the object
        """

        # Sanity check fill type
        style_name = style
        if style_name not in ['light', 'medium', 'dark', 'unfilled']:
            style_name = 'light'

        # Start with base frame
        sym_root = self.symbol_schema.symbol_root_folder

        frame_svg_filename = self.symbol_schema.get_svg_filename_by_code('F-%s' % self.symbol_set.frame_set, self.standard_identity)
        symbol_svg = self.symbol_schema.get_svg_by_filename(frame_svg_filename)

        # Apply dashed outline to frame if appropriate
        uses_dashed_frame = self.standard_identity.uses_dashed_frame or \
                            (self.status is not None and self.status.makes_frame_dashed)
        if uses_dashed_frame:
            make_all_strokes_dashed(symbol_svg, unfilled=(style_name == 'unfilled'))

        if self.entity is None:
            fill_color_set = self.standard_identity.standard_colorset
        else:
            fill_color_set = self.standard_identity.civilian_colorset if self.uses_civilian_coloring() else \
                self.standard_identity.standard_colorset

        fill_color = fill_color_set[style_name]

        # Remove fill if unfilled
        if style_name == 'unfilled':
            make_unfilled(symbol_svg, fill_color)
        else:
            replace_color(symbol_svg, self.symbol_schema.symbol_fill_placeholder, fill_color)

        # def get_entity_icon_name(base_folder, entity, standard_identity):
        #     if entity.icon_type == 'ff':
        #         return os.path.join(base_folder, entity.id_code + '-' + standard_identity.frame_set + '.svg')
        #     else:
        #         return os.path.join(base_folder, entity.id_code + '.svg')

        # Add entity icon
        if self.entity is not None and self.symbol_set is not None:
            # symbol_sets_folder = os.path.join(sym_root, self.symbol_schema.symbol_folders["symbol sets"],
            #                                   self.symbol_set.id_code,
            #                                   self.symbol_schema.symbol_folders['within symbol set']['entities'])
            overlay_svgs = []
            if self.entity.is_overlay() and self.entity.icon_type:
                # print(self.entity.overlay_elements)
                for overlay_code in self.entity.overlay_elements:
                    # print(overlay_code)

                    overlay_svgs.append(self.symbol_schema.get_svg_by_code('E-%s' % overlay_code,
                                        self.standard_identity))

            else:
                # print(get_entity_icon_name(symbol_sets_folder, self.entity, self.standard_identity))
                overlay_svgs.append(self.symbol_schema.get_svg_by_code('E-%s-%s' % (self.symbol_set.id_code,
                                                                                    self.entity.id_code),
                                                                       self.standard_identity))

            # print('Overlay: %s' % str(overlay_svgs))
            for overlay in overlay_svgs:
                if overlay is None:
                    print('ERROR: Null value overlay')
                    continue
                if style_name == 'unfilled':
                    make_unfilled(overlay, fill_color)

                # print(f'Overlay: {xml.etree.ElementTree.tostring(overlay)}')
                layer_svg(symbol_svg, overlay)

        # Adding entity done; add amplifiers
        if self.amplifier is not None and self.symbol_set is not None and \
                self.amplifier.applies_to(self.symbol_set.id_code):

            amplifier_svg = self.symbol_schema.get_svg_by_code('A-%s' % self.amplifier.id_code, self.standard_identity)
            if style_name == 'unfilled':
                make_unfilled(amplifier_svg, fill_color)
            layer_svg(symbol_svg, amplifier_svg)

        # Add HQ/TF/Dummy indicator
        if self.hqtfd is not None:
            overlays = []
            if self.hqtfd.is_overlay():
                overlays = self.hqtfd.overlay_elements
            else:
                overlays.append(self.hqtfd.id_code)

            # print('Overlay for HQTFD on {}: {}, amplifier'.format(self.get_name(), overlays))

            for overlay_code in overlays:
                overlay_svg = self.symbol_schema.get_svg_by_code('H-%s%s' % (
                    overlay_code,
                    '-%s' % self.amplifier.id_code if self.amplifier is not None else '-11'
                ), self.standard_identity)

                offset = self.symbol_schema.hqtfd_codes[overlay_code].get_offset(self.standard_identity.frame_set)
                # print(offset)
                apply_offset(overlay_svg, offset, True)
                if style_name == 'unfilled':
                    make_unfilled(overlay_svg, fill_color)
                layer_svg(symbol_svg, overlay_svg)

        # Add modifiers
        if self.entity is not None and self.entity.icon_type != 'fo' or self.entity is None:
            overlay_svgs = []

            for mod_i in [1, 2]:
                if self.modifiers[mod_i] is not None:
                    modifier = self.modifiers[mod_i]
                    # print(modifier.name)

                    if modifier.is_overlay():
                        for ele in modifier.overlay_elements:
                            overlay_svgs.append(
                                self.symbol_schema.get_svg_by_code('M-%s' % ele, self.standard_identity)
                            )
                    else:
                        overlay_svgs.append(
                            self.symbol_schema.get_svg_by_code('M-%s-%i-%s' % (self.symbol_set.id_code, mod_i,
                                                                               modifier.id_code),
                                                               self.standard_identity)
                        )

            # Add modifiers to SVG
            for mod_svg in overlay_svgs:
                if mod_svg is None:
                    continue
                if style_name == 'unfilled':
                    make_unfilled(mod_svg, fill_color)
                layer_svg(symbol_svg, mod_svg)

        if self.status is not None and (not use_variants or (use_variants and len(self.status.variants) > 0 and self.status.variants[0] != 'nn')):
            overlays = [self.status.id_code]

            for overlay_code in overlays:
                overlay_svg = self.symbol_schema.get_svg_by_code(f'S-{overlay_code}', self.standard_identity,
                                                                 use_variants=use_variants)
                if overlay_svg is None:
                    print(f"Error applying status overlay {overlay_code} -> {self.symbol_schema.get_svg_filename_by_code(f'S-{overlay_code}', self.standard_identity)}")
                    continue
                if style_name == 'unfilled':
                    make_unfilled(overlay_svg, fill_color)
                layer_svg(symbol_svg, overlay_svg)

        ET.register_namespace('', 'http://www.w3.org/2000/svg')

        svg_string = ET.tostring(symbol_svg, encoding='utf8', method='xml').decode('utf-8')

        old_viewbox = [float(s) for s in symbol_svg.attrib['viewBox'].split()]
        # old_center = [old_viewbox[0] + old_viewbox[2]*0.5, old_viewbox[1] + old_viewbox[3] * 0.5]

        if pixel_padding >= 0:
            # Expand the bounding box to fit if that option is selected
            svg_tmp_name = os.path.join(os.getcwd(), 'svg.tmp')
            with open(svg_tmp_name, 'w') as svg_tmp:
                svg_tmp.write(svg_string)

            paths, attributes = svgpathtools.svg2paths(svg_tmp_name)

            bbox = [float('inf'), -float('inf'), float('inf'), -float('inf')]
            for path in paths:
                bb = path.bbox()
                for i in [0, 2]:
                    if bb[i] < bbox[i]:
                        bbox[i] = bb[i]
                for i in [1, 3]:
                    if bb[i] > bbox[i]:
                        bbox[i] = bb[i]

            os.remove(svg_tmp_name)

            scaling = [float(symbol_svg.attrib['width']) / old_viewbox[2],
                       float(symbol_svg.attrib['height']) / old_viewbox[3]]

            new_viewbox = [bbox[0] - (pixel_padding / scaling[0]),
                           bbox[2] - (pixel_padding / scaling[1]),
                           (bbox[1] - bbox[0]) + (pixel_padding*2 / scaling[0]),
                           (bbox[3] - bbox[2]) + (pixel_padding*2 / scaling[1])
                           ]

            new_image_size = [scaling[0] * new_viewbox[2], scaling[1] * new_viewbox[3]]
        else:
            new_image_size = [float(symbol_svg.attrib['width']) + pixel_padding*2,
                              float(symbol_svg.attrib['height']) + pixel_padding*2]
            new_viewbox = old_viewbox

        new_center = [new_viewbox[0] + new_viewbox[2] * 0.5, new_viewbox[1] + new_viewbox[3] * 0.5]

        if pixel_padding >= 0:
            symbol_svg.attrib["width"] = str(int(new_image_size[0]))
            symbol_svg.attrib["height"] = str(int(new_image_size[1]))
            symbol_svg.attrib["viewBox"] = ' '.join(str(i) for i in new_viewbox)

        svg_string = ET.tostring(symbol_svg, encoding='utf8', method='xml').decode('utf-8')

        return svg_string