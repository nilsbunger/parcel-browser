import pytest

from lib.co.co_eligibility_lib import (
    CheckResultEnum,
    CommercialCorridorCheck,
    PrincipallyPermittedUseCheck,
)
from world.models import Parcel


@pytest.mark.django_db(databases=["basedata", "default"])  # TODO: REMOVE DEFAULT
class TestCommercialCorridor:
    def test_on_wide_road(self):
        pass

    def test_multi_match(self):
        # case when there are two roads with similar names, just different suffixes
        apn = "4453701400"
        parcel = Parcel.objects.using("basedata").get(apn=apn)
        cc = CommercialCorridorCheck()
        test_result = cc.run(parcel)
        assert test_result == CheckResultEnum.passed

    def test_on_narrow_road(self):
        pass

    def test_with_alleyway(self):
        pass


@pytest.mark.django_db(databases=["basedata"])
class TestPrincipallyPermittedUse:
    def test_commercial_parcel(self):
        apn = "4151721900"
        parcel = Parcel.objects.using("basedata").get(apn=apn)
        use_check = PrincipallyPermittedUseCheck()
        retval = use_check.run(parcel)
        assert retval == CheckResultEnum.passed == use_check.result
        assert use_check.notes == ["Zone(s): CC-4-2"]

    def test_multifam_parcel(self):
        parcel = Parcel.objects.using("basedata").get(apn="4472421600")  # RM-1-1 zone parcel
        use_check = PrincipallyPermittedUseCheck()
        retval = use_check.run(parcel)
        assert retval == CheckResultEnum.failed == use_check.result
        assert use_check.notes == ["Zone(s): RM-1-1, RM-1-3"]
        # assert test_result == CheckResult(result=CheckResultEnum.failed, notes=["Zone(s): RM-1-1, RM-1-3"])

    def test_no_zone_data_parcel(self):
        parcel = Parcel.objects.using("basedata").get(apn="5571022400")  # not in SD city
        use_check = PrincipallyPermittedUseCheck()
        retval = use_check.run(parcel)
        assert retval == CheckResultEnum.error == use_check.result
        assert use_check.notes == ["No zoning found for this parcel"]
