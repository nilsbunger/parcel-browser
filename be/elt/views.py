# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from vectortiles.postgis.views import MVTView
from world.infra.django_cache import h3_cache_page

from elt.models import (
    RawCaliResourceLevel,
    RawSfHeTableB,
    RawSfParcel,
    RawSfParcelWrap,
    RawSfZoning,
    RawSfZoningHeightBulk,
)

# Another resource for generating vector tiles:
# https://medium.com/@mrgrantanderson/https-medium-com-serving-vector-tiles-from-django-38c705f677cf


# Generate parcel tiles on-demand for ELT models, used in admin view
# @method_decorator(h3_cache_page(60 * 60 * 24), name="dispatch")  # cache time in seconds
class RawSfParcelTile(LoginRequiredMixin, MVTView, ListView):
    model = RawSfParcelWrap
    vector_tile_layer_name = "raw_sf_parcel"
    vector_tile_geom_name = "parcel__geom"

    # fmt:off
    vector_tile_fields = ("apn", "parcel__zoning_cod", "parcel__zoning_dis", "parcel__street_nam",
                          "parcel__from_addre", "parcel__to_address","parcel__street_typ",
                          "he_table_b__m1_zoning", "he_table_b__m2_zoning", "he_table_b__m3_zoning")
    # fmt:on
    def get_vector_tile_queryset(self):
        return self.model.objects.select_related(
            "parcel", "he_table_b__m1_zoning", "he_table_b__m2_zoning", "he_table_b__m3_zoning"
        )
        # return self.model.objects.filter(text__regex=r"^[RC]")


@method_decorator(h3_cache_page(60 * 60 * 24), name="dispatch")  # cache time in seconds
class RawSfZoningTile(LoginRequiredMixin, MVTView, ListView):
    model = RawSfZoning
    vector_tile_layer_name = "raw_sf_zoning"
    vector_tile_fields = ("codesection", "districtname", "gen", "url", "zoning", "zoning_sim")


@method_decorator(h3_cache_page(60 * 60 * 24), name="dispatch")  # cache time in seconds
class RawSfZoningHeightBulkTile(LoginRequiredMixin, MVTView, ListView):
    model = RawSfZoningHeightBulk
    vector_tile_layer_name = "raw_sf_zoning_height_bulk"
    vector_tile_fields = ("height", "gen_height")


@method_decorator(h3_cache_page(60 * 60 * 24), name="dispatch")  # cache time in seconds
class RawSfHeTableBTile(LoginRequiredMixin, MVTView, ListView):
    model = RawSfHeTableB
    vector_tile_layer_name = "raw_sf_he"
    vector_tile_fields = ("m1_zoning", "m2_zoning", "m3_zoning")


@method_decorator(h3_cache_page(60 * 60 * 24), name="dispatch")  # cache time in seconds
class RawCaliResourceLevelTile(LoginRequiredMixin, MVTView, ListView):
    model = RawCaliResourceLevel
    vector_tile_layer_name = "raw_cali_resource_level"
    vector_tile_fields = ("fips", "oppcat")
