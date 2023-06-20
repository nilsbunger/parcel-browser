# Register your models here.

from django import forms
from django.contrib.gis import admin

from django.views.generic import TemplateView
from more_itertools import collapse

from elt.admin_utils import InlineRenderedAdminMixin
from elt.models import RawSfHeTableA, RawSfHeTableB, RawSfHeTableC, RawSfParcel, RawSfZoning, RawSfZoningHeightBulk

# Registering models: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#modeladmin-objects


class RawSfParcelAdminForm(forms.ModelForm):
    """ref: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#adding-custom-validation-to-the-admin"""

    def clean_geom(self):
        raise forms.ValidationError("We don't allow changing geometry in the admin")


class RawParcelMapView(TemplateView):
    template_name = "elt/admin/raw_sf_parcel_map.html"


@admin.register(RawSfParcel)
class RawSfParcelAdmin(admin.GISModelAdmin):
    # Use custom form as a way to disable geometry editing (making field readonly makes it not display the map)
    form = RawSfParcelAdminForm
    # change_list_template = "elt/admin/DEPRECATED__raw_sf_parcel_change_list.html"
    change_form_template = "elt/admin/raw_parcel_change_form.html"
    related_gis_models = [RawSfZoning, RawSfZoningHeightBulk]
    related_apn_models = [RawSfHeTableA, RawSfHeTableB]
    # what to show in list view:
    list_display = ["blklot", "resolved_address", "zoning_cod", "zoning_dis"]  # "show_detail"]
    # fmt:off
    _fieldlist = ['resolved_address', 'geom', ('blklot', 'block_num', 'mapblklot', 'lot_num', 'odd_even'),
                  ('zoning_cod', 'zoning_dis'), ('from_addre', 'to_address', 'street_nam', 'street_typ',),
                  ('in_asr_sec', 'pw_recorde', 'active',), ('date_rec_a', 'date_rec_d'),
                  ('date_map_a', 'date_map_d', 'date_map_2'), ('project_id', 'project_2', 'project_3')]
    # fmt:on
    # what to show in detail view:
    fields = list(_fieldlist)
    readonly_fields = list(collapse(set(_fieldlist) - {"geom"}))
    search_fields = ["mapblklot", "blklot", "street_nam", "from_addre", "zoning_cod"]

    def get_urls(self):
        return [
            # path("<pk>/detail", self.admin_site.admin_view(ParcelDetailView.as_view()), name=f"parcel_detail"),
            *super().get_urls(),
        ]

    # # Example of showing a detail field in a list:
    # def show_detail(self, obj: RawSfParcel) -> str:
    #     # Detail field in list view
    #     url = reverse("admin:parcel_detail", args=[obj.pk])
    #     return format_html(f'<a href="{url}">📝DEETS</a>')

    def has_delete_permission(self, request, obj=None):
        return False

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        # Render data for items which are geographically related to the parcel being rendered: (geometry intersects)
        related_by_geo = list(
            collapse([model.objects.filter(geom__intersects=obj.geom) for model in self.related_gis_models])
        )
        # Render data for items which are related by having the same parcel number (and a field called mapblklot)
        filtered_results = [model.objects.filter(mapblklot=obj.mapblklot) for model in self.related_apn_models]
        related_by_apn = list(collapse(filtered_results))

        rel_forms = []
        for obj in related_by_apn + related_by_geo:
            RelatedModel = obj.__class__  # noqa:N806
            RelatedModelAdmin = admin.site._registry[RelatedModel].__class__  # noqa:N806 # eg RawSfZoningAdmin class
            inline_admin = RelatedModelAdmin(admin_site=self.admin_site, model=RelatedModel)
            related_admin_form = inline_admin.get_inline_context(request, obj, add, change)
            rel_forms.append(dict({"name": str(obj), "form": related_admin_form}))

        context.update({"related_forms": rel_forms})
        return super().render_change_form(request, context, add=add, change=not add, obj=obj, form_url=form_url)


@admin.register(RawSfZoning)
class RawSfZoningAdmin(InlineRenderedAdminMixin, admin.GISModelAdmin):
    list_display = ["codesection", "districtname", "gen", "url", "zoning", "zoning_sim"]
    fields = (("zoning", "zoning_sim"), ("codesection", "districtname"), ("gen", "url"))
    readonly_fields = ("codesection", "districtname", "gen", "url", "zoning", "zoning_sim")


@admin.register(RawSfZoningHeightBulk)
class RawSfZoningHeightBulkAdmin(InlineRenderedAdminMixin, admin.GISModelAdmin):
    list_display = ["gen_height", "height"]
    fields = ["gen_height", "height"]
    readonly_fields = ["gen_height", "height"]
    search_fields = ["gen_height", "height"]


@admin.register(RawSfHeTableA)
class RawSfHeTableAAdmin(InlineRenderedAdminMixin, admin.GISModelAdmin):
    model = RawSfHeTableA
    list_display = ["mapblklot", "address", "ex_gp_des", "ex_zoning", "acres", "ex_use_vac", "run_date"]
    search_fields = ["mapblklot", "address", "ex_gp_des", "ex_zoning"]
    list_filter = ["ex_zoning"]

    # fmt:off
    _fieldlist = [
        ("address", "mapblklot", "acres"),
        ("ex_gp_des", "ex_zoning", "ex_use_vac"),
        ("min_dens", "max_dens", "infra"),
        ("public", "site_stat", "id_last2", "li"),
        ("mod", "amod", "capacity", "con_sites",),
        ("opt1", "opt2", "zip5", "run_date",)
    ]
    # fmt:on
    fields = _fieldlist
    readonly_fields = list(collapse(_fieldlist))


@admin.register(RawSfHeTableB)
class RawSfHeTableBAdmin(InlineRenderedAdminMixin, admin.GISModelAdmin):
    model = RawSfHeTableB
    # fmt:off
    list_display = ["mapblklot", "address", "acres", "ex_zoning", "m1_zoning", "m2_zoning", "m3_zoning", "vacant",
                    "ex_use", "run_date"]
    # fmt:on
    list_filter = ["vacant", "ex_zoning", "m1_zoning", "m2_zoning", "m3_zoning", "run_date"]
    search_fields = ["mapblklot", "address"]

    # fmt:off
    _fieldlist = [
        ('address', 'mapblklot', 'acres',),
        ('ex_use', 'ex_gp_type', 'ex_zoning',),
        ('m1_gp_type', 'm1_zoning', 'm1_maxdens', 'm1_cap',),
        ('m2_gp_type', 'm2_zoning', 'm2_maxdens', 'm2_cap',),
        ('m3_gp_type', 'm3_zoning', 'm3_maxdens', 'm3_cap',),
        ('m1_vli', 'm1_li', 'm1_m', 'm1_am',),
        ('m2_vli', 'm2_li', 'm2_m', 'm2_am',),
        ('m3_vli', 'm3_li', 'm3_m', 'm3_am',),
        ('shortfall', 'min_dens', 'vacant', 'infra',),
        ('ss_map1', 'ss_map2', 'ss_map3',),
        ('zip5', 'run_date',),
    ]
    # fmt:on
    fields = _fieldlist
    readonly_fields = list(collapse(_fieldlist))

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        # Round floats for display
        # TODO: do this for all admin models
        model_inst = context["original"]
        for fieldname in collapse(self._fieldlist):
            fieldval = getattr(model_inst, fieldname, None)
            if fieldval and isinstance(fieldval, float):
                setattr(model_inst, fieldname, round(fieldval, 3))

        return super().render_change_form(request, context, add, change, form_url, obj)


@admin.register(RawSfHeTableC)
class RawSfHeTableCAdmin(admin.GISModelAdmin):
    model = RawSfHeTableC
    list_display = ["zoning", "zoning_name", "zoning_type", "residential_uses_allowed", "run_date"]
    search_fields = ["zoning", "zoning_name", "zoning_type", "residential_uses_allowed"]
