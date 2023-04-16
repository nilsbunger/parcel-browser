from datetime import date

from pydantic import BaseModel, Extra

from elt.models.external_api_data import ApiResponseStatus


class PropertyAddressResponse(BaseModel):
    status: "ApiResponseStatus"
    property: list["AttomPropertyRecord"]
    # raw: any  # raw django model entry for this response (optional)


class Address(BaseModel):
    country: str  # country
    countrySubd: str  # state
    line1: str | None  # address - optiional, some records have no street address
    line2: str  # city, state zip
    locality: str  # city
    matchCode: str | None  # missing from some records
    postal1: str  # zipcode
    # fields typically present in "expanded profile" search but not in "address search":
    situsHouseNumber: int | None
    situsStreetName: str | None
    situsAddressSuffix: str | None

    # skipped:
    # "oneLine": "1646 J ST, SAN DIEGO, CA 92101",
    # "postal2": "7627",
    # "postal3": "C020",

    @property
    def city(self) -> str:
        return self.locality

    @property
    def state(self) -> str:
        return self.countrySubd

    @property
    def zip(self) -> str:
        return self.postal1


class Identifier(BaseModel):
    Id: int
    fips: str
    apn: str
    attomId: int


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
    archStyle: str | None
    absenteeInd: str
    propClass: str
    propSubType: str
    propType: str
    yearBuilt: int
    propLandUse: str
    propIndicator: int
    legal1: str
    quitClaimFlag: bool
    REOflag: bool


class SaleAmount(BaseModel, extra=Extra.allow):
    saleAmt: int | None
    saleCode: str | None  # eg "SALE PRICE (FULL) Full sales price"
    saleDisclosureType: int
    saleDocNum: str
    saleDocType: str | None  # eg "DEED"
    saleRecDate: date
    saleTransType: str  # eg "Resale", "Construcction Loan/Financing",


class Sale(BaseModel, extra=Extra.allow):
    sequenceSaleHistory: int
    sellerName: str
    saleSearchDate: date
    saleTransDate: date | None
    transactionIdent: str
    calculation: dict
    amount: SaleAmount


class BuildingSize(BaseModel, extra=Extra.allow):
    bldgSize: int
    grossSize: int
    grossSizeAdjusted: int
    groundFloorSize: int | None
    livingSize: int
    sizeInd: str  # eg "BUILDING SQFT"
    universalSize: int


class Rooms(BaseModel, extra=Extra.allow):
    bathFixtures: int | None
    bathsFull: int
    bathsTotal: float
    beds: int
    roomsTotal: int | None


class Interior(BaseModel, extra=Extra.allow):
    bsmtSize: int | None
    bsmtFinishedPercent: int | None
    fplcCount: int | None
    fplcInd: str | None
    fplcType: str | None


class Construction(BaseModel, extra=Extra.allow):
    condition: str | None
    wallType: str | None
    propertyStructureMajorImprovementsYear: str | None
    frameType: str | None  # eg "WOOD"
    constructionType: str | None  # eg "WOOD"


class Parking(BaseModel, extra=Extra.allow):
    prkgSize: int | None
    prkgSpaces: int | None


class BuildingSummary(BaseModel, extra=Extra.allow):
    levels: int | None
    unitsCount: int
    view: str  # eg "VIEW - NONE"
    viewCode: str
    storyDesc: str | None  # eg "MISCELLANEOUS"


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
    exemptionAmt: int
    exemptionCode: str
    exemptionDesc: str
    exemptionYear: int


class ExemptionType(BaseModel, extra=Extra.allow):
    # Github pilot made up these fields, but maybe it has seen ATTOM API before?
    exemptionTypeCode: str
    exemptionTypeDesc: str


class Tax(BaseModel, extra=Extra.allow):
    taxAmt: float
    taxPerSizeUnit: float
    taxYear: int
    exemption: Exemption
    exemptiontype: ExemptionType


class OwnerDetail(BaseModel, extra=Extra.allow):
    lastName: str
    trustIndicator: str


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
    lastModified: date
    pubDate: date


class AttomPropertyRecord(BaseModel, extra=Extra.ignore):
    # ATTOM Property record fields:
    identifier: Identifier
    address: Address
    location: Location
    summary: Summary | None  # present in expanded profile views
    sale: Sale | None  # present in expanded profile views
    building: Building | None

    vintage: Vintage
