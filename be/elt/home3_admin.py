from functools import partial

from django import forms
from django.contrib.admin import ModelAdmin, helpers
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.gis import admin
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.forms import Media
from more_itertools import collapse
from django.forms import DecimalField

from parsnip.util import round_to_sig_figs


class Home3AdminForm(forms.ModelForm):
    """ref: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#adding-custom-validation-to-the-admin"""

    def clean_geom(self):
        raise forms.ValidationError("We don't allow changing geometry in the admin")


class Home3Admin(ModelAdmin):
    """Base class for admin pages. Handles special needs for GIS models, foreign key models, etc."""

    extra_inline_fields = []  # override in subclass for any foreign keys to display inline
    related_gis_models = []
    # customized change_form_template to include inline forms
    change_form_template = "elt/admin/home3_admin_change_form.html"
    # Use custom form as a way to disable geometry editing (making field readonly makes it not display the map)
    form = Home3AdminForm
    field_options = {}

    # Method to be dynamically assigned as a display method for readonly fields
    def _custom_display(self, obj, field_name, sig_figs=4):
        assert isinstance(obj, models.Model), f"obj must be a model instance, not {type(obj)}"
        assert isinstance(field_name, str)
        value = getattr(obj, field_name, None)
        if value is not None:
            return round_to_sig_figs(value, sig_figs)
        return None

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

        # apply rounding to float fields generically.
        # self.fields is optional, but if it's not set, we'll use readonly_fields to satisfy our processing below.
        if not self.fields:
            self.fields = self.readonly_fields

        ro_fields = set(self.readonly_fields)
        new_ro_fields = []
        # Process each field_list in self.fields
        if self.fields:
            new_fields = []
            for field_list in self.fields:
                # Check if field_list is a single field name (string) or a tuple/list of field names
                fieldnames = [field_list] if isinstance(field_list, str) else list(field_list)

                # Process each field name in field_names
                for index, field_name in enumerate(fieldnames):
                    try:
                        # Check if this is a model field
                        field = model._meta.get_field(field_name)
                        is_float_field = isinstance(field, models.FloatField)
                    except FieldDoesNotExist:
                        # It's not a field in model's _meta, probably a computed property
                        is_float_field = False

                    # If it is a float field, create a custom display method
                    if is_float_field:
                        custom_display_name = f"custom_{field_name}_display"
                        sig_figs = self.field_options.get(field_name, {}).get("sig_figs", 4)

                        # Create a lambda for custom_display for this field and attach to this ModelAdmin class.
                        custom_display_func = partial(self._custom_display, field_name=field_name, sig_figs=sig_figs)
                        custom_display_func.short_description = field_name.replace("_", " ").title()
                        setattr(self.__class__, custom_display_name, admin.display(custom_display_func))

                        # Replace self.fields and self.readonly_fields with the name of the custom display method
                        fieldnames[index] = custom_display_name
                        if field_name in ro_fields:
                            new_ro_fields.append(custom_display_name)
                    elif field_name in ro_fields:
                        new_ro_fields.append(field_name)

                # Add the processed field_names back to new_fields
                new_fields.append(tuple(fieldnames))

            # Update self.fields and self.readonly_fields with updated field names.
            self.fields = new_fields
            self.readonly_fields = new_ro_fields

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Optimize the number of DB queries by prefetching related models
        if self.extra_inline_fields:
            queryset = queryset.select_related(*self.extra_inline_fields)
        return queryset

    def has_delete_permission(self, request, obj=None):
        """By default don't allow deletes"""
        return False

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        """Render the change form, including inline forms for related models by foreign key or by GIS geo"""

        # Add inline forms for related models by foreign key
        inline_forms = {}
        inline_media = Media()
        for extra_field in self.extra_inline_fields:
            model = getattr(obj, extra_field)
            if not model:
                continue
            model_admin = self.admin_site._registry[model.__class__]
            fieldsets = model_admin.get_fieldsets(request, model)
            ModelForm = model_admin.get_form(request, model, change=True, fields=flatten_fieldsets(fieldsets))
            form = ModelForm(instance=model)
            readonly_fields = model_admin.get_readonly_fields(request, model)
            admin_form = helpers.AdminForm(form, list(fieldsets), {}, readonly_fields, model_admin=model_admin)
            inline_forms[extra_field] = admin_form
            inline_media += admin_form.media

        # Add inline forms for models related by geometry overlap
        related_by_geo = [model.objects.filter(geom__intersects=obj.geom) for model in self.related_gis_models]
        related_by_geo = list(collapse(related_by_geo))

        for obj in related_by_geo:
            RelatedModel = obj.__class__  # noqa:N806
            RelatedModelAdmin = admin.site._registry[RelatedModel].__class__  # noqa:N806 # eg RawSfZoningAdmin class
            inline_admin = RelatedModelAdmin(admin_site=self.admin_site, model=RelatedModel)
            related_admin_form = inline_admin.get_inline_context(request, obj, add, change)

            inline_forms[str(obj)] = related_admin_form
            inline_media += related_admin_form.media

        context["inline_forms"] = inline_forms
        context["inline_media"] = inline_media

        return super().render_change_form(request, context, add, change, form_url, obj)


# Usage
