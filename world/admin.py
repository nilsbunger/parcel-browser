# Register your models here.
from django.contrib.gis import admin
from .models import WorldBorder, Marker, Parcel, ZoningBase

admin.site.register(WorldBorder, admin.GISModelAdmin)


@admin.register(Marker)
class MarkerAdmin(admin.OSMGeoAdmin):
    """Marker admin."""

    list_display = ("name", "location")


@admin.register(Parcel)
class ParcelAdmin(admin.OSMGeoAdmin):
    """Parcel admin."""

    list_display = ("apn", "situs_addr", "situs_stre", "situs_suff")
    search_fields = ('apn', 'situs_stre', 'situs_addr')


@admin.register(ZoningBase)
class ZoningBaseAdmin(admin.OSMGeoAdmin):
    """ZoningBase admin."""

    list_display = ("zone_name", "ordnum")
    search_fields = ("zone_name", "ordnum")
