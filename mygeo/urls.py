"""mygeo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path

from world import views
from world.views import MapView, ParcelView, ParcelData, ParcelTileData

urlpatterns = [
    path('admin/', admin.site.urls),
    path('map/', MapView.as_view()),
    path("api/", include("world.api")),
    path('accounts/', include('django.contrib.auth.urls')),
    path('parcel/<str:apn>', ParcelView.as_view()),
    path('parcel/<str:apn>/geodata', ParcelData.as_view()),
    # path('parceltile', ParcelTileData.as_view()),
    path('parceltile/<int:z>/<int:x>/<int:y>', views.ParcelTileData.as_view(), name="parcel-tile"),
    path('frontend/<path:path>', views.catchall),

]
