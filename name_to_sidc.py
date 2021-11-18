from symbol_schema import SymbolSchema
from fuzzywuzzy import fuzz
import re

def name_to_sidc(name_string:str, symbol_schema:SymbolSchema):
    EMPTY_SIDC = ''
    # Sanitize string
    # Remove extra white spaces
    name_string = name_string.lower()
    name_string = re.sub('[ \t\n]+', ' ', name_string).strip()
    print(f'Matching "{name_string}"')

    # Step 1: Detect standard identity
    si_matches = {}
    for si in symbol_schema.standard_identities.values():
        max_ratio = 0
        for name in si.get_names():
            fuzzy_dist = fuzz.token_set_ratio(name, name_string)
            max_ratio = max(max_ratio, fuzzy_dist)
        si_matches[si.name] = max_ratio
    max_si_match = max(si_matches.items(), key=lambda si_match: si_match[1])
    if max_si_match[1] < 50:
        print("ERROR: No standard identity allegiance found reliably")
        return EMPTY_SIDC
    print('Assuming standard identity \"' + max_si_match[0] + "\"")





    return ''