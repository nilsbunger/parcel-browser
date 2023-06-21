# This is an auto-generated Django model module created by ogrinspect.
from django.contrib.gis.db import models


class RawSfZoning(models.Model):
    class Meta:
        verbose_name = "Raw SF Zoning [Shapefile]"
        verbose_name_plural = "Raw SF Zoning [Shapefile]"

    zoning_sim = models.CharField(max_length=254, null=True, blank=True)
    districtname = models.CharField(max_length=254, null=True, blank=True)
    url = models.CharField(max_length=254, null=True, blank=True)
    gen = models.CharField(max_length=254, null=True, blank=True)
    zoning = models.CharField(max_length=254, null=True, blank=True)
    codesection = models.CharField(max_length=254, null=True, blank=True)
    geom = models.MultiPolygonField(srid=4326)


raw_sf_zoning_mapping = {
    "codesection": "codesectio",
    "districtname": "districtna",
    "gen": "gen",
    "geom": "MULTIPOLYGON",
    "url": "url",
    "zoning": "zoning",
    "zoning_sim": "zoning_sim",
}
