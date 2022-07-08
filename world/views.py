import json
import pprint
from itertools import chain

import geopandas as geopandas
from django.contrib.gis.db.models.functions import Scale
from django.contrib.gis.geos import Point
from django.core.serializers import serialize
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.
from vectortiles.postgis.views import MVTView

from world.models import Parcel, BuildingOutlines, Topography

pp = pprint.PrettyPrinter(indent=2)


# ------------------------------------------------------
# Overall Map viewer at /map
# ------------------------------------------------------

# main map page
class MapView(LoginRequiredMixin, TemplateView):
    template_name = 'map2.html'

# ajax call for vector tiles for big map
class ParcelTileData(LoginRequiredMixin, MVTView, ListView):
    model = Parcel
    vector_tile_layer_name = "parcels"
    vector_tile_fields = ('apn',)

# ajax call for topo tiles for big map
class TopoTileData(LoginRequiredMixin, MVTView, ListView):
    model = Topography
    vector_tile_layer_name = "topogrpahy"
    # vector_tile_fields = ('apn',)


# ------------------------------------------------------
# Parcel detail viewer at /parcel/<apn>
# ------------------------------------------------------

# main detail page
class ParcelDetailView(LoginRequiredMixin, View):
    template_name = 'parcel-detail.html'

    def tuple_sub(self, t1, t2):
        return tuple(map(lambda i, j: (i - j)*1000, t1, t2))

    def get(self, request, apn, *args, **kwargs):
        parcel = Parcel.objects.get(apn=apn)
        buildings = BuildingOutlines.objects.filter(geom__intersects=parcel.geom)
        # Example of how to combine two objects into one geojson serialization:
        # serialized = serialize('geojson', chain([parcel], buildings), geometry_field='geom', fields=('apn', 'geom',))

        # Serializing the data into the template. There's unneeded duplication since we also get the
        # data via JSON, but I haven't figured out how to get the mapping library to use this data.
        serialized_parcel = serialize('geojson', [parcel], geometry_field='geom', fields=('apn', 'geom',))
        serialized_buildings = serialize('geojson', buildings, geometry_field='geom', fields=('apn', 'geom',))

    # https://photon.komoot.io/ -- address resolution
    # https://geopandas.org/en/stable/docs/reference/api/geopandas.tools.geocode.html
        parcel_data_frame = geopandas.GeoDataFrame.from_features(json.loads(serialized_parcel), crs="EPSG:4326")
        parcel_in_utm = parcel_data_frame.to_crs(parcel_data_frame.estimate_utm_crs())
        lot_square_feet = int(parcel_in_utm.area * 3.28084 * 3.28084)
        print (repr(parcel))
        print (pp.pprint(parcel.__dict__))
        print ("Lot size:", lot_square_feet )
        print ("Lot location:", parcel_data_frame.centroid)
        return render(request, self.template_name,
                      {'parcel_data': serialized_parcel,
                       'building_data': serialized_buildings,
                       'latlong': str(list(parcel_data_frame.centroid[0].coords)[0]),
                       'lot_size': lot_square_feet
                       })

# ajax call to get parcel and building info
class ParcelDetailData(LoginRequiredMixin, View):
    def get(self, request, apn, *args, **kwargs):
        parcel = Parcel.objects.get(apn=apn)
        buildings = BuildingOutlines.objects.filter(geom__intersects=parcel.geom)
        serialized = serialize('geojson', chain([parcel], buildings), geometry_field='geom', ) #fields=('apn', 'geom',))
        return HttpResponse(serialized, content_type='application/json')
