import logging
import warnings

import pytest
from django.db import connections

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def run_sql(sql):
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
def django_db_setup():
    from django.conf import settings

    settings.DATABASES["default"]["NAME"] = "pytest_db"
    logging.info("Creating database")
    run_sql("DROP DATABASE IF EXISTS pytest_db")
    run_sql("CREATE DATABASE pytest_db")
    logging.info("Done creating database")
    # Run actual tests
    yield

    # Teardown
    for connection in connections.all():
        connection.close()

    run_sql("DROP DATABASE pytest_db")


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
