from django.urls import path

from elt import views

urlpatterns = [
    path(
        "api/tile/raw_sf_parcel_wrap/<int:z>/<int:x>/<int:y>",
        views.RawSfParcelWrapTile.as_view(),
        name="raw-sf-parcel-wrap-tile",
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
        "api/tile/raw_sf_he/<int:z>/<int:x>/<int:y>", views.RawSfHeTableBTile.as_view(), name="raw-sf-he-table-b-tile"
    ),
    path(
        "api/tile/raw_cali_resource_level/<int:z>/<int:x>/<int:y>",
        views.RawCaliResourceLevelTile.as_view(),
        name="raw-cali-resource-level-tile",
    ),
    path(
        "api/tile/elt_analysis/<str:geo>/<str:analysis>/<int:z>/<int:x>/<int:y>",
        views.EltAnalysisTile.as_view(),
        name="elt-analysis-tile",
    ),
    path(
        "api/tile/raw_geom_data/<str:geo>/<str:datatype>/<str:layer>/<int:z>/<int:x>/<int:y>",
        views.RawGeomDataTile.as_view(),
        name="raw-geom-data-tile",
    ),
]
