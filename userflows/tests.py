from django.test import TestCase
from django.test import Client
from django.urls import get_resolver, reverse
from django.apps import apps as django_apps
import pytest

import mygeo
from mygeo import urls
from mygeo import settings

whitelist_noauth = [
    "/account/login/",
    "/dj/accounts/login/",
    "/dj/accounts/password_reset/",
    "/dj/accounts/password_reset/done/",
    "/dj/accounts/reset/1/2/",
    "/dj/accounts/reset/done/",
    "/1",  # catch-all React view (react router returns 200)
]
whitelist_404 = ["/api/", "/api/co/", "/api/userflows/"]


@pytest.mark.django_db(databases=["default"])
class TestAuthenticationPaths:

    # WARNING: don't include an __init__ method, or pytest will skip the tests
    # def __init__(self):
    #     pass

    def setup_method(self):
        self.url_resolver = get_resolver()

    def test_authentication_flow(self, client: Client):
        # Test login
        login_url = reverse("login")
        response = client.get(login_url)
        assert response.status_code == 200

        # Test logout
        logout_url = reverse("logout")
        response = client.get(logout_url)
        assert response.status_code == 302

    def test_authentication_required(self, client: Client):
        # Test access to React pages - should be allowed through.
        view_url = reverse("frontend_proxy_view", args=["any_path"])
        response = client.get(view_url)
        assert response.status_code == 200, f"Failed on {view_url}"

    def test_account_login(self, client: Client):
        response = client.get("/account/login/")
        assert response.status_code == 200
        User = django_apps.get_model(settings.AUTH_USER_MODEL)
        foo = User.objects.all()
        foo = list(foo)
        print(foo)

    def test_all_urls_logged_out(self, client: Client):
        # Test all URLs that require auth, actually require auth

        url_patterns = urls.urlpatterns
        failures = 0
        tests = 0
        for url in mygeo.util.each_url_with_placeholder(url_patterns):
            # print (f"Testing URL: {url}")
            tests += 1
            if url == "/sentry-debug/":
                with pytest.raises(ZeroDivisionError):
                    response = client.get(url)
            else:
                response = client.get(url)
                if url in whitelist_noauth:
                    assert response.status_code == 200
                else:
                    if response.status_code not in [302, 401, 405]:
                        if response.status_code == 404:
                            if url in whitelist_404:
                                continue
                        print(
                            f"Problem: Url {url} returned code {response.status_code}, expected 302, 401, or 405"
                        )
                        failures += 1
                    # assert response.status_code == 302
        print(f"Finished testing {tests} URLs")
        assert failures == 0, f"Failed {failures} URLs above"
