
from django.contrib.gis.db import models

from world.models import Parcel


class AnalyzedParcel(models.Model):
    apn = models.CharField(max_length=10, blank=True, null=True, unique=True)
    lot_size = models.IntegerField(blank=True, null=True)
    building_size = models.IntegerField(blank=True, null=True)
    skip = models.BooleanField(blank=True, null=True)
    skip_reason = models.CharField(max_length=254, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['apn'])
        ]


class ParcelSlope(models.Model):
    parcel = models.ForeignKey(
        Parcel, on_delete=models.CASCADE, to_field='apn')
    grade = models.IntegerField()
    polys = models.MultiPolygonField(blank=True, null=True)
    # note: only updated on model.save
    run_date = models.DateField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['parcel', 'grade'], name='unique_parcel_grade_bucket'),
        ]


class PropertyListing(models.Model):
    class ListingStatus(models.TextChoices):
        ACTIVE = 'ACTIVE'
        PENDING = 'PENDING'
        SOLD = 'SOLD'
        MISSING = 'MISSING'
        WITHDRAWN = 'WITHDRAWN'
        OFFMARKET = 'OFFMARKET'

    price = models.IntegerField(blank=True, null=True)
    addr = models.CharField(max_length=80)  # street number and name
    neighborhood = models.CharField(max_length=80, null=True, blank=True)  # city or neighborhood
    zipcode = models.IntegerField(blank=True, null=True)
    br = models.IntegerField(blank=True, null=True)
    ba = models.IntegerField(blank=True, null=True)
    founddate = models.DateTimeField(auto_now_add=True)
    # when last seen (date of sale when sold)
    seendate = models.DateTimeField(auto_now=True)
    mlsid = models.CharField(max_length=20, blank=True, null=True)
    size = models.IntegerField(blank=True, null=True)  # living area size in sq ft.
    thumbnail = models.CharField(max_length=200, blank=True, null=True)
    listing_url = models.CharField(max_length=100, blank=True, null=True)
    soldprice = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=ListingStatus.choices)
    parcel = models.ForeignKey(
        Parcel, on_delete=models.CASCADE, to_field='apn', blank=True, null=True)
    prev_listing = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True,
        # note: related_name provides the name used in a *reverse* lookup, from an old listing to the newer one,
        #  hence the name is semantically opposite of previous.
        related_name='next_listing'
    )

    class Meta:
        indexes = [
            models.Index(fields=['zipcode']),
            models.Index(fields=['mlsid'])
        ]


class AnalyzedListing(models.Model):
    # Sometimes, we want to analyze a parcel without saving a listing, so this field
    # should be kept blank. Maybe later we can keep a reference back to the parcel?
    listing = models.OneToOneField(
        PropertyListing, on_delete=models.CASCADE)
    parcel = models.ForeignKey(
        Parcel, on_delete=models.CASCADE, to_field='apn', blank=True, null=True)
    zone = models.CharField(max_length=20, null=True, blank=True)
    is_tpa=models.BooleanField(null=True, blank=True)

    datetime_ran = models.DateTimeField(auto_now_add=True)
    details = models.JSONField()
    dev_scenarios = models.JSONField(null=True, blank=True)
    input_parameters = models.JSONField()
    geometry_details = models.JSONField()