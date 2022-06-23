"""Markers serializers."""
from django.contrib.gis.geos import Point, Polygon
from rest_framework_gis import serializers
from rest_framework_gis.fields import GeometrySerializerMethodField, GeometryField

from world.models import Marker, Parcel


class MarkerSerializer(serializers.GeoFeatureModelSerializer):
    """Marker GeoJSON serializer."""

    class Meta:
        """Marker serializer meta class."""

        fields = ("id", "name")
        geo_field = "location"
        model = Marker

class ParcelSerializer(serializers.GeoFeatureModelSerializer):
    # point_location = GeometrySerializerMethodField()
    #
    # def get_point_location(self, obj):
    #     # overview of EPSG 3857 and 4326: https://gis.stackexchange.com/questions/48949/epsg-3857-or-4326-for-googlemaps-openstreetmap-and-leaflet?rq=1
    #     # # The most common CRS for online maps, used by almost all free and commercial tile providers. Uses Spherical Mercator projection. Set in by default in Map's crs option
    #     # srid = 3857
    #     # # A common CRS among GIS enthusiasts. Uses simple Equirectangular projection
    #     # srid = 4326
    #
    # srid = 4269 # - https://spatialreference.org/ref/epsg/nad83/
    #
    #     return Point(obj.x_coord, obj.y_coord, srid=srid)
    geometry_4326 = GeometrySerializerMethodField()
    def get_geometry_4326(self, state) -> Polygon:
        return state.geom.transform(4326, clone=True)

    class Meta:
        #fields = ()
        fields= ('geom',)
        # geo_field = 'geom'
        geo_field = 'geometry_4326'
        model = Parcel