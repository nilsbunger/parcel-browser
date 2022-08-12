"""mygeo URL Configuration"""
import django
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.defaults import page_not_found

from world import views
from world.infra_views import frontend_proxy_view
from world.views import MapView, ParcelDetailView, ParcelDetailData, IsolatedNeighborDetailData, AddressToLatLong
from world.api import api as world_api
urlpatterns = [
    # Django-rendered routes
    path('dj/admin/', admin.site.urls),
    path('dj/accounts/', include('django.contrib.auth.urls')),
    path('dj/map/', MapView.as_view()),
    path('dj/map/search/<str:address>', AddressToLatLong.as_view()),
    path('dj/parcel/<str:apn>', ParcelDetailView.as_view()),

    # Django-generated API routes
    path('api/', world_api.urls ),
    path('dj/api/parceltile/<int:z>/<int:x>/<int:y>',
         views.ParcelTileData.as_view(), name="parcel-tile"),
    path('dj/api/topotile/<int:z>/<int:x>/<int:y>',
         views.TopoTileData.as_view(), name="topo-tile"),
    path('dj/api/tpatile/<int:z>/<int:x>/<int:y>',
         views.TpaTileData.as_view(), name="tpa-tile"),

    path('dj/api/listings', views.ListingsData.as_view(), name="listings"),
    path('dj/api/analysis/<int:id>',
         views.AnalysisDetailData.as_view(), name="listing analysis"),
    path('dj/api/address-search/<str:address>',
         views.GetParcelByAddressSearch.as_view(), name="address-search"),
    path('dj/parcel/<str:apn>/geodata', ParcelDetailData.as_view()),
    path('dj/parcel/<str:apn>/geodata/neighbor',
         IsolatedNeighborDetailData.as_view()),

    # Add catch-all for routes that should NOT go to react
    re_path(r'^(?:dj|api)/.*$', page_not_found,  {'exception': django.http.Http404()}),
    # All other routes - send to React for rendering
    re_path(r'^(.*)$', frontend_proxy_view),

]
