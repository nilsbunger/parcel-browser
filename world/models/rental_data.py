from django.contrib.gis.db import models

from world.models import Parcel


class RentalData(models.Model):
    class RentalDataType(models.TextChoices):
        UNIT_RENTOMETER_ESTIMATE = 'URE'
        ADU_RENTOMETER_ESTIMATE = 'ARE'
        OVERRIDE = 'OVR'

    location = models.PointField()
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, to_field='apn')

    # Details contains parsed results from API (eg Rentometer right now).
    # Example:
    # {"max": 3395, "min": 2000, "mean": 2813, "baths": 1, "address": null, "samples": 10, "std_dev": 479,
    #  "bedrooms": 2, "latitude": "32.747341", "longitude": "-117.175411", "radius_miles": 0.5, "building_type": "Any",
    #  "percentile_25": 2490, "percentile_75": 3137, "look_back_days": 365, "credits_remaining": 440}
    details = models.JSONField()
    br = models.IntegerField(null=True, blank=True)
    ba = models.FloatField(null=True, blank=True)
    sqft = models.IntegerField(null=True, blank=True)
    data_type = models.CharField(max_length=5, choices=RentalDataType.choices)
    rundate = models.DateTimeField(auto_now_add=True)
