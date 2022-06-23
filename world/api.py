"""Markers API URL Configuration."""

from rest_framework import routers

from world.viewsets import MarkerViewSet, ParcelViewSet

router = routers.DefaultRouter()
router.register(r"markers", MarkerViewSet)
router.register(r"parcels", ParcelViewSet)

urlpatterns = router.urls
