# This is an auto-generated Django model module created by ogrinspect.
from django.contrib.gis.db import models


class RawSfZoningHeightBulk(models.Model):
    class Meta:
        verbose_name = "Raw SF Zoning Height Bulk [Shapefile]"
        verbose_name_plural = "Raw SF Zoning Height Bulk [Shapefile]"

    height = models.CharField(max_length=254, null=True, blank=True)
    gen_height = models.FloatField(null=True, blank=True)
    geom = models.MultiPolygonField(srid=4326)
    run_date = models.DateField()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super().save(force_insert, force_update, using, update_fields)


raw_sf_zoning_height_bulk_mapping = {
    "gen_height": "gen_hght",
    "geom": "MULTIPOLYGON",
    "height": "height",
}
