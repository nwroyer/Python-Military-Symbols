import copy
import re
import xml.etree.ElementTree as ET


def get_svg_string(svg_name, verbose=False):
    """
    Helper function returning an SVG string from the given file
    :param svg_name: The filename to search in
    :param verbose: Whether to print ancillar information
    :return: The contents of the SVG file, or an empty string if none are found.
    """
    try:
        with open(svg_name, 'r') as input_file:
            raw_string_data = input_file.read()

            if verbose:
                print(f'Loading "{svg_name}"')

            return raw_string_data
    except:
        print(f'Error: No file "{svg_name}" found')
        return ''
        None
        ''


def read_string_into_etree(raw_string_data):
    """
    Reads a string into an XML Etree object
    :param raw_string_data: String data to read in
    :return: An xml.etree.ElementTree object
    """
    if raw_string_data is None:
        return None
    return ET.fromstring(raw_string_data)


def make_all_strokes_dashed(svg, unfilled=False):
    """
    Makes all strokes in the SVG dashed
    :param svg: The SVG, in xml.etree.ElementTree format
    :param unfilled: Whether this is an unfilled symbol
    :return: The resulting SVG
    """
    stroke_elements = [ele for ele in svg.findall('.//*[@stroke]') if ele.attrib['stroke'] != 'none']

    if not unfilled:
        stroke_elements_with_dash = [copy.deepcopy(ele) for ele in stroke_elements]

        for ele in stroke_elements:
            ele.attrib['stroke'] = '#ffffff'
        for ele in stroke_elements_with_dash:
            ele.attrib['stroke-dasharray'] = '2 2'

        svg.extend(stroke_elements_with_dash)
    else:
        for ele in stroke_elements:
            ele.attrib['stroke-dasharray'] = '2 2'

    return svg


def make_unfilled(svg, color):
    """
    Turn this SVG into an unfilled symbol
    :param svg: The SVG, in xml.etree.ElementTree format
    :param color: The color to turn all elements to
    :return: The resulting SVG
    """
    stroke_elements = [ele for ele in svg.findall('.//*[@stroke]') if ele.attrib['stroke'] != 'none']
    for ele in stroke_elements:
        ele.attrib['stroke'] = color

    for fill_ele in [ele for ele in svg.findall('.//*[@fill]') if ele.attrib['fill'] != 'none']:
        if fill_ele.attrib['fill'] in ['#000000', '#000']:
            # Element is black; make it the unfilled color
            fill_ele.attrib['fill'] = color
        elif 'stroke' in fill_ele.attrib.keys() and fill_ele.attrib['stroke'] != 'none':
            # Element has a stroke; just set the fill to none
            fill_ele.attrib['fill'] = 'none'
        else:
            # Remove the element entirely
            fill_ele.attrib['fill'] = 'none'

    # Replace default-colored items
    for ele in [ele for ele in svg.findall('.//*') if 'fill' not in ele.attrib.keys()]:
        ele.attrib['fill'] = color

    return svg


def replace_color(svg, from_color, to_color, type='both'):
    """
    Replaces the colors in an SVG
    :param svg: The SVG as an ETree to swap the colors in
    :param from_color: the color to be replaced
    :param to_color: The color to change to
    :param type: Can be "fill", "stroke", or "both"
    :return:
    """

    for element_type in ['fill', 'stroke']:
        if type == element_type or type == 'both':
            replace_elements = [ele for ele in svg.findall('.//*[@%s]' % element_type) \
                                if ele.attrib[element_type] == from_color]
            for ele in replace_elements:
                ele.attrib[element_type] = to_color


def apply_offset(svg_ele, offset, offset_children=True):
    """
    Offsets the specified SVG object by the given offset
    :param svg_ele: The element to offset, in xml.etree.ElementTree form
    :param offset: Offset in [x, y] format
    :param offset_children: Whether to offset the element's children as well
    :return: The resulting SVG
    """
    if svg_ele is None:
        return

    if 'd' in svg_ele.keys():
        path = svg_ele.attrib['d']
        # Identify 'm' attribute
        # print(ET.tostring(svg_ele))

        m_search = re.search('m{1}(-*[\d]*.[\d]+)[\s]*(-*[\d]*.[\d]+)', path)
        if m_search is None:
            return 

        start_of_path = ''.join([c for c in m_search[0] if c not in ['m', 'M']])
        rest_of_path = path[m_search.span()[1]:]
        # print(m_search[0], ' | ', m_search[1], ' | ', m_search[2])
        start_coordinates = [float(m_search[1]), float(m_search[2])]
        finished_coordinates = [start_coordinates[i] + offset[i] for i in [0, 1]]

        # print('!---!')
        # print('m')
        # print(start_of_path)
        # print(rest_of_path)
        # print(finished_coordinates)
        # print('!---!')
        new_path = 'm%.7f %.7f %s' % (finished_coordinates[0], finished_coordinates[1], rest_of_path)
        # print('<path>')
        # print('\t<op>%s</op>' % path)
        # print('\t<np>%s</np>' % new_path)
        svg_ele.attrib['d'] = new_path


    if offset_children:
        for child in list(svg_ele):
            apply_offset(child, offset, offset_children=True)
    # Done


def layer_svg(svg_bottom, svg_top, offset: list = [0.0, 0.0]):
    """
    Adds one SVG over another. Modifies the bottom SVG in place.
    :param svg_bottom: The bottom SVG, in in xml.etree.ElementTree form
    :param svg_top: The top SVG, in in xml.etree.ElementTree form
    :param offset: How far to offset the top SVG elements
    """
    if svg_top is None:
        return
    # print(svg_top.tag)
    for child in list(svg_top):
        apply_offset(child, offset, offset_children=True)
        svg_bottom.append(child)
    pass
