import datetime
import pprint
import tempfile
import traceback
from typing import Any, Dict, List, Optional

import django
from django.contrib.gis.db.models.functions import Centroid
from django.db.models import F
from ninja import ModelSchema, NinjaAPI, Query, Schema
from ninja.pagination import paginate
from ninja.security import HttpBearer, django_auth
from pydantic import Field

from lib.analyze_parcel_lib import analyze_one_parcel
from lib.co.co_eligibility_lib import AB2011Eligible, EligibilityCheck
from lib.crs_lib import get_utm_crs
from lib.listings_lib import address_to_parcel, address_to_parcels_loose
from world.models import AnalyzedListing, Parcel, PropertyListing, RentalData, Roads


# Django-ninja authentication guide: https://django-ninja.rest-framework.com/guides/authentication/
class GlobalAuth(HttpBearer):
    def authenticate(self, request, token):
        if token == "supersecret":
            return token


api = NinjaAPI(auth=django_auth, csrf=True)


def field_exists_on_model(model, field: str) -> bool:
    # A simple function to check if a field exists on a model
    try:
        # Check if this exists
        model._meta.get_field(field)
        return True
    except:
        return False


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


@api.get("/listinghistory", response=List[ListingHistorySchema])
def get_listing_history(request, mlsid: str):
    listings = PropertyListing.objects.filter(mlsid=mlsid).order_by("-founddate")
    return listings


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


@api.get("/rentalrates")  # response=List[RentalRatesSchema])
def get_rental_rates(request) -> List[RentalRatesSchema]:
    rental_data = RentalData.objects.exclude(details__has_key="status_code").order_by(
        "parcel", "-details__mean"
    )
    pid: str = ""
    retlist = []
    for rd in rental_data:
        if rd.parcel_id != pid:
            retlist.append(
                {
                    "pid": rd.parcel_id,
                    "lat": round(rd.location.y, 7),
                    "long": round(rd.location.x, 7),
                    "rents": {},
                }
            )
        assert retlist[-1]["pid"] == rd.parcel_id
        retlist[-1]["rents"][f"{rd.br}BR,{rd.ba}BA"] = {
            "rent_mean": rd.details["mean"],
            "rent_75_percentile": rd.details["percentile_75"],
            "num_samples": rd.details["samples"],
        }
        pid = rd.parcel_id

    # print(f"Returning {len(retlist)} items")
    # pprint.pprint(retlist)
    return retlist


@api.get("/listings", response=List[ListingSchema])
@paginate
def get_listings(
    request, order_by: str = "founddate", asc: bool = False, filters: ListingsFilters = Query(...)
):
    # Strip away the filter params that are none
    # Filters are already validated by the ListingsFilters Schema above
    filters_xlat = {
        "is_mf": "analyzedlisting__is_mf",
        "is_tpa": "analyzedlisting__is_tpa",
        "neighborhood__contains": "neighborhood__in",
    }

    # TODO : Next line is a hack - we're sending neighborhood list as comma-separated string instead of array
    if not filters.neighborhood__contains is None:
        filters.neighborhood__contains = filters.neighborhood__contains[0].split(",")

    filter_params = {}
    for key in filters.dict():
        if filters.dict()[key] is not None:
            if key in ["is_mf", "is_tpa"] and filters.dict()[key] == False:
                # is_mf, or is_mf mean "only mf / only tpa". so if it's false, don't add a filter criteria
                continue
            filter_params[filters_xlat.get(key, key)] = filters.dict()[key]

    # Construct ordering query: if the field doesn't exist on the PropertyListing model, it probably exists
    # either on AnalyzedListing model or AnalyzedListing's detail field, so let's prefix it
    if not field_exists_on_model(PropertyListing, order_by):
        if field_exists_on_model(AnalyzedListing, order_by):
            # field is on AnalyzedListing.
            order_by = "analyzedlisting__" + order_by
        else:
            order_by = "analyzedlisting__details__" + order_by

    if not asc:
        order_by = "-" + order_by

    listings = (
        PropertyListing.active_listings_queryset()
        .filter(analyzedlisting__isnull=False, **filter_params)
        .prefetch_related("analyzedlisting", "prev_listing", "parcel")
        .annotate(centroid=Centroid(F("parcel__geom")))
        .order_by(order_by)
    )

    return listings


@api.post("/analysis/")
def redo_analysis(request, apn: str = None, al_id: int = None):
    """Trigger a re-run of parcel analysis, used by /new-listing frontend"""

    if al_id:
        analyzed_listing = AnalyzedListing.objects.prefetch_related("listing").get(id=al_id)
        property_listing = analyzed_listing.listing
    else:
        parcel = Parcel.objects.get(apn=apn)
        property_listing = PropertyListing.get_latest_or_create(parcel)

    sd_utm_crs = get_utm_crs()  # San Diego specific

    with tempfile.TemporaryDirectory() as tmpdirname:
        # Generally should match this call to analyze_batch() call in scrape.py
        analyzed_listing = analyze_one_parcel(
            property_listing.parcel,
            sd_utm_crs,
            property_listing,
            save_dir=tmpdirname,
            dry_run=False,
            show_plot=False,
            force_uploads=True,
        )

    return {"analysisId": analyzed_listing.id}


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


@api.get("/analysis/{al_id}", response=AnalysisResponseSchema)
def get_analysis(request, al_id: int):
    """Get analysis results for a given analysis id"""
    # al_json = AnalysisResponseSchema.from_orm(analyzed_listing).dict()
    return AnalyzedListing.objects.prefetch_related("listing").get(id=al_id)


@api.get("/parcel/{apn}", response=ParcelSchema)
def get_parcel(request, apn: str):
    """Get parcel info for a given APN"""
    parcel = Parcel.objects.get(apn=apn)
    x = AB2011Eligible()
    x.run(parcel)
    retval = ParcelSchema.from_orm(parcel)
    retval.ab2011_result = x.check
    return retval


@api.get("/road/{road_segid}", response=RoadSchema)
def get_road(request, road_segid: int):
    """Get road info for a given road segid"""
    return Roads.objects.get(roadsegid=road_segid)


@api.get("/address-search/{addr}")
def address_search(request, addr: str):
    """Look up an address and return a parcel if there's a single match."""
    # Takes in an address. Returns a list of possible parcels/APNs
    # Temporary. Let's clean this up later
    try:
        parcel, error = address_to_parcel(addr, jurisdiction="SD")
        # TODO: Finish this better address matcher
        # parcel, error = address_to_parcels_loose(addr)
    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
    if error:
        return {"error": f"An error occurred: {error}"}
    try:
        analyzed_listing = AnalyzedListing.objects.filter(parcel=parcel).order_by("-datetime_ran")[
            0
        ]
    except IndexError as e:
        analyzed_listing = None
    except Exception as e:
        traceback.print_exc()
        return {"error": "AnalyzedListing lookup failed:" + str(e)}

    analysis_id = analyzed_listing.id if analyzed_listing else None
    return {"apn": parcel.apn, "address": parcel.address, "analyzed_listing": analysis_id}
