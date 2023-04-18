from datetime import datetime
from typing import Any, Union

from pydantic import BaseModel, Extra, Field

extra_setting = Extra.forbid


class CompSalesResponse(BaseModel, extra=extra_setting):
    group: "ResponseGroup" = Field(..., alias="RESPONSE_GROUP")


class ResponseGroup(BaseModel, extra=extra_setting):
    resp_party: "RespondingParty" = Field(..., alias="RESPONDING_PARTY")
    resp: "Response" = Field(..., alias="RESPONSE")
    product: dict[Any | None, Any | None] = Field(..., alias="PRODUCT")
    echo_fields: dict[Any | None, Any | None] = Field(..., alias="ECHOED_FIELDS_ext")


class RespondingParty(BaseModel, extra=extra_setting):
    name: str = Field(..., alias="@_Name")
    street_address: str = Field(..., alias="@_StreetAddress")
    city: str = Field(..., alias="@_City")
    state: str = Field(..., alias="@_State")
    postal_code: str = Field(..., alias="@_PostalCode")


class Key(BaseModel, extra=extra_setting):
    name: str = Field(..., alias="@_Name")
    value: str = Field(..., alias="@_Value")


class SubjectPropertyContainer(BaseModel, extra=extra_setting):
    subject_property: "PropertyList" = Field(..., alias="SUBJECT_PROPERTY_ext")


class PropertyInformationResponseExt(BaseModel, extra=extra_setting):
    property_info_response: SubjectPropertyContainer = Field(..., alias="PROPERTY_INFORMATION_RESPONSE_ext")


class Response(BaseModel, extra=extra_setting):
    resp_datetime: datetime = Field(..., alias="@ResponseDateTime")
    key: Key = Field(..., alias="KEY")
    resp_data: PropertyInformationResponseExt = Field(..., alias="RESPONSE_DATA")


class PropertyList(BaseModel, extra=extra_setting):
    properties: list[Union["CompPropertyContainer", "SubjectProperty"]] = Field(..., alias="PROPERTY")


class ProductInfoExt(BaseModel, extra=extra_setting):
    report_id: str = Field(..., alias="@ReportID_ext")
    report_desc: str = Field(..., alias="@ReportDescription_ext")
    product: str = Field(..., alias="@Product_ext")
    record_num: str = Field(..., alias="@RecordNumber_ext")
    map_ver: str = Field(..., alias="@MappingVersion_ext")


class MailingAddressExt(BaseModel, extra=extra_setting):
    street_addr: str = Field(..., alias="@_StreetAddress")
    city: str = Field(..., alias="@_City")
    state: str = Field(..., alias="@_State")
    postal_code: str = Field(..., alias="@_PostalCode")


class Identification(BaseModel, extra=extra_setting):
    rt_property_id: str = Field(..., alias="@RTPropertyID_ext")
    dq_property_id: str = Field(..., alias="@DQPropertyID_ext")
    county_fips_name: str = Field(..., alias="@CountyFIPSName_ext")
    parcel_id: str | None = Field(None, alias="@AssessorsParcelIdentifier")
    parcel_id2: str = Field(..., alias="@AssessorsSecondParcelIdentifier")
    long: str | None = Field(None, alias="@LongitudeNumber")
    lat: str | None = Field(None, alias="@LatitudeNumber")


class LoanExt(BaseModel, extra=extra_setting):
    loan_type: str | None = Field(None, alias="@_Type")
    trust_deed_doc_num: str = Field(None, alias="@TrustDeedDocumentNumber")
    amount: str | None = Field(None, alias="@_Amount")
    seller_carryback: str | None = Field(None, alias="@SellerCarrybackindicator")


class LoansExt(BaseModel, extra=extra_setting):
    seller_carryback: str | None = Field(None, alias="@SellerCarrybackindicator")
    loans: list[LoanExt] = Field(..., alias="LOAN_ext")


class SalesHistory(BaseModel, extra=extra_setting):
    sale_amount: str = Field(..., alias="@PropertySalesAmount")
    buyer_unparsed_name: str = Field(..., alias="@BuyerUnparsedName_ext")
    recorded_doc_id: str | None = Field(None, alias="@RecordedDocumentIdentifier")
    full_or_partial_transfer_value_type: str | None = Field(None, alias="@FullOrPartialTransferValueType_ext")
    multiple_apns: str | None = Field(None, alias="@MultipleApnIndicator_ext")
    seller_unparsed_name: str = Field(..., alias="@SellerUnparsedName")
    price_per_sqft: str = Field(..., alias="@PricePerSquareFootAmount")
    sale_data: datetime | None = Field(None, alias="@PropertySalesDate")
    loans: LoansExt = Field(..., alias="LOANS_ext")
    loan: LoanExt | None = Field(None, alias="LOAN_ext")
    ArmsLengthTransactionIndicatorExt: str | None = Field(None, alias="@ArmsLengthTransactionIndicatorExt")
    TransferDate_ext: datetime | None = Field(None, alias="@TransferDate_ext")


class Owner(BaseModel, extra=extra_setting):
    name: str = Field(..., alias="@_Name")
    owner_type: str | None = Field(None, alias="@_TypeExt")
    descr: str | None = Field(None, alias="@_Description_ext")
    owner2_name: str = Field(..., alias="@_SecondaryOwnerName_ext")


class LegalDescription(BaseModel, extra=extra_setting):
    descr_type: str = Field(..., alias="@_Type")
    descr: str = Field(..., alias="@_TextDescription")


class Site(BaseModel, extra=extra_setting):
    zone_cat: str = Field(..., alias="@PropertyZoningCategoryType")
    depth: str = Field(..., alias="@DepthFeetCount")
    width: str = Field(..., alias="@WidthFeetCount")
    lot_sq_ft: str = Field(..., alias="@LotSquareFeetCount")


class Tax(BaseModel, extra=extra_setting):
    assessed_val: str = Field(..., alias="@_TotalAssessedValueAmount")
    assessor_mkt_val: str = Field(..., alias="@_AssessorMarketValue_ext")
    assessor_cash_val: str | None = Field(None, alias="@_AssessorFullCashValue_ext")


class Attic(BaseModel, extra=extra_setting):
    sqft: str = Field(..., alias="@SquareFeetCount")


class Basement(BaseModel, extra=extra_setting):
    sqft: str = Field(..., alias="@SquareFeetCount")
    finished_percent: str | None = Field(None, alias="@_FinishedPercent")


class Level(BaseModel, extra=extra_setting):
    level_type: str = Field(..., alias="@_Type")
    sqft: str = Field(..., alias="@SquareFeetCount")


class Levels(BaseModel, extra=extra_setting):
    level: list[Level] = Field(..., alias="LEVEL")


class Cooling(BaseModel, extra=extra_setting):
    descr: str = Field(..., alias="@_UnitDescription")


class CarStorageLocation(BaseModel, extra=extra_setting):
    sqft: str = Field(..., alias="@SquareFeetCount")
    # _ParkingSpacesCount: Optional[str] = Field(None, alias="@_ParkingSpacesCount")
    # _Type: Optional[str] = Field(None, alias="@_Type")
    space_count: str = Field(..., alias="@_ParkingSpacesCount")
    loc_type: str = Field(..., alias="@_Type")
    other_descr_type: str = Field(..., alias="@_TypeOtherDescription")


class CarStorage(BaseModel, extra=extra_setting):
    car_storage_loc: CarStorageLocation = Field(..., alias="CAR_STORAGE_LOCATION")


class Heating(BaseModel, extra=extra_setting):
    descr: str = Field(..., alias="@_UnitDescription")
    other_descr_type: str | None = Field(None, alias="@_TypeOtherDescription")


class ExteriorFeature(BaseModel, extra=extra_setting):
    feature_type: str = Field(..., alias="@_Type")
    other_descr_type: str = Field(..., alias="@_TypeOtherDescription")
    descr: str = Field(..., alias="@_Description")


class StructureAnalysis(BaseModel, extra=extra_setting):
    year_built: str = Field(..., alias="@PropertyStructureBuiltYear")


class Amenity(BaseModel, extra=extra_setting):
    amenity_type: str = Field(..., alias="@_Type")
    exists_ind: str | None = Field(None, alias="@_ExistsIndicator")
    descr: str | None = Field(None, alias="@_DetailedDescription")


class SalesContract(BaseModel, extra=extra_setting):
    date: datetime = Field(..., alias="@_Date")


# This is the original subject property (the one that we are requesting comps around)
class Amenities(BaseModel, extra=extra_setting):
    amenity: list[Amenity] = Field(..., alias="AMENITY")


class Structure(BaseModel, extra=extra_setting):
    bath_count: str = Field(..., alias="@TotalBathroomCount")
    br_count: str = Field(..., alias="@TotalBedroomCount")
    bath_full_count: str | None = Field(None, alias="@TotalBathroomFullCount_ext")
    bath_half_count: str | None = Field(None, alias="@TotalBathroomHalfCount_ext")
    bath_qtr_count: str | None = Field(None, alias="@TotalBathroomQuarterCount_ext")
    bath_3qtr_count: str | None = Field(None, alias="@TotalBathroomThreeQuarterCount_ext")
    room_count: str = Field(..., alias="@TotalRoomCount")
    stories_count: str = Field(..., alias="@StoriesCount")
    living_unit_count: str = Field(..., alias="@LivingUnitCount")
    living_area_sqft: str = Field(..., alias="@GrossLivingAreaSquareFeetCount")
    bath_dq_count: str | None = Field(None, alias="@TotalBathroomCountDq_ext")
    structure_analysis: StructureAnalysis = Field(..., alias="STRUCTURE_ANALYSIS")
    car_storage: CarStorage = Field(..., alias="CAR_STORAGE")
    attic: Attic = Field(..., alias="ATTIC")
    basement: Basement = Field(..., alias="BASEMENT")
    amenities: Amenities | None = Field(None, alias="AMENITIES")
    amenity: Amenity | None = Field(None, alias="AMENITY")
    ext_feature: list[ExteriorFeature] | ExteriorFeature = Field(..., alias="EXTERIOR_FEATURE")
    heating: Heating = Field(..., alias="HEATING")
    levels: Levels = Field(..., alias="LEVELS")
    cooling: Cooling = Field(..., alias="COOLING")


class PropertyBase(BaseModel, extra=extra_setting):
    city: str = Field(..., alias="@_City")
    street_addr: str = Field(..., alias="@_StreetAddress")
    state: str = Field(..., alias="@_State")
    postal_code: str = Field(..., alias="@_PostalCode")
    std_use_code: str = Field(..., alias="@StandardUseCode_ext")
    std_use_desc: str = Field(..., alias="@StandardUseDescription_ext")
    site_and_mail_addr_same: str | None = Field(None, alias="@SiteMailAddressSameIndicator_ext")
    ident: Identification = Field(..., alias="_IDENTIFICATION")
    sales_history: SalesHistory = Field(..., alias="SALES_HISTORY")
    structure: Structure = Field(..., alias="STRUCTURE")
    site: Site = Field(..., alias="SITE")
    tax: Tax = Field(..., alias="_TAX")
    legal_desc: LegalDescription = Field(..., alias="_LEGAL_DESCRIPTION")
    mailing_addr: MailingAddressExt = Field(..., alias="MAILING_ADDRESS_ext")
    owner: Owner = Field(..., alias="_OWNER")


class ComparableProperty(PropertyBase, extra=extra_setting):
    seq: str = Field(..., alias="@_Sequence")
    distance_from_subj: str = Field(..., alias="@DistanceFromSubjectPropertyMilesCount")
    lat: str = Field(..., alias="@LatitudeNumber")
    long: str = Field(..., alias="@LongitudeNumber")


class SubjectProperty(PropertyBase, extra=extra_setting):
    parcel_id: str = Field(..., alias="@PropertyParcelID")
    PrivacyType_ext: str = Field(..., alias="@PrivacyType_ext")
    site_and_mail_addr_same: str | None = Field(None, alias="@SiteMailAddressSameIndicator")
    PRODUCT_INFO_ext: ProductInfoExt = Field(..., alias="PRODUCT_INFO_ext")
    SALES_CONTRACT: SalesContract = Field(..., alias="SALES_CONTRACT")


class CompPropertyContainer(BaseModel, extra=extra_setting):
    product_info: ProductInfoExt = Field(..., alias="PRODUCT_INFO_ext")
    comp_prop: ComparableProperty = Field(..., alias="COMPARABLE_PROPERTY_ext")


CompSalesResponse.update_forward_refs()
ResponseGroup.update_forward_refs()
SubjectPropertyContainer.update_forward_refs()
PropertyList.update_forward_refs()
# PropertyUnion.update_forward_refs()
