from datetime import datetime

from django.contrib.gis.db import models
from django.contrib.gis.geos import Polygon


class RawSantaAnaParcel(models.Model):
    run_date = models.DateField(auto_now=True)

    assessment_no = models.IntegerField()
    geom = models.PolygonField(srid=4326, blank=True, null=True)
    object_id = models.IntegerField()
    legal_lot_id = models.IntegerField()
    name = models.CharField(max_length=32, blank=True, null=True)
    legal_start_date = models.DateField(blank=True, null=True)
    lot_type = models.CharField(max_length=32, blank=True, null=True)
    doc_num = models.CharField(max_length=32, blank=True, null=True)
    map_num = models.CharField(max_length=64, blank=True, null=True)
    doc_ref_no = models.CharField(max_length=32, blank=True, null=True)
    doc_ref_date = models.CharField(max_length=32, blank=True, null=True)  # TODO: convert to date?
    legal_descr = models.CharField(max_length=256, blank=True, null=True)
    site_address = models.CharField(max_length=64, blank=True, null=True)
    use_dq_landuse = models.CharField(max_length=32, blank=True, null=True)
    shape_area = models.IntegerField()
    shape_length = models.IntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["assessment_no", "legal_lot_id", "name"], name="unique_parcel"),
        ]

    @classmethod
    def create(cls, arcgis_data):
        parcel = cls()
        # Fields which need some translation:
        poly = arcgis_data["geometry"]["coordinates"]
        if len(poly) != 1:
            print(
                "WARNING: Parcel doesn't have one polygon: " "Assessment #",
                arcgis_data["properties"]["AssessmentNo"],
                "has ",
                len(poly),
                "polygons",
            )
        # assert len(poly) == 1  # make sure there is only one polygon
        parcel.geom = Polygon(poly[0])
        sd = arcgis_data["properties"]["LegalStartDate"]
        if sd:
            parcel.legal_start_date = datetime.fromtimestamp(arcgis_data["properties"]["LegalStartDate"] // 1000)
        else:
            parcel.legal_start_date = None
        parcel.assessment_no = arcgis_data["properties"]["AssessmentNo"].replace("-", "")
        parcel.site_address = arcgis_data["properties"]["SiteAddress"].removesuffix(" SANTA ANA")

        # Fields which just map directly:
        parcel.object_id = arcgis_data["properties"]["OBJECTID"]
        parcel.legal_lot_id = arcgis_data["properties"]["LegalLotID"]
        parcel.name = arcgis_data["properties"]["Name"]
        parcel.lot_type = arcgis_data["properties"]["LotType"]
        parcel.doc_num = arcgis_data["properties"]["DocNum"]
        parcel.map_num = arcgis_data["properties"]["MapNum"]
        parcel.doc_ref_no = arcgis_data["properties"]["DocRefNo"]
        parcel.doc_ref_date = arcgis_data["properties"]["DocRefDate"]
        parcel.legal_descr = arcgis_data["properties"]["LegalDescr"]
        parcel.use_dq_landuse = arcgis_data["properties"]["UseDqLanduse"]
        parcel.shape_area = arcgis_data["properties"]["Shape__Area"]
        parcel.shape_length = arcgis_data["properties"]["Shape__Length"]
        return parcel

    def __init__(self, *args, **kwargs):
        # Note: Django recommends NOT overriding init on models. See
        # https://docs.djangoproject.com/en/4.1/ref/models/instances/#django.db.models.Model
        # Instead, added create() classmethod above.
        super().__init__(*args, **kwargs)
