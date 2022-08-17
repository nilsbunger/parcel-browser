from ninja.pagination import paginate
from typing import List

from ninja import NinjaAPI, ModelSchema, Schema, Query
from ninja.orm import create_schema
from ninja.security import HttpBearer, django_auth

from world.models import AnalyzedListing, PropertyListing
from django.contrib.gis.db.models.functions import Centroid
from django.db.models import F, Subquery


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
        model_fields = ['id', 'price', 'addr', 'neighborhood', 'zipcode', 'br', 'ba', 'founddate', 'seendate', 'mlsid',
                        'size', 'thumbnail', 'listing_url', 'soldprice', 'status', 'prev_listing']


@api.get("/listinghistory", response=List[ListingHistorySchema])
def get_listing_history(request, mlsid: str):
    listings = PropertyListing.objects.filter(
        mlsid=mlsid).order_by('-founddate')
    return listings


class AnalyzedListingSchema(ModelSchema):
    class Config:
        model = AnalyzedListing
        model_fields = ['id', 'details']


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
            'id', 'price', 'addr', 'neighborhood', 'zipcode', 'br', 'ba', 'founddate', 'seendate', 'mlsid',
                        'size', 'thumbnail', 'listing_url', 'soldprice', 'status', 'prev_listing']

    # These resolve_xx methods resolve certain fields on the response automatically
    # Functionality provided by Django-Ninja
    @staticmethod
    def resolve_analysis(obj):
        # Only return the latest analysis
        analysis : AnalyzedListing = obj.analyzedlisting
        analysis_dict = analysis.details
        analysis_dict['analysis_id'] = analysis.id
        analysis_dict['is_tpa'] = analysis.is_tpa
        analysis_dict['is_mf'] = analysis.is_mf
        analysis_dict['apn'] = analysis.parcel.apn
        analysis_dict['zone'] = analysis.zone
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
            return {'category': 'updated', 'prev_values': {
                # Add more fields here as needed
                "price": obj.prev_listing.price,
            }}
        else:
            return {'category': 'new', 'prev_values': {}}


class ListingsFilters(Schema):
    price__gte: int = None
    price__lte: int = None
    neighborhood__contains: str = None


@api.get("/listings", response=List[ListingSchema])
@paginate
def get_listings(request, order_by: str = 'founddate', asc: bool = False,
                 filters: ListingsFilters = Query(...)):

    # Strip away the filter params that are none
    # Filters are already validated by the ListingsFilters Schema above
    filter_params = {}
    for key in filters.dict():
        if filters.dict()[key] is not None:
            filter_params[key] = filters.dict()[key]

    # If the field doesn't exist on the PropertyListing model, it probably exists
    # either on AnalyzedListing model or AnalyzedListing's detail field, so let's prefix it
    if not field_exists_on_model(PropertyListing, order_by):
        if field_exists_on_model(AnalyzedListing, order_by):
            # field is on AnalyzedListing.
            order_by = 'analyzedlisting__' + order_by
        else:
            order_by = 'analyzedlisting__details__' + order_by

    if not asc:
        order_by = '-' + order_by

    # A subquery that contains the primary keys of each latest listing per property
    # This avoids having different listings of the same property but at different price points
    latest_listings_pks = Subquery(
        PropertyListing.objects
        # Ensure that any property listings we find have an analysis attached to it
        .filter(analyzedlisting__isnull=False, **filter_params)
        .order_by('mlsid', '-founddate')
        .distinct('mlsid')
        .values('pk')
    )

    return (PropertyListing.objects
            .filter(pk__in=latest_listings_pks)
            # Prefetch because we need details on the analysis in the response.
            # Later on, we should optimize so as to only pre-fetch the latest analysis, as there can
            # be multiple for a property. We would also want to join all fields of the analysis
            # directly into the response, but haven't found a good way to do this yet
            .prefetch_related('analyzedlisting')
            # Used to see if this listing is new or not, and for extracting previous price info
            .prefetch_related('prev_listing')
            # Prefetch parcel to attach information on the centroid of each parcel, used for map plotting
            .prefetch_related('parcel')
            .annotate(centroid=Centroid(F('parcel__geom')))
            .order_by(order_by)
            )
