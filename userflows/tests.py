from django.test import TestCase
from django.test import Client
from django.urls import get_resolver, reverse
import pytest


@pytest.mark.django_db(databases=["basedata", "default"])
class TestAuthenticationPaths:

    # WARNING: don't include an __init__ method, or pytest will skip the tests
    # def __init__(self):
    #     pass

    def setup(self):
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
        # Test view access without being authenticated
        view_url = reverse("view_name")
        response = client.get(view_url)
        assert response.status_code == 302  # Expect a redirect to login page

    def test_all_urls_authentication(self):
        # Test that all URLs are valid

        # Iterate over the URL patterns in the resolver
        for url_pattern in self.url_resolver.url_patterns:
            # Get the URL pattern name and path
            name = url_pattern.name
            path = url_pattern.pattern.regex.pattern
            print(f"{name}: {path}")
