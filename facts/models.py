from django.db import models
from ninja import Schema
from pydantic import BaseModel, Extra

from lib.util import LongLat


# Create your models here.
class StdAddress(models.Model):
    street_addr = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)
    zip = models.CharField(max_length=5, null=True, blank=True)
    address_features = models.JSONField(null=True, blank=True)


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
