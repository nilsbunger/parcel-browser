import re
from pprint import pprint

import pytest
from django.core import mail
from django.test import Client
from django.urls import get_resolver, reverse
from parsnip import urls
from parsnip.util import each_url_with_placeholder

whitelist_noauth = [
    "/user/login",
    "/",
    "/1",  # catch-all React view (react router returns 200)
]
whitelist_404 = ["/api/", "/api/co/", "/api/userflows/", "/api/properties/"]


@pytest.mark.django_db(databases=["default"])
class TestAuthenticationPaths:
    # WARNING: don't include an __init__ method, or pytest will skip the tests
    # def __init__(self):
    #     pass

    def setup_method(self):
        self.url_resolver = get_resolver()

    def test_authentication_flow(self, client: Client):
        # Test login
        login_url = reverse("magic_link_login")
        response = client.get(login_url, secure=True)
        assert response.status_code == 200

        # Test logout
        logout_url = reverse("logout")
        response = client.get(logout_url, secure=True)
        assert response.status_code == 302

    def test_authentication_required(self, client: Client):
        # Test access to React pages - should be allowed through.
        view_url = reverse("frontend_proxy_view") + "any_path"
        response = client.get(view_url, secure=True)
        assert response.status_code == 200, f"Failed on {view_url}"

    def test_account_login(self, client_and_user):
        client, user = client_and_user
        client.logout()
        # make sure we're logged out
        client.json_get(reverse("userflows_api:_user"), exp_status=401)

        view_url = reverse("frontend_proxy_view") + "any_path"
        response = client.get(view_url, secure=True)
        assert response.status_code == 200, f"Failed on {view_url}"

        # try an API call to log in
        data = {"email": user.email, "rememberMe": "true"}
        resp = client.json_post(reverse("userflows_api:_magic_link_login"), data=data)
        assert resp["message"] == "Email sent"
        assert resp["errors"] is False

        # make sure we're STILL logged out
        client.json_get(reverse("userflows_api:_user"), exp_status=401)

        # check we got an email, and use token to login.
        assert len(mail.outbox) == 1
        magic_url = re.search("(https:[^\n]*)", mail.outbox[0].body)[0]
        resp = client.get(magic_url, secure=True)

        # check we're logged in
        resp = client.json_get(reverse("userflows_api:_user"))
        assert resp["email"] == user.email

    def test_all_urls_logged_out(self, client: Client):
        # Test all URLs that require auth, actually require auth

        url_patterns = urls.urlpatterns
        failures = []
        tests = 0
        for url in each_url_with_placeholder(url_patterns):
            # print (f"Testing URL: {url}")
            tests += 1
            if url == "/sentry-debug/":
                with pytest.raises(ZeroDivisionError):
                    response = client.get(url, secure=True)
                continue
            response = client.get(url, secure=True)
            if url in whitelist_noauth:
                assert response.status_code == 200
            elif response.status_code == 404 and url in whitelist_404:
                continue
            elif response.status_code not in [302, 401, 403, 405]:
                problem = f"{url} returned code {response.status_code}, expected 302, 401, or 405"
                print(f"Problem: {problem}")
                failures.append(problem)
            # assert response.status_code == 302
        print(f"Finished testing {tests} URLs. {'Failures' if len(failures) else 'No failures'}")
        pprint(failures)
        failure_str = "\n  -->".join(failures)
        assert len(failures) == 0, f"Failed URLs: {failure_str}"
