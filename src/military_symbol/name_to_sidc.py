import re

from . import symbol_template
from .individual_symbol import MilitarySymbol
from .symbol_schema import SymbolSchema
from thefuzz import fuzz
from functools import cmp_to_key
import sys

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

def fuzzy_match(symbol_schema, name_string, candidate_list, match_longest=True, verbose=False, print_candidates=False):
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

        ent_a = a[1]
        ent_b = b[1]

        sym_set_a = symbol_schema.symbol_sets[a[1].symbol_set]
        sym_set_b = symbol_schema.symbol_sets[b[1].symbol_set]

        match_weight_a = sym_set_a.match_weight + ent_a.match_weight
        match_weight_b = sym_set_b.match_weight + ent_b.match_weight

        if score_a == score_b:
            if match_weight_a > match_weight_b:
                return -1
            elif match_weight_a < match_weight_b:
                return 1

            if len(a[0]) == len(b[0]):
                return 0
            return 1 if len(a[0]) < len(b[0]) else -1

        return 1 if score_a > score_b else -1

    matches = sorted(matches, key=cmp_to_key(sort_func))
    if verbose and 'symbol_set' in dir(matches[0][1]):
        print('\tMatches ' + f"{[f'{entity.names[0]} ({entity.symbol_set}-{entity.id_code}) (score {score})' for (name, entity, score) in matches]}")

    return matches[0][1], name_string.replace(matches[0][0], '').strip().replace('  ', ' ')

def symbol_set_from_name(symbol_schema, item, verbose:bool=False) -> SymbolSchema.SymbolSet:
    if item is None or symbol_schema is None:
        return None
    if isinstance(item, SymbolSchema.SymbolSet):
        return item

    if not isinstance(item, str):
        print(f"Can't parse symbol set from item {item}", file=sys.stderr)
        return None

    # Guess from names
    sym_set_candidates = symbol_schema.symbol_sets.values()
    sym_set, sym_set_name = fuzzy_match(symbol_schema, item, sym_set_candidates, verbose=verbose)
    return sym_set


def name_to_symbol(name_string: str, symbol_schema: SymbolSchema, verbose: bool = False, limit_to_symbol_sets=[]) -> MilitarySymbol:
    """
    Function to return a NATOSymbol object from the provided name, using a best guess
    :param name_string: The string representing the name to construct a best-guess symbol from, e.g. "Friendly infantry platoon"
    :param symbol_schema: The symbol schema to use
    :param verbose: Whether to print ancillary information during execution; defaults to false.
    :param limit_to_symbol_sets: A list of symbol set objects or names to restrict guessing to
    :return:
    """
    proc_name_string = name_string

    # Handle symbol categories
    symbol_set_tags = re.findall(r"\[([\w\d\s]+)\]", proc_name_string)
    if len(symbol_set_tags) > 0:
        if limit_to_symbol_sets is not None:
            limit_to_symbol_sets.extend([d.lower() for d in symbol_set_tags])
        else:
            limit_to_symbol_sets = list([d.lower() for d in symbol_set_tags])
    
    # Remove category tags
    proc_name_string = re.sub(r"\[([\w\d\s]+)\]", "", proc_name_string)
    proc_name_string = re.sub(r"\s+", " ", proc_name_string)

    if verbose and len(symbol_set_tags) > 0:
        print('\tIdentified tags ' + ", ".join([f'\"{d}\"' for d in symbol_set_tags]) + f" -> {proc_name_string}")

    # Handle restricting to specific symbol sets
    if limit_to_symbol_sets is not None and isinstance(limit_to_symbol_sets, list) and len(limit_to_symbol_sets) > 0:
        limit_to_symbol_sets = [symbol_set_from_name(symbol_schema, item) for item in limit_to_symbol_sets if symbol_set_from_name(symbol_schema, item) is not None]
    else:
        limit_to_symbol_sets = None

    if verbose:
        print(f'\tLimiting to symbol sets {limit_to_symbol_sets}')

    # Sanitize string
    # Remove extra white spaces
    proc_name_string = proc_name_string.lower()
    proc_name_string = re.sub('[ \t\n]+', ' ', proc_name_string).strip()

    if verbose:
        print(f'\tMatching "{proc_name_string}"')

    # Step 0: Check for templates
    template: symbol_template.SymbolTemplate = None
    template, new_name_string = fuzzy_match(symbol_schema, proc_name_string, symbol_schema.get_template_list())
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
        standard_identity, new_name_string = fuzzy_match(symbol_schema, proc_name_string.lower(),
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

        # Limit to given symbol sets
        if limit_to_symbol_sets is not None:
            candidate_amplifiers = [amp for amp in candidate_amplifiers if amp.applies_to_any_in_symbol_sets(limit_to_symbol_sets)]

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

        # Limit to symbol sets
        if limit_to_symbol_sets is not None:
            candidates = [c for c in candidates if c.is_in_any_of_symbol_sets(limit_to_symbol_sets)]

        if ret_symbol.amplifier is not None:
            candidates = [c for c in candidates if ret_symbol.amplifier.applies_to_entity(c)]

        entity_type, new_name_string = fuzzy_match(symbol_schema, proc_name_string, candidates,
                                               match_longest=True, verbose=verbose)

        symbol_set = None
        if entity_type is None:
            print(f"\tWARNING: Unable to determine entity type from string \"{name_string}\"; defaulting to land unit")
            if limit_to_symbol_sets is None or len(limit_to_symbol_sets) < 1:
                symbol_set = [set for set in symbol_schema.symbol_sets.values() if set.names[0] == 'land unit'][0]
            else:
                symbol_set = limit_to_symbol_sets[0]

            ret_symbol.entity = symbol_set.get_entity("000000")
            ret_symbol.symbol_set = symbol_set
        else:
            symbol_set = symbol_schema.symbol_sets[entity_type.symbol_set]
            proc_name_string = new_name_string
            ret_symbol.symbol_set = symbol_schema.symbol_sets[entity_type.symbol_set]
            ret_symbol.entity = entity_type

            if verbose:
                name = entity_type.names[0] if len(entity_type.names) > 0 else ''
                print(f'\tAssuming entity "{name}" ({entity_type.id_code}) ' + 
                    f'from symbol set {entity_type.symbol_set} leaving \"{proc_name_string}\"')

    # Amplifier post-run
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