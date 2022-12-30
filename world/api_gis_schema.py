import datetime
from typing import Any, Dict, List, Optional

from ninja import ModelSchema, Schema
from pydantic import Field

from lib.co.co_eligibility_lib import EligibilityCheck
from world.models import AnalyzedListing, Parcel, PropertyListing, RentalData, Roads


class ListingHistorySchema(ModelSchema):
    class Config:
        model = PropertyListing
        model_fields = [
            "id",
            "price",
            "addr",
            "neighborhood",
            "zipcode",
            "br",
            "ba",
            "founddate",
            "seendate",
            "mlsid",
            "size",
            "thumbnail",
            "listing_url",
            "soldprice",
            "status",
            "prev_listing",
        ]


class AnalyzedListingSchema(ModelSchema):
    class Config:
        model = AnalyzedListing
        model_fields = ["id", "details"]


class MetadataSchema(Schema):
    category: str
    prev_values: dict


class ListingSchema(ModelSchema):
    analysis: dict
    centroid_x: float
    centroid_y: float
    metadata: MetadataSchema

    class Config:
        model = PropertyListing
        arbitrary_types_allowed = True
        model_fields = [
            "id",
            "price",
            "addr",
            "neighborhood",
            "zipcode",
            "br",
            "ba",
            "founddate",
            "seendate",
            "mlsid",
            "size",
            "thumbnail",
            "listing_url",
            "soldprice",
            "status",
            "prev_listing",
        ]

    # These resolve_xx methods resolve certain fields on the response automatically
    # Functionality provided by Django-Ninja
    @staticmethod
    def resolve_analysis(obj):
        # Only return the latest analysis
        analysis: AnalyzedListing = obj.analyzedlisting
        analysis_dict = analysis.details
        analysis_dict["analysis_id"] = analysis.id
        analysis_dict["is_tpa"] = analysis.is_tpa
        analysis_dict["is_mf"] = analysis.is_mf
        analysis_dict["apn"] = analysis.parcel.apn
        analysis_dict["zone"] = analysis.zone
        return analysis_dict

    @staticmethod
    def resolve_centroid_x(obj):
        return obj.centroid[0]

    @staticmethod
    def resolve_centroid_y(obj):
        return obj.centroid[1]

    @staticmethod
    def resolve_metadata(obj):
        # metadata is used to store the status or category of a listing, and things like previous price
        if obj.prev_listing:
            return {
                "category": "updated",
                "prev_values": {
                    # Add more fields here as needed
                    "price": obj.prev_listing.price,
                },
            }
        else:
            return {"category": "new", "prev_values": {}}


class ListingsFilters(Schema):
    price__gte: int = None
    price__lte: int = None
    is_mf: bool = False
    is_tpa: bool = False
    # neighborhood__contains: str = None
    neighborhood__contains: List[str] = Field(None)


class RentalRatesSchema(ModelSchema):
    lat: float
    long: float
    sqft: Optional[int]
    rent_mean: int
    rent_75_percentile: int

    class Config:
        model = RentalData
        arbitrary_types_allowed = True
        model_fields = [
            "rundate",
        ]


class PropertyListingSchema(ModelSchema):
    class Config:
        model = PropertyListing
        model_exclude = ("addr", "parcel", "prev_listing")


class AnalysisResponseSchema(Schema):
    datetime_ran: datetime.datetime
    is_tpa: bool
    is_mf: bool
    zone: str
    salt: str
    dev_scenarios: List[Dict[str, Any]]
    details: Dict[str, Any]
    listing: PropertyListingSchema
    apn: str = Field(None, alias="parcel.apn")
    centroid: tuple = Field(None, alias="parcel.geom.centroid.coords")


class ParcelSchema(ModelSchema):
    ab2011_result: Optional[EligibilityCheck] = None

    class Config:
        model = Parcel
        model_exclude = ("geom",)


class RoadSchema(ModelSchema):
    segclass_decoded: str  # custom field which is a property on model Road
    funclass_decoded: str  # custom field which is a property on model Road

    class Config:
        model = Roads
        model_fields = ("roadsegid", "segclass", "funclass")
