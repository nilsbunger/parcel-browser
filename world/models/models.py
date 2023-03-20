import datetime
import logging
from collections import defaultdict

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.db.models import Subquery

from lib.types import CheckResultEnum
from world.models import Parcel, Roads


class AnalyzedRoad(models.Model):
    class Status(models.IntegerChoices):
        OK = 0
        TOO_SHORT = 1
        INSIDE_PARCEL = 2
        CROSSES_PARCEL = 3
        NO_WIDTHS = 4
        UNSTABLE_WIDTHS = 5
        EXCEPTION = 6

    status = models.IntegerField(choices=Status.choices, default=Status.OK)

    road = models.OneToOneField(Roads, on_delete=models.CASCADE, primary_key=True, unique=True)
    low_width = models.FloatField(null=True)  # conservatively low width, in meters
    avg_width = models.FloatField(null=True)  # average width without outliers, in meters
    high_width = models.FloatField(null=True)  # believably high width, in meters
    stdev_width = models.FloatField(null=True)  # standard deviation of "good widths", in meters
    all_widths = ArrayField(models.FloatField(), null=True)

    class Meta:
        indexes = [
            models.Index(fields=["low_width"]),
            models.Index(fields=["avg_width"]),
            models.Index(fields=["high_width"]),
        ]


class AnalyzedParcel(models.Model):
    apn = models.OneToOneField(max_length=10, unique=True, primary_key=True, to=Parcel, on_delete=models.CASCADE)
    ab2011_eligible = models.CharField(max_length=20, choices=[(x.value, x.name) for x in CheckResultEnum])
    # lot_size = models.IntegerField(blank=True, null=True)
    # building_size = models.IntegerField(blank=True, null=True)
    # skip = models.BooleanField(blank=True, null=True)
    # skip_reason = models.CharField(max_length=254, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["apn"]),
            models.Index(fields=["ab2011_eligible"]),
        ]


class ParcelSlope(models.Model):
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, to_field="apn")
    grade = models.IntegerField()
    polys = models.MultiPolygonField(blank=True, null=True)
    # note: only updated on model.save
    run_date = models.DateField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["parcel", "grade"], name="unique_parcel_grade_bucket"),
        ]


class PropertyListing(models.Model):
    class ListingStatus(models.TextChoices):
        ACTIVE = "ACTIVE"
        PENDING = "PENDING"
        SOLD = "SOLD"
        MISSING = "MISSING"  # means it was listed as active and no longer is. it might have gone pending
        WITHDRAWN = "WITHDRAWN"
        OFFMARKET = "OFFMARKET"

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
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, to_field="apn", blank=True, null=True)
    prev_listing = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        # note: related_name provides the name used in a *reverse* lookup, from an old listing to the newer one,
        #  hence the name is semantically opposite of previous.
        related_name="next_listing",
    )

    class Meta:
        indexes = [
            models.Index(fields=["zipcode"]),
            models.Index(fields=["mlsid"]),
            models.Index(fields=["parcel"]),
        ]

    @classmethod
    def get_latest_or_create(cls, parcel):
        try:
            property_listing = cls.objects.filter(parcel=parcel).order_by("-founddate")[0]
        except IndexError:
            # No property listing for this parcel. Create an off-market property listing
            property_listing = cls.objects.create(
                mlsid=parcel.apn,
                addr=parcel.address,
                parcel=parcel,
                status=cls.ListingStatus.OFFMARKET,
                br=parcel.br,
                ba=parcel.ba,
            )
        return property_listing

    @classmethod
    def active_listings_queryset(cls):
        """Find listings where the latest listing is active or OFFMARKET (meaning we are tracking it)."""
        latest_entries = Subquery(cls.objects.order_by("mlsid", "-founddate").distinct("mlsid").values("pk"))
        listings = (
            cls.objects.filter(pk__in=latest_entries)
            .filter(status__in=["ACTIVE", "OFFMARKET"])
            .prefetch_related("parcel")
        )
        return listings

    @classmethod
    def mark_all_stale(cls, days_for_stale: int) -> dict:
        """Find all stale listings, meaning ones that haven't been seen in N days, and mark them as "MISSING".
        Returns a stats dictionary."""
        listings = cls.active_listings_queryset().prefetch_related("parcel")
        now = datetime.datetime.now(datetime.timezone.utc)
        stale_listings = []
        stats = defaultdict(int)
        logging.info("Looking for stale listings:")
        for listing in listings:
            days_since_seen = (now - listing.seendate).days
            if days_since_seen < days_for_stale:
                if listing.parcel:
                    stats["seen_recently"] += 1
                else:
                    stats["seen_recently_no_parcel"] += 1
            elif not listing.parcel:
                stats["stale_no_parcel"] += 1
            else:
                stats["stale"] += 1
                prev_listing_id = listing.pk
                # Duplicate this entry and record it as 'missing'
                listing.pk = None
                listing.prev_listing_id = prev_listing_id
                listing.status = cls.ListingStatus.MISSING
                listing._state.adding = True
                listing.save()
                stale_listings.append(listing)
        return stats


class AnalyzedListing(models.Model):
    # Sometimes, we want to analyze a parcel without saving a listing, so this field
    # should be kept blank. Maybe later we can keep a reference back to the parcel?
    listing = models.OneToOneField(PropertyListing, on_delete=models.CASCADE)
    parcel = models.ForeignKey(Parcel, on_delete=models.CASCADE, to_field="apn")
    zone = models.CharField(max_length=20, null=True, blank=True)
    is_tpa = models.BooleanField(null=True, blank=True)
    is_mf = models.BooleanField(null=True, blank=True)
    salt = models.CharField(max_length=20, null=True, blank=True)

    datetime_ran = models.DateTimeField(auto_now_add=True)
    details = models.JSONField()
    dev_scenarios = models.JSONField(null=True, blank=True)
    input_parameters = models.JSONField()
    geometry_details = models.JSONField()
