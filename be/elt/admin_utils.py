from django.contrib.admin import helpers
from django.contrib.admin.utils import flatten_fieldsets


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
