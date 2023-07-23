from pprint import pprint

import pandas as pd
import pytest
import responses
from facts.models import StdAddress
from responses import matchers

from elt.lib.ext_api.attom_data_api import AttomDataApi
from elt.lib.ext_api.attom_property_types import AttomPropertyRecord, PropertyAddressResponse
from elt.tests.fixtures import (
    AttomCompsFixture,
    AttomPropertyAddressFixture,
)
from elt.tests.fixtures.attom_data_fixtures import expanded_profile_resp, multifam_92101_resp


class TestAttomApi:
    @pytest.mark.django_db
    def test_get_properties_in_zipcode(self, mocker):
        attom_api = AttomDataApi(api_key="5050505050", api_url="http://test:9191")
        expected_req_headers = {"Accept": "application/json", "Apikey": "5050505050"}
        with responses.RequestsMock() as rsps:
            rsp1 = rsps.get(
                "http://test:9191/propertyapi/v1.0.0/property/address?"
                "postalcode=92101&propertytype=Apartment&minBeds=12&page=1&pagesize=200",
                status=200,
                json=multifam_92101_resp,
                match=[matchers.header_matcher(expected_req_headers)],
            )
            resp: PropertyAddressResponse = attom_api.get_properties_in_zip("92101")
            # check that the second call used the cached value
            resp: PropertyAddressResponse = attom_api.get_properties_in_zip("92101")
            assert rsp1.call_count == 1

        # mocker.patch.object(requests, "get", return_value=multifam_92101_resp)
        assert len(resp.property) == len(multifam_92101_resp["property"])
        assert resp.status.msg == "SuccessWithResult"

    @pytest.mark.django_db
    def test_get_multipage_properties_in_zipcode(self, mocker):
        attom_api = AttomDataApi(api_key="5050505050", api_url="http://test:9191")
        expected_req_headers = {"Accept": "application/json", "Apikey": "5050505050"}
        with responses.RequestsMock() as rsps:
            # set up mock responses:
            rsp1 = rsps.get(
                "http://test:9191/propertyapi/v1.0.0/property/address?"
                "postalcode=90006&minBeds=12&propertytype=Apartment&page=1&pagesize=200",
                status=200,
                json=AttomPropertyAddressFixture.APTS_90006_PG1,
                match=[matchers.header_matcher(expected_req_headers)],
            )
            rsp2 = rsps.get(
                "http://test:9191/propertyapi/v1.0.0/property/address?"
                "postalcode=90006&minBeds=12&propertytype=Apartment&page=2&pagesize=200",
                status=200,
                json=AttomPropertyAddressFixture.APTS_90006_PG2,
                match=[matchers.header_matcher(expected_req_headers)],
            )
            resp: PropertyAddressResponse = attom_api.get_properties_in_zip("90006")
            # check that the second call used the cached value
            resp: PropertyAddressResponse = attom_api.get_properties_in_zip("90006")
            assert rsp1.call_count == 1
            assert rsp2.call_count == 1

        # mocker.patch.object(requests, "get", return_value=multifam_92101_resp)
        assert len(resp.property) == len(AttomPropertyAddressFixture.APTS_90006_PG1["property"]) + len(
            AttomPropertyAddressFixture.APTS_90006_PG2["property"]
        )
        assert resp.status.msg == "SuccessWithResult"

    @pytest.mark.django_db
    def test_get_expanded_profile(self, mocker):
        attom_api = AttomDataApi(api_key="5050505050", api_url="http://test:9191")
        expected_req_headers = {"Accept": "application/json", "Apikey": "5050505050"}
        addr = StdAddress.objects.create(street_addr="4529 Winona Court", city="Denver", state="CO", zip="99999")
        with responses.RequestsMock() as rsps:
            rsp1 = rsps.get(
                "http://test:9191/propertyapi/v1.0.0/property/expandedprofile?"
                "address1=4529%20Winona%20Court&address2=Denver%2C%20CO&page=1&pagesize=200",
                status=200,
                json=expanded_profile_resp,
                match=[matchers.header_matcher(expected_req_headers)],
            )
            resp: AttomPropertyRecord = attom_api.get_property_expanded_profile(addr)
            # check that the second call used the cached value
            resp: AttomPropertyRecord = attom_api.get_property_expanded_profile(addr)
            assert rsp1.call_count == 1

        # mocker.patch.object(requests, "get", return_value=multifam_92101_resp)
        assert resp.address.line1 == "4529 WINONA CT"
        assert resp.building.parking.prkgSize == 240
        assert resp.building.construction.condition == "GOOD"
        assert resp.building.size.grossSize == 1414
        assert resp.building.size.livingSize == 934

    @pytest.mark.django_db
    def test_get_comps(self, mocker):
        attom_api = AttomDataApi(api_key="5050505050", api_url="http://test:9191")
        expected_req_headers = {"Accept": "application/json", "Apikey": "5050505050"}
        with responses.RequestsMock() as rsps:
            rsp1 = rsps.get(
                "http://test:9191/property/v2/salescomparables/apn/5077-028-025/Los%20Angeles/CA"
                "?searchType=Radius&minComps=1&maxComps=20&miles=5&bedroomsRange=10&bathroomRange=10&sqFeetRange=10000"
                "&lotSizeRange=10000&saleDateRange=24&ownerOccupied=IncludeAbsentOwnerOnly"
                "&distressed=IncludeDistressed",
                status=200,
                json=AttomCompsFixture.COMPS_2769_SAN_MARINO,
                match=[matchers.header_matcher(expected_req_headers)],
            )
            x = attom_api.get_comps("5077-028-025", "Los Angeles", "CA")
            assert rsp1.call_count == 1

        prop_list = x.group.resp.resp_data.property_info_response.subject_property.properties
        subject_property = prop_list[0]
        comps = [x.comp_prop for x in prop_list[1:]]
        pprint(comps[0].__dict__)

        # generate a dataframe
        comps_df = pd.json_normalize([comp.dict() for comp in comps], sep=".")


#            resp: AttomCompsResponse = x
