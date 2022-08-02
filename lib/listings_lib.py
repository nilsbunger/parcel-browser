from __future__ import annotations

import re

from world.models import PropertyListing, Parcel


street_suffixes = [
    'dr', 'drive', 'way', 'ave', 'avenue', 'ct', 'court', 'blvd', 'st', 'street', 'pl', 'place', 'rd', 'road', 'ln',
    'lane', 'cove', 'cir', 'circle', 'w']

normalize_suffix = {
    'cove': 'cv',
    'court': 'ct',
    'street': 'st',
    'place': 'pl',
    'circle': 'cir',
    'drive': 'dr',
    'road': 'rd',
    'lane': 'ln',
    'w': 'way'
}

normalize_prefix = {
    'north': 'n',
    'south': 's',
    'east': 'e',
    'west': 'w'
}


def listing_to_parcel(l: PropertyListing) -> (Parcel | None, str | None):
    """ Take a current property listing object, and find its associated Parcel"""
    return address_to_parcel(l.addr)


def address_to_parcel(addr: str) -> (Parcel | None, str | None):
    street_suffix = None
    street_prefix = None
    addr_normalized = re.sub(r'\.', '', addr.lower())
    addr_num, *rest = addr_normalized.split()
    # If the first word needs to be normalized, do so:
    if rest[0] == 'mount':
        rest[0] = 'mt'
    if len(rest) > 1:
        if rest[0] in ['south', 'north', 'east', 'west', 'n', 'w', 'e', 's']:
            street_prefix = normalize_prefix.get(rest[0], rest[0])
            rest = rest[1:]
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
        parcels = Parcel.objects.filter(
            situs_addr=addr_num, situs_stre__istartswith=street_name)
    except Exception as e:
        print(f"Error processing {addr_normalized}")
        return None, 'dberror'
    matched_parcel = None
    if len(parcels) > 1:
        # more than one match using street name -- see if the street suffix ('way', 'rd', ...) disambiguates it
        matched_parcel_candidates = list()
        for p in parcels:
            if p.situs_suff and (p.situs_suff.lower() == street_suffix):
                matched_parcel_candidates.append(p)
        if len(matched_parcel_candidates) == 1:
            matched_parcel = matched_parcel_candidates[0]
        else:
            print(f"Multiple matches ({len(parcels)}) for {addr_normalized}!")
            return None, 'multimatch'
    elif len(parcels) == 0:
        if hyphenated_addr_num:
            # Need to build out this case: we found a hyphenated address, but the first address didn't work.
            # Maybe another address in the hyphen range would?
            raise
        print(f"No match in Parcel table for {addr_normalized}")
        return None, 'unmatched'
    else:
        # Found exactly one match, that's good
        matched_parcel = parcels[0]
    return matched_parcel, None
