import os

from src import db_models  # Ensures models are registered
from src.database import get_engine, init_db


def test_database_initialization(tmp_path):
    db_file = tmp_path / "test_abtest.db"
    database_url = f"sqlite:///{db_file}"

    engine = get_engine(database_url)
    init_db(engine)

    # Assert database file was created
    assert db_file.exists()
