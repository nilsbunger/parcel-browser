from django.db import models
from elt.lib.attom_data_struct import Address as AttomAddress
from lib import mapbox
from lib.util import LongLat
from pydantic import BaseModel, Extra


# Create your models here.
class StdAddress(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["street_addr", "city", "zip"], name="unique_address"),
        ]

    street_addr = models.CharField(max_length=255, default="BADADDRESS")
    city = models.CharField(max_length=255, default="San Francisco")
    state = models.CharField(max_length=2, default="CA")
    zip = models.CharField(max_length=5, default="NOZIP")
    address_features = models.JSONField(null=True, blank=True)

    # convert an AttomAddress to a StdAddress
    @classmethod
    def from_attom(cls, attom_address: AttomAddress) -> "StdAddress":
        print(
            "TODO: make sure address is regularized: no unit # in addr, consistent capitalization,"
            " city name is full name, etc"
        )
        return cls(
            street_addr=attom_address.line1,
            city=attom_address.city,
            state=attom_address.state,
            zip=attom_address.zip,
            address_features=attom_address.dict(),
        )

    @classmethod
    def from_addr(cls, street_addr: str, city: str = "", state: str = "", zip: str = "") -> ("StdAddress", bool):
        """Create a StdAddress from a street address, city, state, and zip. If the address already exists, return it.
        Return object, created(bool) similar to get_or_create."""
        normed_addr = mapbox.AddressNormalizer(street_addr=street_addr, city=city, state=state, zip=zip)
        street_addr = normed_addr.streetnum + " " + normed_addr.streetname
        try:
            obj = cls.objects.get(street_addr=street_addr, city=normed_addr.city, zip=normed_addr.zip)
            return obj, False
        except cls.DoesNotExist:
            pass
        obj = cls(
            street_addr=normed_addr.streetnum + " " + normed_addr.streetname,
            city=normed_addr.city,
            state=normed_addr.state,
            zip=normed_addr.zip,
        )
        obj.save()
        return obj, True


# Definition of address details. Came from Mapbox JSON "property profile" but should be made generic if we switch
# vendors.
class GeometrySchema(BaseModel, extra=Extra.forbid):
    # geometry:
    type: str  # e.g. "Point"
    coordinates: LongLat


class AddressFeatures(BaseModel, extra=Extra.ignore):
    type: str
    properties: dict
    text_en: str
    geometry: GeometrySchema
