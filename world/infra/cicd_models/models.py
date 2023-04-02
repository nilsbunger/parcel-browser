# from django.db.models import Model as DjangoModel
#
# from django.db.models import *  # NOQA isort:skip
import django.db.models
from django.contrib.gis.db.models.fields import (
    MultiLineStringField,
    MultiPolygonField,
    PointField,
    PolygonField,
)

from mygeo.settings import TEST_ENV

assert TEST_ENV

django.db.models.MultiPolygonField = MultiPolygonField
django.db.models.PolygonField = PolygonField
django.db.models.MultiLineStringField = MultiLineStringField
django.db.models.PointField = PointField

print("**** TEST-ENV: MONKEYPATCHED GEOM FIELDS ****")

#
# class Model(DjangoModel, metaclass=ModelBase):
#     pass
#
# #
# class GeometryField:
#     def __init__(self, verbose_name=None, srid=4326, spatial_index=True, **kwargs):
#         pass
#
#
# class MultiPolygonField(GeometryField):
#     pass
#
# class PolygonField(GeometryField):
#     pass
#
#
# class MultiLineStringField(GeometryField):
#     pass
#
#
# class PointField(GeometryField):
#     pass
