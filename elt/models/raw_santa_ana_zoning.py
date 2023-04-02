from mygeo.settings import TEST_ENV

if TEST_ENV:
    from world.infra.cicd_models import models
else:
    from django.contrib.gis.db import models


class RawSantaAnaZoning(models.Model):
    objectid = models.IntegerField(null=True, blank=True)
    zoneclass = models.CharField(max_length=5, null=True, blank=True)
    zonedesc = models.CharField(max_length=47, null=True, blank=True)
    zonesuffix = models.CharField(max_length=4, null=True, blank=True)
    zoneoverla = models.CharField(max_length=3, null=True, blank=True)
    zoneusesuf = models.CharField(max_length=4, null=True, blank=True)
    sdm = models.CharField(max_length=7, null=True, blank=True)
    ord_no = models.CharField(max_length=8, null=True, blank=True)
    ord_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=64, null=True, blank=True)
    shape_leng = models.FloatField(null=True, blank=True)
    shape_area = models.FloatField(null=True, blank=True)
    geom = models.MultiPolygonField(srid=2230)


raw_santa_ana_zoning_mapping = {
    "geom": "MULTIPOLYGON",
    "notes": "NOTES",
    "objectid": "OBJECTID",
    "ord_date": "ORD_DATE",
    "ord_no": "ORD_NO",
    "sdm": "SDM",
    "shape_area": "SHAPE_Area",
    "shape_leng": "SHAPE_Leng",
    "zoneclass": "ZONECLASS",
    "zonedesc": "ZONEDESC",
    "zoneoverla": "ZONEOVERLA",
    "zonesuffix": "ZONESUFFIX",
    "zoneusesuf": "ZONEUSESUF",
}
