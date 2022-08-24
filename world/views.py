from collections import defaultdict
from itertools import chain
import json
import pprint

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers import serialize
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import ListView, TemplateView
import geopandas as geopandas
# Create your views here.
from vectortiles.postgis.views import MVTView

from lib.crs_lib import get_utm_crs
from world.models import AnalyzedListing, BuildingOutlines, Parcel, PropertyListing, Topography, TransitPriorityArea

pp = pprint.PrettyPrinter(indent=2)


# ------------------------------------------------------
# Overall Map viewer at /map
# ------------------------------------------------------

# main map page
class MapView(TemplateView):  # LoginRequiredMixin
    template_name = 'map2.html'


# ajax call for parcel tiles for big map
class ParcelTileData(MVTView, ListView):  # LoginRequiredMixin
    model = Parcel
    vector_tile_layer_name = "parcels"
    vector_tile_fields = ('apn',)


# ajax call for topo tiles for big map
class TopoTileData(MVTView, ListView):  # LoginRequiredMixin
    model = Topography
    vector_tile_layer_name = "topography"


class TpaTileData(MVTView, ListView):  # LoginRequiredMixin
    model = TransitPriorityArea
    vector_tile_layer_name = "tpa"


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


def listing_prev_values(listing):
    """ Return dict of relevant values that changed in the listing since the previously
        linked listing."""
    retval = dict()
    if not listing.prev_listing:
        return retval
    for field in ['price', 'status', 'br', 'ba', 'size', 'addr', 'soldprice']:
        if getattr(listing, field) != getattr(listing.prev_listing, field):
            retval[field] = getattr(listing.prev_listing, field)
    return retval


# ajax call to get current MLS listings. Return them from most recently created / updated to least.
class ListingsData(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        assert (False, "THis route should no longer be used")
        listings = PropertyListing.active_listings_queryset().prefetch_related('analyzedlisting', 'prev_listing')
        # listings = PropertyListing.acti.prefetch_related('analyzedlisting').prefetch_related(
        #     'prev_listing').filter(
        #     analyzedlisting__isnull=False).distinct().order_by('-founddate')[0:500]
        serialized_listings = serialize('json', listings)

        # An ad-hoc way of doing formatting for now
        listings_formatted = []
        for listing, listing_dict in zip(listings, json.loads(serialized_listings)):
            # founddate = str(listing.founddate.astimezone(
            #     tz=ZoneInfo("America/Los_Angeles")).date())
            latest_analysis = listing.analyzedlisting
            if latest_analysis:
                l = latest_analysis.details
                l.update(listing_dict['fields'])
                l['datetime_ran'] = latest_analysis.datetime_ran
                l['analysis_id'] = latest_analysis.id
            else:
                l = listing_dict['fields']
            l['metadata'] = defaultdict()
            if listing.parcel:
                l['centroid_x'] = listing.parcel.geom.centroid.coords[0]
                l['centroid_y'] = listing.parcel.geom.centroid.coords[1]

            del l['parcel']
            del l['addr']
            del l['prev_listing']
            # Record new and updated listings
            if not listing.prev_listing:
                l['metadata']['category'] = 'new'
                l['metadata']['prev_values'] = {}
            else:
                l['metadata']['category'] = 'updated'
                l['metadata']['prev_values'] = listing_prev_values(listing)
            listings_formatted.append(l)
            # if founddate in listings_formatted:
            #     listings_formatted[founddate].append(l)
            # else:
            #     listings_formatted[founddate] = [l]
        return JsonResponse(listings_formatted, content_type='application/json', safe=False)

class AnalysisDetailData(View):  # LoginRequiredMixin
    def get(self, request, id, *args, **kwargs):
        analysis = AnalyzedListing.objects.get(id=id)

        # An ad-hoc way of doing formatting for now
        d = analysis.details
        d['datetime_ran'] = analysis.datetime_ran
        d['apn'] = analysis.parcel.apn
        d['is_tpa'] = analysis.is_tpa
        d['is_mf'] = analysis.is_mf
        d['zone'] = analysis.zone
        d['salt'] = analysis.salt
        d['dev_scenarios'] = analysis.dev_scenarios
        assert analysis.listing

        listing_dict = json.loads(serialize('json', [analysis.listing]))[0]
        d.update(listing_dict['fields'])
        d['centroid_x'] = analysis.parcel.geom.centroid.coords[0]
        d['centroid_y'] = analysis.parcel.geom.centroid.coords[1]
        del d['parcel']
        del d['addr']
        del d['prev_listing']

        return JsonResponse(d, content_type='application/json', safe=False)


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


class AddressToLatLong(View): # LoginRequiredMixin,
    def get(self, request, address):
        suffixDict = {'Alley': 'ALY', 'Avenue': 'AVE', 'Boulevard': 'BLVD', 'Causeway': 'CSWY', 'Center': 'CTR', 'Circle':'CIR', 'Court': 'CT', 'Cove': 'CV', 'Crossing': 'XING', 'Drive': 'DR', 'Expressway': 'EXPY', 'Extension': 'EXT', 'Freeway': 'FWY', 'Grove': 'GRV', 'Highway': 'HWY', 'Hollow': 'HOLW', 'Junction': 'JCT', 'Lane': 'LN', 'Motorway': 'MTWY', 'Overpass': 'OPAS', 'Park': 'PARK', 'Parkway': 'PKWY', 'Place': 'PL', 'Plaza': 'PLZ', 'Point': 'PT', 'Road': 'RD', 'Route': 'RTE', 'Skyway': 'SKWY', 'Square': 'SQ', 'Street': 'ST', 'Terrace': 'TER', 'Trail': 'TRL', 'Way': 'WAY'}
        addr = address.split(' ')
        print(addr)

        if len(addr) == 2:
            return self.search(addr)
        
        elif len(addr) == 3:
            suff = self.isStreetSuffix(addr[2], suffixDict)
            if bool(suff):
                addr[2] = suff
                return self.search(addr)
            else:
                addr[1] = addr[1] + " " + addr.pop(2)
                return self.search(addr)

        elif len(addr) == 4:
            suff = self.isStreetSuffix(addr.pop(3), suffixDict)
            addr[1] = addr[1] + " " + addr.pop(2)
            addr.append(suff)
            return self.search(addr)
        
        else:
            return HttpResponse('404')
    
    def isStreetSuffix(self, string, suffixDict):
        if string.upper() in list(suffixDict.values()):
            return string.upper()
        elif string.title() in list(suffixDict.keys()):
            return suffixDict[string.title()]
        else:
            return False

    def search(self, addr):
        parcel = None
        if len(addr) == 2:
            try:
                parcel = Parcel.objects.get(situs_addr__iexact=addr[0], situs_stre__iexact=addr[1])
            except Parcel.DoesNotExist:
                pass
        elif len(addr) == 3:
            try:
                parcel = Parcel.objects.get(situs_addr__iexact=addr[0], situs_stre__iexact=addr[1], situs_suff__iexact=addr[2])
            except Parcel.DoesNotExist:
                pass
        
        if parcel != None:
            coords = parcel.geom.centroid
            return HttpResponse(json.dumps({'x': coords.x, 'y': coords.y}), content_type='application/json')
        return HttpResponse('404')
