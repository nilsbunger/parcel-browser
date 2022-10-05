from django.contrib.gis.db.models import GeometryField
from django.contrib.gis.db.models.functions import GeoFunc
from django.db.models.fields import FloatField
from django.db.models import Func


class MakeEnvelope(Func):
    function = "ST_MAKEENVELOPE"

    def __init__(self, *expressions, output_field=None, **extra):
        super().__init__(*expressions, output_field=None, **extra)
        self.output_field = GeometryField(srid=expressions[4])


class ST_AsMVTGeom(GeoFunc):
    function = "ST_ASMVTGEOM"
    # arity = 2
    output_field = GeometryField()


class ST_X(GeoFunc):
    function = "ST_X"
    output_field = FloatField()
    # @cached_property
    # def output_field(self):
    #     return RawGeometryField()


# class ST_Y(GeoFunc):
#     function = "ST_Y"
#
#     @cached_property
#     def output_field(self):
#         return RawGeometryField()
