# Register your models here.
from django.contrib.admin.utils import flatten_fieldsets
from django.contrib.gis import admin
from django import forms
from more_itertools import collapse, flatten
import numpy as np

from elt.models import RawSfParcel


# Registering models: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#modeladmin-objects

# Register as a default model
# admin.site.register(RawSfParcel)


class RawSfParcelAdminForm(forms.ModelForm):
    """ref: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#adding-custom-validation-to-the-admin"""

    ...
    # def clean_geom(self):
    #     raise forms.ValidationError("We don't allow changing geometry in the admin")


@admin.register(RawSfParcel)
class RawSfParcelAdmin(admin.GISModelAdmin):
    # Use custom form as a way to disable geometry editing (making field readonly makes it not display the map)
    form = RawSfParcelAdminForm
    change_list_template = "elt/admin/raw_sf_parcel_change_list.html"
    list_display = [
        "id",
        "resolved_address",  # from Model file
        "zoning_cod",
        "zoning_dis",
        # "street_nam",
        # "geom",
    ]
    # fmt:off
    _fieldlist = ['resolved_address', 'geom', ('mapblklot', 'blklot', 'block_num', 'lot_num', 'odd_even'),
              ('zoning_cod', 'zoning_dis'), ('in_asr_sec', 'pw_recorde', 'active',), ('date_rec_a', 'date_rec_d'),
              ('date_map_a', 'date_map_d', 'date_map_2'), ('project_id', 'project_2', 'project_3')]
    # fmt:on
    fields = list(_fieldlist)
    readonly_fields = list(collapse(set(_fieldlist) - {"geom"}))

    def has_delete_permission(self, request, obj=None):
        return False
