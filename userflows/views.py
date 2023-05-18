# Create your views here.
import sesame
import sesame.utils
from django import forms
from django.contrib.auth import get_user_model, logout
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView


class MagicLinkLoginForm(forms.Form):
    email = forms.EmailField()


class MagicLinkLoginView(FormView):
    template_name = "userflows/magic_link_login.html"
    form_class = MagicLinkLoginForm

    def get_user(self, email):
        """Find the user with this email address."""
        User = get_user_model()
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            new_user = User.objects.create_user(email=email)
            return new_user

    def create_link(self, user):
        """Create a login link for this user."""
        link = reverse("magic_link_auth")
        link = self.request.build_absolute_uri(link)
        link += sesame.utils.get_query_string(user)
        return link

    def send_email(self, user, link):
        """Send an email with this login link to this user."""
        user.email_user(
            subject="[Turboprop] Log in to our app",
            message=f"""\
Hello,

You requested that we send you a link to log in to our app:

    {link}

Thank you for using Turboprop!
""",
        )

    def email_submitted(self, email):
        user = self.get_user(email)
        link = self.create_link(user)
        self.send_email(user, link)

    def form_valid(self, form):
        self.email_submitted(form.cleaned_data["email"])
        return render(self.request, "userflows/magic_link_login_success.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")
