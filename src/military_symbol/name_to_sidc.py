import re
import sys
import os
import copy

sys.path.append(os.path.dirname(__file__))

from thefuzz import fuzz
from functools import cmp_to_key

from symbol import Symbol
from schema import Schema, SymbolSet
from template import Template

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

def fuzzy_match(schema, name_string, candidate_list, match_longest=True, verbose=False, print_candidates=False):
    """
    Returns a list of closest candidates for the given name string from the provided list of candidates
    :param schema: The symbol schema to consider the candidates to be part of
    :param name_string: The string to match against
    :param candidate_list: A list of candidates containing name, names, or alt_names attributes to choose from
    :param match_longest: Whether to prefer matching the longest possible (most specific) match, or the shortest. Defaults to true (longest).
    :return: A list containing the closest-matched candidates
    """

    name_string = name_string.lower().strip()

    # Step 1: calculate the number of words in candidate_list_of_lists
    matches = []  # Set of (candidate, weight) pairs
    candidate_name_list = [(name.lower().strip(), candidate) for candidate in candidate_list for name in candidate.names if (not hasattr(candidate, 'match_name') or candidate.match_name)]

    print_candidates = False
    if len(name_string) < 1:
        return None, None

    if print_candidates:
        print(f'Searching for \"{name_string}\" in {candidate_name_list}')

    # Return matching candidates
    matches = [(name, candidate) for (name, candidate) in candidate_name_list if name in name_string]

    if print_candidates:
        print(matches)

    # Handle exact matches
    for match in matches:
        if exact_match(name_string, match[0]):
            matches = [(name, cand) for (name, cand) in matches if exact_match(name, name_string)]
            break
    
            if print_candidates:
                print('An exact match was found')
                print(matches)

    # Handle 0 and 1-match weights
    if len(matches) < 1:
        return None, None
    elif len(matches) == 1:
        return matches[0][1], name_string.replace(matches[0][0], '').strip().replace('  ', ' ')

    # Apply fuzzy match score
    matches = [(name, cand, fuzz.partial_ratio(name, name_string)) for (name, cand) in matches]
    if print_candidates:
        print([(n, r) for (n, c, r) in matches])

    def sort_func(a, b):
        score_a = fuzz.partial_ratio(a[0], name_string)
        score_b = fuzz.partial_ratio(b[0], name_string)

        ent_a = a[1]
        ent_b = b[1]

        def calc_match_weight(obj) -> bool:
            op = getattr(obj, 'get_match_weight', None)
            if callable(op):
                return obj.get_match_weight()
            else:
                return 0.0

        sym_set_a = a[1].symbol_set if hasattr(a[1], 'symbol_set') else None
        sym_set_b = b[1].symbol_set if hasattr(b[1], 'symbol_set') else None

        match_weight_a = calc_match_weight(ent_a)
        match_weight_b = calc_match_weight(ent_b)

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
        print('\tMatches ' + f"{[f'{entity.names[0]} ({entity.symbol_set}-{entity.id_code}) (score {score}, match weight {entity.get_match_weight()})' for (name, entity, score) in matches]}")

    return matches[0][1], name_string.replace(matches[0][0], '').strip().replace('  ', ' ')

def symbol_set_from_name(schema, item, verbose:bool=False) -> SymbolSet:
    if item is None or schema is None:
        return None
    if isinstance(item, SymbolSet):
        return item

    if not isinstance(item, str):
        print(f"Can't parse symbol set from item {item}", file=sys.stderr)
        return None

    # Guess from names
    sym_set_candidates = schema.symbol_sets.values()
    sym_set, sym_set_name = fuzzy_match(schema, item, sym_set_candidates, verbose=verbose)
    return sym_set


def name_to_symbol(name: str, schema:Schema, verbose: bool = False, limit_to_symbol_sets:list=[], templates:list=[]) -> Symbol:
    """
    Function to return a NATOSymbol object from the provided name, using a best guess
    :param name: The string representing the name to construct a best-guess symbol from, e.g. "Friendly infantry platoon"
    :param schema: The symbol schema to use
    :param verbose: Whether to print ancillary information during execution; defaults to false.
    :param limit_to_symbol_sets: A list of symbol set objects or names to restrict guessing to
    :return:
    """

    if not Schema:
        print('Schema must be provided for name_to_symbol', file=sys.stderr)
        return None

    templates_to_use = schema.templates + templates

    limit_to_symbol_sets = copy.copy(limit_to_symbol_sets)

    proc_name_string = name
    if verbose:
        print(f'Matching "{name}"')

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
        limit_to_symbol_sets = [symbol_set_from_name(schema, item) for item in limit_to_symbol_sets if symbol_set_from_name(schema, item) is not None]
    else:
        limit_to_symbol_sets = None

    if verbose and limit_to_symbol_sets is not None:
        print(f'\tLimiting to symbol sets {[e.names[0] for e in limit_to_symbol_sets]}')
    
    # Sanitize string
    proc_name_string = proc_name_string.lower()
    proc_name_string = re.sub('[ \t\n]+', ' ', proc_name_string).strip()

    if verbose:
        print(f'\tMatching "{proc_name_string}"')

    # Step 0: Check for templates
    template: template.Template = None
    template, new_name_string = fuzzy_match(schema, proc_name_string, templates_to_use, print_candidates=True)
    ret_symbol: Symbol = None

    if template is not None:
        proc_name_string = new_name_string
        if verbose:
            print(f"\tMatches template \"{template.names[0]}\" leaving \"{proc_name_string}\"; affiliation is {'not ' if template.affiliation_is_flexible else ''}fixed: {template.symbol}")

        ret_symbol = copy.copy(template.symbol)
        ret_symbol.symbol_set = template.symbol.symbol_set
    else:
        ret_symbol = Symbol()

    ret_symbol.schema = schema

    # Step 1: Detect standard identity
    if template is None or template.affiliation_is_flexible:
        affiliation, new_name_string = fuzzy_match(schema, proc_name_string.lower(), schema.affiliations.values(), match_longest=True)

        if affiliation is None:
            print("\tUnable to determine standard identity; assuming unknown")
            affiliation = [si for si in schema.affiliations.values() if si.names[0] == 'unknown'][0]
        else:
            proc_name_string = new_name_string

        if verbose:
            print(f'\tAssuming affiliation "{affiliation.names[0]}" leaving "{proc_name_string}"')

        ret_symbol.affiliation = affiliation

    # Assume context is reality
    ret_symbol.context = schema.contexts['0']

    # Amplifier
    prerun_amplifier = False

    if template is None or template.amplifier_is_flexible:
        candidate_amplifiers = [amp for amp in schema.amplifiers.values() if amp.prerun]

        # Limit to given symbol sets
        if limit_to_symbol_sets is not None:
            candidate_amplifiers = [amp for amp in candidate_amplifiers if amp.applies_to_any_in_symbol_sets(limit_to_symbol_sets)]

        amplifier, new_name_string = fuzzy_match(schema, proc_name_string, candidate_amplifiers, match_longest=True)
        if amplifier is not None:
            proc_name_string = new_name_string
            if verbose:
                print(f'\tAssuming amplifier "{amplifier.names[0]}" leaving "{proc_name_string}"')
            prerun_amplifier = True

        ret_symbol.amplifier = amplifier


    # Entity type
    if template is None or template.entity_is_flexible:
        candidates = schema.get_flat_entities()

        # Limit to symbol sets
        if limit_to_symbol_sets is not None:
            candidates = [c for c in candidates if c.is_in_any_of_symbol_sets(limit_to_symbol_sets)]

        # Limit by amplifiers TODO
        if ret_symbol.amplifier is not None:
            if verbose:
                print(f"\tLimiting to symbol sets \"{[e.names[0] for e in ret_symbol.amplifier.get_applicable_symbol_sets(schema)]}\" due to amplifier \"{ret_symbol.amplifier.names[0]}\"")
            candidates = [c for c in candidates if ret_symbol.amplifier.applies_to_entity(c)]

        entity_type, new_name_string = fuzzy_match(schema, proc_name_string, candidates, match_longest=True, verbose=verbose)

        symbol_set = None
        if entity_type is None:
            print(f"\tWARNING: Unable to determine entity type from string \"{proc_name_string}\"; defaulting to land unit")
            if limit_to_symbol_sets is None or len(limit_to_symbol_sets) < 1:
                symbol_set = [set for set in schema.symbol_sets.values() if set.names[0] == 'land unit'][0]
            else:
                symbol_set = limit_to_symbol_sets[0]

            ret_symbol.entity = symbol_set.entities.get('000000', None)
            ret_symbol.symbol_set = symbol_set
        else:
            symbol_set = entity_type.symbol_set
            proc_name_string = new_name_string
            ret_symbol.symbol_set = symbol_set
            ret_symbol.entity = entity_type

            if verbose:
                name = entity_type.names[0] if len(entity_type.names) > 0 else ''
                print(f'\tAssuming entity "{name}" ({entity_type.id_code}) ' + 
                    f'from symbol set "{entity_type.symbol_set.names[0]}" leaving \"{proc_name_string}\"')

    # Amplifier post-run
    if (template is None or template.amplifier_is_flexible) and not prerun_amplifier:
        ret_symbol.amplifier = None
        candidate_amplifiers = [amp for amp in schema.amplifiers.values() if amp.applies_to_entity(ret_symbol.entity)]
        amplifier, new_name_string = fuzzy_match(schema, proc_name_string, candidate_amplifiers, match_longest=True)
        if amplifier is not None:
            proc_name_string = new_name_string
        ret_symbol.amplifier = amplifier

    # Double-check amplifier
    if prerun_amplifier and ret_symbol.amplifier is not None and not ret_symbol.amplifier.applies_to_symbol_set(ret_symbol.symbol_set):
        if not ret_symbol.amplifier.applies_to_symbol_set(ret_symbol.symbol_set):
            print('No symset apply')
        if not ret_symbol.amplifier.applies_to_dimension(ret_symbol.symbol_set.dimension):
            print(f'No dimension {ret_symbol.amplifier.applies_to}')
        print(f'Removing amplifier "{ret_symbol.amplifier.names[0]}" due to mismatch with symbol set {ret_symbol.symbol_set}')
        ret_symbol.amplifier = None

    if verbose:
        if ret_symbol.amplifier is not None:
            print(f'\tConfirming amplifier "{ret_symbol.amplifier.names[0]}" leaving "{proc_name_string}"')
        else:
            print('\tNo modifier assigned')

    # Find task force / headquarters / dummy
    if template is None or template.hqtfd_is_flexible:

        candidates = [hc for hc in schema.hqtfds.values() if not hc.matches_blacklist(proc_name_string) and hc.applies_to_symbol_set(ret_symbol.symbol_set)]

        hqtfd, new_name_string = fuzzy_match(schema, proc_name_string,
                                             [code for code in schema.hqtfds.values() if code in candidates],
                                             match_longest=True)
        if hqtfd is not None:
            proc_name_string = new_name_string
            if verbose:
                print(f'\tAssuming HQTFD code "{hqtfd.names[0]}" leaving "{proc_name_string}"')

        ret_symbol.hqtfd = hqtfd

    # Find status code
    if template is None or template.status_is_flexible:
        # print([status.names for status in symbol_schema.statuses.values()])
        status_code, new_name_string = fuzzy_match(schema, proc_name_string,
                                                   [code for code in schema.statuses.values()],
                                                   match_longest=True)
        if status_code is not None:
            proc_name_string = new_name_string
            if verbose:
                print(f'\tAssuming status code "{status_code.names[0]}" leaving "{proc_name_string}"')

        ret_symbol.status = status_code

    # Find modifiers

    # Assemble options
    modifier_candidates = []
    mod_candidate_sets = {}
    for mod_set in [1, 2]:
        if template is None or getattr(template, f'modifier_{mod_set}_is_flexible'):
            sym_set_mods = list(getattr(symbol_set, f'm{mod_set}').values())
            modifier_candidates += sym_set_mods
            for c in sym_set_mods:
                mod_candidate_sets[c] = mod_set

            for extra_symbol_set in schema.symbol_sets.values():
                if extra_symbol_set.common:
                    modifier_candidates += list(getattr(extra_symbol_set, f'm{mod_set}').values())
                    for c in sym_set_mods:
                        mod_candidate_sets[c] = mod_set

    # Pick the modifier
    mod, new_name_string = fuzzy_match(schema, proc_name_string, modifier_candidates, match_longest=True, print_candidates=True)

    if mod is not None:
        proc_name_string = new_name_string
        mod_set = mod_candidate_sets[mod]

        if verbose:
            print(f'\tAssuming modifier {mod_set} "{mod.names[0]}" ({mod.id_code}) from "{mod.symbol_set.names[0]}" leaving "{proc_name_string}"')

        setattr(ret_symbol, f'modifier_{mod_set}', mod)

    return ret_symbol

if __name__ == '__main__':

    TEST_NAMES = [
        'friendly wheeled x infantry platoon',
        'hostile amphibious artillery battery HQ',
        "joker network",
        "neutral MILCO general",
        "enemy attack planetary lander",
        "assumed friend space station",
        "friendly military base [land installation]",
        "neutral infantry battalion HQ unit",
        "hostile wheeled x MLRS artillery battalion"
    ]

    schema = Schema.load_from_directory()

    test_dir = os.path.join(os.path.dirname(__file__), '..', 'test')
    os.makedirs(test_dir, exist_ok=True)

    template_list = Template.load_from_file('example_template.yml', schema=schema)

    for name in TEST_NAMES:
        print(f'Testing "{name}"')
        symbol = name_to_symbol(name=name, schema=schema, verbose=True, templates=template_list)       
        svg = symbol.get_svg()

        with open(os.path.join(test_dir, f'{name}.svg'), 'w') as out_file:
            out_file.write(svg)

    pass