from django.contrib.gis.db import models

from elt.models.model_utils import SanitizedModelMixin


# # DB model that relates SF Parcel data to other models. Lets us create admin views.
class RawSfParcelWrap(SanitizedModelMixin, models.Model):
    admin_priority = 1

    class Meta:
        verbose_name = "Raw SF Parcel Wrap [wrapper]"
        verbose_name_plural = "Raw SF Parcel Wrap [wrapper]"
        indexes = [models.Index(fields=["apn"])]

    apn = models.CharField(max_length=20, primary_key=True, unique=True)
    parcel = models.ForeignKey("RawSfParcel", on_delete=models.PROTECT, null=True, blank=True)
    he_table_a = models.ForeignKey("RawSfHeTableA", on_delete=models.PROTECT, null=True, blank=True)
    he_table_b = models.ForeignKey("RawSfHeTableB", on_delete=models.PROTECT, null=True, blank=True)
    reportall_parcel = models.ForeignKey("RawSfReportall", on_delete=models.PROTECT, null=True, blank=True)
