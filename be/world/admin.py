# Register your models here.
from django.contrib.gis import admin

from .models import Parcel, RentalData, ZoningBase

#
# class RentalDataInline(admin.TabularInline):
#     model = RentalData
#
#     def has_add_permission(self, request, obj):
#         return False
#
#     def has_delete_permission(self, request, obj):
#         return False
#
#
# @admin.register(Parcel)
# class ParcelAdmin(admin.OSMGeoAdmin):
#     """Parcel admin."""
#
#     list_display = ("apn", "situs_addr", "situs_stre", "situs_suff")
#     fields = ("geom", ("apn", "situs_addr", "situs_stre", "situs_suff"))
#     search_fields = ("apn", "situs_stre", "situs_addr")
#     inlines = [RentalDataInline]
#
#
# @admin.register(RentalData)
# class RentalDataAdmin(admin.ModelAdmin):
#     """RentalData admin."""
#
#     list_display = ("parcel", "br", "sqft")
#
#
# @admin.register(ZoningBase)
# class ZoningBaseAdmin(admin.OSMGeoAdmin):
#     """ZoningBase admin."""
#
#     list_display = ("zone_name", "ordnum")
#     search_fields = ("zone_name", "ordnum")
