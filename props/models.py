from django.db import models


# Create your models here.
class PropertyProfile(models.Model):
    legal_entity = models.ForeignKey("LegalEntity", on_delete=models.CASCADE, null=True, blank=True)
    address = models.ForeignKey("facts.StdAddress", on_delete=models.CASCADE, null=True, blank=True)


class LegalEntity(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
