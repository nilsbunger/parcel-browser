# This is an auto-generated Django model module created by ogrinspect.
from django.contrib.gis.db import models

from elt.models.model_utils import SanitizedModelMixin


class RawSfParcel(SanitizedModelMixin, models.Model):
    class Meta:
        verbose_name = "Raw SF Parcel [Shapefile]"
        verbose_name_plural = "Raw SF Parcel [Shapefile]"

    # run_date = models.DateField()  # note: see extract_from_excel for example
    # TODO: create run_date field, populate it from extract_from_shapefile, ...
    mapblklot = models.CharField(max_length=254, null=True, blank=True)
    blklot = models.CharField(max_length=254, null=True, blank=True, unique=True)
    block_num = models.CharField(max_length=254, null=True, blank=True)
    lot_num = models.CharField(max_length=254, null=True, blank=True)
    from_addre = models.CharField(max_length=254, null=True, blank=True)
    to_address = models.CharField(max_length=254, null=True, blank=True)
    street_nam = models.CharField(max_length=254, null=True, blank=True)
    street_typ = models.CharField(max_length=254, null=True, blank=True)
    odd_even = models.CharField(max_length=254, null=True, blank=True)
    in_asr_sec = models.CharField(max_length=1, null=True, blank=True)
    pw_recorde = models.CharField(max_length=1, null=True, blank=True)
    zoning_cod = models.CharField(max_length=254, null=True, blank=True)
    zoning_dis = models.CharField(max_length=254, null=True, blank=True)
    date_rec_a = models.CharField(max_length=254, null=True, blank=True)
    date_rec_d = models.CharField(max_length=254, null=True, blank=True)
    date_map_a = models.CharField(max_length=254, null=True, blank=True)
    date_map_d = models.CharField(max_length=254, null=True, blank=True)
    date_map_2 = models.CharField(max_length=254, null=True, blank=True)
    project_id = models.CharField(max_length=254, null=True, blank=True)
    project_2 = models.CharField(max_length=254, null=True, blank=True)
    project_3 = models.CharField(max_length=254, null=True, blank=True)
    active = models.CharField(max_length=1, null=True, blank=True)
    geom = models.MultiPolygonField(srid=4326)

    @property
    def resolved_address(self):
        try:
            if not self.from_addre:
                long, lat = self.geom.centroid.coords
                return f"No addr - lat/long={round(lat,5)},{round(long, 5)}"
            street_num = self.from_addre + (
                "-" + self.to_address if (self.to_address and self.to_address != self.from_addre) else ""
            )
            return f"{street_num} {self.street_nam} {self.street_typ}"
        except Exception as e:
            print(e)
            raise e


raw_sf_parcel_mapping = {
    "active": "active",
    "blklot": "blklot",
    "block_num": "block_num",
    "date_map_2": "date_map_2",
    "date_map_a": "date_map_a",
    "date_map_d": "date_map_d",
    "date_rec_a": "date_rec_a",
    "date_rec_d": "date_rec_d",
    "from_addre": "from_addre",
    "geom": "MULTIPOLYGON",
    "in_asr_sec": "in_asr_sec",
    "lot_num": "lot_num",
    "mapblklot": "mapblklot",
    "odd_even": "odd_even",
    "project_2": "project__2",
    "project_3": "project__3",
    "project_id": "project_id",
    "pw_recorde": "pw_recorde",
    "street_nam": "street_nam",
    "street_typ": "street_typ",
    "to_address": "to_address",
    "zoning_cod": "zoning_cod",
    "zoning_dis": "zoning_dis",
}
