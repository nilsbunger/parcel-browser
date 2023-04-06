from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, Extra

from elt.models import ExternalApiData
from elt.models.external_api_data import ApiResponseStatus, CacheableApi
from facts.models import StdAddress


# process response to propertyapi/v1.0.0/property/address - list of properties in a zip
class PropertyAddressResponse(BaseModel):
    status: "ApiResponseStatus"
    property: list["AttomPropertyRecord"]
    # raw: any  # raw django model entry for this response (optional)


# returned by/property/address, /property/expandedprofile, and probably more api calls.
class AttomPropertyRecord(BaseModel, extra=Extra.ignore):
    class Address(BaseModel):
        country: str  # country
        countrySubd: str  # state  # noqa: N815
        line1: str  # address
        line2: str  # city, state zip
        locality: str
        matchCode: str | None  # missing from some records  # noqa: N815
        postal1: str
        # fields typically present in "expanded profile" search but not in "address search":
        situsHouseNumber: int | None  # noqa: N815
        situsStreetName: str | None  # noqa: N815
        situsAddressSuffix: str | None  # noqa: N815
        # skipped:
        # "oneLine": "1646 J ST, SAN DIEGO, CA 92101",
        # "postal2": "7627",
        # "postal3": "C020",

    class Identifier(BaseModel):
        Id: int
        fips: str
        apn: str
        attomId: int  # noqa: N815

    class Location(BaseModel):
        # location data is missing from some records
        accuracy: str | None
        latitude: float | None
        longitude: float | None
        distance: int
        # skipped:
        # "geoid": "CO06073, CS0692780, DB0634320, PL0666000, ZI92101",
        # "geoIdV4": {
        #     "CO": "886e6f26978969cee1b66ca5395912f8",
        #     "CS": "8f319ce931f118bb23a273843734d1f3",
        #     "DB": "1697d091e8943eeee0383f86912789f5",
        #     "N1": "4e3c011a03118402dad38a9665d9b9d0",
        #     "N2": "8ac324d5bcee2632497ed29f6433ebb4",
        #     "PL": "337aec169b64ca28ae95db835cf33392",
        #     "SB": "ca6f86295736dbdd36407e80315f9822,...",
        #     "ZI": "d1137929af787483e1603ce26df3e79a",
        # },

    class Summary(BaseModel, extra=Extra.allow):
        # allow extra fields here since there may be variability in what's returned
        archStyle: str  # noqa: N815
        absenteeInd: str  # noqa: N815
        propClass: str  # noqa: N815
        propSubType: str  # noqa: N815
        propType: str  # noqa: N815
        yearBuilt: int  # noqa: N815
        propLandUse: str  # noqa: N815
        propIndicator: int  # noqa: N815
        legal1: str  # noqa: N815
        quitClaimFlag: bool  # noqa: N815
        REOflag: bool  # noqa: N815

    class Sale(BaseModel, extra=Extra.allow):
        class SaleAmount(BaseModel, extra=Extra.allow):
            saleRecDate: date  # noqa: N815
            saleDisclosureType: int  # noqa: N815
            saleDocNum: str  # noqa: N815
            saleTransType: str  # noqa: N815

        sequenceSaleHistory: int  # noqa: N815
        sellerName: str  # noqa: N815
        saleSearchDate: date  # noqa: N815
        saleTransDate: date  # noqa: N815
        transactionIdent: str  # noqa: N815
        calculation: dict  # noqa: N815
        amount: SaleAmount  # noqa: N815

    class Building(BaseModel, extra=Extra.allow):
        class BuildingSize(BaseModel, extra=Extra.allow):
            bldgSize: int
            grossSize: int
            grossSizeAdjusted: int
            groundFloorSize: int
            livingSize: int
            sizeInd: str
            universalSize: int

        class Rooms(BaseModel, extra=Extra.allow):
            bathFixtures: int
            bathsFull: int
            bathsTotal: int
            beds: int
            roomsTotal: int

        class Interior(BaseModel, extra=Extra.allow):
            bsmtSize: int
            bsmtFinishedPercent: int
            fplcCount: int
            fplcInd: str
            fplcType: str

        class Construction(BaseModel, extra=Extra.allow):
            condition: str
            wallType: str
            propertyStructureMajorImprovementsYear: str

        class Parking(BaseModel, extra=Extra.allow):
            prkgSize: int
            prkgSpaces: int

        class BuildingSummary(BaseModel, extra=Extra.allow):
            levels: int
            unitsCount: int
            view: str
            viewCode: str

        size: BuildingSize
        rooms: Rooms
        interior: Interior
        construction: Construction
        parking: Parking
        summary: BuildingSummary

    class Assessment(BaseModel, extra=Extra.allow):
        class AssessedValue(BaseModel, extra=Extra.allow):
            assdImprValue: int
            assdLandValue: int
            assdTtlValue: int

        class MarketValue(BaseModel, extra=Extra.allow):
            mktImprValue: int
            mktLandValue: int
            mktTtlValue: int

        class Tax(BaseModel, extra=Extra.allow):
            class Exemption(BaseModel, extra=Extra.allow):
                # Github pilot made up these fields, but maybe it has seen ATTOM API before?
                exemptionAmt: int  # noqa: N815
                exemptionCode: str  # noqa: N815
                exemptionDesc: str  # noqa: N815
                exemptionYear: int  # noqa: N815

            class ExemptionType(BaseModel, extra=Extra.allow):
                # Github pilot made up these fields, but maybe it has seen ATTOM API before?
                exemptionTypeCode: str  # noqa: N815
                exemptionTypeDesc: str  # noqa: N815

            taxAmt: float  # noqa: N815
            taxPerSizeUnit: float  # noqa: N815
            taxYear: int  # noqa: N815
            exemption: Exemption  # noqa: N815
            exemptiontype: ExemptionType  # noqa: N815

        class Owner(BaseModel, extra=Extra.allow):
            class OwnerDetail(BaseModel, extra=Extra.allow):
                lastName: str  # noqa: N815
                trustIndicator: str  # noqa: N815

            corporateIndicator: str
            type: str
            description: str
            owner1: OwnerDetail
            owner2: OwnerDetail
            owner3: OwnerDetail
            owner4: OwnerDetail
            absenteeOwnerStatus: str
            mailingAddressOneLine: str

        class Mortgage(BaseModel, extra=Extra.allow):
            class Title(BaseModel, extra=Extra.allow):
                companyName: str

            class MortgageDetail(BaseModel, extra=Extra.allow):
                amount: int
                companyCode: str
                deedType: str

            FirstConcurrent: MortgageDetail
            SecondConcurrent: MortgageDetail | None
            ThirdConcurrent: MortgageDetail | None
            title: Title

        # assessment fields:
        appraised: dict
        assessed: AssessedValue
        market: MarketValue
        tax: Tax
        improvementPercent: int
        owner: Owner
        mortgage: Mortgage

    class Vintage(BaseModel):
        lastModified: date  # noqa: N815
        pubDate: date  # noqa: N815

    # ATTOM Property record fields:
    identifier: Identifier
    address: Address
    location: Location
    summary: Summary | None  # present in expanded profile views
    sale: Sale | None  # present in expanded profile views
    building: Building | None

    vintage: Vintage


@dataclass(kw_only=True)
class AttomDataApi(CacheableApi):
    api_key: str
    api_url: str
    zoo: int = 1
    vendor: ExternalApiData.Vendor = ExternalApiData.Vendor.ATTOM

    # https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/address?postalcode=82009&page=1&pagesize=100

    # Transaction V3 : preforeclosure detail
    # https://api.gateway.attomdata.com/property/v3/preforeclosuredetails?combinedAddress=11235%20S%20STEWART%20AVE%2C%20Chicago%2C%20IL%2C%2060628

    # ########################################
    # Property-centric APIs:  https://api.developer.attomdata.com/docs#!/Property32V1
    # ########################################
    def get_properties_in_zip(self, zipcode: str) -> PropertyAddressResponse:
        # List of properties within a zip code.
        # Check that we called with:
        #   https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/address?postalcode=92101&propertytype=MULTI%20FAMILY%20DWELLING&orderby=beds&page=1&pagesize=200
        #  - a valid zip code
        url = self.api_url + "/propertyapi/v1.0.0/property/address"
        propertytype = "MULTI FAMILY DWELLING"
        params = {"postalcode": zipcode, "propertytype": propertytype}
        # lookup key should be unique within the vendor
        lookup_key = f"property/address:{zipcode}:{propertytype}"
        hash_version = 1  # change when we change lookup key

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
            paged=False,
        )
        assert len(external_data.data["property"]) == 1, "Expected only one property record"
        prop_expanded_profile = AttomPropertyRecord.parse_obj(external_data.data["property"][0])
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
