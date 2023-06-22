from django.contrib.gis.db import models

from elt.models.model_utils import SanitizedModelMixin


# # DB model that relates SF Parcel data to other models. Lets us create admin views.
class RawSfParcelWrap(SanitizedModelMixin, models.Model):
    apn = models.CharField(max_length=20, primary_key=True, unique=True)
    parcel = models.ForeignKey("RawSfParcel", on_delete=models.PROTECT, null=True, blank=True)
    he_table_a = models.ForeignKey("RawSfHeTableA", on_delete=models.PROTECT, null=True, blank=True)
    he_table_b = models.ForeignKey("RawSfHeTableB", on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["apn"])]
