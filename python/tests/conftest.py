import os
import sys
import pytest


@pytest.fixture(scope="session")
def config():
    return {"testing": True}
