"""mygeo URL Configuration"""
import django
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.urls import path, include, re_path
from django.views.defaults import page_not_found

from mygeo import settings
import world
from world import views
import world.auth_views
from world.infra_views import frontend_proxy_view
from world.views import (
    ParcelDetailView,
    ParcelDetailData,
    IsolatedNeighborDetailData,
    AddressToLatLong,
)
from world.api import api as world_api
from co.co_api import api as co_api


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
    #### ---- Django-rendered routes
    path("dj/admin/", admin.site.urls),
    # django-two-factor-auth URLS
    path("", include(tf_urls)),
    # # django-allauth routes
    # path("dj/all-auth/accounts/", include("allauth.urls")),
    # # auth0 auth routes
    # path("dj/", world.auth_views.index, name="auth0_index"),
    # path("dj/login", world.auth_views.login, name="auth0_login"),
    # path("dj/logout", world.auth_views.logout, name="auth0_logout"),
    # path("dj/callback", world.auth_views.callback, name="auth0_callback"),
    # # Original django-auth.... not sure what to do with it yet
    # path("dj/accounts/", include("django.contrib.auth.urls")),
    # Deprecated routes:
    # path("dj/map/", MapView.as_view()),
    path("dj/map/search/<str:address>", AddressToLatLong.as_view()),
    path("dj/parcel/<str:apn>", ParcelDetailView.as_view()),
    path("dj/co/", include("co.urls")),
    # Django-generated API routes
    path("api/co/", co_api.urls),
    # new-school APIs using django-ninja
    path("api/", world_api.urls),
    # old-school APIs serving vector tiles
    path(
        "dj/api/parceltile/<int:z>/<int:x>/<int:y>",
        views.ParcelTileData.as_view(),
        name="parcel-tile",
    ),
    path(
        "dj/api/roadtile/<int:z>/<int:x>/<int:y>",
        views.RoadTileData.as_view(),
        name="road-tile",
    ),
    path(
        "dj/api/zoningtile/<int:z>/<int:x>/<int:y>",
        views.ZoningTileData.as_view(),
        name="zoning-tile",
    ),
    path(
        "dj/api/zoninglabeltile/<int:z>/<int:x>/<int:y>",
        views.ZoningLabelTile.as_view(),
        name="zoning-label-tile",
    ),
    path("dj/api/topotile/<int:z>/<int:x>/<int:y>", views.TopoTileData.as_view(), name="topo-tile"),
    path("dj/api/tpatile/<int:z>/<int:x>/<int:y>", views.TpaTileData.as_view(), name="tpa-tile"),
    path(
        "dj/api/ab2011tile/<int:z>/<int:x>/<int:y>",
        views.Ab2011TileData.as_view(),
        name="ab2011-tile",
    ),
    path(
        "dj/api/compcommtile/<int:z>/<int:x>/<int:y>",
        views.CompCommTileData.as_view(),
        name="compcomm-tile",
    ),
    # path("dj/api/listings", views.ListingsData.as_view(), name="listings"),
    # path("dj/api/analysis/<int:id>", views.AnalysisDetailData.as_view(), name="listing analysis"),
    path("dj/parcel/<str:apn>/geodata", ParcelDetailData.as_view()),
    path("dj/parcel/<str:apn>/geodata/neighbor", IsolatedNeighborDetailData.as_view()),
    # Add catch-all for routes that should NOT go to react (ones starting with dj/ or api/)
    re_path(r"^(?:dj|api)/.+$", page_not_found, {"exception": django.http.Http404()}),
    # All other routes - send to React for rendering
    re_path(r"^(.*)$", frontend_proxy_view),
]

if settings.DEV_ENV:
    urlpatterns.insert(0, path("dj/silk/", include("silk.urls", namespace="silk")))
