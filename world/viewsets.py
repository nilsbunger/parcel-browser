"""Markers API views."""
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import GEOSGeometry
from rest_framework import viewsets
from rest_framework_gis import filters

from world.models import Marker, Parcel, ZoningBase
from world.serializers import MarkerSerializer, ParcelSerializer, ZoningBaseSerializer


class MarkerViewSet(viewsets.ReadOnlyModelViewSet):
    """Marker view set."""

    bbox_filter_field = "location"
    filter_backends = (filters.InBBoxFilter,)
    queryset = Marker.objects.all()
    serializer_class = MarkerSerializer

# # Version of filter which transforms from WGS84 to NAD83 coordinate systems.
# class TranslatingInBboxFilter(filters.InBBoxFilter):
#     def get_filter_bbox(self, request):
#         x = super().get_filter_bbox(request)
#         ct = CoordTransform(source=SpatialReference('WGS84'), target=SpatialReference('NAD83'))
#         geom = GEOSGeometry(x).transform(ct=ct, clone=True)
#
#         # print ("Get filter:", x)
#         # print ("GEOM", geom)
#         return geom
#
#     def filter_queryset(self, request, queryset, view):
#         queryset = super().filter_queryset(request, queryset, view)
#         # print ("Queryset", queryset.query)
#         return queryset

class ParcelViewSet(viewsets.ReadOnlyModelViewSet):
    """Parcel view set."""

    bbox_filter_field = "geom"
    filter_backends = (filters.InBBoxFilter,)
    bbox_filter_include_overlapping = True
    queryset = Parcel.objects.all() # .order_by('-id')[:10]
    serializer_class = ParcelSerializer

class ZoningBaseViewSet(viewsets.ReadOnlyModelViewSet):
    bbox_filter_field = "geom"
    filter_backends = (filters.InBBoxFilter,)
    bbox_filter_include_overlapping = True
    queryset = ZoningBase.objects.all()
    serializer_class = ZoningBaseSerializer

# class SingleParcelViewSet(viewsets.ReadOnlyModelViewSet):
