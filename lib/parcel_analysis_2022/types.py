from dataclasses import dataclass
from enum import Enum
from typing import Union

from shapely.geometry import MultiPolygon, Polygon

from world.models import Parcel

""" CheckResultEnum represents the result of an analysis check """


# Note: Inheriting Enum from str allows JSON serialization.
# See https://stackoverflow.com/questions/24481852/serialising-an-enum-member-to-json
class CheckResultEnum(str, Enum):
    passed: str = "passed"
    assumed_pass: str = "assumed_pass"
    likely_passed: str = "likely_passed"
    not_run: str = "not_run"
    uncertain: str = "uncertain"
    likely_failed: str = "likely_failed"
    failed: str = "failed"
    error: str = "error"

    def or_check(self, other: "CheckResultEnum") -> "CheckResultEnum":
        if self.passed in [self, other]:
            return CheckResultEnum(self.passed)
        elif self.assumed_pass in [self, other]:
            return CheckResultEnum(self.assumed_pass)
        elif self.likely_passed in [self, other]:
            return CheckResultEnum(self.likely_passed)
        elif self.not_run in [self, other]:
            return CheckResultEnum(self.not_run)
        elif self.uncertain in [self, other]:
            return CheckResultEnum(self.uncertain)
        elif self.likely_failed in [self, other]:
            return CheckResultEnum(self.likely_failed)
        elif self.failed in [self, other]:
            return CheckResultEnum(self.failed)
        elif self.error in [self, other]:
            return CheckResultEnum(self.error)

    def and_check(self, other: "CheckResultEnum") -> "CheckResultEnum":
        if self.error in [self, other]:
            return CheckResultEnum(self.error)
        elif self.failed in [self, other]:
            return CheckResultEnum(self.failed)
        elif self.not_run in [self, other]:
            return CheckResultEnum(self.not_run)
        elif self.likely_failed in [self, other]:
            return CheckResultEnum(self.likely_failed)
        elif self.uncertain in [self, other]:
            return CheckResultEnum(self.uncertain)
        elif self.likely_passed in [self, other]:
            return CheckResultEnum(self.likely_passed)
        elif self.assumed_pass in [self, other]:
            return CheckResultEnum(self.assumed_pass)
        elif self.passed in [self, other]:
            return CheckResultEnum(self.passed)
        else:
            raise ValueError("Invalid CheckResultEnum value")


@dataclass
class ParcelDC:
    geometry: MultiPolygon
    model: Parcel


# Helper type to define a MultiPolygon or Polygon
Polygonal = Union[Polygon, MultiPolygon]
