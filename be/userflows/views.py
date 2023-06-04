# Create your views here.
import logging

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
import sesame
import sesame.utils
from django import forms
from django.contrib.auth import get_user_model, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView

from .lib import send_magic_link_email

log = logging.getLogger(__name__)


class MagicLinkLoginForm(forms.Form):
    email = forms.EmailField()


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MagicLinkLoginView(FormView):
    template_name = "userflows/magic_link_login.html"
    form_class = MagicLinkLoginForm

    def get_user(self, email) -> get_user_model() | None:
        """Find the user with this email address, return its instance or None"""
        User = get_user_model()
        return User.objects.get_or_create(email=email)

    def create_link(self, user):
        """Create a login link for this user."""
        link = reverse("magic_link_auth")
        link = self.request.build_absolute_uri(link)
        link += sesame.utils.get_query_string(user)
        return link

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        user = self.get_user(email)
        link = self.create_link(user)
        send_magic_link_email(user, link)
        return render(self.request, "userflows/magic_link_login_success.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")
