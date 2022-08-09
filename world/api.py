from typing import List

from ninja import NinjaAPI, ModelSchema

from world.models import PropertyListing

api = NinjaAPI()


class ListingSchema(ModelSchema):
    class Config:
        model = PropertyListing
        model_fields = ['id', 'price', 'addr', 'neighborhood', 'zipcode', 'br', 'ba', 'founddate', 'seendate', 'mlsid',
                        'size', 'thumbnail', 'listing_url', 'soldprice', 'status', 'prev_listing']


@api.get("/listinghistory", response=List[ListingSchema])
def get(request, mlsid: str):
    listings = PropertyListing.objects.filter(mlsid=mlsid).order_by('-founddate')
    return listings
