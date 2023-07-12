from django.contrib.gis.db import models

from elt.models.model_utils import SanitizedRawModelMixin


# # DB model that relates SF Parcel data to other models. Lets us create admin views.
class RawSfParcelWrap(SanitizedRawModelMixin, models.Model):
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

    @classmethod
    def find_by_address(cls, address: str, city: str = "SF") -> "RawSfParcelWrap":
        addr_num, *addr_name, rest = address.split(" ")
        assert addr_num.isdigit()
        addr_name = " ".join(addr_name)
        # TODO: search from-address and to-address range
        return cls.objects.filter(parcel__fromaddre=str(addr_num), parcel__streetnam=addr_name)
