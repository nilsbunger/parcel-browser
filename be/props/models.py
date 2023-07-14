import logging

from django.db import models

from elt.models import RawSfParcelWrap
from facts.models import StdAddress

log = logging.getLogger(__name__)


# Create your models here.
class PropertyProfile(models.Model):
    legal_entity = models.ForeignKey("LegalEntity", on_delete=models.CASCADE, null=True, blank=True)
    address = models.ForeignKey("facts.StdAddress", on_delete=models.CASCADE, null=True, blank=True)
    # TODO: for now this is SF-specific, but this should be a link to a generic parcel entity
    parcel_wrap = models.ForeignKey("elt.RawSfParcelWrap", on_delete=models.PROTECT, null=True, blank=True)

    @classmethod
    def create_and_link_to_apn(cls, address: StdAddress, legal_entity=None):
        """Accept a standard address, create or find a property profile, and link it to an APN."""
        obj, created = cls.objects.get_or_create(address=address, legal_entity=legal_entity)
        if obj.parcel_wrap is None:
            results = RawSfParcelWrap.find_by_address(address.street_addr, raise_on_empty=True)
            if len(results) > 1:
                raise ValueError(f"Multiple APNs found for address {address}")
            obj.parcel_wrap = results[0]
            obj.save()
            log.info(f"Linked {obj} to Parcel Wrap with APN {obj.parcel_wrap.apn}")
        return obj, created


class LegalEntity(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
