import logging

import pytest
from django.core.management import call_command
from parsnip.settings import BASE_DIR

log = logging.getLogger(__name__)

## Disable monkeypatching of network calls. It interferes with Response mocking (eg in test_attom_api.py)
# # Don't allow network calls during test. Cool use of monkeypatch. Saw on Real Python.
# @pytest.fixture(autouse=True)
# def disable_network_calls(monkeypatch):
#     def stunted_get(*args, **kwargs):
#         raise RuntimeError("Network access not allowed during testing!")
#
#     monkeypatch.setattr(requests, "get", lambda *args, **kwargs: stunted_get(args, kwargs))


# def pytest_collectstart(collector):
# # pytest skips test classes that have a constructor... this snippet generates a warning if we see one.
# for item in collector.collect():
#     if hasattr(item.obj, '__init__'):
#         print(f"Test class {item.name} has a constructor and will be skipped")
#         logging.warning(f"WARNING2: Test class {item.name} has a constructor and will be skipped")
#         warnings.warn(f"WARNING3: Test class {item.name} has a constructor and will be skipped")


@pytest.fixture(scope="session")  # session scope means it'll only run once.
def django_db_setup(django_db_setup, django_db_blocker):
    """Load fixture data. Overrides pytest-django default. Includes django_db_setup as a parameter to ensure that
    the base django_db_setup fixture is executed. See
    https://pytest-django.readthedocs.io/en/latest/database.html#django-db-setup"""
    # including django_db_setup as an argument ensures that the base django_db_setup fixture is executed
    # See https://pytest-django.readthedocs.io/en/latest/database.html#django-db-setup for more info

    with django_db_blocker.unblock():
        ## NB: commented out old fixtures.
        # logging.info("Adding parcel / roads / zoning fixtures")
        # call_command("loaddata", BASE_DIR / "world/test_fixtures/parcel_data.yaml")
        # call_command("loaddata", BASE_DIR / "world/test_fixtures/roads_data.yaml")
        # call_command("loaddata", BASE_DIR / "world/test_fixtures/analyzed_road_data.yaml")
        # call_command("loaddata", BASE_DIR / "world/test_fixtures/zoning_base_data.yaml")

        # Add ELT fixtures created by ./manage.py elt_dump:
        logging.info("Adding elt fixtures")
        call_command("loaddata", BASE_DIR / "elt/tests/fixtures/elt_dump.json.gz")
        yield
        # teardown code here
        logging.info("Hypothetical teerdown code in django_db_setup fixture")


def _json_post(self, path: str, data: str, exp_status=200) -> dict:
    resp = self.post(path, data=data, content_type="application/json", secure=True)
    assert resp.status_code == exp_status
    return resp.json()


def _json_get(self, path: str, data: str = None, exp_status=200) -> dict:
    resp = self.get(path, data=data, content_type="application/json", secure=True)
    assert resp.status_code == exp_status
    return resp.json()


@pytest.fixture()
def client_and_user(django_user_model, client):
    """Provide a logged-in test client (with json_get and json_post methods) and user"""
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.create_user(email="testuser@test.home3.co", password="testpassword")
    assert client.login(email="testuser@test.home3.co", password="testpassword")
    client.defaults["content_type"] = "application/json"
    client.defaults["secure"] = True

    client_cls = type(client)
    client_cls.json_post = _json_post
    client_cls.json_get = _json_get
    yield client, user

    client.logout()
    user.delete()
