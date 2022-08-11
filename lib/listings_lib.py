from __future__ import annotations

import re

from world.models import PropertyListing, Parcel


street_suffixes = [
    'dr', 'drive', 'way', 'ave', 'avenue', 'ct', 'court', 'blvd', 'boulevard', 'st', 'street', 'pl', 'place', 'rd', 'road', 'ln',
    'lane', 'cove', 'cv', 'cir', 'circle', 'glen', 'gln', 'w', 'loop', 'point', 'pt', 'trail', 'trl', 'ridge', 'rdg', 'highway', 'hwy',
    'parkway', 'pkwy', 'row', 'terrace', 'ter', 'terr', 'bend']

normalize_suffix = {
    'avenue': 'ave',
    'bend': 'bnd',
    'boulevard': 'blvd',
    'circle': 'cir',
    'court': 'ct',
    'cove': 'cv',
    'drive': 'dr',
    'highway': 'hwy',
    'lane': 'ln',
    'place': 'pl',
    'point': 'pt',
    'road': 'rd',
    'parkway': 'pkwy',
    'ridge': 'rdg',
    'street': 'st',
    'terrace': 'ter',
    'terr': 'ter',
    'trail': 'trl',
    'w': 'way',
    'glen': 'gln',
}

normalize_prefix = {
    'north': 'n',
    'south': 's',
    'east': 'e',
    'west': 'w'
}


def listing_to_parcel(l: PropertyListing) -> (Parcel | None, str | None):
    """ Take a current property listing object, and find its associated Parcel"""
    return address_to_parcel(l.addr, l.neighborhood)


def address_to_parcel(addr: str, neighborhood: str = None) -> (Parcel | None, str | None):
    """ Take a street address and look for a matching Parcel. Return the Parcel or an error string"""
    street_suffix = None
    street_prefix = None
    addr_normalized = re.sub(r'\.', '', addr.lower())
    addr_num, *rest = addr_normalized.split()
    # do more address normalization if the address broke up properly:
    if len(rest) == 0:
        print(f"Error, address is single-word: {addr_normalized}")
        return None,"error_single_word_address"
    if rest[0] == 'mount':
        rest[0] = 'mt'
    if rest[0] == 'saint':
        rest[0] = 'st'
    if len(rest) > 2:
        if rest[0] in ['south', 'north', 'east', 'west', 'n', 'w', 'e', 's']:
            street_prefix = normalize_prefix.get(rest[0], rest[0])
            rest = rest[1:]
    # Check for a postfix and remove if present
    if rest[-1] in ['n', 's', 'w', 'e']:
        postfix = rest[-1]
        rest = rest[:-1]
    # Separate the street suffix if it exists
    if rest[-1] in street_suffixes:
        street_name = ' '.join(rest[:-1])
        # get normalized street suffix if it exists... otherwise use the one given.
        street_suffix = normalize_suffix.get(rest[-1], rest[-1])
    else:
        street_name = ' '.join(rest)
    # Use first address of a hyphenated address range
    hyphenated_addr_num = re.match(r'(\d+)-(\d+)', addr_num)
    if hyphenated_addr_num:
        print(f"Hyphenated address -- {addr_normalized}")
        addr_num = hyphenated_addr_num.groups()[0]

    try:
        parcels_exact = Parcel.objects.filter(
            situs_addr=addr_num, situs_stre__iexact=street_name,)
        parcels_inexact = Parcel.objects.filter(
            situs_addr=addr_num, situs_stre__istartswith=street_name,)
    except Exception as e:
        print(f"Error processing {addr_normalized} {str(e)}")
        return None, 'dberror'
    # repeat loop twice, looking at exact match first.
    for parcels in [parcels_exact, parcels_inexact]:
        matched_parcel = None
        if len(parcels) == 1:
            # happy path - exact match. get out of here.
            return parcels[0], None
        elif len(parcels) == 0:
            # no match, but continue to second loop if needed
            continue
        # more than one match -- see if the street suffix ('way', 'rd', ...) or jurisdiction ('SD') disambiguates it
        # We track jurisdition because if we DO match in another jurisdiction, we know we didn't miss anything.
        matched_parcel_candidates = list()
        matched_jurisdiction_candidates = list()
        jurisdictions = set()
        for p in parcels:
            if p.situs_suff and (p.situs_suff.lower() == street_suffix):
                matched_parcel_candidates.append(p)
            jurisdictions.add(p.situs_juri)
            if p.situs_juri == 'SD':
                matched_jurisdiction_candidates.append(p)
        if len(matched_jurisdiction_candidates) == 1:
            return matched_jurisdiction_candidates[0], None
        elif len(matched_jurisdiction_candidates) == 0:
            return None, 'match_out_of_jurisdiction'
        elif len(matched_parcel_candidates) == 1 and matched_parcel_candidates[0].situs_juri == 'SD':
            return matched_parcel_candidates[0], None
        else:
            print(f"Multiple matches ({len(parcels)}) for {addr_normalized} in jurisdiction SD")
            return None, f'multimatch_{jurisdictions}'
    # After exact and inexact attempts, we're still here, and nothing matched.
    if hyphenated_addr_num:
        # Need to build out this case: we found a hyphenated address, but the first address didn't work.
        # Maybe another address in the hyphen range would?
        print("Error processing {addr_normalized}: hyphenated address we didn't find")
        return None, 'dberror'
    print(f"No match in Parcel table for {addr_normalized}, {neighborhood}")
    return None, 'unmatched'
