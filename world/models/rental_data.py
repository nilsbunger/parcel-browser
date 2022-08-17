from django.contrib.gis.db import models

from world.models import Parcel


class RentalData(models.Model):
    class RentalDataType(models.TextChoices):
        UNIT_RENTOMETER_ESTIMATE = 'URE'
        ADU_RENTOMETER_ESTIMATE = 'ARE'
        OVERRIDE = 'OVR'

    location = models.PointField()
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, to_field='apn')
    details = models.JSONField()
    br = models.IntegerField(null=True, blank=True)
    ba = models.FloatField(null=True, blank=True)
    sqft = models.IntegerField(null=True, blank=True)
    data_type = models.CharField(max_length=5, choices=RentalDataType.choices)
    rundate = models.DateTimeField(auto_now_add=True)
