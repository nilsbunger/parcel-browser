# Register your models here.
from django import forms
from django.contrib.admin import helpers
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.gis import admin
from django.urls import path, reverse
from django.utils.html import format_html
from django.views.generic import DetailView
from more_itertools import collapse

from elt.models import RawSfParcel, RawSfZoning, RawSfZoningHeightBulk

# Registering models: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#modeladmin-objects


class RawSfParcelAdminForm(forms.ModelForm):
    """ref: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#adding-custom-validation-to-the-admin"""

    def clean_geom(self):
        raise forms.ValidationError("We don't allow changing geometry in the admin")


@admin.register(RawSfParcel)
class RawSfParcelAdmin(admin.GISModelAdmin):
    # Use custom form as a way to disable geometry editing (making field readonly makes it not display the map)
    form = RawSfParcelAdminForm
    change_list_template = "elt/admin/raw_sf_parcel_change_list.html"
    change_form_template = "elt/admin/raw_parcel_change_form.html"
    associated_models = [RawSfZoning, RawSfZoningHeightBulk]
    # what to show in list view:
    list_display = [
        "blklot",
        "resolved_address",  # from Model file
        "zoning_cod",
        "zoning_dis",
        "show_detail",
        # "street_nam",
        # "geom",
    ]
    # fmt:off
    _fieldlist = ['resolved_address', 'geom', ('blklot', 'block_num', 'mapblklot', 'lot_num', 'odd_even'),
                  ('zoning_cod', 'zoning_dis'), ('from_addre', 'to_address', 'street_nam', 'street_typ',),
                  ('in_asr_sec', 'pw_recorde', 'active',), ('date_rec_a', 'date_rec_d'),
                  ('date_map_a', 'date_map_d', 'date_map_2'), ('project_id', 'project_2', 'project_3')]
    # fmt:on
    # what to show in detail view:
    fields = list(_fieldlist)
    readonly_fields = list(collapse(set(_fieldlist) - {"geom"}))

    def get_urls(self):
        return [
            path("<pk>/detail", self.admin_site.admin_view(ParcelDetailView.as_view()), name=f"parcel_detail"),
            *super().get_urls(),
        ]

    def show_detail(self, obj: RawSfParcel) -> str:
        # Detail field in list view
        url = reverse("admin:parcel_detail", args=[obj.pk])
        return format_html(f'<a href="{url}">📝DEETS</a>')

    def has_delete_permission(self, request, obj=None):
        return False

    def inline_render(self, request, obj=None):
        related_instances = [model.objects.filter(geom__intersects=obj.geom) for model in self.associated_models]
        related_instances = list(collapse(related_instances))
        return related_instances

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        # InlineAdminFormSet()
        related_models = list(
            collapse([model.objects.filter(geom__intersects=obj.geom) for model in self.associated_models])
        )
        rel_forms = []
        for obj in related_models:
            RelatedModel = obj.__class__  # noqa:N806
            RelatedModelAdmin = admin.site._registry[RelatedModel].__class__  # noqa:N806 # eg RawSfZoningAdmin class
            inline_admin = RelatedModelAdmin(admin_site=self.admin_site, model=RelatedModel)
            related_admin_form = inline_admin.get_inline_context(request, obj, add, change)
            rel_forms.append(dict({"name": str(obj), "form": related_admin_form}))
        context.update({"related_forms": rel_forms})
        return super().render_change_form(request, context, add=add, change=not add, obj=obj, form_url=form_url)


class InlineRenderedAdminMixin:
    def get_inline_context(self, request, obj=None, add=False, change=False):
        # adapted from _changeform_view in ModelAdmin class in django.contrib.admin.options to render inline
        # associated models which don't have a FK relationship (so can't use Django's inline admin)
        fieldsets = self.get_fieldsets(request, obj)
        ModelForm = self.get_form(request, obj, change=not add, fields=flatten_fieldsets(fieldsets))  # noqa:N806
        form = ModelForm(instance=obj)
        formsets, inline_instances = self._create_formsets(request, obj, change=True)
        if not add and not self.has_change_permission(request, obj):
            readonly_fields = flatten_fieldsets(fieldsets)
        else:
            readonly_fields = self.get_readonly_fields(request, obj)
        related_admin_form = helpers.AdminForm(
            form,
            list(fieldsets),
            # Clear prepopulated fields on a view-only form to avoid a crash.
            self.get_prepopulated_fields(request, obj) if add or self.has_change_permission(request, obj) else {},
            readonly_fields,
            model_admin=self,
        )
        return related_admin_form


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


# non-model-backed view
class ParcelDetailView(DetailView):
    template_name = "elt/admin/raw_sf_parcel_detail.html"
    model = RawSfParcel
    associated_models = [RawSfZoning, RawSfZoningHeightBulk]

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # related_models = [model.objects.filter(geom__intersects=self.object.geom) for model in self.associated_models]

        context = self.get_context_data(object=self.object)
        retval = self.render_to_response(context)
        return retval
