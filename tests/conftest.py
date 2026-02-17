import pytest

from src.core import ABTestFramework
from src.database import get_engine, get_session_factory, init_db
from src.storage import DatabaseStorage, InMemoryStorage


@pytest.fixture(params=["memory", "database"])
def framework(request):
    if request.param == "memory":
        return ABTestFramework(storage_backend=InMemoryStorage())
    else:
        # SQLite in-memory database for fast isolated DB tests
        engine = get_engine("sqlite:///:memory:")
        init_db(engine)
        session_factory = get_session_factory(engine)
        return ABTestFramework(storage_backend=DatabaseStorage(session_factory))
