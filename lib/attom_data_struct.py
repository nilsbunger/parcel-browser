from datetime import date

from pydantic import BaseModel, Extra

from elt.models.external_api_data import ApiResponseStatus


class PropertyAddressResponse(BaseModel):
    status: "ApiResponseStatus"
    property: list["AttomPropertyRecord"]
    # raw: any  # raw django model entry for this response (optional)


class Address(BaseModel):
    country: str  # country
    countrySubd: str  # state  # noqa: N815
    line1: str | None  # address - optiional, some records have no street address
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


class SaleAmount(BaseModel, extra=Extra.allow):
    saleRecDate: date  # noqa: N815
    saleDisclosureType: int  # noqa: N815
    saleDocNum: str  # noqa: N815
    saleTransType: str  # noqa: N815


class Sale(BaseModel, extra=Extra.allow):
    sequenceSaleHistory: int  # noqa: N815
    sellerName: str  # noqa: N815
    saleSearchDate: date  # noqa: N815
    saleTransDate: date  # noqa: N815
    transactionIdent: str  # noqa: N815
    calculation: dict  # noqa: N815
    amount: SaleAmount  # noqa: N815


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


class Building(BaseModel, extra=Extra.allow):
    size: BuildingSize
    rooms: Rooms
    interior: Interior
    construction: Construction
    parking: Parking
    summary: BuildingSummary


class AssessedValue(BaseModel, extra=Extra.allow):
    assdImprValue: int
    assdLandValue: int
    assdTtlValue: int


class MarketValue(BaseModel, extra=Extra.allow):
    mktImprValue: int
    mktLandValue: int
    mktTtlValue: int


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


class Tax(BaseModel, extra=Extra.allow):
    taxAmt: float  # noqa: N815
    taxPerSizeUnit: float  # noqa: N815
    taxYear: int  # noqa: N815
    exemption: Exemption  # noqa: N815
    exemptiontype: ExemptionType  # noqa: N815


class OwnerDetail(BaseModel, extra=Extra.allow):
    lastName: str  # noqa: N815
    trustIndicator: str  # noqa: N815


class Owner(BaseModel, extra=Extra.allow):
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


class Assessment(BaseModel, extra=Extra.allow):
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


class AttomPropertyRecord(BaseModel, extra=Extra.ignore):
    # ATTOM Property record fields:
    identifier: Identifier
    address: Address
    location: Location
    summary: Summary | None  # present in expanded profile views
    sale: Sale | None  # present in expanded profile views
    building: Building | None

    vintage: Vintage
