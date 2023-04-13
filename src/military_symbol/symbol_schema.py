import json
import os

from ._json_filesystem import JSONFilesystem
from ._svg_tools import *


class SymbolSchema:
    """
    Class representing the symbol schema to use, defining all possible values and permissible relations between them
    """

    class StandardIdentity:
        """
        A class defining a standard identity per the NATO APP-6D standard.
        """
        class Context:
            def __init__(self):
                self.name = ''
                self.id_code = 0

        def get_names(self):
            """
            Returns a list containing all names, including alternates, of the standard identity.
            """
            ret = [self.name]
            ret.extend(self.alt_names)
            return ret

        def __init__(self):  # Init for StandardIdentity class
            self.name = 'undefined'
            self.alt_names = []
            self.id_code = 0
            self.frame_set = 0

            self.standard_colorset = {
                'light': '#ffffff',
                'medium': '#ffffff',
                'dark': '#ffffff',
                'unfilled': '#000000'
            }
            self.civilian_colorset = {
                'light': '#ffffff',
                'medium': '#ffffff',
                'dark': '#ffffff',
                'unfilled': '#000000'
            }

        def __str__(self):
            ret = '#%s (%s)%s [%s]' % (self.id_code,
                                       self.name + ('/' + '/'.join(self.alt_names) if len(self.alt_names) > 0 else ''),
                                       '+c' if self.standard_colorset != self.civilian_colorset else '',
                                       self.frame_set)

            ret += ' - colors %s' % self.standard_colorset
            ret += ' - civ colors %s' % self.civilian_colorset
            return ret

        def __repr__(self):
            return str(self)

    class Status:
        """
        A class representing a status, per the NATO APP-6D standard
        """
        def __init__(self):
            self.names = []
            self.id_code = 0
            self.applies_to_all = True
            self.applies_to_list = []
            self.makes_frame_dashed = False
            self.variants = []

        def __str__(self):
            return '#%i (%s) - applies to %s' % (self.id_code, self.names[0],
                                                 'all' if self.applies_to_all else str(self.applies_to_list))

    class HQTFDCode:
        """
        A class representing the headquarters, task force, or dummy indicator, per the NATO APP-6D standard. Note that
        this only applies to symbol set 10 (land units).
        """
        def __init__(self):
            self.names = []
            self.id_code = 0
            self.overlay_elements = []
            self.offsets = {}
            self.applies_to_symbol_sets = []

        def is_overlay(self):
            return len(self.overlay_elements) > 0

        def get_offset(self, frame_set):
            """
            Returns an [x, y] pair indicating the offset for the symbols to apply, indexed by standard identity
            :param frame_set: The frame set to consider when offsetting
            :return: An [x, y] list indicating the offset
            """
            if frame_set not in self.offsets.keys():
                return [0, 0]
            else:
                return self.offsets[frame_set]

        def applies_to_symbol_set(self, symbol_set):
            """
            Indicates whether this HQTFD code applies to a particular symbol set.
            :param symbol_set: The symbol set to check against
            :return: True if the HQTFD code applies to the symbol set, false otherwise.
            """
            if symbol_set is None:
                return False
            return symbol_set.id_code in self.applies_to_symbol_sets

        def __str__(self):
            ret = '#%i (%s)' % (self.id_code, self.names[0])
            if self.is_overlay():
                ret += ' - composition of %s' % self.overlay_elements
            if len(self.offsets) > 0:
                ret += ' / offsets from default symbol %s' % str(self.offsets)
            return ret

    class Amplifier:
        """
        A class representing an amplifier, per the NATO APP-6D standard.
        """
        def __init__(self):
            self.id_code = 0
            self.names = ['']
            self.match_weight = 0
            self.applies_to_list = []
            self.category = ''

        def applies_to(self, symbol_set_code):
            """
            Indicates whether an amplifier can apply to entities in the given symbol set.
            :param symbol_set_code: The symbol set to check against in two-digit string form
            :return: True if the amplifier can apply to the given symbol set, false otherwise
            """
            return True if symbol_set_code in self.applies_to_list else False

        def __str__(self):
            return '#%s (%s) - applies to %s / category "%s"' % (self.id_code, self.names, self.applies_to_list,
                                                                 self.category)

    class SymbolSet:
        """
        Class representing a symbol set per the NATO APP-6D standard, including entities and modifiers
        """

        class Entity:
            """
            Class representing an entity, per the NATO APP-6D standard, belonging to a specific symbol set
            """
            def __init__(self):
                self.id_code = "000000"
                self.symbol_set = '00'
                self.name = ''
                self.notes = ''
                self.short_subtype_name = ''
                # Type can be 'mn' for 'main', 'ff for 'full frame', 'fo' 'full octagon', or 'm1/m2'
                # for 'main + 1', or 'main + 2', or 'nn' if none (only for hierarchical purposes)
                self.icon_type = 'mn'
                self.overlay_elements = []
                self.children = {}
                self.parent = ''
                self.is_special_entity_subtype = False
                self.modifier_categories = []
                self.uses_civilian_coloring = False
                self.local_only = False
                self.use_with_unfilled_frames = False
                self.variants = 0
                self.alt_names = []
                self.match_weight = 0

            def get_names(self) -> list:
                """
                Returns a list of names for the given entity, including alternate ones
                :return: List of names
                """
                ret = [self.name]
                ret.extend(self.alt_names)
                return ret

            def get_flat_entities(self):
                """
                Returns a flat list containing this entity and all its sub-entities and sub-sub-entities, as applicable.
                :return: List containing entity and descendants
                """
                ret = [self]
                for child in self.children.values():
                    ret = ret + child.get_flat_entities()
                return ret

            def is_overlay(self):
                """
                Indicates whether this entity's symbol is an overlay of existing elements or not.
                :return: True if this entity is an overlay, false otherwise
                """
                return len(self.overlay_elements) > 0

            def __str__(self):
                ret = '%s-%s%s%s (%s) [%s%s]' % (self.symbol_set, self.id_code,
                                                 'c' if self.uses_civilian_coloring else '',
                                                 'L' if self.local_only else '',
                                                 self.name,
                                                 self.icon_type,
                                                 "/UF" if self.use_with_unfilled_frames else '')
                if self.is_overlay():
                    ret += ' (overlay of %s)' % str(self.overlay_elements)
                if len(self.children) > 0:
                    ret += '*'
                if self.variants > 0:
                    ret += ' (+%i variant%s)' % (self.variants, 's' if self.variants > 1 else '')
                if len(self.modifier_categories) > 0:
                    ret += ' / modcats %s' % self.modifier_categories

                return ret

            def print(self, tab_stops='', max_depth_level=2):
                """
                Recursive helper function to print out an entity structure in a human-readable format for debugging.
                :param tab_stops: Current tab stops, defaulting to ''.
                :param max_depth_level: Max depth level to print to
                :return:
                """
                if max_depth_level < 1:
                    return
                print(tab_stops + str(self))
                for child in self.children.values():
                    child.print(tab_stops + '\t', max_depth_level - 1)

            def get_child(self, id_code):
                """
                Returns the child of the given entity with the specified code
                :param id_code: Two-digit ID code for entity's child to check for
                :return: The child entity, or None if it's not found
                """
                if id_code in self.children.keys():
                    return self.children[id_code]
                for child_key, child_value in self.children.items():
                    test_val = child_value.get_child(id_code)
                    if test_val is not None:
                        return test_val
                return None

        class Modifier:
            """
            Class representing a modifier in a symbol set, per the NATO APP-6D standard.
            """
            def __init__(self):
                self.modifier_set = 0  # Whether this is part of modifier set 1 or 2, per APP-6D standard
                self.name = ''
                self.symbol_set = '00'
                self.id_code = '00'
                self.mod_category = ''
                self.has_civilian_coloring_override = False  # Whether this modifier applies an automatic override that renders an entity with a civilian coloration
                self.civilian_coloring_override_value = False  # The actual value to override with
                self.alt_names = []
                self.type = "mn"  # Types: mn = main icon, ff = full frame, nn = no icon, fo = full octagon
                self.overlay_elements = []
                self.match_weight = 0

            def is_overlay(self):
                return len(self.overlay_elements) > 0

            def __str__(self):
                ret = '%s-%i-%s (%s) %s' % (self.symbol_set, self.modifier_set, self.id_code, self.name,
                                            '[%s]' % self.type if self.type != 'mn' else '')
                if self.mod_category != '':
                    ret += ' [%s]' % self.mod_category
                if self.is_overlay():
                    ret += ' (overlay of %s)' % str(self.overlay_elements)
                if self.has_civilian_coloring_override:
                    ret += ' - CCO to %s' % ('military' if not self.civilian_coloring_override_value
                                             else 'civilian')
                return ret

        def __init__(self):
            self.id_code = '00'
            self.name = ''
            self.notes = ''
            self.implemented = False
            self.uses_civilian_coloring = False
            self.entities = {}
            self.special_entity_subtypes = {}
            self.modifiers = {1: {}, 2: {}}
            self.frame_set = ''
            self.match_weight = 0

        def __str__(self):
            ret = '#%s (%s) [%s] %s' % (self.id_code, self.name, self.frame_set,
                                        '(not yet implemented)' if not self.implemented else '')
            return ret

        def print(self, tab_stops='', max_depth_level=2):
            """
            Recursive helper function to print modifiers in human-readable form to aid debugging
            :param tab_stops: The current tab stops, defaulting to ''
            :param max_depth_level: Max depth level to recurse to
            :return:
            """
            if max_depth_level < 1:
                return
            print(tab_stops + str(self))
            for ent in self.entities.values():
                ent.print(tab_stops + '\t', max_depth_level - 1)
            for key, ent in self.special_entity_subtypes.items():
                print(tab_stops + '\tSES {%s}: %s' % (key, ent))
            for mod_num in [1, 2]:
                if len(self.modifiers[mod_num]) < 1:
                    continue
                print(tab_stops + '\tModifier set %i' % mod_num)
                for mod_id, mod in self.modifiers[mod_num].items():
                    print(tab_stops + '\t\t' + str(mod))

        def get_entity_internal(self, id_code):
            """
            Returns the entity in the symbol set with the given ID code
            :param id_code: ID code to search for
            :return:
            """
            if id_code in self.entities.keys():
                return self.entities[id_code]
            for ent_key, ent_val in self.entities.items():
                test_val = ent_val.get_child(id_code)
                if test_val is not None:
                    return test_val

            return None

        def get_entity(self, id_code, frame_type=0):
            """
            Returns an entity with the given frame type
            :param id_code: Type to search for
            :param frame_type: Frame type to use
            :return:
            """
            test_val = self.get_entity_internal(id_code)
            if test_val is not None:
                return test_val

            # Still no entity; check for a 0X
            if frame_type != 0:
                return self.get_entity_internal('%s-%s' % (id_code, frame_type))

            return None

        def get_flat_entities(self):
            """
            Returns a flat list of this symbol set's entities
            :return: List of Entity objects
            """
            ret = []
            for ent in self.entities.values():
                ret = ret + ent.get_flat_entities()
            return ret

        def get_modifier(self, index, mod_code):
            """
            Returns the given modifier if it exists
            :param index: The modifier index (1 or 2) to search in
            :param mod_code: The two-digit modifier code in str format
            :return: The found Modifier object, or None if it wasn't found
            """
            if int(index) not in self.modifiers.keys():
                return None

            mod_list = self.modifiers[int(index)]
            if mod_code not in mod_list.keys():
                return None

            return mod_list[mod_code]

    # Data for SymbolSchema class itself
    def __init__(self):
        self.version = '00'
        self.standard_identities = {}  # Digit 2; SI itself
        self.contexts = {}  # Digit 1; first digit of SI
        self.statuses = {}  # Digit 7
        self.hqtfd_codes = {}  # Digit 8
        self.amplifiers = {}  # Digits 9 and 10
        self.symbol_sets = {}

        self.symbol_root_folder = ''
        self.symbol_folders = {}
        self.symbol_fill_placeholder = ''
        self.template_sets = {}
        self.symbol_svg_json:JSONFilesystem = None
        pass

    def get_flat_entities(self):
        """
        Returns a flat list of all entities in the symbol schema
        :return: List of `SymbolSet.Entity` objects
        """
        ret = []
        for sym_set in self.symbol_sets.values():
            ret += sym_set.get_flat_entities()
        return ret

    def add_template_set(self, template) -> None:
        """
        Adds a template set to the given schema
        :param template: Template to add
        """
        if template is not None:
            self.template_sets[template.name] = template

    def get_template_list(self):
        """
        Returns the list of all templates recognized by this SymbolSchema, regardless of symbol sets.
        """
        ret = []
        for template_set in self.template_sets.values():
            ret.extend(template_set.get_template_list())
        return ret

    @classmethod
    def load_symbol_schema_from_file(cls, json_filepath='', verbose=False):
        """
        A function to load a symbol schema from JSON file at a particular filepath
        :param json_filepath: The filepath to the JSON file to load
        :param verbose: Whether to print or not
        :return: A SymbolSchema object containing the loaded symbol schema
        """

        def import_symbol_set(id_code, symbol_set_json):
            """
            Function to load a symbol set from JSON
            :param id_code: The ID code of the symbol set to load, since it's a key externally
            :param symbol_set_json: The JSON dict containing the symbol set to be loaded
            :return: A SymbolSchema.SymbolSet object containing the loaded symbol set
            """
            new_symbol_set = SymbolSchema.SymbolSet()

            new_symbol_set.id_code = id_code
            new_symbol_set.name = symbol_set_json['name']
            new_symbol_set.frame_set = symbol_set_json['frame set']

            if 'implemented' in symbol_set_json.keys():
                new_symbol_set.implemented = symbol_set_json['implemented']
                if not new_symbol_set.implemented:
                    return new_symbol_set
            else:
                new_symbol_set.implemented = True

            if 'match weight' in symbol_set_json.keys():
                new_symbol_set.match_weight = int(symbol_set_json['match weight'])

            # Load notes and frame set
            new_symbol_set.notes = symbol_set_json['notes'] if 'notes' in symbol_set_json.keys() else ''

            def load_entity(symbol_set, new_id_code, entity_json, level=0, inherit_icon_type=False,
                            icon_type_to_inherit='main',
                            inherit_modcats=False,
                            modcats_to_inherit: list = [], inherited_civilian_coloring=False,
                            inherited_use_with_unfilled_frames=False,
                            inherit_variants=False, variants_to_inherit=0):
                """
                A utility function to load an entity from JSON
                :param symbol_set: The parent symbol set object for this entity
                :param new_id_code: The new ID code for this entity
                :param entity_json: The JSON the entity should be loaded from
                :param level: The level the entity is (0 = entity, 1 = entity type, 2 = entity subtype)
                :param inherit_icon_type: Whether this entity should inherit from its parent icon type
                :param icon_type_to_inherit: The icon type this entity should inherit, if applicable
                :param inherit_modcats: Whether this entity inherits the modifier categories of its parent
                :param modcats_to_inherit: What modifier categories this entity inherits from its parent, if applicable
                :param inherited_civilian_coloring: The inherited civilian coloring of this icon (always follows)
                :param inherited_use_with_unfilled_frames: Whether this icon should use unfilled frames
                :param inherit_variants: Whether this icon should inherit variants
                :param variants_to_inherit: How many variants this entity inherits from its parent
                :return:
                """
                created_entity: SymbolSchema.SymbolSet.Entity = SymbolSchema.SymbolSet.Entity()
                created_entity.id_code = new_id_code
                created_entity.symbol_set = symbol_set.id_code

                if isinstance(entity_json, str) or isinstance(entity_json, list):  # simple string entity
                    if isinstance(entity_json, str):
                        created_entity.name = entity_json
                    else:
                        created_entity.name = entity_json[0]
                        created_entity.alt_names = entity_json[1:]

                    created_entity.modifier_categories = modcats_to_inherit
                    created_entity.icon_type = icon_type_to_inherit
                    created_entity.uses_civilian_coloring = inherited_civilian_coloring
                    created_entity.use_with_unfilled_frames = inherited_use_with_unfilled_frames
                    created_entity.variants = variants_to_inherit
                else:  # Complex entity with entity types or more information

                    if 'name' in entity_json.keys():
                        created_entity.name = entity_json['name']
                    elif 'names' in entity_json.keys():
                        created_entity.name = entity_json['names'][0]
                        created_entity.alt_names = entity_json['names'][1:]
                    created_entity.icon_type = entity_json[
                        'type'] if 'type' in entity_json.keys() else icon_type_to_inherit
                    type_inherit = entity_json[
                        'type-inherit'] if 'type-inherit' in entity_json.keys() else inherit_icon_type
                    modcat_inherit = entity_json['modcats-inherit'] if 'modcats-inherit' in entity_json.keys() \
                        else inherit_modcats
                    created_entity.use_with_unfilled_frames = entity_json['use with unfilled frames'] if \
                        'use with unfilled frames' in entity_json.keys() else inherited_use_with_unfilled_frames
                    inherit_use_with_unfilled_frames = entity_json['inherit use with unfilled frames'] if \
                        'inherit use with unfilled frames' in entity_json.keys() else created_entity.use_with_unfilled_frames

                    # Load overlays
                    if 'overlay' in entity_json.keys():
                        for overlay_item in entity_json['overlay']:
                            if overlay_item[2] != '-':
                                created_entity.overlay_elements.append(created_entity.symbol_set + '-' + overlay_item)
                            else:
                                created_entity.overlay_elements.append(overlay_item)

                    # Load modifier categories
                    if 'modcats' in entity_json.keys():
                        created_entity.modifier_categories = []
                        for modcat in entity_json['modcats']:
                            created_entity.modifier_categories.append(modcat)
                    else:
                        created_entity.modifier_categories = modcats_to_inherit

                    # Load civilian coloring
                    created_entity.uses_civilian_coloring = entity_json['uses-civilian-coloring'] \
                        if 'uses-civilian-coloring' in entity_json.keys() else inherited_civilian_coloring
                    children_inherit_civilian_coloring = entity_json['civilian-coloring-inherit'] \
                        if 'civilian-coloring-inherit' in entity_json.keys() else created_entity.uses_civilian_coloring

                    # Load local only
                    created_entity.local_only = entity_json[
                        'local-only'] if 'local-only' in entity_json.keys() else False
                    created_entity.notes = entity_json['notes'] if 'notes' in entity_json.keys() else False

                    # Load variants
                    created_entity.variants = entity_json['variants'] if 'variants' in entity_json.keys() \
                        else variants_to_inherit
                    new_inherit_variants = entity_json['variants-inherit'] if 'variants-inherit' in entity_json.keys() \
                        else inherit_variants

                    # Load children
                    if level < 2:
                        sublevel_key = 'entity types' if level == 0 else 'entity subtypes'
                        if sublevel_key in entity_json.keys():
                            for child_ent_key in entity_json[sublevel_key]:
                                if level == 0:
                                    new_child_code = new_id_code[0:2] + child_ent_key + '00'
                                else:
                                    new_child_code = new_id_code[0:4] + child_ent_key

                                new_child_entity = load_entity(symbol_set=symbol_set,
                                                               new_id_code=new_child_code,
                                                               entity_json=entity_json[sublevel_key][child_ent_key],
                                                               level=level + 1,
                                                               inherit_icon_type=type_inherit,
                                                               icon_type_to_inherit=created_entity.icon_type if
                                                               type_inherit else 'mn',
                                                               inherit_modcats=modcat_inherit,
                                                               modcats_to_inherit=created_entity.modifier_categories.copy() if
                                                               modcat_inherit else [],
                                                               inherited_civilian_coloring=
                                                               created_entity.uses_civilian_coloring if
                                                               children_inherit_civilian_coloring else False,
                                                               inherited_use_with_unfilled_frames=
                                                               created_entity.use_with_unfilled_frames if
                                                               inherit_use_with_unfilled_frames else False,
                                                               variants_to_inherit=created_entity.variants
                                                               if new_inherit_variants
                                                               else 0,
                                                               inherit_variants=new_inherit_variants)

                                # Create short/long name
                                if '*' in new_child_entity.name:
                                    # Child uses a name substitution
                                    new_child_entity.short_subtype_name = new_child_entity.name.replace('*', '').strip()
                                    new_child_entity.name = new_child_entity.name.replace('*', created_entity.name)
                                else:
                                    # Child doesn't use a name substitution
                                    new_child_entity.short_subtype_name = new_child_entity.name

                                alt_names = []
                                for name in new_child_entity.alt_names:
                                    alt_names.append(name.replace('*', created_entity.name))
                                new_child_entity.alt_names = alt_names

                                # Remove duplicate categories
                                new_child_entity.modifier_categories = list(
                                    dict.fromkeys(new_child_entity.modifier_categories))
                                created_entity.children[new_child_code] = new_child_entity
                        # Done loading children

                    # Load additional modcats so they're not passed to children
                    if 'modcats-additional' in entity_json.keys():
                        for modcat in entity_json['modcats-additional']:
                            created_entity.modifier_categories.append(modcat)

                    if 'match weight' in entity_json.keys():
                        created_entity.match_weight = int(entity_json['match weight'])
                    # Done with simple category
                    # Load modifier categories

                return created_entity

            # ------------------------------------------------------------------------------------
            # / End load_entity ------------------------------------------------------------------
            # ------------------------------------------------------------------------------------

            for ent_json_key in symbol_set_json['entities']:
                ent_json_value = symbol_set_json['entities'][ent_json_key]
                new_entity = load_entity(new_symbol_set, ent_json_key + '0000', ent_json_value, 0)
                new_symbol_set.entities[new_entity.id_code] = new_entity

            # Load special entity subtypes
            if 'special entity subtypes' in symbol_set_json.keys():
                for key, value in symbol_set_json['special entity subtypes'].items():
                    new_special_entity_subtype = load_entity(new_symbol_set,
                                                             key,
                                                             value,
                                                             level=2)
                    new_special_entity_subtype.id_code = 'XXXX' + new_special_entity_subtype.id_code
                    new_special_entity_subtype.is_special_entity_subtype = True
                    new_symbol_set.special_entity_subtypes[key] = new_special_entity_subtype

            # Load modifiers
            for mod_num in [1, 2]:
                if 'modifier set %i' % mod_num not in symbol_set_json.keys():
                    continue

                for mod_id, mod_json in symbol_set_json['modifier set %i' % mod_num].items():
                    new_modifier = SymbolSchema.SymbolSet.Modifier()
                    new_modifier.symbol_set = new_symbol_set.id_code
                    new_modifier.modifier_set = mod_num
                    new_modifier.id_code = mod_id

                    if isinstance(mod_json, str):
                        new_modifier.name = mod_json
                    else:
                        if 'name' in mod_json.keys():
                            new_modifier.name = mod_json['name']
                        elif 'names' in mod_json.keys():
                            # print(f"Mod with alt names: {mod_json['names']}")
                            new_modifier.name = mod_json['names'][0]
                            new_modifier.alt_names = mod_json['names'][1:]
                        new_modifier.mod_category = mod_json['cat'] if 'cat' in mod_json.keys() else ''
                        new_modifier.type = mod_json['type'] if 'type' in mod_json.keys() else 'mn'
                        new_modifier.match_weight = int(mod_json['match weight']) if 'match weight' in mod_json.keys() else 0

                        if 'overlay' in mod_json.keys():
                            for overlay_item in mod_json['overlay']:
                                if overlay_item[2] != '-':
                                    new_modifier.overlay_elements.append(new_symbol_set.id_code + '-' + overlay_item)
                                else:
                                    new_modifier.overlay_elements.append(overlay_item)

                        new_modifier.has_civilian_coloring_override = 'civilian-coloring-override' in mod_json.keys()
                        if new_modifier.has_civilian_coloring_override:
                            new_modifier.civilian_coloring_override_value = mod_json['civilian-coloring-override']
                    new_symbol_set.modifiers[mod_num][new_modifier.id_code] = new_modifier

            return new_symbol_set

        # End load symbol set subroutine

        opening_filepath = json_filepath
        if json_filepath is None or json_filepath == '':
            module_dir = os.path.dirname(os.path.realpath(__file__))
            opening_filepath = os.path.join(module_dir, 'symbols.json')

        if verbose:
            print('Importing master JSON schema')
        with open(opening_filepath, 'r') as json_file:
            json_data = json.load(json_file)  # TODO load from string instead

        new_symbol_schema = SymbolSchema()
        new_symbol_schema.version = json_data['version']
        new_symbol_schema.symbol_root_folder = json_data['symbol root folder']
        directory = os.path.dirname(json_filepath)
        new_symbol_schema.symbol_root_folder = os.path.join(directory, new_symbol_schema.symbol_root_folder)
        new_symbol_schema.symbol_folders = json_data['symbol folders']
        new_symbol_schema.symbol_fill_placeholder = json_data['symbol fill placeholder']

        # Load standard identities themselves
        si_json = json_data['standard identities']
        if verbose:
            print('Loading SIs')
        for sd in [sdi for sdi in si_json['second digits'] if sdi != 'notes']:
            sd_key = sd
            sd_value = si_json['second digits'][sd]

            # Load basic information about standard identity
            new_si = SymbolSchema.StandardIdentity()
            new_si.id_code = str(sd_key)
            new_si.name = sd_value['name']
            new_si.alt_names = []
            if 'alt name' in sd_value.keys():
                new_si.alt_names.append(sd_value['alt name'])
            if 'alt names' in sd_value.keys():
                for alt_name in sd_value['alt names']:
                    new_si.alt_names.append(alt_name)

            new_si.uses_dashed_frame = sd_value['uses dashed frame'] if 'uses dashed frame' in sd_value.keys() \
                else False

            # Load frame set
            if 'frame alias' in sd_value.keys():
                new_si.frame_set = str(sd_value['frame alias'])
            else:
                new_si.frame_set = str(sd_key)

                # Load colors
                # Load standard colors
                for cv in ['light', 'medium', 'dark', 'unfilled']:
                    new_si.standard_colorset[cv] = sd_value["colors"][cv]

                # Load civilian colors
                if 'civilian colors' in sd_value.keys():
                    for cv in ['light', 'medium', 'dark', 'unfilled']:
                        new_si.civilian_colorset[cv] = sd_value["civilian colors"][cv]
                else:
                    new_si.civilian_colorset = new_si.standard_colorset

            # SI loading is complete; add it to the symbol set
            new_symbol_schema.standard_identities[str(new_si.id_code)] = new_si

        # Load colors back into SIs that use aliases
        for si in new_symbol_schema.standard_identities.values():
            if si.frame_set != si.id_code:
                si.standard_colorset = new_symbol_schema.standard_identities[si.frame_set].standard_colorset
                si.civilian_colorset = new_symbol_schema.standard_identities[si.frame_set].civilian_colorset
            if verbose:
                print('\t' + str(si))

        # Load realities for SIs
        contexts_json = si_json['first digits']
        for si_r in contexts_json:
            new_reality = SymbolSchema.StandardIdentity.Context()
            new_reality.id_code = str(si_r)
            new_reality.name = contexts_json[si_r]
            new_symbol_schema.contexts[new_reality.id_code] = new_reality

        # Load statuses
        if verbose:
            print('Loading statuses')
        statuses_json = json_data['statuses']

        for status_json_code in [st for st in statuses_json if st != 'notes']:
            status_data = statuses_json[status_json_code]
            new_status: SymbolSchema.Status = SymbolSchema.Status()
            new_status.id_code = str(status_json_code)
            if 'name' in status_data.keys():
                new_status.names = [status_data['name']]
            else:
                new_status.names = status_data['names']

            if 'applies to' in status_data.keys():
                new_status.applies_to_all = False
                for applies_to_item in status_data['applies to']:
                    new_status.applies_to_list.append(applies_to_item)
            else:
                new_status.applies_to_all = True

            if 'variants' in status_data.keys():
                new_status.variants = status_data['variants']

            new_status.makes_frame_dashed = status_data['makes frame dashed'] if 'makes frame dashed' in \
                                                                                 status_data.keys() else False

            new_symbol_schema.statuses[new_status.id_code] = new_status
            if verbose:
                print('\t' + str(new_status))

        # Load HQTFD
        if verbose:
            print('Loading HQTFD codes')
        hqtfd_codes_json = json_data['HQTFD codes']
        for hqtfd_code_key in [key for key in hqtfd_codes_json if key != 'notes']:
            hqtfd_value = hqtfd_codes_json[hqtfd_code_key]
            new_hqtfd_code = SymbolSchema.HQTFDCode()
            new_hqtfd_code.id_code = str(hqtfd_code_key)
            if 'names' in hqtfd_value.keys():
                new_hqtfd_code.names = hqtfd_value['names']
            else:
                new_hqtfd_code.names = [hqtfd_value['name']]
            if 'offsets' in hqtfd_value.keys():
                for offset_key in hqtfd_value['offsets']:
                    new_hqtfd_code.offsets[offset_key] = hqtfd_value['offsets'][offset_key]
            if 'overlay' in hqtfd_value.keys():
                new_hqtfd_code.overlay_elements = hqtfd_value['overlay']

            if 'applies to' in hqtfd_value.keys():
                new_hqtfd_code.applies_to_symbol_sets = hqtfd_value['applies to']

            if verbose:
                print(f'\t{new_hqtfd_code}')
            new_symbol_schema.hqtfd_codes[new_hqtfd_code.id_code] = new_hqtfd_code

        # Load amplifiers
        if verbose:
            print('Loading amplifiers')
        amplifier_groups_json = json_data['amplifiers']
        for amplifier_first_digit in [key for key in amplifier_groups_json if key != 'notes']:
            applies_to_codes = [str(code) for code in amplifier_groups_json[amplifier_first_digit]['applies to']]
            category = amplifier_groups_json[amplifier_first_digit]['name']

            for amplifier_second_digit in amplifier_groups_json[amplifier_first_digit]['second digit']:
                new_amplifier = SymbolSchema.Amplifier()

                new_amplifier.id_code = '%s%s' % (amplifier_first_digit, amplifier_second_digit)
                new_amplifier.applies_to_list = applies_to_codes
                new_amplifier.category = category

                specific_data = amplifier_groups_json[amplifier_first_digit]['second digit'][amplifier_second_digit]
                if isinstance(specific_data, str):
                    new_amplifier.names = [specific_data]
                elif isinstance(specific_data, list):
                    new_amplifier.names = specific_data
                elif isinstance(specific_data, dict):
                    if 'names' in specific_data:
                        new_amplifier.names = specific_data['names']
                    elif 'name' in specific_data:
                        new_amplifier.names = [specific_data['name']]
                    if 'match weight' in specific_data.keys():
                        new_amplifier.match_weight = int(specific_data['match weight'])

                if verbose:
                    print('\t' + str(new_amplifier))
                new_symbol_schema.amplifiers[new_amplifier.id_code] = new_amplifier

        # Load symbol sets
        if verbose:
            print('Loading symbol sets')
        for symbol_set_json_code in [key for key in json_data['symbol sets'] if key != 'notes']:
            loaded_symbol_set = import_symbol_set(symbol_set_json_code,
                                                  json_data['symbol sets'][symbol_set_json_code])
            new_symbol_schema.symbol_sets[loaded_symbol_set.id_code] = loaded_symbol_set

            if verbose:
                loaded_symbol_set.print(tab_stops='\t', max_depth_level=4)

        new_symbol_schema.symbol_svg_json = JSONFilesystem()
        new_symbol_schema.symbol_svg_json.json = json_data['SVGs']

        return new_symbol_schema

    def get_entity(self, symbol_set, entity_code, frame_set=0):
        """
        Finds an entity in the given symbol schema
        :param symbol_set: The symbol set to search in
        :param entity_code: The entity code to search for
        :param frame_set: The frame set to use when returning
        :return: The Entity object if found, None otherwise
        """
        if symbol_set not in self.symbol_sets.keys():
            return None
        return self.symbol_sets[symbol_set].get_entity(entity_code, frame_set)

    def get_modifier(self, symbol_set, mod_index, mod_code):
        """
        Searches for a modifier from the given symbol schema
        :param symbol_set: Symbol set to search in
        :param mod_index: Modifier index [1, 2] to look in within the symbol set
        :param mod_code: Modifier code to search for
        :return: The Modifier object if found, None otherwise
        """
        if symbol_set not in self.symbol_sets.keys():
            return None
        return self.symbol_sets[symbol_set].get_modifier(mod_index, mod_code)

    def get_svg_by_filename(self, svg_name):
        """
        Returns an ETree from the given SVG filename, whether internally (default) or by filename if there's no
        JSONFilesystem defined for this symbol schema
        :param svg_name: The name of the SVG to return
        :return: An ETree object containing the SVG contents, or None if not found
        """

        if self.symbol_svg_json is None:
            raw_string_data = _svg_tools.get_svg_string(svg_name)
        else:
            try:
                raw_string_data = self.symbol_svg_json.get_contents_at_path(svg_name)
            except FileNotFoundError:
                # Try without SI code
                re_match = [it for it in re.finditer('-\d', svg_name)]
                if len(re_match) < 1:
                    raise FileNotFoundError

                new_svg_name:str = svg_name[:re_match[-1].span()[0]] + svg_name[re_match[-1].span()[1]:]
                raw_string_data = self.symbol_svg_json.get_contents_at_path(new_svg_name)

        ret = read_string_into_etree(raw_string_data)
        if ret is None:
            print(f'Error: No file "{svg_name}" found by filename')
        return ret

    def get_svg_filename_by_code(self, code, standard_identity, use_variants=False):
        """
        Returns an SVG filename using a shorthand code
        :param code: The string of code to search for
        :param standard_identity: The standard identity to use
        :param use_variants: Whether to use the variant form (mainly applies to status and mine warfare symbols)
        :return:
        """
        if code is None:
            print(f'Error: No SVG code "{code}" found')
            return None
        code = ''.join([c for c in code if c.isalnum()])

        # First part of code:
        #   E = entity
        #   M = modifier
        #   H = HQTFD
        #   A = amplifier
        #   S = status
        #   F = frame
        svg_type = code[0].upper()
        path_name = ''  # Formerly self.symbol_root_folder

        if svg_type in ['E', 'M']:
            # Get entity
            symbol_set = code[1:3]
            if symbol_set not in self.symbol_sets:
                return None

            path_name = os.path.join(path_name, self.symbol_folders['symbol sets'],
                                     symbol_set)
            if svg_type == 'E':
                # Entity
                # Format E-00-111111
                #   0 = symbol set
                #   1 = entity code

                # print('Finding overlay %s' % code)
                path_name = os.path.join(path_name, self.symbol_folders['within symbol set']['entities'])
                entity_code = code[3:]

                # if entity_code[:2] == '0X':
                #     print('\tEntity is 0X-type overlay')

                entity = self.get_entity(symbol_set, entity_code, standard_identity.frame_set)
                if entity is None:
                    # print('Can\'t find overlay %s' % entity_code)
                    filename = entity_code + '.svg'
                    if os.path.exists(os.path.join(path_name, filename)):
                        # print('Path exists')
                        pass
                    else:
                        filename = entity_code + '-' + standard_identity.frame_set + '.svg'
                else:
                    # print('\tFound overlay%s' % ('*' if entity.icon_type == 'ff' else ''))
                    filename = entity.id_code + ('-%s' % standard_identity.frame_set
                                                 if entity.icon_type == 'ff' else '') + '.svg'
                path_name = os.path.join(path_name, filename)

            elif svg_type == 'M':
                # Modifier
                # Format M-00-1-22
                #   0 = symbol set
                #   1 = modifier set (i.e. 1 or 2)
                #   2 = modifier code

                symbol_set = code[1:3]
                mod_set = code[3]
                mod_code = code[4:]
                path_name = os.path.join(path_name,
                                         self.symbol_folders['within symbol set']['modifiers'].replace('*', mod_set), )
                # Check if modifier is full frame
                if int(mod_set) not in [1, 2] or mod_code not in \
                        self.symbol_sets[symbol_set].modifiers[int(mod_set)].keys():
                    print('Invalid mod set or code %s / %s' % (mod_set, mod_code))
                    print(code)
                    return None

                modifier = self.symbol_sets[symbol_set].modifiers[int(mod_set)][mod_code]
                if modifier.type == 'ff':
                    path_name = os.path.join(path_name,
                                             mod_code + '-' + str(standard_identity.frame_set) + '.svg')
                else:
                    path_name = os.path.join(path_name, mod_code + '.svg')
        elif svg_type == 'F':
            # Frame
            # Format F-00-1
            #   0 = frame set
            #   1 = standard identity (optional)
            frame_set = code[1:3]
            path_name = os.path.join(path_name, self.symbol_folders['frames'],
                                     frame_set + '-' + standard_identity.frame_set + '.svg')
        elif svg_type == 'A':
            # Amplifier
            # Format A-00
            #   0 = amplifier code
            amplifier_code = code[1:3]
            path_name = os.path.join(path_name, self.symbol_folders['amplifiers'],
                                     amplifier_code + '-' + standard_identity.frame_set + '.svg')
        elif svg_type == 'H':
            # HQTFD
            # Format H-0-11
            #   0 = HQTFD flag
            #   1 = amplifier, used only for HQTFD code 4

            hqtfd_code = code[1]
            amp_code = code[2:]

            if hqtfd_code == '4':
                # print(amp_code)
                path_name = os.path.join(path_name, self.symbol_folders['hqtfd'],
                                         hqtfd_code + '-' + amp_code + '.svg')
            else:
                path_name = os.path.join(path_name, self.symbol_folders['hqtfd'],
                                         hqtfd_code + '-' + standard_identity.frame_set + '.svg')
        elif svg_type == 'S':
            # Status
            # Format S-0
            status_code = code[1]
            if status_code not in self.statuses.keys():
                print(f"Unrecognized status code \"{status_code}\"")
                return ''

            status = self.statuses[status_code]

            if not use_variants:
                status_code = status_code + '-' + standard_identity.frame_set
            elif len(status.variants) > 0:
                if status.variants[0] == 'nn':
                    return ''
                elif status.variants[0] == 'mn':
                    status_code = status_code + "-V1"

            path_name = os.path.join(path_name, self.symbol_folders['statuses'],
                                     status_code + '.svg')
            return path_name
        else:
            print(f"Unrecognized status code \"{svg_type}\"")
            return ''

        # print(path_name)
        return path_name

    def get_svg_by_code(self, code, standard_identity, use_variants=False):
        """
        Returns an SVG using a shorthand code
        :param code: The string of code to search for
        :param standard_identity: The standard identity to use
        :param use_variants: Whether to use the variant form (mainly applies to status and mine warfare symbols)
        :return:
        """
        return self.get_svg_by_filename(self.get_svg_filename_by_code(code, standard_identity, use_variants))
