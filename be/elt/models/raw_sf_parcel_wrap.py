from django.contrib.gis.db import models
from django.db.models import QuerySet

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
    reportall_parcel = models.ForeignKey("elt.RawReportall", on_delete=models.PROTECT, null=True, blank=True)

    @classmethod
    def find_by_address(cls, address: str, city: str = "SF", *, raise_on_empty=False) -> QuerySet["RawSfParcelWrap"]:
        addr_num, *addr_name, rest = address.split(" ")
        assert addr_num.isdigit()
        if addr_name[0] in ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th"]:
            addr_name[0] = "0" + addr_name[0]
        addr_name = " ".join(addr_name)
        # TODO: search from-address and to-address range
        # NOTE: __iexact means case-insensitive exact match
        qs = cls.objects.filter(parcel__from_addre=str(addr_num), parcel__street_nam__iexact=addr_name)
        if raise_on_empty and not qs.exists():
            raise cls.DoesNotExist(f"No APN found for address {address}")
        return qs
