from django.urls import path
from sesame.views import LoginView

from userflows import views

urlpatterns = [
    path("login/auth", LoginView.as_view(), name="magic_link_auth"),
    path("login", views.MagicLinkLoginView.as_view(), name="magic_link_login"),
    path("logout", views.logout_view, name="logout"),
]
