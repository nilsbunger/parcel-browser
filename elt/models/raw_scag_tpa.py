# This is an auto-generated Django model module created by ogrinspect.
from mygeo.settings import TEST_ENV

if TEST_ENV:
    from django.db import models
else:
    from django.contrib.gis.db import models


class RawScagTpa(models.Model):
    objectid = models.IntegerField(null=True, blank=True)
    names = models.CharField(max_length=62, null=True, blank=True)
    acres = models.FloatField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    shapearea = models.FloatField(null=True, blank=True)
    shapelen = models.FloatField(null=True, blank=True)
    geom = models.MultiPolygonField()


raw_scag_tpa_mapping = {
    "acres": "ACRES",
    "geom": "MULTIPOLYGON",
    "names": "NAMES",
    "objectid": "OBJECTID",
    "shapearea": "Shapearea",
    "shapelen": "Shapelen",
    "year": "YEAR",
}
