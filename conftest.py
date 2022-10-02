import logging

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
