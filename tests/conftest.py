import pytest

from src.core import ABTestFramework
from src.storage import InMemoryStorage


@pytest.fixture
def framework():
    return ABTestFramework(storage_backend=InMemoryStorage())
