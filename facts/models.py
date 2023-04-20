from django.db import models
from pydantic import BaseModel, Extra

from elt.lib.attom_data_struct import Address as AttomAddress
from lib.util import LongLat


# Create your models here.
class StdAddress(models.Model):
    street_addr = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)
    zip = models.CharField(max_length=5, null=True, blank=True)
    address_features = models.JSONField(null=True, blank=True)

    # convert an AttomAddress to a StdAddress
    @classmethod
    def from_attom(cls, attom_address: AttomAddress) -> "StdAddress":
        return cls(
            street_addr=attom_address.line1,
            city=attom_address.city,
            state=attom_address.state,
            zip=attom_address.zip,
            address_features=attom_address.dict(),
        )


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
