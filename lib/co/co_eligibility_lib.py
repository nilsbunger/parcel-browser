from abc import abstractmethod
from enum import Enum
import re
from typing import List

from pydantic import BaseModel

from world.models import Parcel, ZoningBase


class TestResultEnum(str, Enum):
    passed: str = "passed"
    assumed_pass: str = "assumed_pass"
    likely_passed: str = "likely_passed"
    not_run: str = "not_run"
    uncertain: str = "uncertain"
    likely_failed: str = "likely_failed"
    failed: str = "failed"
    error: str = "error"

    def or_test(self, other: "TestResultEnum") -> "TestResultEnum":
        if self.passed in [self, other]:
            return TestResultEnum(self.passed)
        elif self.assumed_pass in [self, other]:
            return TestResultEnum(self.assumed_pass)
        elif self.likely_passed in [self, other]:
            return TestResultEnum(self.likely_passed)
        elif self.not_run in [self, other]:
            return TestResultEnum(self.not_run)
        elif self.uncertain in [self, other]:
            return TestResultEnum(self.uncertain)
        elif self.likely_failed in [self, other]:
            return TestResultEnum(self.likely_failed)
        elif self.failed in [self, other]:
            return TestResultEnum(self.failed)
        elif self.error in [self, other]:
            return TestResultEnum(self.error)

    def and_test(self, other: "TestResultEnum") -> "TestResultEnum":
        if self.error in [self, other]:
            return TestResultEnum(self.error)
        elif self.failed in [self, other]:
            return TestResultEnum(self.failed)
        elif self.not_run in [self, other]:
            return TestResultEnum(self.not_run)
        elif self.likely_failed in [self, other]:
            return TestResultEnum(self.likely_failed)
        elif self.uncertain in [self, other]:
            return TestResultEnum(self.uncertain)
        elif self.likely_passed in [self, other]:
            return TestResultEnum(self.likely_passed)
        elif self.assumed_pass in [self, other]:
            return TestResultEnum(self.assumed_pass)
        elif self.passed in [self, other]:
            return TestResultEnum(self.passed)
        else:
            raise ValueError("Invalid TestResultEnum value")


class TestResult(BaseModel):
    result: TestResultEnum
    notes: list[str] = []
    children: list["TestResult"] = []


# zoned appropriately
class EligibilityTest:
    def __init__(self, name: str, description: str, test_function: callable):
        self.name = name
        self.description = description
        self.test_function = test_function

    def run(self, *args, **kwargs) -> TestResult:
        return self.test_function(*args, **kwargs)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class LogicTest(EligibilityTest):
    def __init__(self, name: str, description: str, tests: List[EligibilityTest]):
        super().__init__(name, description, self.run)
        self.tests = tests

    @abstractmethod
    def run(self, parcel: Parcel) -> TestResult:
        pass


class AndTest(LogicTest):
    def __init__(self, tests: List[EligibilityTest]):
        description = "All tests must pass"
        super().__init__("And", description, tests)

    def run(self, parcel: Parcel) -> TestResult:
        tr = TestResult(children=[test.run(parcel) for test in self.tests])
        result = TestResultEnum.passed


class OrTest(EligibilityTest):
    def __init__(self, tests: List[EligibilityTest]):
        description = "At least one test must pass"
        super().__init__("Or", description, tests)

    def run(self, parcel: Parcel) -> TestResult:
        return any(test.run(parcel) for test in self.tests)


# ----- SPECIFIC TESTS FOR AB 2011 COMMERCIAL ZONING IN SAN DIEGO ------ #
# Office, retail or parking is a Principally Permitted use (no Conditional User Permit or Discretionary Review required)
# Anything w/ CC, CN, CO, CR, CP, or CV is eligible
class PrincipallyPermittedUseTest(EligibilityTest):
    def __init__(self):
        description = "Office, retail or parking is a Principally Permitted use (no Conditional User Permit or Discretionary Review required)"
        super().__init__("Principally Permitted Use", description, self.run)

    def run(self, parcel: Parcel) -> TestResult:
        self.zones = ZoningBase.objects.using("basedata").filter(geom__intersects=parcel.geom)
        if len(self.zones) == 0:
            return TestResult(result=TestResultEnum.error, notes=["No zoning found for parcel"])
        zone_names: list[str] = [zone.zone_name for zone in self.zones]
        matches = [bool(re.match(r"^(CC|CN|CO|CR|CP|CV)", zone_name)) for zone_name in zone_names]
        notes = ["Zone(s): " + ", ".join(zone_names)]
        if all(matches):
            result = TestResultEnum.passed
        elif not any(matches):
            result = TestResultEnum.failed
        else:
            result = TestResultEnum.uncertain
            notes.append("Overlapping zones, some of which are eligible")
        return TestResult(result=result, notes=notes)


class UrbanizedAreaTest(EligibilityTest):
    def __init__(self):
        description = "Located within a city with an urbanized area or urban use area"
        super().__init__("Urbanized Area", description, self.run)

    def run(self, parcel: Parcel) -> TestResult:
        return TestResult(result=TestResult.result.not_run)


class DevelopedNeighborsTest(EligibilityTest):
    def __init__(self):
        description = "At least 75 percent of the perimeter of the site adjoins parcels that are developed with urban uses. For purposes of this subdivision, parcels that are only separated by a street or highway shall be considered to be adjoined."
        super().__init__("Developed Neighbors", description, self.run)

    def run(self, parcel: Parcel) -> TestResult:
        return TestResult(result=TestResult.result.not_run)


class CommercialCorridorTest(EligibilityTest):
    def __init__(self):
        description = "Abuts a commercial corridor (a local road 70 to 150 feet wide)"
        super().__init__("Commercial Corridor", description, self.run)

    def run(self, parcel: Parcel) -> TestResult:
        return TestResult(result=TestResult.result.not_run)


class CommercialFrontageTest(EligibilityTest):
    def __init__(self):
        description = "Frontage along the commercial corridor of a minimum of 50 feet"
        super().__init__("Commercial Frontage", description, self.run)

    def run(self, parcel: Parcel) -> TestResult:
        return TestResult(result=TestResult.result.not_run)


class UnderAcresTest(EligibilityTest):
    def __init__(self, acres):
        description = f"Not greater than {acres} acres"
        super().__init__(f"Under {acres} Acres", description, self.run)

    def run(self, parcel: Parcel) -> TestResult:
        return TestResult(result=TestResult.result.not_run)


class NoHousingTest(EligibilityTest):
    # - **Prior protected housing / historic structure.
    # - ** Existing housing or historic structure on the lot
    # - **Demolition of ANY type protected housing**
    #     - Housing with deed restricted rents, OR any form of rent or price control
    #     - Tenant occupied housing (within 10 yrs), excluding manager's units
    #     - lot where protected housing was demolished within 10 yrs
    #     - historic structure
    #     - 1 to 4 dwelling units
    #     - vacant and zoned for housing but not multifamily
    def __init__(self, acres):
        description = f"There can't be any housing on the lot in the past N years (CHECK DETAILS)"
        super().__init__(f"Under{acres}Acres", description, self.run)

    def run(self, parcel: Parcel) -> TestResult:
        return TestResult(result=TestResult.result.not_run)


class NoIndustrialNeighborsTest(EligibilityTest):
    def __init__(self):
        description = "Not a site or adjoined to any site where more than one-third of the square footage on the site is dedicated to industrial use"
        super().__init__("No Industrial Neighbors", description, self.run)


class NoMobileHomePark(EligibilityTest):
    def __init__(self):
        description = "Not a lot governed under the Mobilehome Residency Law, RV Park Law, or Special Occupancy Parks Acts"
        super().__init__("No Mobile Home Park", description, self.run)


class TribalResourceTest(EligibilityTest):
    def __init__(self):
        description = "Not located on a site that contains tribal resources"
        super().__init__("No Tribal Resource", description, self.run)


class NotHighFireHazardTest(EligibilityTest):
    def __init__(self):
        description = "Not located in a very high fire hazard severity zone"
        super().__init__("Not High Fire Hazard", description, self.run)


class NotNearFreeway(EligibilityTest):
    def __init__(self):
        description = "Not located within 500 feet of a freeway, including limited access roads(?)"
        super().__init__("Not Near Freeway", description, self.run)


class NotNearOilGas(EligibilityTest):
    def __init__(self):
        description = "Not located within 3,200 feet of an oil or gas extraction well"
        super().__init__("Not Near Oil/Gas", description, self.run)


class NotNeighborhoodPlan(EligibilityTest):
    def __init__(self):
        description = "Not part of Neighborhood Plan (master planned community), unless multifamily is allowed in the plan"
        super().__init__("Not Neighborhood Plan", description, self.run)


class EligibilityTestSuite:
    def __init__(self, test, name, description):
        self.test = test
        self.name = name
        self.description = description

    def run(self, parcel: Parcel) -> TestResult:
        results = []
        for test in self.tests:
            results.append(test.run(parcel))
        return results
