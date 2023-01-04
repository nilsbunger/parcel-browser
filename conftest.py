import logging
import warnings

from django.core.management import call_command
import pytest
from django.db import connections

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


# Define django_db_setup for pytest initialization. Originally we created a test DB based on template, though
# I abandoned that approach and instead our tests use TWO databases (one with read-only geo data, and
# one with actual application data).


def _run_sql(sql):
    conn = psycopg2.connect(database="postgres")
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(sql)
    conn.close()


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
    from django.conf import settings

    with django_db_blocker.unblock():
        call_command("loaddata", "world/test_fixtures/parcel_data.yaml")
        call_command("loaddata", "world/test_fixtures/roads_data.yaml")
        call_command("loaddata", "world/test_fixtures/analyzed_road_data.yaml")
        call_command("loaddata", "world/test_fixtures/zoning_base_data.yaml")
