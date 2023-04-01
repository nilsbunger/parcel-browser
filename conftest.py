import pytest
import requests
from django.core.management import call_command

from mygeo.settings import BASE_DIR


# Don't allow network calls during test. Cool use of monkeypatch. Saw on Real Python.
@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    def stunted_get():
        raise RuntimeError("Network access not allowed during testing!")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: stunted_get())


# def pytest_collectstart(collector):
# # pytest skips test classes that have a constructor... this snippet generates a warning if we see one.
# for item in collector.collect():
#     if hasattr(item.obj, '__init__'):
#         print(f"Test class {item.name} has a constructor and will be skipped")
#         logging.warning(f"WARNING2: Test class {item.name} has a constructor and will be skipped")
#         warnings.warn(f"WARNING3: Test class {item.name} has a constructor and will be skipped")


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    # including django_db_setup as an argument ensures that the base django_db_setup fixture is executed
    # See https://pytest-django.readthedocs.io/en/latest/database.html#django-db-setup for more info

    with django_db_blocker.unblock():
        print("Adding parcel / roads / zoning fixtures")
        call_command("loaddata", BASE_DIR / "world/test_fixtures/parcel_data.yaml")
        call_command("loaddata", BASE_DIR / "world/test_fixtures/roads_data.yaml")
        call_command("loaddata", BASE_DIR / "world/test_fixtures/analyzed_road_data.yaml")
        call_command("loaddata", BASE_DIR / "world/test_fixtures/zoning_base_data.yaml")
