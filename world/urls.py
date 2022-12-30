from django.urls import path

from . import views
from .views import AddressToLatLong, IsolatedNeighborDetailData, ParcelDetailData, ParcelDetailView

# These are all scoped with 'dj/' in front of them. These are old-school URL paths -
#  we do api paths with django-ninja, and the others are mostly deprecated pages.
urlpatterns = [
    path("map/search/<str:address>", AddressToLatLong.as_view()),
    path("parcel/<str:apn>", ParcelDetailView.as_view()),
    # old-school APIs serving vector tiles
    path(
        "api/parceltile/<int:z>/<int:x>/<int:y>",
        views.ParcelTileData.as_view(),
        name="parcel-tile",
    ),
    path(
        "api/roadtile/<int:z>/<int:x>/<int:y>",
        views.RoadTileData.as_view(),
        name="road-tile",
    ),
    path(
        "api/zoningtile/<int:z>/<int:x>/<int:y>",
        views.ZoningTileData.as_view(),
        name="zoning-tile",
    ),
    path(
        "api/zoninglabeltile/<int:z>/<int:x>/<int:y>",
        views.ZoningLabelTile.as_view(),
        name="zoning-label-tile",
    ),
    path("api/topotile/<int:z>/<int:x>/<int:y>", views.TopoTileData.as_view(), name="topo-tile"),
    path("api/tpatile/<int:z>/<int:x>/<int:y>", views.TpaTileData.as_view(), name="tpa-tile"),
    path(
        "api/ab2011tile/<int:z>/<int:x>/<int:y>",
        views.Ab2011TileData.as_view(),
        name="ab2011-tile",
    ),
    path(
        "api/compcommtile/<int:z>/<int:x>/<int:y>",
        views.CompCommTileData.as_view(),
        name="compcomm-tile",
    ),
    path("parcel/<str:apn>/geodata", ParcelDetailData.as_view()),
    path("parcel/<str:apn>/geodata/neighbor", IsolatedNeighborDetailData.as_view()),
]
