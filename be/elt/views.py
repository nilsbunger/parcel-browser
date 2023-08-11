# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseNotFound
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from vectortiles.postgis.views import MVTView
from world.infra.django_cache import h3_cache_page

from elt.models import (
    RawCaliResourceLevel,
    RawGeomData,
    RawSfHeTableB,
    RawSfParcelWrap,
    RawSfZoning,
    RawSfZoningHeightBulk,
)

# Another resource for generating vector tiles:
# https://medium.com/@mrgrantanderson/https-medium-com-serving-vector-tiles-from-django-38c705f677cf


# Generate parcel tiles on-demand for ELT models, used in admin view
@method_decorator(h3_cache_page(60 * 60 * 24), name="dispatch")  # cache time in seconds
class RawSfParcelWrapTile(LoginRequiredMixin, MVTView, ListView):
    model = RawSfParcelWrap
    vector_tile_layer_name = "raw_sf_parcel_wrap"
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


# @method_decorator(h3_cache_page(seconds=30), name="dispatch")  # cache time in seconds
class RawGeomDataTile(LoginRequiredMixin, MVTView, ListView):
    model = RawGeomData
    vector_tile_layer_name = "raw_geom_data"
    vector_tile_fields = ("data",)

    def get(self, request, geo: str, datatype: str, layer: str, z: int, x: int, y: int):
        if geo != "sf" or datatype != "he":
            # return a 404 response
            return HttpResponseNotFound()
        self.geo = geo
        self.datatype = datatype
        self.layerquery = [Q(data__LAYER=l) for l in layer.split("|")]
        self.q_object = self.layerquery[0]
        for l in self.layerquery[1:]:
            self.q_object |= l

        return super().get(request, z, x, y)

    def get_vector_tile_queryset(self, *args, **kwargs):
        q = self.model.objects.filter(
            self.q_object,
            juri=self.geo,
            data_type=self.datatype,
        )
        print("getting vector tile")
        return q


# @method_decorator(h3_cache_page(60 * 60 * 24), name="dispatch")  # cache time in seconds
# @method_decorator(h3_cache_page(60 * 60 * 24), name="dispatch")  # cache time in seconds
class EltAnalysisTile(LoginRequiredMixin, MVTView, ListView):
    model = RawSfParcelWrap
    vector_tile_layer_name = "elt_analysis"
    # vector_tile_fields = ("fips", "oppcat")
    vector_tile_geom_name = "parcel__geom"

    def get(self, request, geo: str, analysis: str, z: int, x: int, y: int):
        if geo != "sf" or analysis != "yigby":
            # return a 404 response
            return HttpResponseNotFound()
        return super().get(request, z, x, y)

    def get_vector_tile_queryset(self, *args, **kwargs):
        query = self.request.GET.get("min_lot_size", "")
        query = int(query) if query.isdigit() else 0
        acres = query / 43560  # convert sqft to acres
        print("Filtering for acres >= ", acres)
        return self.model.objects.filter(
            reportall_parcel__calc_acrea__gte=acres,
            eltanalysis__analysis="yigby",
            eltanalysis__juri="sf",
        )
