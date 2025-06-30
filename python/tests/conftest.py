import os
import sys
import pytest


@pytest.fixture(scope="session")
def config():
    return {"testing": True}


@pytest.fixture(scope="session")
def anyio_backend():
    return 'asyncio'
