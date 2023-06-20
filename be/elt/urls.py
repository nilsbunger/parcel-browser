from django.urls import path

from elt import views

urlpatterns = [
    path(
        "api/tile/raw_sf_parcel/<int:z>/<int:x>/<int:y>", views.RawSfParcelTile.as_view(), name="raw-sf-parcel-tile"
    ),
    path(
        "api/tile/raw_sf_zoning/<int:z>/<int:x>/<int:y>", views.RawSfZoningTile.as_view(), name="raw-sf-zoning-tile"
    ),
    path(
        "api/tile/raw_sf_zoning_height_bulk/<int:z>/<int:x>/<int:y>",
        views.RawSfZoningHeightBulkTile.as_view(),
        name="raw-sf-zoning-height-bulk-tile",
    ),
    path(
        "api/tile/raw_sf_he_tile/<int:z>/<int:x>/<int:y>",
        views.RawSfHeTableBTile.as_view(),
        name="raw-sf-he-table-b-tile",
    ),
]
