from collections import defaultdict
from itertools import chain
import json
import pprint

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers import serialize
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView
import geopandas as geopandas

from mygeo import settings

from vectortiles.mixins import BaseVectorTileView

# Create your views here.
from vectortiles.postgis.views import MVTView

from lib.crs_lib import get_utm_crs
from lib.types import CheckResultEnum
from world.django_cache import h3_cache_page
from world.models import (
    AnalyzedParcel,
    BuildingOutlines,
    Parcel,
    Roads,
    Topography,
    TransitPriorityArea,
    ZoningBase,
)
from world.models.base_models import HousingSolutionArea, ZoningMapLabel

if settings.ENABLE_SILK:
    from silk.profiling.profiler import silk_profile


pp = pprint.PrettyPrinter(indent=2)


# ajax call for parcel tiles for big map
@method_decorator(h3_cache_page(60 * 60 * 24 * 365), name="dispatch")  # cache for 365 days
class ParcelTileData(LoginRequiredMixin, MVTView, ListView):
    model = Parcel
    vector_tile_layer_name = "parcel"
    vector_tile_fields = ("apn", "pk")

    def get_vector_tile_queryset(self):
        return self.vector_tile_queryset if self.vector_tile_queryset is not None else self.get_queryset()


@method_decorator(h3_cache_page(60 * 60 * 24 * 365), name="dispatch")  # cache for 365 days
class ZoningLabelTile(LoginRequiredMixin, MVTView, ListView):
    model = ZoningMapLabel
    vector_tile_fields = ("text",)

    def get_vector_tile_queryset(self):
        return self.model.objects.filter(text__regex=r"^[RC]")


# ajax call for zoning tiles for big map
@method_decorator(h3_cache_page(60 * 60 * 24 * 365), name="dispatch")  # cache for 365 days
class ZoningTileData(LoginRequiredMixin, MVTView, ListView):
    model = ZoningBase
    vector_tile_layer_name = "zone_name"
    vector_tile_fields = ("zone_name",)

    def get(self, request, *args, **kwargs):
        """This is the same as the default get method, but I keep it here to show how it works"""
        return BaseVectorTileView.get(
            self, request=request, z=kwargs.get("z"), x=kwargs.get("x"), y=kwargs.get("y")
        )

    def get_vector_tile_queryset(self):
        return self.model.objects.all()
        # return self.model.objects.filter(zone_name__startswith='RS').select_related('zoningmaplabel')


# ajax call for topo tiles for big map
@method_decorator(h3_cache_page(60 * 60 * 24 * 365), name="dispatch")  # cache for 365 days
class TopoTileData(LoginRequiredMixin, MVTView, ListView):
    model = Topography
    vector_tile_layer_name = "topography"


@method_decorator(h3_cache_page(60 * 60 * 24 * 365), name="dispatch")  # cache for 365 days
class CompCommTileData(LoginRequiredMixin, MVTView, ListView):
    model = HousingSolutionArea
    vector_tile_layer_name = "compcomm"
    vector_tile_fields = ("tier", "allowance")


@method_decorator(h3_cache_page(60 * 60 * 24 * 365), name="dispatch")  # cache for 365 days
class TpaTileData(LoginRequiredMixin, MVTView, ListView):
    model = TransitPriorityArea
    vector_tile_layer_name = "tpa"
    vector_tile_fields = ("name", "pk")

    def get_vector_tile_queryset(self):
        return self.vector_tile_queryset if self.vector_tile_queryset is not None else self.get_queryset()


@method_decorator(h3_cache_page(60 * 60 * 24 * 365), name="dispatch")  # cache for 365 days
class RoadTileData(LoginRequiredMixin, MVTView, ListView):
    model = Roads
    vector_tile_layer_name = "road"
    vector_tile_fields = ("rd30full", "roadsegid", "rightway", "abloaddr", "abhiaddr")

    def get_vector_tile_queryset(self):
        return self.vector_tile_queryset if self.vector_tile_queryset is not None else self.get_queryset()


@method_decorator(h3_cache_page(60 * 60 * 24 * 365), name="dispatch")  # cache for 365 days
class Ab2011TileData(MVTView, ListView):
    model = AnalyzedParcel
    vector_tile_fields = ("apn__geom",)
    vector_tile_geom_name = "apn__geom"

    def get_vector_tile_queryset(self):
        return self.model.objects.filter(ab2011_eligible__in=[CheckResultEnum.passed, CheckResultEnum.uncertain])

    # @silk_profile(name="Get AB2011 tile")
    def get_tile(self, x, y, z):
        return super().get_tile(x, y, z)


# ------------------------------------------------------
# Parcel detail viewer at /dj/parcel/<apn>
# ------------------------------------------------------

# main detail page
class ParcelDetailView(LoginRequiredMixin, View):
    template_name = "parcel-detail.html"

    def tuple_sub(self, t1, t2):
        return tuple(map(lambda i, j: (i - j) * 1000, t1, t2))

    def get(self, request, apn, *args, **kwargs):
        try:
            parcel = Parcel.objects.get(apn=apn)
        except Parcel.DoesNotExist as e:
            return HttpResponseNotFound(f"Parcel with apn={apn} not found")
        buildings = BuildingOutlines.objects.filter(geom__intersects=parcel.geom)
        # Example of how to combine two objects into one geojson serialization:
        # serialized = serialize('geojson', chain([parcel], buildings), geometry_field='geom', fields=('apn', 'geom',))

        # Serializing the data into the template. There's unneeded duplication since we also get the
        # data via JSON, but I haven't figured out how to get the mapping library to use this data.
        serialized_parcel = serialize(
            "geojson",
            [parcel],
            geometry_field="geom",
            fields=(
                "apn",
                "geom",
            ),
        )
        serialized_buildings = serialize(
            "geojson",
            buildings,
            geometry_field="geom",
            fields=(
                "apn",
                "geom",
            ),
        )

        # https://photon.komoot.io/ -- address resolution
        # https://geopandas.org/en/stable/docs/reference/api/geopandas.tools.geocode.html
        utm_crs = get_utm_crs()
        parcel_data_frame = geopandas.GeoDataFrame.from_features(json.loads(serialized_parcel), crs="EPSG:4326")
        parcel_in_utm = parcel_data_frame.to_crs(utm_crs)
        lot_square_feet = int(parcel_in_utm.area * 3.28084 * 3.28084)
        print(repr(parcel))
        print(pp.pprint(parcel.__dict__))
        print("Lot size:", lot_square_feet)
        print("Lot location:", parcel_data_frame.centroid)
        return render(
            request,
            self.template_name,
            {
                "parcel_data": serialized_parcel,
                "building_data": serialized_buildings,
                "latlong": str(list(parcel_data_frame.centroid[0].coords)[0]),
                "lot_size": lot_square_feet,
            },
        )


def listing_prev_values(listing):
    """Return dict of relevant values that changed in the listing since the previously
    linked listing."""
    retval = dict()
    if not listing.prev_listing:
        return retval
    for field in ["price", "status", "br", "ba", "size", "addr", "soldprice"]:
        if getattr(listing, field) != getattr(listing.prev_listing, field):
            retval[field] = getattr(listing.prev_listing, field)
    return retval


class AnalysisDetailData(LoginRequiredMixin, View):
    def get(self, request, id, *args, **kwargs):
        assert False, "This route should no longer be used"


class ParcelDetailData(LoginRequiredMixin, View):
    def get(self, request, apn, *args, **kwargs):
        try:
            parcel = Parcel.objects.get(apn=apn)
        except Parcel.DoesNotExist as e:
            return HttpResponseNotFound(f"Parcel with apn={apn} not found")
        buildings = BuildingOutlines.objects.filter(geom__intersects=parcel.geom)
        serialized = serialize(
            "geojson",
            chain([parcel], buildings),
            geometry_field="geom",
        )  # fields=('apn', 'geom',))
        return HttpResponse(serialized, content_type="application/json")


# ajax call to get neighboring building data
class IsolatedNeighborDetailData(LoginRequiredMixin, View):
    def get(self, request, apn, *args, **kwargs):
        try:
            parcel = Parcel.objects.get(apn=apn)
        except Parcel.DoesNotExist as e:
            return HttpResponseNotFound(f"Parcel with apn={apn} not found")

        buildings = BuildingOutlines.objects.filter(geom__intersects=parcel.geom.buffer(0.001))
        serializedBuildings = serialize("geojson", buildings, geometry_field="geom")

        return HttpResponse(serializedBuildings, content_type="application/json")


class AddressToLatLong(LoginRequiredMixin, View):
    def get(self, request, address):
        suffixDict = {
            "Alley": "ALY",
            "Avenue": "AVE",
            "Boulevard": "BLVD",
            "Causeway": "CSWY",
            "Center": "CTR",
            "Circle": "CIR",
            "Court": "CT",
            "Cove": "CV",
            "Crossing": "XING",
            "Drive": "DR",
            "Expressway": "EXPY",
            "Extension": "EXT",
            "Freeway": "FWY",
            "Grove": "GRV",
            "Highway": "HWY",
            "Hollow": "HOLW",
            "Junction": "JCT",
            "Lane": "LN",
            "Motorway": "MTWY",
            "Overpass": "OPAS",
            "Park": "PARK",
            "Parkway": "PKWY",
            "Place": "PL",
            "Plaza": "PLZ",
            "Point": "PT",
            "Road": "RD",
            "Route": "RTE",
            "Skyway": "SKWY",
            "Square": "SQ",
            "Street": "ST",
            "Terrace": "TER",
            "Trail": "TRL",
            "Way": "WAY",
        }
        addr = address.split(" ")
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
            return HttpResponse("404")

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
                parcel = Parcel.objects.get(
                    situs_addr__iexact=addr[0],
                    situs_stre__iexact=addr[1],
                    situs_suff__iexact=addr[2],
                )
            except Parcel.DoesNotExist:
                pass

        if parcel != None:
            coords = parcel.geom.centroid
            return HttpResponse(json.dumps({"x": coords.x, "y": coords.y}), content_type="application/json")
        return HttpResponse("404")
