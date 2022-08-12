from ninja.pagination import paginate
from typing import List

from ninja import NinjaAPI, ModelSchema, Schema, Query
from ninja.orm import create_schema

from world.models import AnalyzedListing, PropertyListing
from django.contrib.gis.db.models.functions import Centroid
from django.db.models import F, Subquery

api = NinjaAPI()


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
    analyzedlisting_set: AnalyzedListingSchema
    centroid_x: float
    centroid_y: float
    metadata: MetadataSchema

    class Config:
        model = PropertyListing
        arbitrary_types_allowed = True
        model_fields = ['id', 'price', 'addr', 'neighborhood', 'zipcode', 'br', 'ba', 'founddate', 'seendate', 'mlsid',
                        'size', 'thumbnail', 'listing_url', 'soldprice', 'status', 'prev_listing']

    @staticmethod
    def resolve_analyzedlisting_set(obj):
        return obj.analyzedlisting_set.latest('datetime_ran')
        # return [i.id for i in obj.owner.all()]

    @staticmethod
    def resolve_centroid_x(obj):
        return obj.centroid[0]

    @staticmethod
    def resolve_centroid_y(obj):
        return obj.centroid[1]

    @staticmethod
    def resolve_metadata(obj):
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


@api.get("/listings", response=List[ListingSchema])
@paginate
def get_listings(request, order_by: str = 'founddate', asc: bool = False,
                 filters: ListingsFilters = Query(...)):

    # Temporary way to build a new dict
    filter_params = {}
    for key in filters.dict():
        if filters.dict()[key] is not None:
            filter_params[key] = filters.dict()[key]

    # If the field doesn't exist on the PropertyListing model, it probably exists
    # in the details JSON on the AnalyzedListing model, so let's prefix it
    if not field_exists_on_model(PropertyListing, order_by):
        order_by = 'analyzedlisting__details__' + order_by

    if not asc:
        order_by = '-' + order_by

    return PropertyListing.objects \
        .filter(pk__in=Subquery(
            PropertyListing.objects.all().order_by(
                'mlsid', '-founddate').distinct('mlsid').values('pk')
        ), analyzedlisting__isnull=False, **filter_params) \
        .prefetch_related('analyzedlisting_set') \
        .prefetch_related('prev_listing') \
        .prefetch_related('parcel') \
        .annotate(centroid=Centroid(F('parcel__geom'))) \
        .distinct() \
        .order_by(order_by)
