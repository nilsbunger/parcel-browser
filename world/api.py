from ninja.pagination import paginate
from typing import List

from ninja import NinjaAPI, ModelSchema, Schema, Query
from ninja.orm import create_schema

from world.models import AnalyzedListing, PropertyListing

api = NinjaAPI()


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


class ListingSchema(ModelSchema):
    analyzedlisting_set: AnalyzedListingSchema
    centroid_x: float
    centroid_y: float

    class Config:
        model = PropertyListing
        arbitrary_types_allowed = True
        model_fields = ['id', 'price', 'addr', 'neighborhood', 'zipcode', 'br', 'ba', 'founddate', 'seendate', 'mlsid',
                        'size', 'thumbnail', 'listing_url', 'soldprice', 'status', 'prev_listing']

    @staticmethod
    def resolve_analyzedlisting_set(self):
        return self.analyzedlisting_set.latest('datetime_ran')
        # return [i.id for i in obj.owner.all()]

    @staticmethod
    def resolve_centroid_x(self):
        return self.parcel.geom.centroid.coords[0]

    @staticmethod
    def resolve_centroid_y(self):
        return self.parcel.geom.centroid.coords[1]


class ListingsFilters(Schema):
    price__gte: int = None
    price__lte: int = None


@api.get("/listings", response=List[ListingSchema])
@paginate
def get_listings(request, filters: ListingsFilters = Query(...)):
    print(filters.dict())

    # Temporary way to build a new dict
    filter_params = {}
    for key in filters.dict():
        if filters.dict()[key] is not None:
            filter_params[key] = filters.dict()[key]
    print(filter_params)

    return PropertyListing.objects.prefetch_related('analyzedlisting_set').prefetch_related(
        'prev_listing').filter(
        analyzedlisting__isnull=False).distinct().order_by('-founddate')
