from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.urls import path


class CustomAdminSite(AdminSite):  # 1.
    site_header = "Turboprop Admin Site"
    site_title = "Turboprop Site Title"

    def get_urls(self):  # 2.
        urls = super().get_urls()
        my_urls = [
            path("elt/parcelmap", self.admin_view(self.parcelmapview), name="elt-parcel-map-view"),
        ]
        return my_urls + urls  # 4.

    # # More potential override points for overriding full admin index or app view
    # def app_index(self, request, app_label, extra_context=None):
    #     """ App index view """
    #     ret = super().app_index(request, app_label, extra_context)
    #     return ret
    #
    # def index(self, request, extra_context=None):
    #     """ Site index view """
    #     ret = super().index(request, extra_context)
    #     return ret

    def get_app_list(self, request, app_label=None):
        """Extend 'app' list to include custom pages like the Parcel Map"""
        app_list = super().get_app_list(request, app_label)
        # Add custom views to the app list
        model_dict = {
            "model": None,  # model,
            "name": "Parcel Map",  # capfirst(model._meta.verbose_name_plural),
            # "object_name": "parcel_map_no_real_obj_name",
            "admin_url": "/dj/admin/elt/parcelmap",
            "add_url": None,
            "view_only": True,
        }
        elt_app = next((app for app in app_list if app["app_label"] == "elt"))
        elt_app["models"].insert(0, model_dict)
        return app_list

    def parcelmapview(self, request, *args, **kwargs):
        """Display interactive parcel map (shown as another model in app_list)"""
        print("parcel map view, ", request, args, kwargs)
        print("wait")
        app_list = self.get_app_list(request)

        context = {
            **self.each_context(request),
            "title": self.index_title,
            "subtitle": None,
            "app_list": app_list,
        }
        request.current_app = "elt"  # self.name
        # return HttpResponse("Hello parcel map view")
        return TemplateResponse(request, "elt/admin/raw_sf_parcel_map.html", context)
