import sys
from enum import Enum

if sys.version_info >= (3, 12):
    raise ImportError("Update enums here to StrEnum when on 3.11")


class Juri(Enum):
    # Cities have a 2 or 3-letter abbreviation.
    santa_ana = "sta"
    san_diego = "sd"
    sf = "sf"

    # Counties, State, and large regions have a 4-letter abbreviation. Counties end in 'c'
    california = "cali"
    scag = "scag"
    orange_county = "orac"


class GisData(Enum):
    parcel = "parcel"
    zoning = "zoning"
    oppzone = "oppzone"
    tpa = "tpa"
    road = "road"
    he = "he"  # housing element
    reportall = "reportall"

    # postprocess raw data -- create / update wrapper models, find duplicates, etc.
    post = "post"

    # California resource areas from CTCAD/HCD Opportunity maps: https://www.treasurer.ca.gov/ctcac/opportunity.asp
    #   Not to be confused with Opportunity Zones.
    resource_level = "resource_level"


class EltAnalysisEnum(Enum):
    yigby = "yigby"
