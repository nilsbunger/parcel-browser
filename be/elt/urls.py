from django.urls import path

from elt import views

urlpatterns = [
    path(
        "api/tile/raw_sf_parcel/<int:z>/<int:x>/<int:y>", views.RawSfParcelTile.as_view(), name="raw-sf-parcel-tile"
    ),
]
