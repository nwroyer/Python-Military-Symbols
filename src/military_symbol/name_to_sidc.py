import re

from . import symbol_template
from .individual_symbol import MilitarySymbol
from .symbol_schema import SymbolSchema
from thefuzz import fuzz
from functools import cmp_to_key

def get_names_list(item) -> list:
    """
    Helper function to return the names of an object, searching through "alt_names", "name", and "names" attributes to get
    a single list of name strings.
    :param item: The item to assess for names
    :return: A list containing the found names of the object
    """
    candidate_members = dir(item)

    if 'get_names' in candidate_members:
        return item.get_names()

    if 'name' in candidate_members:
        ret = [item.name]
        if 'alt_names' in candidate_members:
            ret.extend(item.alt_names)
        return ret
    elif 'names' in candidate_members:
        return item.names
    return []


def split_into_words(in_str:str) -> list:
    """
    Helper function splitting the given string into a list of words. Hyphens are considered to separate words.
    :param in_str: The string to split into words
    :return: A list of words in the given string
    """
    in_str = re.sub(r'[/ \-\t\n]+', ' ', in_str).strip().lower()
    in_str = ''.join([c for c in in_str if c.isalpha() or c == ' '])
    return [word.strip() for word in in_str.strip().split(' ') if len(word) > 0]

def exact_match(a, b):
    if a.lower() == b.lower():
        return True

    return False

def fuzzy_match(symbol_schema, name_string, candidate_list, match_longest=True, verbose=False, match_algorithm='basic', print_candidates=False):
    """
    Returns a list of closest candidates for the given name string from the provided list of candidates
    :param symbol_schema: The symbol schema to consider the candidates to be part of
    :param name_string: The string to match against
    :param candidate_list: A list of candidates containing name, names, or alt_names attributes to choose from
    :param match_longest: Whether to prefer matching the longest possible (most specific) match, or the shortest. Defaults to true (longest).
    :return: A list containing the closest-matched candidates
    """

    name_string = name_string.lower().strip()

    # Step 1: calculate the number of words in candidate_list_of_lists
    matches = []  # Set of (candidate, weight) pairs
    candidate_name_list = [(name.lower().strip(), candidate) for candidate in candidate_list for name in candidate.get_names() ]

    print_candidates = False
    if len(name_string) < 1:
        return None, None

    if print_candidates:
        print(f'Searching for \"{name_string}\"')

    # Check for exact matches    
    name_string_words = split_into_words(name_string)
    # Return matching candidates
    matches = [(name, candidate) for (name, candidate) in candidate_name_list if name in name_string]
    if print_candidates:
        print(f'\tMatches: {[f[0] for f in matches]}')

    # Handle exact matches
    for match in matches:
        if exact_match(name_string, match[0]):
            matches = [(name, cand) for (name, cand) in matches if exact_match(name, name_string)]
            break
    
    # Handle 0 and 1-match weights
    if len(matches) < 1:
        return None, None
    elif len(matches) == 1:
        return matches[0][1], name_string.replace(matches[0][0], '').strip().replace('  ', ' ')

    # Apply fuzzy match score
    matches = [(name, cand, fuzz.partial_ratio(name, name_string)) for (name, cand) in matches]

    def sort_func(a, b):
        score_a = fuzz.partial_ratio(a[0], name_string)
        score_b = fuzz.partial_ratio(b[0], name_string)
        if score_a == score_b:
            if len(a[0]) == len(b[0]):
                return 0
            return 1 if len(a[0]) < len(b[0]) else -1

        return 1 if score_a > score_b else -1

    matches = sorted(matches, key=cmp_to_key(sort_func))
    return matches[0][1], name_string.replace(matches[0][0], '').strip().replace('  ', ' ')

    # # Sort matches by match weight
    # for match in matches:
    #     match_weight = 0
    #     if 'symbol_set' in dir(match[1]):
    #         sym_set_weight = symbol_schema.symbol_sets[match[1].symbol_set].match_weight
    #         match_weight = sym_set_weight if abs(sym_set_weight) > abs(match[1].match_weight) else match[1].match_weight
    #     elif 'match_weight' in dir(match[1]):
    #         match_weight = match[1].match_weight
    #     match.append(match_weight)

    # matches = sorted(matches, key=lambda item: item[2])
    # max_match_weight = max(item[2] for item in matches)
    # matches = [match for match in matches if match[2] == max_match_weight]
    # if len(matches) == 1:
    #     return matches[0][1], name_string.replace(matches[0][0], '').strip().replace('  ', ' ')

    # # Sort matches by string length name
    # matches = sorted(matches, key=lambda item: len(item[0]))
    # match_index = -1 if match_longest else 0
    # return matches[match_index][1], name_string.replace(matches[match_index][0], '').strip().replace('  ', ' ')


def name_to_symbol(name_string: str, symbol_schema: SymbolSchema, verbose: bool = False) -> MilitarySymbol:
    """
    Function to return a NATOSymbol object from the provided name, using a best guess
    :param name_string: The string representing the name to construct a best-guess symbol from, e.g. "Friendly infantry platoon"
    :param symbol_schema: The symbol schema to use
    :param verbose: Whether to print ancillary information during execution; defaults to false.
    :return:
    """
    proc_name_string = name_string

    # Sanitize string
    # Remove extra white spaces
    proc_name_string = proc_name_string.lower()
    proc_name_string = re.sub('[ \t\n]+', ' ', proc_name_string).strip()

    if verbose:
        print(f'\tMatching "{proc_name_string}"')

    # Step 0: Check for templates
    template: symbol_template.SymbolTemplate = None
    template, new_name_string = fuzzy_match(symbol_schema, name_string, symbol_schema.get_template_list())
    ret_symbol: MilitarySymbol = None

    if template is not None:
        proc_name_string = new_name_string
        if verbose:
            print(f"\tMatches template \"{template.names[0]}\" leaving \"{proc_name_string}\"; standard identity is {'not ' if not template.standard_identity_fixed else ''}fixed")

        ret_symbol = template.symbol
    else:
        ret_symbol = MilitarySymbol(symbol_schema)

    # Step 1: Detect standard identity

    if template is None or not template.standard_identity_fixed:
        standard_identity, new_name_string = fuzzy_match(symbol_schema, name_string.lower(),
                                                     symbol_schema.standard_identities.values(), match_longest=True)

        if standard_identity is None:
            print("\tUnable to determine standard identity; assuming unknown")
            standard_identity = [si for si in symbol_schema.standard_identities.values() if si.name == 'unknown'][0]
        else:
            proc_name_string = new_name_string

        if verbose:
            print(f'\tAssuming standard identity "{standard_identity.name}" leaving "{proc_name_string}"')

        ret_symbol.standard_identity = standard_identity

    # Amplifier
    prerun_amplifier = False

    if template is None or not template.amplifier_fixed:
        candidate_amplifiers = [amp for amp in symbol_schema.amplifiers.values() if amp.prerun]
        amplifier, new_name_string = fuzzy_match(symbol_schema, proc_name_string, candidate_amplifiers, match_longest=True)
        if amplifier is not None:
            proc_name_string = new_name_string
            if verbose:
                print(f'\tAssuming amplifier "{amplifier.names[0]}" leaving "{proc_name_string}"')
            prerun_amplifier = True

        ret_symbol.amplifier = amplifier


    # Entity type
    if template is None or not template.entity_fixed:
        candidates = symbol_schema.get_flat_entities()
        if ret_symbol.amplifier is not None:
            candidates = [c for c in candidates if ret_symbol.amplifier.applies_to_entity(c)]

        entity_type, new_name_string = fuzzy_match(symbol_schema, proc_name_string, candidates,
                                               match_longest=True, verbose=verbose, match_algorithm='advanced')

        symbol_set = None
        if entity_type is None:
            print(f"\tWARNING: Unable to determine entity type from string \"{name_string}\"; defaulting to land unit")
            symbol_set = [set for set in symbol_schema.symbol_sets.values() if set.name == 'land unit'][0]
            ret_symbol.entity = symbol_set.get_entity("000000")
            ret_symbol.symbol_set = symbol_set
        else:
            symbol_set = symbol_schema.symbol_sets[entity_type.symbol_set]
            proc_name_string = new_name_string
            ret_symbol.symbol_set = symbol_schema.symbol_sets[entity_type.symbol_set]
            ret_symbol.entity = entity_type

            if verbose:
                print(f'\tAssuming entity "{entity_type.names[0] if len(entity_type.names) > 0 else ''}" ({entity_type.id_code}) leaving \"{proc_name_string}\"')

    if (template is None or not template.amplifier_fixed) and not prerun_amplifier:
        ret_symbol.amplifier = None
        candidate_amplifiers = [amp for amp in symbol_schema.amplifiers.values() if amp.applies_to_entity(ret_symbol.entity)]
        amplifier, new_name_string = fuzzy_match(symbol_schema, proc_name_string, candidate_amplifiers, match_longest=True)
        if amplifier is not None:
            proc_name_string = new_name_string

        ret_symbol.amplifier = amplifier

    # Double-check amplifier
    if prerun_amplifier and ret_symbol.amplifier is not None and not ret_symbol.amplifier.applies_to(ret_symbol.symbol_set.id_code):
        print(f'Removing amplifier "{ret_symbol.amplifier}"')
        ret_symbol.amplifier = None

    if verbose:
        if ret_symbol.amplifier is not None:
            print(f'\tConfirming amplifier "{ret_symbol.amplifier}" leaving "{proc_name_string}"')
        else:
            print('\tNo modifier assigned')

    # Find task force / headquarters / dummy
    if template is None or not template.hqtfd_fixed:

        candidates = [hc for hc in symbol_schema.hqtfd_codes.values() if not hc.matches_blacklist(proc_name_string) and hc.applies_to_symbol_set(ret_symbol.symbol_set)]

        hqtfd, new_name_string = fuzzy_match(symbol_schema, proc_name_string,
                                             [code for code in symbol_schema.hqtfd_codes.values() if code in candidates],
                                             match_longest=True)
        if hqtfd is not None:
            proc_name_string = new_name_string
            if verbose:
                print(f'\tAssuming HQTFD code "{hqtfd.names[0]}" leaving "{proc_name_string}"')

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
                print(f'\tAssuming status code "{status_code.names[0]}" leaving "{proc_name_string}"')

        ret_symbol.status = status_code

    # Find modifiers
    for mod_set in [1, 2]:
        if template is None or not template.modifiers_fixed[mod_set - 1]:
            modifier_candidates = list(symbol_set.modifiers[mod_set].values())
            # print([get_names_list(mod) for mod in modifier_candidates])
            mod, new_name_string = fuzzy_match(symbol_schema, proc_name_string, modifier_candidates, match_longest=True, print_candidates=False)
            if mod is not None:
                proc_name_string = new_name_string

                if verbose:
                    print(f'\tAssuming modifier "{mod.names[0]}" leaving "{proc_name_string}"')
                ret_symbol.modifiers[mod_set] = mod

    return ret_symbol