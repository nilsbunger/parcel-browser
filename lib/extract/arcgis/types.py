from enum import Enum
import sys

if sys.version_info >= (3, 11):
    raise ImportError("Update enums here to StrEnum when on 3.11")


class GeoEnum(Enum):
    santa_ana = "sta"
    san_diego = "sd"


class GisDataTypeEnum(Enum):
    parcel = "parcel"
    zoning = "zoning"
