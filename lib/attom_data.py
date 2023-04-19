from dataclasses import dataclass

from pydantic import ValidationError

from elt.models import ExternalApiData
from elt.models.external_api_data import CacheableApi
from facts.models import StdAddress
from lib.attom_comp_data_struct import CompPropertyContainer, CompSalesResponse, SubjectProperty
from lib.attom_data_struct import AttomPropertyRecord, PropertyAddressResponse
from mygeo import settings


@dataclass(kw_only=True)
class AttomDataApi(CacheableApi):
    api_key: str
    api_url: str = "https://api.gateway.attomdata.com"
    zoo: int = 1
    vendor: ExternalApiData.Vendor = ExternalApiData.Vendor.ATTOM

    # https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/address?postalcode=82009&page=1&pagesize=100

    # Transaction V3 : preforeclosure detail
    # https://api.gateway.attomdata.com/property/v3/preforeclosuredetails?combinedAddress=11235%20S%20STEWART%20AVE%2C%20Chicago%2C%20IL%2C%2060628

    # ########################################
    # Property-centric APIs:  https://api.developer.attomdata.com/docs#!/Property32V1
    # ########################################
    def get_properties_in_zip(self, zipcode: str) -> PropertyAddressResponse:
        # List of multifam properties with 12 or more BRs in a zip code.
        # Check that we called with:
        #   https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/address?postalcode=92101&propertytype=MULTI%20FAMILY%20DWELLING&orderby=beds&page=1&pagesize=200
        #  - a valid zip code
        url = self.api_url + "/propertyapi/v1.0.0/property/address"
        # propertytype = "MULTI FAMILY DWELLING"
        propertytype = "Apartment"
        params = {"postalcode": zipcode, "propertytype": propertytype, "minBeds": 12}
        # lookup key should be unique within the vendor
        lookup_key = f"property/address:{sorted(params.items())}"
        hash_version = 2  # change when we change lookup key

        external_data = self.get(
            url,
            params,
            lookup_key=lookup_key,
            hash_version=hash_version,
            headers={"Apikey": self.api_key, "Accept": "application/json"},
            paged=True,
        )
        prop_addr_resp = PropertyAddressResponse.parse_obj(external_data.data)
        # prop_addr_resp.raw = external_data
        return prop_addr_resp

    def get_property_expanded_profile(self, address: StdAddress) -> AttomPropertyRecord:
        # Get a detailed property information and most recent transaction and taxes for a specific address.
        # example URL: https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/expandedprofile?address1=4529%20Winona%20Court&address2=Denver%2C%20CO
        ...
        url = self.api_url + "/propertyapi/v1.0.0/property/expandedprofile"
        assert len(address.state) == 2
        params = {"address1": address.street_addr, "address2": f"{address.city}, {address.state}"}
        # lookup key should be unique within the vendor
        lookup_key = f"property/expandedprofile:{address.street_addr}:{address.city}:{address.state}"
        hash_version = 1  # change when we change lookup key

        external_data = self.get(
            url,
            params,
            lookup_key=lookup_key,
            hash_version=hash_version,
            headers={"Apikey": self.api_key, "Accept": "application/json"},
            paged=True,
        )
        assert len(external_data.data["property"]) == 1, "Expected only one property record"
        try:
            prop_expanded_profile = AttomPropertyRecord.parse_obj(external_data.data["property"][0])
        except ValidationError as e:
            print(e)
            print("...")
            raise e
        return prop_expanded_profile

    def get_comps(self, apn, county: str, state: str):
        # Get comparable sales for a property from the ATTOM API with some reasonable parameters
        # https://api.gateway.attomdata.com/property/v2/salescomparables/apn/5077-028-025/Los%20Angeles/CA
        #   ?searchType=Radius&minComps=1&maxComps=20&miles=5&bedroomsRange=10&bathroomRange=10&sqFeetRange=10000
        #   &lotSizeRange=10000&saleDateRange=24&ownerOccupied=IncludeAbsentOwnerOnly&distressed=IncludeDistressed
        assert len(state) == 2
        url = self.api_url + f"/property/v2/salescomparables/apn/{apn}/{county}/{state}"
        params = {
            "searchType": "Radius",
            "minComps": 1,
            "maxComps": 20,
            "miles": 5,
            "bedroomsRange": 10,
            "bathroomRange": 10,
            "sqFeetRange": 10000,
            "lotSizeRange": 10000,
            "saleDateRange": 24,
            "ownerOccupied": "IncludeAbsentOwnerOnly",
            "distressed": "IncludeDistressed",
        }
        # lookup key should be unique within the vendor
        lookup_key = f"property/v2/salescomp/apn:{sorted(params.items())}"
        hash_version = 1  # change when we change lookup key
        external_data = self.get(
            url,
            params,
            lookup_key=lookup_key,
            hash_version=hash_version,
            headers={"Apikey": self.api_key, "Accept": "application/json"},
            paged=False,
        )
        try:
            if settings.DEV_ENV:
                # parse subject and comps separately in debug to make it easier to untangle a validation error.
                resp_data = external_data.data["RESPONSE_GROUP"]["RESPONSE"]["RESPONSE_DATA"]
                prop_list = resp_data["PROPERTY_INFORMATION_RESPONSE_ext"]["SUBJECT_PROPERTY_ext"]["PROPERTY"]
                subj_property, comp_property = prop_list[0:2]
                subj_prop = SubjectProperty.parse_obj(subj_property)
                comp_prop = CompPropertyContainer.parse_obj(comp_property)
            prop_expanded_profile = CompSalesResponse.parse_obj(external_data.data)
        except ValidationError as e:
            print(e)
            print("...")
            raise e
        return prop_expanded_profile


PropertyAddressResponse.update_forward_refs()

# def get_property_tax_data(self, address, city, state, postal_code):
#     """
#     Get property tax data from the ATTOM Data API
#     :param address: property address
#     :param city: property city
#     :param state: property state
#     :param postal_code: property postal code
#     :return: property tax data
#     """
#     # build the url
#     url = self.api_url + "tax/assessmenthistory?"
#     url += "address=" + address
#     url += "&city=" + city
#     url += "&state=" + state
#     url += "&postalcode=" + postal_code
#     url += "&apikey=" + self.api_key
#
#     # make the request
#     response = requests.get(url)
#
#     # check for errors
#     if response.status_code != 200:
#         raise Exception("ATTOM Data API returned an error: " + str(response.status_code))
#
#     # parse the response
#     data = response.json()
#
#     # return the data
#     return data
#
# def get_property_tax_assessment_data(self, address, city, state, postal_code):
#     """
#     Get property tax assessment data from the ATTOM Data API
#     :param address: property address
#     :param city: property city
#     """
#     pass
