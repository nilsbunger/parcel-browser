"""mygeo URL Configuration"""

from django.contrib import admin
from django.urls import path, include, re_path

from world import views
from world.infra_views import frontend_proxy_view
from world.views import MapView, ParcelDetailView, ParcelDetailData, IsolatedNeighborDetailData

urlpatterns = [
    # Django-rendered routes
    path('dj/admin', admin.site.urls),
    path('dj/accounts', include('django.contrib.auth.urls')),
    path('dj/map', MapView.as_view()),
    # path("api/", include("world.api")),
    path('dj/parcel/<str:apn>', ParcelDetailView.as_view()),

    # Django-generated API routes
    path('dj/api/parceltile/<int:z>/<int:x>/<int:y>',
         views.ParcelTileData.as_view(), name="parcel-tile"),
    path('dj/api/topotile/<int:z>/<int:x>/<int:y>',
         views.TopoTileData.as_view(), name="topo-tile"),
    path('dj/api/listings', views.ListingsData.as_view(), name="listings"),
    path('dj/parcel/<str:apn>/geodata', ParcelDetailData.as_view()),
    path('dj/parcel/<str:apn>/geodata/neighbor',
         IsolatedNeighborDetailData.as_view()),

    # All other routes - send to React for rendering
    re_path(r'^(.*)$', frontend_proxy_view),

]
