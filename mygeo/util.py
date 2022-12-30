import sys


# Print to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def field_exists_on_model(model, field: str) -> bool:
    # A simple function to check if a field exists on a model
    try:
        # Check if this exists
        model._meta.get_field(field)
        return True
    except:
        return False


# import pytest
# pytest_is_running = False
#
#
# def is_pytest_running() -> bool:
#     return pytest_is_running
#
#
# # Detect pytest running, from https://github.com/adamchainz/pytest-is-running/blob/main/src/pytest_is_running/plugin.py
# # pytest missing type hints for @hookimpl
# @pytest.hookimpl(tryfirst=True)
# def pytest_load_initial_conftests() -> None:
#     global pytest_is_running
#     pytest_is_running = True
#
#
# def pytest_unconfigure() -> None:
#     global pytest_is_running
#     pytest_is_running = False
