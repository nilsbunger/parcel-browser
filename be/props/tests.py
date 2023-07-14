import json
import urllib

import pytest
import responses

from elt.models import RawSfParcelWrap
from facts.models import AddressFeatures, StdAddress
from props.models import PropertyProfile


class TestProperty:
    def test_property_features_schema(self, property_feature):
        # Test that the property schema is valid
        x = AddressFeatures.parse_raw(property_feature)
        keys = sorted(x.dict().keys())
        assert keys == ["geometry", "properties", "text_en", "type"]
        assert x.geometry.coordinates.long == -122.147775


class TestApi:
    @pytest.mark.django_db
    def test_database_settings(self, db):
        from django.conf import settings

        count = RawSfParcelWrap.objects.count()
        print("Parcel Wrap Count = ", count)
        assert settings.DATABASES["default"]["NAME"] == "test_railway"

    @pytest.mark.django_db
    @responses.activate  # responses module for mocking
    def test_create_property_api(self, client_and_user, create_new_property_req, mapbox_normalize_addr_resp):
        client, user = client_and_user
        # create mock response
        addrs = (  # input, output pairs for address
            ("3756 jackson st, sf", "3756 Jackson Street, San Francisco"),
            ("45 parker ave, sf", "45 Parker Avenue, San Francisco"),
            ("45 parker ave, sf", "45 Parker Avenue, San Francisco"),
        )
        for addr in addrs:
            responses.add(
                responses.GET,
                f"https://localmapboxstub:8181/geocoding/v5/mapbox.places/{urllib.parse.quote(addr[0])}.json",
                json=mapbox_normalize_addr_resp(addr[1]),  # mock response to generate
                status=200,
            )
        # NOTE: have to hardcode Django URL - can't use reverse() when there is a get and post at same location.
        resp = client.json_post("/api/properties/profiles", data=create_new_property_req("3756 jackson st", "sf", ""))
        print(responses.calls)
        assert resp == {"errors": False, "message": "Property created", "data": {"id": 1}}
        resp = client.json_post("/api/properties/profiles", data=create_new_property_req("45 parker ave", "sf", ""))
        assert resp == {"errors": False, "message": "Property created", "data": {"id": 2}}
        # using same address a second time should result in same property id.
        resp = client.json_post("/api/properties/profiles", data=create_new_property_req("45 parker ave", "sf", ""))
        assert resp == {"errors": False, "message": "Property created", "data": {"id": 2}}
        # response = api._create_property(request, data=create_new_property_request)

    def test_list_properties_api(self, client_and_user, dummy_properties):
        # Test the list-properties API
        client, user = client_and_user
        path = "/api/properties/profiles"
        resp = client.json_get(path)
        assert len(resp) == 10
        # check that related model got pulled
        assert resp[5]["address"]["street_addr"] == "6 Dummy Rd"

    def test_get_property_api(self, client_and_user, dummy_properties):
        # Test the get-property API
        client, user = client_and_user
        prop_under_test = dummy_properties[3]
        path = f"/api/properties/profiles/{prop_under_test.id}"
        resp = client.json_get(path)
        assert resp["address"]["street_addr"] == "4 Dummy Rd"

    def test_get_property_no_exist(self, client_and_user, dummy_properties):
        # Test the get-property API
        client, user = client_and_user

        response = client.get("/dj/supadupa", secure=True)
        assert response.status_code == 404

        prop_under_test = dummy_properties[3]  # noqa: F841 - unused variable
        path = f"/api/properties/profiles/9999999"
        response = client.json_get(path, exp_status=404)  # noqa: F841 - unused variable


####################
# Fixtures
####################


@pytest.fixture
def dummy_addresses(db):
    addrs = [
        StdAddress.objects.create(
            street_addr=f"{idx + 1} Dummy Rd", city="La Honda", state="CA", zip="94020", address_features={}
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
def mapbox_normalize_addr_resp():
    """This is the response from the Mapbox API when normalizing an address.
    Accepts an addr_dict with keys being 'input' to the server, and value being output to generate."""

    def _inner(output_addr):
        return _mapbox_normalize_addr_fixture(output_addr)

    return _inner


def _mapbox_normalize_addr_fixture(output_addr: str):
    # output_addr should be a well-formed address like "3756 Jackson Street"
    street, city = output_addr.split(", ")
    return {
        "type": "FeatureCollection",
        "query": ["1234", "dummy"],  # ["3756", "jackson", "st", "sf"],
        "features": [
            {
                "id": "address.4765053304903338",
                "type": "Feature",
                "place_type": ["address"],
                "relevance": 1,
                "properties": {
                    "accuracy": "rooftop",
                    "mapbox_id": "dXJuOm1ieGFkcjplZTAyMWNjZi05NTE4LTRmMzYtYTMyMS0xNTFiNmFmMzE4M2M",
                },
                "text": "Dummy",  # "Jackson Street",
                "place_name": f"{output_addr}, California 94118, United States",
                "matching_place_name": f"Dummy match",  # f"{output_addr}, SF, California 94118, United States",
                "center": [0, 0],  # [-122.45676, 37.78991],
                "geometry": {"type": "Point", "coordinates": [0, 0]},  # [-122.45676, 37.78991]},
                "address": street.split(" ")[0],  # "3756",
                "context": [
                    {
                        "id": "neighborhood.516025580",
                        "mapbox_id": "dXJuOm1ieHBsYzpIc0hzN0E",
                        "text": "Dummy",  # "Presidio Heights",
                    },
                    {"id": "postcode.312536812", "mapbox_id": "dXJuOm1ieHBsYzpFcUR1N0E", "text": "94118"},
                    {
                        "id": "place.292358380",
                        "mapbox_id": "dXJuOm1ieHBsYzpFVzBJN0E",
                        "wikidata": "Q62",
                        "text": city,
                    },
                    {
                        "id": "district.20547308",
                        "mapbox_id": "dXJuOm1ieHBsYzpBVG1HN0E",
                        "wikidata": "Q62",
                        "text": "Dummy county",  # "San Francisco County",
                    },
                    {
                        "id": "region.419052",
                        "mapbox_id": "dXJuOm1ieHBsYzpCbVRz",
                        "wikidata": "Q99",
                        "short_code": "US-CA",
                        "text": "California",
                    },
                    {
                        "id": "country.8940",
                        "mapbox_id": "dXJuOm1ieHBsYzpJdXc",
                        "wikidata": "Q30",
                        "short_code": "us",
                        "text": "United States",
                    },
                ],
            },
            {
                "id": "address.2269403891027682",
                "type": "Feature",
                "place_type": ["address"],
                "relevance": 0.972222,
                "properties": {
                    "accuracy": "interpolated",
                    "mapbox_id": "dXJuOm1ieGFkcjo0ODhhZDc1OC1mYzQ0LTQ3MTktYWNhZC1mZmNiZjU0NWVlMWE",
                },
                "text": "Jackson Street Southeast",
                "place_name": "3756 Jackson Street Southeast, Albany, Oregon 97322, United States",
                "center": [-123.095363, 44.610387],
                "geometry": {"type": "Point", "coordinates": [-123.095363, 44.610387], "interpolated": True},
                "address": "3756",
            },
            {
                "id": "neighborhood.318475500",
                "type": "Feature",
                "place_type": ["neighborhood"],
                "relevance": 0.693333,
                "properties": {"mapbox_id": "dXJuOm1ieHBsYzpFdnVNN0E", "wikidata": "Q14682502"},
                "text": "Jackson Square",
                "place_name": "Jackson Square, San Francisco, California, United States",
                "matching_place_name": "Jackson Square, SF, California, United States",
                "bbox": [-122.406921387, 37.793242962, -122.387695312, 37.804358869],
                "center": [-122.398793, 37.800613],
                "geometry": {"type": "Point", "coordinates": [-122.398793, 37.800613]},
                "context": [
                    {"id": "postcode.312487660", "mapbox_id": "dXJuOm1ieHBsYzpFcUF1N0E", "text": "94111"},
                    {
                        "id": "place.292358380",
                        "mapbox_id": "dXJuOm1ieHBsYzpFVzBJN0E",
                        "wikidata": "Q62",
                        "text": "San Francisco",
                    },
                    {
                        "id": "district.20547308",
                        "mapbox_id": "dXJuOm1ieHBsYzpBVG1HN0E",
                        "wikidata": "Q62",
                        "text": "San Francisco County",
                    },
                    {
                        "id": "region.419052",
                        "mapbox_id": "dXJuOm1ieHBsYzpCbVRz",
                        "wikidata": "Q99",
                        "short_code": "US-CA",
                        "text": "California",
                    },
                    {
                        "id": "country.8940",
                        "mapbox_id": "dXJuOm1ieHBsYzpJdXc",
                        "wikidata": "Q30",
                        "short_code": "us",
                        "text": "United States",
                    },
                ],
            },
        ],
    }


@pytest.fixture
def property_feature():
    # Return a feature from the Mapbox Geocoding API, used in the address autocomplete for creating new properties
    return """{
        "type": "Feature",
        "properties": {
            "accuracy": "rooftop",
            "mapbox_id": "xxx=",
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
                    "mapbox_id": "xxx",
                    "text_en": "College Terrace",
                    "text": "College Terrace"
                },
                {
                    "id": "postcode.313356012",
                    "mapbox_id": "xxx",
                    "text_en": "94306",
                    "text": "94306"
                },
                {
                    "id": "place.250554604",
                    "wikidata": "Q47265",
                    "mapbox_id": "xxx",
                    "text_en": "Palo Alto",
                    "language_en": "en",
                    "text": "Palo Alto",
                    "language": "en"
                },
                {
                    "id": "district.20686572",
                    "wikidata": "Q110739",
                    "mapbox_id": "xxx",
                    "text_en": "Santa Clara County",
                    "language_en": "en",
                    "text": "Santa Clara County",
                    "language": "en"
                },
                {
                    "id": "region.419052",
                    "short_code": "US-CA",
                    "wikidata": "Q99",
                    "mapbox_id": "xxx",
                    "text_en": "California",
                    "language_en": "en",
                    "text": "California",
                    "language": "en"
                },
                {
                    "id": "country.8940",
                    "short_code": "us",
                    "wikidata": "Q30",
                    "mapbox_id": "xxx",
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


@pytest.fixture
def create_new_property_req():
    """Return a method that takes an address and simulates a request to the server to create a property profile."""

    def _inner(addr: str, city: str, zip: str):
        return json.dumps(_create_new_property_fixture(addr, city, zip))

    return _inner


def _create_new_property_fixture(addr: str, city: str, zip: str):
    return {
        "formFields": {"streetAddress": addr, "city": city, "zip": zip},
        "features": {
            "type": "Feature",
            "properties": {
                "accuracy": "rooftop",
                "mapbox_id": "xxx=",
                "match_code": {
                    "exact_match": False,
                    "house_number": "unmatched",
                    "street": "unmatched",
                    "postcode": "unmatched",
                    "place": "unmatched",
                    "region": "unmatched",
                    "locality": "not_applicable",
                    "country": "inferred",
                    "confidence": "low",
                },
                "place_type": ["address"],
                "place_name": "8901 Alpine Road, La Honda, California 94020, United States",
                "address_number": "8901",
                "street": "Alpine Road",
                "context": [
                    {"id": "postcode.312135404", "mapbox_id": "xxx", "text_en": "94020", "text": "94020"},
                    {
                        "id": "place.175499500",
                        "wikidata": "Q2454633",
                        "mapbox_id": "xxx",
                        "text_en": "La Honda",
                        "language_en": "en",
                        "text": "La Honda",
                        "language": "en",
                    },
                    {
                        "id": "district.20629228",
                        "wikidata": "Q108101",
                        "mapbox_id": "xxx",
                        "text_en": "San Mateo County",
                        "language_en": "en",
                        "text": "San Mateo County",
                        "language": "en",
                    },
                    {
                        "id": "region.419052",
                        "short_code": "US-CA",
                        "wikidata": "Q99",
                        "mapbox_id": "xxx",
                        "text_en": "California",
                        "language_en": "en",
                        "text": "California",
                        "language": "en",
                    },
                    {
                        "id": "country.8940",
                        "short_code": "us",
                        "wikidata": "Q30",
                        "mapbox_id": "xxx",
                        "text_en": "United States",
                        "language_en": "en",
                        "text": "United States",
                        "language": "en",
                    },
                ],
                "id": "address.5785944174450600",
                "external_ids": {
                    "carmen": "address.5785944174450600",
                    "federated": "carmen.address.5785944174450600",
                },
                "feature_name": "8901 Alpine Road",
                "matching_name": "8901 Alpine Road",
                "description": "La Honda, California 94020, United States",
                "metadata": {"iso_3166_2": "US-CA", "iso_3166_1": "us"},
                "language": "en",
                "maki": "marker",
                "postcode": "94020",
                "place": "La Honda",
                "district": "San Mateo County",
                "region": "California",
                "region_code": "CA",
                "country": "United States",
                "country_code": "us",
                "full_address": "8901 Alpine Road, La Honda, California 94020, United States",
                "address_line1": "8901 Alpine Road",
                "address_line2": "",
                "address_line3": "",
                "address_level1": "CA",
                "address_level2": "La Honda",
                "address_level3": "",
                "postcode_plus": "9771",
                "is_deliverable": True,
                "missing_unit": False,
            },
            "text_en": "Alpine Road",
            "geometry": {"type": "Point", "coordinates": [-122.2306, 37.294425]},
        },
    }
