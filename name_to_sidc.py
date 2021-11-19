from symbol_schema import SymbolSchema
from nato_symbol import  NATOSymbol
from fuzzywuzzy import fuzz
import re


def get_names_list(item) -> list:
    candidate_members = dir(item)
    if 'get_names' in candidate_members:
        return item.get_names()
    elif 'name' in candidate_members:
        return [item.name]
    elif 'names' in candidate_members:
        return item.names
    return []

def get_match_weights(name_string, candidates, match_type='partial_token_sort_ratio'):
    matches = []
    for candidate in candidates:
        candidate_names = get_names_list(candidate)
        if len(candidate_names) < 1:
            print("ERROR: No candidate names; skipping")
            continue
        max_ratio = 0
        for name in candidate_names:
            fuzzy_dist = getattr(fuzz, match_type)(name, name_string)
            max_ratio = max(max_ratio, fuzzy_dist)
        matches.append((candidate, max_ratio))
    return matches

def fuzzy_match(symbol_schema, name_string, candidate_list, match_threshold=50):
    # Step 1: calculate the number of words in candidate_list_of_lists
    matches = [] # Set of (candidate, weight) pairs
    for candidate in candidate_list:
        # Iterate over the possible names
        for candidate_name in get_names_list(candidate):
            name_sanitized = re.sub('[/ \t\n]+', ' ', candidate_name).strip().lower()
            name_sanitized = ''.join([c for c in name_sanitized if c.isalpha() or c == ' '])
            candidate_name_words = [word for word in name_sanitized.split(' ') if len(word) > 0]
            #print(candidate_name_words)

    return None
    # matches = get_match_weights(name_string, candidate_list_of_lists)
    #
    # if len(matches) < 1:
    #     # print("No matches")
    #     return None
    #
    # max_match_score = max(matches, key=lambda match: match[1])[1]
    # if max_match_score < match_threshold:
    #     # print(f"ERROR: No match for \"{name_string}\": \"{[get_names_list(item) for item in candidates]}")
    #     return None
    #
    # max_match_candidates = [match for match in matches if match[1] == max_match_score]
    # if len(max_match_candidates) < 2:
    #     # print(f'Match {max_match_candidates[0][0]}: {max_match_candidates[0][1]}')
    #     return max_match_candidates[0][0]
    # else:
    #     # Try searching for a full match
    #     # print([f'Match scores: {get_names_list(can[0])[0]} from \"{can[0].symbol_set if "symbol_set" in dir(can[0])
    #     # else ""}\" [{can[1]}]' for can in max_match_candidates])
    #     matches = get_match_weights(name_string, candidate_list_of_lists, 'ratio')
    #     max_match_score = max(matches, key=lambda match: match[1])[1]
    #     max_match_candidates = [match for match in matches if match[1] == max_match_score]
    #
    #     # print([f'Match scores: {get_names_list(can[0])[0]} from \"{can[0].symbol_set if "symbol_set" in dir(can[0])
    #     # else ""}\" [{can[1]}]' for can in max_match_candidates])
    #
    # weighted_max_candidates = [[can[0], can[0].match_weight] for can in max_match_candidates]
    #
    # # Pick most extreme of symbol set and individual match weight
    # if 'symbol_set' in dir(max_match_candidates[0][0]):
    #     for weight_can in weighted_max_candidates:
    #         sym_set = symbol_schema.symbol_sets[weight_can[0].symbol_set]
    #         if abs(sym_set.match_weight) > abs(weight_can[0].match_weight):
    #             weight_can[1] = sym_set.match_weight
    #
    # weighted_max_candidates = sorted(weighted_max_candidates, key=lambda item: item[1])
    # # print([f'Match scores: {get_names_list(can[0])[0]} from \"{can[0].symbol_set if "symbol_set" in dir(can[0])
    # # else ""}\" [{can[1]}]' for can in max_match_candidates])
    #
    # max_weight = max(can[1] for can in weighted_max_candidates)
    # weighted_max_candidates = [can for can in weighted_max_candidates if can[1] == max_weight]
    # # print(f'Max weight: {max_weight} / {weighted_max_candidates}')
    #
    # if len(weighted_max_candidates) <  2:
    #     return weighted_max_candidates[0][0]
    # else:
    #     # Front and back have same weight; pick the shortest-named one
    #     length_sorted_candidates = sorted(weighted_max_candidates, key=lambda item: len(get_names_list(item[0])[0]))
    #     # print(f'Weighted by length: {length_sorted_candidates}')
    #     return length_sorted_candidates[0][0]

def name_to_symbol(name_string:str, symbol_schema:SymbolSchema) -> NATOSymbol:
    EMPTY_SIDC = ''

    # Sanitize string
    # Remove extra white spaces
    name_string = name_string.lower()
    name_string = re.sub('[ \t\n]+', ' ', name_string).strip()
    print(f'Matching "{name_string}"')

    # Step 1: Detect standard identity
    standard_identity = fuzzy_match(symbol_schema, name_string, symbol_schema.standard_identities.values(), 50)

    if standard_identity is None:
        print("Unable to determine standard identity; assuming friendly")
        standard_identity = [si for si in symbol_schema.standard_identities.values() if si.name == 'friendly'][0]
    else:
        # Detect where the standard identity is in the string - modifiers go before, amplifiers go after
        si_splits = [0, len(name_string)-1]
        for name in standard_identity.get_names():
            matches = re.finditer(name, name_string)
            for match in matches:
                if match.start() > si_splits[0]:
                    si_splits[0] = match.start()
                if match.end() < si_splits[1]:
                    si_splits[1] = match.end()
        # Excise the standard identity from the string
        name_string = (name_string[:si_splits[0]] + name_string[si_splits[1]+1:]).strip()
        print(name_string)

    print(f'Assuming standard identity "{standard_identity.name}"')

    # mod_entity_combos, mod_entity_indexes = get_modifier_entity_combinations(symbol_schema)

    # Step 2: Detect entity type
    entity_type = fuzzy_match(symbol_schema, name_string, symbol_schema.get_flat_entities(), 50)

    if entity_type is None:
        print("Unable to determine entity type")
        return None

    symbol_set = symbol_schema.symbol_sets[entity_type.symbol_set]
    print(f'Assuming entity "{entity_type.name}" from symbol set "{symbol_set.name}"')

    # Detect where the entity is in the string - modifiers go before, amplifiers go after
    entity_splits = [0, len(name_string)-1]
    for name in entity_type.get_names():
        matches = re.finditer(name, name_string)
        for match in matches:
            if match.start() > entity_splits[0]:
                entity_splits[0] = match.start()
            if match.end() < entity_splits[1]:
                entity_splits[1] = match.end()

    post_entity_string = name_string[entity_splits[1]+1:].strip()
    pre_entity_string = name_string[:entity_splits[0]].strip()

    candidate_amplifiers = [amp for amp in symbol_schema.amplifiers.values() if amp.applies_to(symbol_set.id_code)]
    amplifier = fuzzy_match(symbol_schema, post_entity_string, candidate_amplifiers, 50)
    if amplifier is not None:
        print(f'Assuming amplifier "{amplifier.names[0]}"')

        # Excise amplifier name from post-entity string
        amplifier_splits = [0, len(post_entity_string) - 1]
        for name in get_names_list(amplifier):
            matches = re.finditer(name, post_entity_string)
            for match in matches:
                if match.start() > entity_splits[0]:
                    amplifier_splits[0] = match.start()
                if match.end() < entity_splits[1]:
                    amplifier_splits[1] = match.end()

        post_entity_string = (post_entity_string[:amplifier_splits[0]] + post_entity_string[amplifier_splits[1]+1:]).strip()
    else:
        print("Assuming no amplifier")

    name_string = pre_entity_string.strip() + ' ' + post_entity_string.strip()

    # Find modifiers

    ret_symbol:NATOSymbol = NATOSymbol(symbol_schema)
    ret_symbol.standard_identity = standard_identity
    ret_symbol.symbol_set = symbol_set
    ret_symbol.entity = entity_type
    ret_symbol.amplifier = amplifier

    return ret_symbol