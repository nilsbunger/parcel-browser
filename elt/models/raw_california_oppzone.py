# This is an auto-generated Django model module created by ogrinspect.
from mygeo.settings import TEST_ENV

if TEST_ENV:
    from django.db import models
else:
    from django.contrib.gis.db import models


class RawCaliforniaOppzone(models.Model):
    statefp = models.CharField(max_length=2, null=True, blank=True)
    countyfp = models.CharField(max_length=3, null=True, blank=True)
    tractce = models.CharField(max_length=6, null=True, blank=True)
    geoid = models.CharField(max_length=11, null=True, blank=True)
    name = models.CharField(max_length=7, null=True, blank=True)
    namelsad = models.CharField(max_length=20, null=True, blank=True)
    mtfcc = models.CharField(max_length=5, null=True, blank=True)
    funcstat = models.CharField(max_length=1, null=True, blank=True)
    aland = models.FloatField(null=True, blank=True)
    awater = models.FloatField(null=True, blank=True)
    intptlat = models.CharField(max_length=11, null=True, blank=True)
    intptlon = models.CharField(max_length=12, null=True, blank=True)
    geom = models.MultiPolygonField(srid=4269)


raw_california_oppzone_mapping = {
    "aland": "ALAND",
    "awater": "AWATER",
    "countyfp": "COUNTYFP",
    "funcstat": "FUNCSTAT",
    "geoid": "GEOID",
    "geom": "MULTIPOLYGON",
    "intptlat": "INTPTLAT",
    "intptlon": "INTPTLON",
    "mtfcc": "MTFCC",
    "name": "NAME",
    "namelsad": "NAMELSAD",
    "statefp": "STATEFP",
    "tractce": "TRACTCE",
}
