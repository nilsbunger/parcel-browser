from django.contrib.gis.db import models


class ExternalApiData(models.Model):
    class Vendor(models.IntegerChoices):
        ATTOM = 1
        SOMEONE_ELSE = 99

    vendor = models.IntegerField(choices=Vendor.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    data = models.JSONField()
    lookup_hash = models.BigIntegerField()
    lookup_key = models.CharField(max_length=512)
    hash_version = models.IntegerField(
        default=1
    )  # hash and data version - increase when using a new hash function or changing the data

    class Meta:
        indexes = [
            models.Index(fields=["vendor", "lookup_hash", "hash_version"]),
        ]
