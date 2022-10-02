from django.urls import path

from co.views import CoParcelDetail

urlpatterns = [
    path("parcel/<str:apn>", CoParcelDetail.as_view()),
]
