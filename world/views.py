import json
import pprint
from itertools import chain

import pandas
import json
import geopandas as geopandas
from django.core.serializers import serialize
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView, ListView
# from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
from vectortiles.postgis.views import MVTView
from lib.analyze_parcel_lib import analyze_by_apn

from lib.crs_lib import get_utm_crs
from lib.listings_lib import address_to_parcel
from world.models import AnalyzedListing, Parcel, BuildingOutlines, Topography, PropertyListing
from lib.crs_lib import get_utm_crs


pp = pprint.PrettyPrinter(indent=2)


# ------------------------------------------------------
# Overall Map viewer at /map
# ------------------------------------------------------

# main map page
class MapView(TemplateView):  # LoginRequiredMixin
    template_name = 'map2.html'


# ajax call for vector tiles for big map
class ParcelTileData(MVTView, ListView):  # LoginRequiredMixin
    model = Parcel
    vector_tile_layer_name = "parcels"
    vector_tile_fields = ('apn',)


# ajax call for topo tiles for big map
class TopoTileData(MVTView, ListView):  # LoginRequiredMixin
    model = Topography
    vector_tile_layer_name = "topogrpahy"
    # vector_tile_fields = ('apn',)


# ------------------------------------------------------
# Parcel detail viewer at /parcel/<apn>
# ------------------------------------------------------

# main detail page
class ParcelDetailView(View):  # LoginRequiredMixin
    template_name = 'parcel-detail.html'

    def tuple_sub(self, t1, t2):
        return tuple(map(lambda i, j: (i - j) * 1000, t1, t2))

    def get(self, request, apn, *args, **kwargs):
        parcel = Parcel.objects.get(apn=apn)
        buildings = BuildingOutlines.objects.filter(
            geom__intersects=parcel.geom)
        # Example of how to combine two objects into one geojson serialization:
        # serialized = serialize('geojson', chain([parcel], buildings), geometry_field='geom', fields=('apn', 'geom',))

        # Serializing the data into the template. There's unneeded duplication since we also get the
        # data via JSON, but I haven't figured out how to get the mapping library to use this data.
        serialized_parcel = serialize(
            'geojson', [parcel], geometry_field='geom', fields=('apn', 'geom',))
        serialized_buildings = serialize(
            'geojson', buildings, geometry_field='geom', fields=('apn', 'geom',))

        # https://photon.komoot.io/ -- address resolution
        # https://geopandas.org/en/stable/docs/reference/api/geopandas.tools.geocode.html
        utm_crs = get_utm_crs()
        parcel_data_frame = geopandas.GeoDataFrame.from_features(
            json.loads(serialized_parcel), crs="EPSG:4326")
        parcel_in_utm = parcel_data_frame.to_crs(utm_crs)
        lot_square_feet = int(parcel_in_utm.area * 3.28084 * 3.28084)
        print(repr(parcel))
        print(pp.pprint(parcel.__dict__))
        print("Lot size:", lot_square_feet)
        print("Lot location:", parcel_data_frame.centroid)
        return render(request, self.template_name,
                      {'parcel_data': serialized_parcel,
                       'building_data': serialized_buildings,
                       'latlong': str(list(parcel_data_frame.centroid[0].coords)[0]),
                       'lot_size': lot_square_feet
                       })


# ajax call to get current MLS listings
class ListingsData(View):  # LoginRequiredMixin
    def get(self, request, *args, **kwargs):
        listings = PropertyListing.objects.prefetch_related('analyzedlisting_set').filter(
            analyzedlisting__isnull=False)
        serialized_listings = serialize('json', listings)

        # An ad-hoc way of doing formatting for now
        listings_formatted = []
        for listing, listing_dict in zip(listings, json.loads(serialized_listings)):
            latest_analysis = listing.analyzedlisting_set.latest(
                'datetime_ran')
            l = latest_analysis.details
            l.update(listing_dict['fields'])
            l['datetime_ran'] = latest_analysis.datetime_ran
            del l['parcel']
            del l['addr']
            del l['prev_listing']
            listings_formatted.append(l)

        return JsonResponse(listings_formatted, content_type='application/json', safe=False)

    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)
        apn = body['apn']

        # First, make sure it doesn't already exist in the database
        existing_listings = PropertyListing.objects.filter(parcel__apn=apn)
        if len(existing_listings) > 0:
            return JsonResponse({'error': 'listing already exists'})
        parcel = Parcel.objects.get(apn=apn)

        # Then, we unpickle, save to dataframe, and pickle again
        sd_utm_crs = get_utm_crs()
        try:
            result = analyze_by_apn(
                apn, sd_utm_crs, False, True, "./frontend/static/temp_computed_imgs")

            # Add it as a listing
            listing = PropertyListing(
                addr=result['address'], br=parcel.bedrooms, ba=parcel.baths,
                size=result['existing_living_area'], status="OFFMARKET", parcel=parcel)
            listing.save()
        except Exception as e:
            return JsonResponse({'error': str(e)})

        # This is mainly copied from scrape.py. Refactor later to make it cleaner
        new_df = pandas.DataFrame.from_records([result], exclude=[
            'buildings', 'input_parameters', 'no_build_zones',
            'new_buildings', 'avail_geom'])
        new_df.set_index('apn', inplace=True)

        new_df.loc[apn, 'address'] = listing.addr
        new_df.loc[apn, 'bedrooms'] = listing.br
        new_df.loc[apn, 'bathrooms'] = listing.ba

        # Now append stuff about the listing
        new_df.loc[apn, 'price'] = listing.price
        new_df.loc[apn, 'zipcode'] = listing.zipcode
        new_df.loc[apn, 'founddate'] = listing.founddate
        new_df.loc[apn, 'seendate'] = listing.seendate
        new_df.loc[apn, 'mlsid'] = listing.mlsid
        new_df.loc[apn, 'mls_floor_area'] = listing.size
        new_df.loc[apn, 'thumbnail'] = listing.thumbnail
        new_df.loc[apn, 'listing_url'] = listing.listing_url
        new_df.loc[apn, 'soldprice'] = listing.soldprice
        new_df.loc[apn, 'status'] = listing.status

        # Now append the new df to the old one
        df = pandas.read_pickle('./world/data/pickled_scrape')
        df = pandas.concat([df, new_df])

        # Save it
        df.to_pickle('./world/data/pickled_scrape')

        # Return a success message, at which point browser would redirect to that screen
        return JsonResponse({"msg": "success", "apn": apn}, content_type='application/json', safe=False)


class ListingDetailData(View):  # LoginRequiredMixin
    def get(self, request, apn, *args, **kwargs):
        # Pickled data. later, grab this from a database table
        df = pandas.read_pickle('./world/data/pickled_scrape')
        df_json = json.loads(df.loc[apn].to_json())
        return JsonResponse(df_json, content_type='application/json', safe=False)


class GetParcelByAddressSearch(View):  # LoginRequiredMixin
    def get(self, request, address, *args, **kwargs):
        # Takes in an address. Returns a list of possible parcels/APNs
        # Temporary. Let's clean this up later
        try:
            parcel, error = address_to_parcel(address)
        except Exception as e:
            return JsonResponse({"error": str(e)})

        if error:
            return JsonResponse({"error": f"An error occured: {error}"}, content_type='application/json')

        return JsonResponse({"apn": parcel.apn}, content_type='application/json')


class ParcelDetailData(View):  # LoginRequiredMixin
    def get(self, request, apn, *args, **kwargs):
        parcel = Parcel.objects.get(apn=apn)
        buildings = BuildingOutlines.objects.filter(
            geom__intersects=parcel.geom)
        serialized = serialize('geojson', chain([parcel], buildings),
                               geometry_field='geom', )  # fields=('apn', 'geom',))
        return HttpResponse(serialized, content_type='application/json')

# ajax call to get neighboring building data


class IsolatedNeighborDetailData(View):  # LoginRequiredMixin
    def get(self, request, apn, *args, **kwargs):
        parcel = Parcel.objects.get(apn=apn)
        buildings = BuildingOutlines.objects.filter(
            geom__intersects=parcel.geom.buffer(0.001))
        serializedBuildings = serialize(
            'geojson', buildings, geometry_field='geom')

        return HttpResponse(serializedBuildings, content_type='application/json')
