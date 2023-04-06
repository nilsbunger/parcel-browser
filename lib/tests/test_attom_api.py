import pytest
import responses
from responses import matchers

from facts.models import StdAddress
from lib.attom_data import AttomDataApi, AttomPropertyRecord, PropertyAddressResponse
from lib.tests.attom_data_fixtures import expanded_profile_resp, multifam_92101_resp


class TestAttomApi:
    @pytest.mark.django_db
    def test_get_properties_in_zipcode(self, mocker):
        attom_api = AttomDataApi(api_key="5050505050", api_url="http://test:9191")
        expected_req_headers = {"Accept": "application/json", "Apikey": "5050505050"}
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "http://test:9191/propertyapi/v1.0.0/property/address?"
                "postalcode=92101&propertytype=MULTI+FAMILY+DWELLING&page=1&pagesize=200",
                status=200,
                json=multifam_92101_resp,
                match=[matchers.header_matcher(expected_req_headers)],
            )
            resp: PropertyAddressResponse = attom_api.get_properties_in_zip("92101")
        # mocker.patch.object(requests, "get", return_value=multifam_92101_resp)
        assert len(resp.property) == len(multifam_92101_resp["property"])
        assert resp.status.msg == "SuccessWithResult"

    @pytest.mark.django_db
    def test_get_expanded_profile(self, mocker):
        attom_api = AttomDataApi(api_key="5050505050", api_url="http://test:9191")
        expected_req_headers = {"Accept": "application/json", "Apikey": "5050505050"}
        addr = StdAddress.objects.create(street_addr="4529 Winona Court", city="Denver", state="CO", zip="99999")
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "http://test:9191/propertyapi/v1.0.0/property/expandedprofile?"
                "address1=4529%20Winona%20Court&address2=Denver%2C%20CO",
                status=200,
                json=expanded_profile_resp,
                match=[matchers.header_matcher(expected_req_headers)],
            )
            resp: AttomPropertyRecord = attom_api.get_property_expanded_profile(addr)
        # mocker.patch.object(requests, "get", return_value=multifam_92101_resp)
        assert resp.address.line1 == "4529 WINONA CT"
        assert resp.building.parking.prkgSize == 240
        assert resp.building.construction.condition == "GOOD"
        assert resp.building.size.grossSize == 1414
        assert resp.building.size.livingSize == 934
