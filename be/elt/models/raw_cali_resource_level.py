# This is an auto-generated Django model module created by ogrinspect.
from django.contrib.gis.db import models

from elt.models.model_utils import SanitizedRawModelMixin


class RawCaliResourceLevel(SanitizedRawModelMixin, models.Model):
    class Meta:
        verbose_name = "Raw Cali Resource Level [Shapefile]"
        verbose_name_plural = "Raw Cali Resource Level [Shapefile]"

    fips = models.CharField(max_length=80, null=True, blank=True)
    fips_bg = models.CharField(max_length=80, null=True, blank=True)
    cnty_nm = models.CharField(max_length=80, null=True, blank=True)
    countyd = models.CharField(max_length=80, null=True, blank=True)
    region = models.CharField(max_length=80, null=True, blank=True)
    ecn_dmn = models.FloatField(null=True, blank=True)
    env_hl_field = models.FloatField(null=True, blank=True)
    ed_domn = models.FloatField(null=True, blank=True)
    index = models.FloatField(null=True, blank=True)
    oppcat = models.CharField(max_length=80, null=True, blank=True)
    geom = models.MultiPolygonField(srid=4326)
    run_date = models.DateField()


raw_cali_resource_level_mapping = {
    "cnty_nm": "cnty_nm",
    "countyd": "countyd",
    "ecn_dmn": "ecn_dmn",
    "ed_domn": "ed_domn",
    "env_hl_field": "env_hl_",
    "fips": "fips",
    "fips_bg": "fips_bg",
    "geom": "MULTIPOLYGON",
    "index": "index",
    "oppcat": "oppcat",
    "region": "region",
}
