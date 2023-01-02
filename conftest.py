import logging
import warnings

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

## TODO: I originally created this setup function, but it prevents migrations from being applied, so i'm removing it
##  for now. It was used by the lib/test_* scripts.
# @pytest.fixture(scope="session")
def IGNORE_django_db_setup():
    # Unique DB configuration code. I *think* the only thing that's different is that we're using TWO databases,
    # and we specify the default DB to be pytest_db.
    from django.conf import settings

    settings.DATABASES["default"]["NAME"] = "pytest_db"
    logging.info("Creating database")
    _run_sql("DROP DATABASE IF EXISTS pytest_db")
    _run_sql("CREATE DATABASE pytest_db")
    logging.info("Done creating database")
    # Run actual tests
    yield

    # Teardown
    for connection in connections.all():
        connection.close()

    _run_sql("DROP DATABASE pytest_db")


# @pytest.fixture(scope='session')
# def django_db_setup():
#     from django.conf import settings
#     # Setup
#     settings.DATABASES['default']['NAME'] = 'pytest_db'
#     logging.info("Creating database")
#     run_sql('DROP DATABASE IF EXISTS pytest_db')
#     run_sql('CREATE DATABASE pytest_db TEMPLATE geodjango')
#     logging.info("Done creating database")
#
#     # Run actual tests
#     yield
#
#     # Teardown
#     for connection in connections.all():
#         connection.close()
#
#     run_sql('DROP DATABASE pytest_db')
