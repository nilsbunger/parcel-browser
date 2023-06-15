from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models

from elt.models import RawSfParcel


# DB model that relates SF Parcel data to other models. Lets us create admin views.
class RawSfParcelMeta(models.Model):
    parcel = models.ForeignKey(RawSfParcel, on_delete=models.CASCADE)
    # record the type of model being pointed to
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # the ID of the field being related to
    object_id = models.PositiveIntegerField()
    # the foreign key field
    content_object = GenericForeignKey("content_type", "object_id")
