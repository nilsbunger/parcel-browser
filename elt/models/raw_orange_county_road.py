# This is an auto-generated Django model module created by ogrinspect.
from mygeo.settings import TEST_ENV

if TEST_ENV:
    from django.db import models
else:
    from django.contrib.gis.db import models


class RawOrangeCountyRoad(models.Model):
    objectid = models.IntegerField(null=True, blank=True)
    streetname = models.CharField(max_length=31, null=True, blank=True)
    oldstreetn = models.CharField(max_length=36, null=True, blank=True)
    prefix = models.CharField(max_length=2, null=True, blank=True)
    suffix = models.CharField(max_length=4, null=True, blank=True)
    streetcode = models.IntegerField(null=True, blank=True)
    notes = models.CharField(max_length=102, null=True, blank=True)
    foid = models.IntegerField(null=True, blank=True)
    shapestlen = models.FloatField(null=True, blank=True)
    geom = models.MultiLineStringField(srid=2230)


raw_orange_county_road_mapping = {
    "foid": "FOID",
    "geom": "MULTILINESTRING",
    "notes": "NOTES",
    "objectid": "OBJECTID",
    "oldstreetn": "OLDSTREETN",
    "prefix": "PREFIX",
    "shapestlen": "SHAPESTLen",
    "streetcode": "STREETCODE",
    "streetname": "STREETNAME",
    "suffix": "SUFFIX",
}
