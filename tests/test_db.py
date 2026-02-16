from datetime import datetime

from src import db_models  # Ensures models are registered
from src.database import get_engine, get_session_factory, init_db
from src.models import ModelVariant, Request
from src.storage import DatabaseStorage


def test_database_initialization(tmp_path):
    db_file = tmp_path / "test_abtest.db"
    database_url = f"sqlite:///{db_file}"

    engine = get_engine(database_url)
    init_db(engine)

    # Assert database file was created
    assert db_file.exists()


def test_save_request_persists_to_db(tmp_path):
    db_file = tmp_path / "test_storage.db"
    database_url = f"sqlite:///{db_file}"

    engine = get_engine(database_url)
    init_db(engine)
    session_factory = get_session_factory(engine)

    storage = DatabaseStorage(session_factory)

    request = Request(
        request_id="req_1",
        selected_model=ModelVariant.A,
        input_data=None,
        timestamp=datetime.utcnow().timestamp(),
    )

    storage.save_request(request)

    # Verify row exists
    session = session_factory()
    result = session.query(db_models.DBRequest).filter_by(request_id="req_1").first()
    session.close()

    assert result is not None
    assert str(result.model_variant) == "A"
