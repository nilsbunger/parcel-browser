from collections import defaultdict
import datetime
import logging
from typing import Dict

from django.contrib.gis.db import models
from django.db.models import Subquery

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
        MISSING = 'MISSING'  # means it was listed as active and no longer is. it might have gone pending
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

    @classmethod
    def active_listings_queryset(cls):
        """ Find listings where the latest listing is active or OFFMARKET (meaning we are tracking it). """
        latest_entries = Subquery(cls.objects
                                  .order_by('mlsid', '-founddate')
                                  .distinct('mlsid')
                                  .values('pk'))
        listings = (cls.objects.filter(pk__in=latest_entries)
                    .filter(status__in=['ACTIVE', 'OFFMARKET']).prefetch_related('parcel'))
        return listings

    @classmethod
    def mark_all_stale(cls, days_for_stale: int) -> Dict:
        """ Find all stale listings, meaning ones that haven't been seen in N days, and mark them as "MISSING".
            Returns a stats dictionary. """
        listings = cls.active_listings_queryset().prefetch_related('parcel')
        now = datetime.datetime.now(datetime.timezone.utc)
        seen_recently = not_seen_recently = not_in_sd = stale_no_parcel = seen_recently_no_parcel = 0
        stale_listings = []
        stats = defaultdict(int)
        logging.info("Looking for stale listings:")
        for l in listings:
            days_since_seen = (now - l.seendate).days
            if days_since_seen < days_for_stale:
                if l.parcel:
                    stats['seen_recently'] += 1
                else:
                    stats['seen_recently_no_parcel'] += 1
            else:
                if not l.parcel:
                    stats['stale_no_parcel'] += 1
                else:
                    stats['stale'] += 1
                    prev_listing_id = l.pk
                    # Duplicate this entry and record it as 'missing'
                    l.pk = None
                    l.prev_listing_id = prev_listing_id
                    l.status = cls.ListingStatus.MISSING
                    l._state.adding = True
                    l.save()
                    stale_listings.append(l)
        return stats


class AnalyzedListing(models.Model):
    # Sometimes, we want to analyze a parcel without saving a listing, so this field
    # should be kept blank. Maybe later we can keep a reference back to the parcel?
    listing = models.OneToOneField(
        PropertyListing, on_delete=models.CASCADE)
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, to_field='apn')
    zone = models.CharField(max_length=20, null=True, blank=True)
    is_tpa = models.BooleanField(null=True, blank=True)
    is_mf = models.BooleanField(null=True, blank=True)
    salt = models.CharField(max_length=20, null=True, blank=True)

    datetime_ran = models.DateTimeField(auto_now_add=True)
    details = models.JSONField()
    dev_scenarios = models.JSONField(null=True, blank=True)
    input_parameters = models.JSONField()
    geometry_details = models.JSONField()
