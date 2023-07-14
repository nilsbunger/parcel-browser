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
