import pytest

from lib.co.co_eligibility_lib import PrincipallyPermittedUseTest, TestResult, TestResultEnum
from world.models import Parcel


@pytest.mark.django_db(databases=["basedata"])
class PrincipallyPermittedUseTest:
    def test_commercial_parcel(self):
        apn = "4151721900"
        parcel = Parcel.objects.using("basedata").get(apn=apn)
        test_result = PrincipallyPermittedUseTest().run(parcel)
        assert test_result == TestResult(result=TestResultEnum.passed, notes=["Zone(s): CC-4-2"])
        print("Running method A")

    def test_multifam_parcel(self):
        parcel = Parcel.objects.using("basedata").get(apn="4472421600")  # RM-1-1 zone parcel
        test_result = PrincipallyPermittedUseTest().run(parcel)
        assert test_result == TestResult(
            result=TestResultEnum.failed, notes=["Zone(s): RM-1-1, RM-1-3"]
        )

    def test_no_zone_data_parcel(self):
        parcel = Parcel.objects.using("basedata").get(apn="5571022400")  # not in SD city
        test_result = PrincipallyPermittedUseTest().run(parcel)
        assert test_result == TestResult(
            result=TestResultEnum.error, notes=["No zoning found for parcel"]
        )
