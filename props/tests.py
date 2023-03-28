import pytest

from facts.models import AddressFeatures


class TestProperty:
    def test_property_features_schema(self, property_feature):
        # Test that the property schema is valid
        x = AddressFeatures.parse_raw(property_feature)
        print(x)
        keys = sorted(x.dict().keys())
        assert keys == ["geometry", "properties", "type"]
        assert x.geometry.coordinates.long == -122.147775


####################
# Fixtures
####################


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
