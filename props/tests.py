from django.http import Http404
import pytest

from facts.models import AddressFeatures, StdAddress
from props.models import PropertyProfile


class TestProperty:
    def test_property_features_schema(self, property_feature):
        # Test that the property schema is valid
        x = AddressFeatures.parse_raw(property_feature)
        keys = sorted(x.dict().keys())
        assert keys == ["geometry", "properties", "text_en", "type"]
        assert x.geometry.coordinates.long == -122.147775


@pytest.fixture()
def client_and_user(django_user_model, client):
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.create_user(email="testuser@foo.com", password="testpassword")
    assert client.login(email="testuser@foo.com", password="testpassword")
    yield client, user

    client.logout()
    user.delete()


class TestApi:
    @pytest.mark.django_db
    def test_create_property_api(self, client_and_user, create_new_property_request: str):
        client, user = client_and_user
        # NOTE: have to hardcode URL - can't use reverse() when there is a get and post at same location.
        response = client.post(
            "/api/properties/profiles", data=create_new_property_request, content_type="application/json"
        )
        assert response.status_code == 200
        result = response.json()
        assert result == {"errors": False, "message": "Property created", "data": {"id": 1}}
        # response = api._create_property(request, data=create_new_property_request)

    def test_list_properties_api(self, client_and_user, dummy_properties):
        # Test the list-properties API
        client, user = client_and_user
        path = "/api/properties/profiles"
        response = client.get(path)
        assert response.status_code == 200
        result = response.json()
        assert len(result) == 10
        # check that related model got pulled
        assert result[5]["address"]["street_addr"] == "6 Dummy Rd"

    def test_get_property_api(self, client_and_user, dummy_properties):
        # Test the get-property API
        client, user = client_and_user
        prop_under_test = dummy_properties[3]
        path = f"/api/properties/profiles/{prop_under_test.id}"
        response = client.get(path)
        assert response.status_code == 200
        result = response.json()
        assert result["address"]["street_addr"] == "4 Dummy Rd"

    def test_get_property_no_exist(self, client_and_user, dummy_properties):
        # Test the get-property API
        client, user = client_and_user

        response = client.get("/dj/supadupa")
        assert response.status_code == 404

        prop_under_test = dummy_properties[3]
        path = f"/api/properties/profiles/9999999"
        response = client.get(path)
        assert response.status_code == 404
        result = response.json()


####################
# Fixtures
####################


@pytest.fixture
def dummy_addresses(db):
    addrs = [
        StdAddress.objects.create(
            street_addr=f"{idx+1} Dummy Rd", city="La Honda", state="CA", zip="94020", address_features={}
        )
        for idx in range(10)
    ]
    return addrs


@pytest.fixture
def dummy_properties(db, dummy_addresses):
    properties = [PropertyProfile.objects.create(legal_entity=None, address=addr) for addr in dummy_addresses]
    return properties


@pytest.fixture
def create_user(db, django_user_model):
    def make_user(**kwargs):
        return django_user_model.objects.create_user(**kwargs)

    return make_user


@pytest.fixture
def create_new_property_request():
    return """{"formFields":{"streetAddress":"8901 Alpine Road","city":"La Honda","zip":"94020"},"features":{"type":"Feature","properties":{"accuracy":"rooftop","mapbox_id":"dXJuOm1ieGFkcjphODc1Y2Y3Yy04MDc4LTRlMDUtYTIzZC0wNjRmZGRiOTdiNDY=","match_code":{"exact_match":false,"house_number":"unmatched","street":"unmatched","postcode":"unmatched","place":"unmatched","region":"unmatched","locality":"not_applicable","country":"inferred","confidence":"low"},"place_type":["address"],"place_name":"8901 Alpine Road, La Honda, California 94020, United States","address_number":"8901","street":"Alpine Road","context":[{"id":"postcode.312135404","mapbox_id":"dXJuOm1ieHBsYzpFcHJPN0E","text_en":"94020","text":"94020"},{"id":"place.175499500","wikidata":"Q2454633","mapbox_id":"dXJuOm1ieHBsYzpDblhvN0E","text_en":"La Honda","language_en":"en","text":"La Honda","language":"en"},{"id":"district.20629228","wikidata":"Q108101","mapbox_id":"dXJuOm1ieHBsYzpBVHJHN0E","text_en":"San Mateo County","language_en":"en","text":"San Mateo County","language":"en"},{"id":"region.419052","short_code":"US-CA","wikidata":"Q99","mapbox_id":"dXJuOm1ieHBsYzpCbVRz","text_en":"California","language_en":"en","text":"California","language":"en"},{"id":"country.8940","short_code":"us","wikidata":"Q30","mapbox_id":"dXJuOm1ieHBsYzpJdXc","text_en":"United States","language_en":"en","text":"United States","language":"en"}],"id":"address.5785944174450600","external_ids":{"carmen":"address.5785944174450600","federated":"carmen.address.5785944174450600"},"feature_name":"8901 Alpine Road","matching_name":"8901 Alpine Road","description":"La Honda, California 94020, United States","metadata":{"iso_3166_2":"US-CA","iso_3166_1":"us"},"language":"en","maki":"marker","postcode":"94020","place":"La Honda","district":"San Mateo County","region":"California","region_code":"CA","country":"United States","country_code":"us","full_address":"8901 Alpine Road, La Honda, California 94020, United States","address_line1":"8901 Alpine Road","address_line2":"","address_line3":"","address_level1":"CA","address_level2":"La Honda","address_level3":"","postcode_plus":"9771","is_deliverable":true,"missing_unit":false},"text_en":"Alpine Road","geometry":{"type":"Point","coordinates":[-122.2306,37.294425]}}}"""


@pytest.fixture
def property_feature():
    # Return a feature from the Mapbox Geocoding API, used in the address autocomplete for creating new properties
    return """{
        "type": "Feature",
        "properties": {
            "accuracy": "rooftop",
            "mapbox_id": "dXJuOm1ieGFkcjo0MDE3NTRlNi02NzNjLTQzMDQtYThhNS0wYTliZmI3NDc0Yzc=",
            "match_code": {
                "exact_match": false,
                "house_number": "matched",
                "street": "unmatched",
                "postcode": "unmatched",
                "place": "unmatched",
                "region": "unmatched",
                "locality": "not_applicable",
                "country": "inferred",
                "confidence": "low"
            },
            "place_type": [
                "address"
            ],
            "place_name": "555 College Avenue, Palo Alto, California 94306, United States",
            "address_number": "555",
            "street": "College Avenue",
            "context": [
                {
                    "id": "neighborhood.127036652",
                    "mapbox_id": "dXJuOm1ieHBsYzpCNUpzN0E",
                    "text_en": "College Terrace",
                    "text": "College Terrace"
                },
                {
                    "id": "postcode.313356012",
                    "mapbox_id": "dXJuOm1ieHBsYzpFcTF1N0E",
                    "text_en": "94306",
                    "text": "94306"
                },
                {
                    "id": "place.250554604",
                    "wikidata": "Q47265",
                    "mapbox_id": "dXJuOm1ieHBsYzpEdThvN0E",
                    "text_en": "Palo Alto",
                    "language_en": "en",
                    "text": "Palo Alto",
                    "language": "en"
                },
                {
                    "id": "district.20686572",
                    "wikidata": "Q110739",
                    "mapbox_id": "dXJuOm1ieHBsYzpBVHVtN0E",
                    "text_en": "Santa Clara County",
                    "language_en": "en",
                    "text": "Santa Clara County",
                    "language": "en"
                },
                {
                    "id": "region.419052",
                    "short_code": "US-CA",
                    "wikidata": "Q99",
                    "mapbox_id": "dXJuOm1ieHBsYzpCbVRz",
                    "text_en": "California",
                    "language_en": "en",
                    "text": "California",
                    "language": "en"
                },
                {
                    "id": "country.8940",
                    "short_code": "us",
                    "wikidata": "Q30",
                    "mapbox_id": "dXJuOm1ieHBsYzpJdXc",
                    "text_en": "United States",
                    "language_en": "en",
                    "text": "United States",
                    "language": "en"
                }
            ],
            "id": "address.8098767896859408",
            "external_ids": {
                "carmen": "address.8098767896859408",
                "federated": "carmen.address.8098767896859408"
            },
            "feature_name": "555 College Avenue",
            "matching_name": "555 College Avenue",
            "description": "Palo Alto, California 94306, United States",
            "metadata": {
                "iso_3166_2": "US-CA",
                "iso_3166_1": "us"
            },
            "language": "en",
            "maki": "marker",
            "neighborhood": "College Terrace",
            "postcode": "94306",
            "place": "Palo Alto",
            "district": "Santa Clara County",
            "region": "California",
            "region_code": "CA",
            "country": "United States",
            "country_code": "us",
            "full_address": "555 College Avenue, Palo Alto, California 94306, United States",
            "address_line1": "555 College Avenue",
            "address_line2": "",
            "address_line3": "",
            "address_level1": "CA",
            "address_level2": "Palo Alto",
            "address_level3": "College Terrace",
            "postcode_plus": "1433",
            "is_deliverable": true,
            "missing_unit": false
        },
        "text_en": "College Avenue",
        "geometry": {
            "type": "Point",
            "coordinates": [
                -122.147775,
                37.42552
            ]
        }
    }"""
