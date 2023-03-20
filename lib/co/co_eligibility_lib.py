import re
from abc import ABC, abstractmethod
from typing import Any

from django.contrib.gis.db.models.functions import Distance
from pydantic import BaseModel

from lib.crs_lib import meters_to_latlong
from lib.types import CheckResultEnum
from world.models import Parcel, Roads, ZoningBase
from world.models.models import AnalyzedRoad


class EligibilityCheck(BaseModel):
    name: str
    description: str
    result: CheckResultEnum = CheckResultEnum.not_run
    notes: list[str] = []
    children: list["EligibilityCheck"] = []

    def __init__(self, name: str, description: str, **data: Any) -> None:
        super().__init__(name=name, description=description, **data)
        # noinspection PyTypeChecker

    # noinspection PyTypeChecker
    @abstractmethod
    def run(self, *args, **kwargs) -> CheckResultEnum:
        raise AssertionError("run() needs to be implemented in child class")

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class LogicCheck(EligibilityCheck, ABC):
    def __init__(self, name: str, description: str, checks: list[EligibilityCheck]) -> None:
        super().__init__(name, description)
        self.children = checks


class AndCheck(LogicCheck):
    def __init__(self, checks: list[EligibilityCheck]) -> None:
        super().__init__("And", "All checks must pass", checks)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        self.result: CheckResultEnum = CheckResultEnum.passed
        for check in self.children:
            self.result = self.result.and_check(check.run(parcel))
            if self.result in [CheckResultEnum.error, CheckResultEnum.failed]:
                return self.result
        return self.result


class OrCheck(LogicCheck):
    def __init__(self, checks: list[EligibilityCheck]) -> None:
        super().__init__("Or", "At least one check must pass", checks)

    def run(self, parcel: Parcel):
        raise AssertionError("Finish implementation, see AndCheck")
        return any(check.run(parcel) for check in self.checks)


# ----- SPECIFIC TESTS FOR AB 2011 COMMERCIAL ZONING IN SAN DIEGO ------ #
# Office, retail or parking is a Principally Permitted use (no Conditional User Permit or Discretionary Review required)
# Anything w/ CC, CN, CO, CR, CP, or CV is eligible
class PrincipallyPermittedUseCheck(EligibilityCheck):
    def __init__(self) -> None:
        description = "Office, retail or parking is a Principally Permitted use (no Conditional User Permit or Discretionary Review required)"
        super().__init__("Principally Permitted Use", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        zones = ZoningBase.objects.using("basedata").filter(geom__intersects=parcel.geom)
        if len(zones) == 0:
            self.notes.append("No zoning found for this parcel")
            # noinspection PyTypeChecker
            self.result = CheckResultEnum.error
            return self.result
        zone_names: list[str] = [zone.zone_name for zone in zones]
        matches = [bool(re.match(r"^(CC|CN|CO|CR|CP|CV)", zone_name)) for zone_name in zone_names]
        self.notes.append("Zone(s): " + ", ".join(zone_names))
        if all(matches):
            # noinspection PyTypeChecker
            self.result = CheckResultEnum.passed
        elif not any(matches):
            # noinspection PyTypeChecker
            self.result = CheckResultEnum.failed
        else:
            # noinspection PyTypeChecker
            self.result = CheckResultEnum.uncertain
            self.notes.append("Overlapping zones, some of which are eligible")
        # noinspection PyTypeChecker
        return self.result


class UrbanizedAreaCheck(EligibilityCheck):
    def __init__(self) -> None:
        description = "Located within a city with an urbanized area or urban use area"
        super().__init__("Urbanized Area", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class DevelopedNeighborsCheck(EligibilityCheck):
    def __init__(self) -> None:
        description = "At least 75 percent of the perimeter of the site adjoins parcels that are developed with urban uses. For purposes of this subdivision, parcels that are only separated by a street or highway shall be considered to be adjoined."
        super().__init__("Developed Neighbors", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class CommercialCorridorCheck(EligibilityCheck):
    def __init__(self) -> None:
        description = "Abuts a commercial corridor (a local road 70 to 150 feet wide)"
        super().__init__("Commercial Corridor", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        x = AnalyzedRoad.objects.using("basedata").filter(
            road__rd30pred=parcel.situs_pre_field,
            road__rd30name=parcel.situs_stre,
            road__rd30sfx=parcel.situs_suff,
            road__abloaddr__lte=parcel.situs_addr,
            road__abhiaddr__gte=parcel.situs_addr,
        )
        parcel_addr = f"{parcel.situs_addr} {parcel.situs_stre}"
        if len(x) == 0:
            # noinspection PyTypeChecker
            self.result = CheckResultEnum.error
            self.notes.append(f"Didn't find road for addr = {parcel_addr} for this parcel")
        elif len(x) > 1:
            # noinspection PyTypeChecker
            self.result = CheckResultEnum.error
            self.notes.append(f"Found multiple roads for addr = {parcel_addr} for this parcel")
        else:
            road = x[0]
            if road.status != road.Status.OK:
                # noinspection PyTypeChecker
                self.result = CheckResultEnum.error
                self.notes.append(f"Found road for {parcel_addr}, but road analysis failed with error: {road.status}")
                return self.result
            min_width_meters = 70 / 3.28084
            max_width_meters = 150 / 3.28084
            low_width = round(road.low_width * 3.28084, 1)
            high_width = round(road.high_width * 3.28084, 1)
            width_range = f"{low_width} ft" if (low_width == high_width) else f"{low_width} to {high_width} ft"

            if road.low_width >= min_width_meters and road.high_width <= max_width_meters:
                # noinspection PyTypeChecker
                self.result = CheckResultEnum.passed
                self.notes.append(f"Road at {parcel_addr} is {width_range} wide")
            elif road.high_width < min_width_meters:
                # noinspection PyTypeChecker
                self.result = CheckResultEnum.failed
                self.notes.append(f"Road at {parcel_addr} is too narrow ({width_range})")
            elif road.low_width > max_width_meters:
                # noinspection PyTypeChecker
                self.result = CheckResultEnum.failed
                self.notes.append(f"Road at {parcel_addr} is too wide ({width_range})")
            else:
                # noinspection PyTypeChecker
                self.result = CheckResultEnum.uncertain
                self.notes.append(f"Part of road at {parcel_addr} is in range ({width_range})")
        return self.result


class CommercialFrontageCheck(EligibilityCheck):
    def __init__(self) -> None:
        description = "Frontage along the commercial corridor of a minimum of 50 feet"
        super().__init__("Commercial Frontage", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class UnderAcresCheck(EligibilityCheck):
    def __init__(self, acres: int) -> None:
        description = f"Not greater than {acres} acres"
        super().__init__(f"Under {acres} Acres", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class NoHousingCheck(EligibilityCheck):
    # - **Prior protected housing / historic structure.
    # - ** Existing housing or historic structure on the lot
    # - **Demolition of ANY type protected housing**
    #     - Housing with deed restricted rents, OR any form of rent or price control
    #     - Tenant occupied housing (within 10 yrs), excluding manager's units
    #     - lot where protected housing was demolished within 10 yrs
    #     - historic structure
    #     - 1 to 4 dwelling units
    #     - vacant and zoned for housing but not multifamily
    def __init__(self) -> None:
        description = "There can't be any housing on the lot in the past N years (CHECK DETAILS)"
        super().__init__("NoHousingInPast", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class NoIndustrialNeighborsCheck(EligibilityCheck):
    def __init__(self) -> None:
        description = "Not a site or adjoined to any site where more than one-third of the square footage on the site is dedicated to industrial use"
        super().__init__("No Industrial Neighbors", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class NoMobileHomePark(EligibilityCheck):
    def __init__(self) -> None:
        description = (
            "Not a lot governed under the Mobilehome Residency Law, RV Park Law, or Special Occupancy Parks Acts"
        )
        super().__init__("No Mobile Home Park", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class TribalResourceCheck(EligibilityCheck):
    def __init__(self) -> None:
        description = "Not located on a site that contains tribal resources"
        super().__init__("No Tribal Resource", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class NotHighFireHazardCheck(EligibilityCheck):
    def __init__(self) -> None:
        description = "Not located in a very high fire hazard severity zone"
        super().__init__("Not High Fire Hazard", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class NotNearFreeway(EligibilityCheck):
    def __init__(self) -> None:
        description = "Not located within 500 feet of a freeway, including limited access roads(?)"
        super().__init__("Not Near Freeway", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # for fast (not 100% accurate) distance calculations, keep calculation in degrees.
        # Lat and long delta aren't necessarily the same, so we use the average of them.
        (lat_delta, long_delta) = meters_to_latlong(
            500 / 3.28, baselat=parcel.geom.centroid.y, baselong=parcel.geom.centroid.x
        )

        roads = (
            Roads.objects.filter(funclass="F")
            .filter(geom__dwithin=(parcel.geom.centroid, (lat_delta + long_delta) / 2 * 1.5))
            .annotate(distance=Distance("geom", parcel.geom.centroid))
        )
        if len(roads) == 0:
            self.notes.append("No freeways within 500 feet")
            # noinspection PyTypeChecker
            self.result = CheckResultEnum.passed
            return self.result
        else:
            self.notes.append(f"Near freeway: {roads[0].rd30full}, {round(roads[0].distance.standard)} feet away")
            # noinspection PyTypeChecker
            self.result = CheckResultEnum.failed
            return self.result


class NotNearOilGas(EligibilityCheck):
    def __init__(self) -> None:
        description = "Not located within 3,200 feet of an oil or gas extraction well"
        super().__init__("Not Near Oil/Gas", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class NotNeighborhoodPlan(EligibilityCheck):
    def __init__(self) -> None:
        description = (
            "Not part of Neighborhood Plan (master planned community), unless multifamily is allowed in the plan"
        )
        super().__init__("Not Neighborhood Plan", description)

    def run(self, parcel: Parcel) -> CheckResultEnum:
        # noinspection PyTypeChecker
        return CheckResultEnum.not_run


class EligibilityCheckSuite:
    def __init__(self, check, name, description) -> None:
        self.check = check
        self.name = name
        self.description = description
        self.result = CheckResultEnum.not_run

    def run(self, parcel: Parcel) -> CheckResultEnum:
        self.result = self.check.run(parcel)
        return self.result


class AB2011Eligible(EligibilityCheckSuite):
    def __init__(self) -> None:
        name = "AB 2011 Eligible"
        description = "AB 2011 Eligible description"
        check = AndCheck(
            [
                PrincipallyPermittedUseCheck(),
                # UrbanizedAreaCheck(),
                # DevelopedNeighborsCheck(),
                CommercialCorridorCheck(),
                # CommercialFrontageCheck(),
                # UnderAcresCheck(5),
                # NoHousingCheck(),
                # NoIndustrialNeighborsCheck(),
                # NoMobileHomePark(),
                # TribalResourceCheck(),
                # NotHighFireHazardCheck(),
                NotNearFreeway(),
                # NotNearOilGas(),
                # NotNeighborhoodPlan(),
            ]
        )
        super().__init__(check, name, description)
