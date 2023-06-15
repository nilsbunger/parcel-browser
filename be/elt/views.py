# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from vectortiles.postgis.views import MVTView
from world.infra.django_cache import h3_cache_page

from elt.models import RawSfParcel, RawSfZoningDistricts, RawSfZoningHeightBulkDistricts


# Generate parcel tiles on-demand for ELT models, used in admin view
@method_decorator(h3_cache_page(60 * 60 * 24 * 14), name="dispatch")  # cache for 1 hour
class RawSfParcelTile(LoginRequiredMixin, MVTView, ListView):
    model = RawSfParcel
    vector_tile_layer_name = "raw_sf_parcel"

    # fmt:off
    vector_tile_fields = ("blklot", "zoning_cod", "zoning_dis", "street_nam", "from_addre", "to_address","street_typ")
    # fmt:on
    def get_vector_tile_queryset(self):
        return self.model.objects.all()
        # return self.model.objects.filter(text__regex=r"^[RC]")


@method_decorator(h3_cache_page(60 * 60 * 24 * 14), name="dispatch")  # cache time in seconds
class RawSfZoningTile(LoginRequiredMixin, MVTView, ListView):
    model = RawSfZoningDistricts
    vector_tile_layer_name = "raw_sf_zoning"
    vector_tile_fields = ("codesection", "districtname", "gen", "url", "zoning", "zoning_sim")


@method_decorator(h3_cache_page(60 * 60 * 24 * 14), name="dispatch")  # cache for 1 hour
class RawSfZoningHeightBulkTile(LoginRequiredMixin, MVTView, ListView):
    model = RawSfZoningHeightBulkDistricts
    vector_tile_layer_name = "raw_sf_zoning_height_bulk"
    vector_tile_fields = ("height", "gen_height")
