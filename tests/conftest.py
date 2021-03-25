"""
A shared file auto-discovered by all pytests that holds shared tests and config
NOTE: This is a *magical* pytest file name
"""
import os
import pytest

TESTS = os.path.abspath("tests")


@pytest.fixture
def yaml_output():
    """
    Remove "tests.yaml" after the test
    """

    yaml = os.path.join(TESTS, "tests.yaml")

    if os.path.isfile(yaml):
        os.remove(yaml)

    yield yaml

    os.remove(yaml)
