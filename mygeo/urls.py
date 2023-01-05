"""mygeo URL Configuration"""
import django
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.urls import path, include, re_path
from django.views.defaults import page_not_found

from mygeo import settings
from userflows.api import userflows_api
from world.infra_views import frontend_proxy_view
from world.api import world_api
from co.co_api import api as co_api

# from userflows.api import userflows_api


def trigger_error(request):
    division_by_zero = 1 / 0


def check_if_superuser(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    raise PermissionDenied


# To protect against brute force and other attacks, protect admin login behind the main login
superuser_login_required = user_passes_test(check_if_superuser)

# admin.site.login = superuser_login_required(admin.site.login)
from two_factor.urls import urlpatterns as tf_urls

urlpatterns = [
    path("sentry-debug/", trigger_error, name="sentry-debug"),
    #### ---- Django-rendered routes
    # TODO: make admin require two-factor auth - https://django-two-factor-auth.readthedocs.io/en/1.14.0/class-reference.html
    path("dj/admin/", admin.site.urls),
    # django-two-factor-auth URLS
    path("", include(tf_urls), name="two-factor-urls"),
    # # django-allauth routes
    # path("dj/allauth/accounts/", include("allauth.urls")),
    # # Original django-auth.... not sure what to do with it yet
    path("dj/accounts/", include("django.contrib.auth.urls")),
    path("dj/co/", include("co.urls")),
    # path("dj/userflows/", include("userflows.urls")),
    # Django-ninja API routes, per app
    path("api/co/", co_api.urls),
    path("api/userflows/", userflows_api.urls),
    path("api/", world_api.urls),  # generic / fallback APIs
    # Old-school django routes (including dj/api/ stuff, which should transition to django-ninja)
    path("dj/", include("world.urls")),
    # Add catch-all for routes that should NOT go to react (ones starting with dj/ or api/)
    re_path(r"^(?:dj|api)/.+$", page_not_found, {"exception": django.http.Http404()}, name="page_not_found"),
    # All other routes - send to React for rendering
    re_path(r"^(.*)$", frontend_proxy_view, name="frontend_proxy_view"),
]

if settings.ENABLE_SILK:
    urlpatterns.insert(0, path("dj/silk/", include("silk.urls", namespace="silk")))
