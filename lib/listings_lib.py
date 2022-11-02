from __future__ import annotations

import re
import traceback
from typing import List

from django.db.models.expressions import RawSQL

from world.models import PropertyListing, Parcel


street_suffixes = [
    "dr",
    "drive",
    "way",
    "ave",
    "avenue",
    "ct",
    "court",
    "blvd",
    "boulevard",
    "st",
    "street",
    "pl",
    "place",
    "rd",
    "road",
    "ln",
    "lane",
    "cove",
    "cv",
    "cir",
    "circle",
    "glen",
    "gln",
    "w",
    "loop",
    "point",
    "pt",
    "trail",
    "trl",
    "ridge",
    "rdg",
    "highway",
    "hwy",
    "parkway",
    "pkwy",
    "row",
    "terrace",
    "ter",
    "terr",
    "bend",
]

normalize_suffix = {
    "avenue": "ave",
    "bend": "bnd",
    "boulevard": "blvd",
    "circle": "cir",
    "court": "ct",
    "cove": "cv",
    "drive": "dr",
    "highway": "hwy",
    "lane": "ln",
    "place": "pl",
    "point": "pt",
    "road": "rd",
    "parkway": "pkwy",
    "ridge": "rdg",
    "street": "st",
    "terrace": "ter",
    "terr": "ter",
    "trail": "trl",
    "w": "way",
    "glen": "gln",
}

normalize_prefix = {"north": "n", "south": "s", "east": "e", "west": "w"}


# TODO: THIS IS NOT COMPLETE - MEANT TO BE AN ADDRESS MATCHER
def address_to_parcels_loose(addr: str) -> List[Parcel]:
    """Take a street address, and return any that loosely match, best match on top. For typeahead matching"""
    addr_normalized = re.sub(r"\.", "", addr.lower())
    addr_parts = addr_normalized.split()
    pquery = Parcel.objects.annotate(str_situs_addr=RawSQL("select cast(situs_addr as VARCHAR)", ()))
    if addr_parts[0].isnumeric():
        pquery = pquery.filter(str_situs_addr__regex=r"%s" % addr_parts[0])
        x = addr_parts.pop()
    # pquery = pquery.filter(str_situs_str)
    # Concatenating address in postgres:
    # select apn, concat_ws(
    #    ' ', situs_pre_field, situs_addr, situs_stre, situs_suff, situs_post
    #    ) as addr from world_parcel

    # Using pg_tgrm extension (Trigram word similarity)
    # CREATE EXTENSION btree_gin;
    # CREATE EXTENSION pg_trgm;
    # CREATE OR REPLACE FUNCTION immutable_concat_ws(text, VARIADIC text[])
    # create index str_search_try_index on world_parcel using GIN (immutable_concat_ws(' ', situs_pre_field, situs_addr::text, situs_stre, situs_suff, situs_post));
    # https://leandronsp.com/a-powerful-full-text-search-in-postgresql-in-less-than-20-lines


def address_to_parcel(
    addr: str,
    jurisdiction: str,
    neighborhood: str = None,
) -> (Parcel | None, str | None):
    """Take a street address and look for a matching Parcel. Return the Parcel or an error string"""
    street_suffix = None
    street_prefix = None
    addr_normalized = re.sub(r"\.", "", addr.lower())
    addr_num, *rest = addr_normalized.split()
    # do more address normalization if the address broke up properly:
    if len(rest) == 0:
        print(f"Error, address is single-word: {addr_normalized}")
        return None, "error_single_word_address"
    if rest[0] == "mount":
        rest[0] = "mt"
    if rest[0] == "saint":
        rest[0] = "st"
    if len(rest) > 2:
        if rest[0] in ["south", "north", "east", "west", "n", "w", "e", "s"]:
            street_prefix = normalize_prefix.get(rest[0], rest[0])
            rest = rest[1:]
    # Check for a postfix and remove if present
    if rest[-1] in ["n", "s", "w", "e"]:
        postfix = rest[-1]
        rest = rest[:-1]
    # Separate the street suffix if it exists
    if rest and (rest[-1] in street_suffixes):
        street_name = " ".join(rest[:-1])
        # get normalized street suffix if it exists... otherwise use the one given.
        street_suffix = normalize_suffix.get(rest[-1], rest[-1])
    else:
        street_name = " ".join(rest)
    # Use first address of a hyphenated address range
    hyphenated_addr_num = re.match(r"(\d+)-(\d+)", addr_num)
    if hyphenated_addr_num:
        print(f"Hyphenated address -- {addr_normalized}")
        addr_num = hyphenated_addr_num.groups()[0]

    try:
        parcels_exact = Parcel.objects.filter(
            situs_addr=addr_num,
            situs_stre__iexact=street_name,
        )
        parcels_inexact = Parcel.objects.filter(
            situs_addr=addr_num,
            situs_stre__istartswith=street_name,
        )
    except ValueError as e:
        # This can happen when address has a non-number in it. allow it to pass for now
        print(f"Error processing {addr_normalized} {str(e)}")
        return None, "dberror-valueerror"
    except Exception as e:
        print(f"Error processing {addr_normalized} {str(e)}")
        traceback.print_exc()
        return None, "dberror"
    # repeat loop twice, looking at exact match first.
    for parcels in [parcels_exact, parcels_inexact]:
        matched_parcel = None
        if len(parcels) == 1:
            # exact match but check jurisdiction
            if parcels[0].situs_juri == jurisdiction:
                # happy path - exact match. get out of here.
                return parcels[0], None
            else:
                return None, "match_out_of_jurisdiction"
        elif len(parcels) == 0:
            # no match, but continue to second loop if needed
            continue
        # more than one match -- see if the street suffix ('way', 'rd', ...), prefix ('e', 'w', ...)
        # or jurisdiction ('SD') disambiguates it
        # We track jurisdition because if we DO match in another jurisdiction, we know we didn't miss anything.
        matched_parcel_candidates = list()
        matched_jurisdiction_candidates = list()
        jurisdictions = set()
        for p in parcels:
            if not p.situs_pre_field or (p.situs_pre_field and (p.situs_pre_field.lower() == street_prefix)):
                if not street_suffix or (p.situs_suff.lower() == street_suffix):
                    matched_parcel_candidates.append(p)
                jurisdictions.add(p.situs_juri)
            # keep jurisdiction match loose, since prefix and suffix are not always present
            if p.situs_juri == jurisdiction:
                matched_jurisdiction_candidates.append(p)
        if len(matched_jurisdiction_candidates) == 1:
            return matched_jurisdiction_candidates[0], None
        elif len(matched_jurisdiction_candidates) == 0:
            return None, "match_out_of_jurisdiction"
        elif len(matched_parcel_candidates) == 1 and matched_parcel_candidates[0].situs_juri == jurisdiction:
            return matched_parcel_candidates[0], None
        else:
            print(f"Multiple matches ({len(parcels)}) for {addr_normalized} in jurisdiction {jurisdiction}")
            return None, f"multimatch_{jurisdictions}"
    # After exact and inexact attempts, we're still here, and nothing matched.
    if hyphenated_addr_num:
        # Need to build out this case: we found a hyphenated address, but the first address didn't work.
        # Maybe another address in the hyphen range would?
        print(f"Error processing {addr_normalized}: hyphenated address we didn't find")
        return None, "dberror"
    print(f"No match in Parcel table for {addr_normalized}, {neighborhood}")
    return None, "unmatched"
