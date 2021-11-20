import re

import symbol_template
from nato_symbol import NATOSymbol
from symbol_schema import SymbolSchema


def get_names_list(item) -> list:
    candidate_members = dir(item)

    if 'name' in candidate_members:
        ret = [item.name]
        if 'alt_names' in candidate_members:
            ret.extend(item.alt_names)
        return ret
    elif 'names' in candidate_members:
        return item.names
    return []


def split_into_words(in_str:str) -> list:
    in_str = re.sub('[/ \-\t\n]+', ' ', in_str).strip().lower()
    in_str = ''.join([c for c in in_str if c.isalpha() or c == ' '])
    return [word.strip() for word in in_str.strip().split(' ') if len(word) > 0]


def fuzzy_match(symbol_schema, name_string, candidate_list, match_longest=True):

    # Step 1: calculate the number of words in candidate_list_of_lists
    matches = [] # Set of (candidate, weight) pairs
    name_string_words = split_into_words(name_string)

    for candidate in candidate_list:

        # Iterate over the possible names
        for candidate_name in get_names_list(candidate):
            candidate_name_words = split_into_words(candidate_name)

            matching = False

            for start_i in range(len(name_string_words) - len(candidate_name_words) + 1):
                matching_count = 0
                for i in range(len(candidate_name_words)):
                    if name_string_words[start_i + i] != candidate_name_words[i]:
                        break
                    else:
                        matching_count += 1
                        if matching_count == len(candidate_name_words):
                            matching = True
                            break
                if matching:
                    break

            if matching:
                matches.append([str(candidate_name), candidate])
                continue
            else:
                pass

    if len(matches) < 1:
        return None, None
    elif len(matches) == 1:
        return matches[0][1], name_string.replace(matches[0][0], '').strip().replace('  ', ' ')

    # Sort matches by match weight
    for match in matches:
        match_weight = 0
        if 'symbol_set' in dir(match[1]):
            sym_set_weight = symbol_schema.symbol_sets[match[1].symbol_set].match_weight
            match_weight = sym_set_weight if abs(sym_set_weight) > abs(match[1].match_weight) else match[1].match_weight
        elif 'match_weight' in dir(match[1]):
            match_weight = match[1].match_weight
        match.append(match_weight)

    matches = sorted(matches, key=lambda item: item[2])
    max_match_weight = max(item[2] for item in matches)
    matches = [match for match in matches if match[2] == max_match_weight]
    if len(matches) == 1:
        return matches[0][1], name_string.replace(matches[0][0], '').strip().replace('  ', ' ')

    # Sort matches by string length name
    matches = sorted(matches, key=lambda item: len(item[0]))
    match_index = -1 if match_longest else 0
    return matches[match_index][1], name_string.replace(matches[match_index][0], '').strip().replace('  ', ' ')


def name_to_symbol(name_string:str, symbol_schema:SymbolSchema, verbose:bool=False) -> NATOSymbol:
    proc_name_string = name_string

    # Sanitize string
    # Remove extra white spaces
    proc_name_string = proc_name_string.lower()
    proc_name_string = re.sub('[ \t\n]+', ' ', proc_name_string).strip()

    if verbose:
        print(f'Matching "{proc_name_string}"')

    # Step 0: Check for templates
    template: symbol_template.SymbolTemplate = None
    template, new_name_string = fuzzy_match(symbol_schema, name_string, symbol_schema.get_template_list())

    ret_symbol:NATOSymbol = None

    if template is not None:
        proc_name_string = new_name_string
        if verbose:
            print(f"\tMatches template \"{template.name}\" -> \"{proc_name_string}\"")

        ret_symbol = template.symbol
    else:
        ret_symbol = NATOSymbol(symbol_schema)

    # Step 1: Detect standard identity

    if template is None or not template.standard_identity_fixed:
        standard_identity, new_name_string = fuzzy_match(symbol_schema, name_string,
                                                     symbol_schema.standard_identities.values(), match_longest=True)

        if standard_identity is None:
            print("\tUnable to determine standard identity; assuming unknown")
            standard_identity = [si for si in symbol_schema.standard_identities.values() if si.name == 'unknown'][0]
        else:
            proc_name_string = new_name_string

        if verbose:
            print(f'\tAssuming standard identity "{standard_identity.name}" -> "{proc_name_string}"')

        ret_symbol.standard_identity = standard_identity

    # Step 2: Detect entity type
    if template is None or not template.entity_fixed:
        entity_type, new_name_string = fuzzy_match(symbol_schema, proc_name_string, symbol_schema.get_flat_entities(),
                                               match_longest=True)

        symbol_set = None
        if entity_type is None:
            print(f"\tWARNING: Unable to determine entity type from string \"{name_string}\"; defaulting to land unit")
            ret_symbol:NATOSymbol = NATOSymbol(symbol_schema)
            symbol_set = [set for set in symbol_schema.symbol_sets.values() if set.name == 'land unit'][0]
            ret_symbol.entity = symbol_set.get_entity("000000")
        else:
            if verbose:
                print(f'\tAssuming entity "{entity_type.name}" -> "{proc_name_string}"')
            symbol_set = symbol_schema.symbol_sets[entity_type.symbol_set]
            proc_name_string = new_name_string

        ret_symbol.entity = entity_type
        ret_symbol.symbol_set = symbol_schema.symbol_sets[entity_type.symbol_set]

    if template is None or not template.amplifier_fixed:
        candidate_amplifiers = [amp for amp in symbol_schema.amplifiers.values() if amp.applies_to(ret_symbol.symbol_set.id_code)]
        amplifier, new_name_string = fuzzy_match(symbol_schema, proc_name_string, candidate_amplifiers, match_longest=True)
        if amplifier is not None:
            proc_name_string = new_name_string
            if verbose:
                print(f'\tAssuming amplifier "{amplifier.names[0]}" -> "{proc_name_string}"')

        ret_symbol.amplifier = amplifier

    # Find task force / headquarters / dummy
    if template is None or not template.hqtfd_fixed:
        hqtfd, new_name_string = fuzzy_match(symbol_schema, proc_name_string,
                                             [code for code in symbol_schema.hqtfd_codes.values() if code.applies_to_symbol_set(ret_symbol.symbol_set)],
                                             match_longest=True)
        if hqtfd is not None:
            proc_name_string = new_name_string
            if verbose:
                print(f'\tAssuming HQTFD code "{hqtfd.names[0]}" -> "{proc_name_string}"')

        ret_symbol.hqtfd = hqtfd

    # Find status code
    if template is None or not template.status_fixed:
        # print([status.names for status in symbol_schema.statuses.values()])
        status_code, new_name_string = fuzzy_match(symbol_schema, proc_name_string,
                                                   [code for code in symbol_schema.statuses.values()],
                                                   match_longest=True)
        if status_code is not None:
            proc_name_string = new_name_string
            if verbose:
                print(f'\tAssuming status code "{status_code.names[0]}" -> "{proc_name_string}"')

        ret_symbol.status = status_code

    # Find modifiers
    for mod_set in [1, 2]:
        if template is None or not template.modifiers_fixed[mod_set - 1]:
            modifier_candidates = list(symbol_set.modifiers[mod_set].values())
            # print([get_names_list(mod) for mod in modifier_candidates])
            mod, new_name_string = fuzzy_match(symbol_schema, proc_name_string, modifier_candidates, match_longest=True)
            if mod is not None:
                proc_name_string = new_name_string

                if verbose:
                    print(f'\tAssuming modifier "{mod.name}" -> "{proc_name_string}"')
                ret_symbol.modifiers[mod_set] = mod

    return ret_symbol