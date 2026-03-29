from datetime import datetime

from src import db_models  # Ensures models are registered
from src.database import get_engine, get_session_factory, init_db
from src.models import ModelVariant, Outcome, Request
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


def test_save_outcome_and_filter_by_variant(tmp_path):
    db_file = tmp_path / "test_storage.db"
    database_url = f"sqlite:///{db_file}"

    engine = get_engine(database_url)
    init_db(engine)
    session_factory = get_session_factory(engine)

    storage = DatabaseStorage(session_factory)

    # Create two requests with different variants
    req_a = Request(
        request_id="req_A",
        selected_model=ModelVariant.A,
        input_data=None,
        timestamp=datetime.utcnow().timestamp(),
    )

    req_b = Request(
        request_id="req_B",
        selected_model=ModelVariant.B,
        input_data=None,
        timestamp=datetime.utcnow().timestamp(),
    )

    storage.save_request(req_a)
    storage.save_request(req_b)

    # Save outcomes for both
    outcome_a = Outcome(
        request_id="req_A",
        outcome_value=1.0,
        timestamp=datetime.utcnow().timestamp(),
    )

    outcome_b = Outcome(
        request_id="req_B",
        outcome_value=0.0,
        timestamp=datetime.utcnow().timestamp(),
    )

    storage.save_outcome(outcome_a)
    storage.save_outcome(outcome_b)

    # Now query outcomes by variant
    outcomes_a = storage.get_outcomes_by_variant(ModelVariant.A)
    outcomes_b = storage.get_outcomes_by_variant(ModelVariant.B)

    assert outcomes_a == [1.0]
    assert outcomes_b == [0.0]


def test_route_request_works_with_both_backends(framework):
    framework.register_models(lambda x: x + 1, lambda x: x * 2)

    prediction, request_id, _ = framework.route_request(5, 0.5)

    assert request_id is not None
    assert prediction in [6, 10]


def test_outcome_storage_and_retrieval(framework):
    framework.register_models(lambda x: x, lambda x: x)

    # Force A
    for _ in range(2):
        _, request_id, _ = framework.route_request(1, 1.0)
        framework.record_delayed_outcome(request_id, 1.0)

    # Force B
    for _ in range(2):
        _, request_id, _ = framework.route_request(1, 0.0)
        framework.record_delayed_outcome(request_id, 0.0)

    result = framework.compile_evidence()

    assert result != "Not enough data to compute statistics."


def test_multiple_requests(framework):
    framework.register_models(lambda x: x, lambda x: x)

    for _ in range(10):
        _, request_id, _ = framework.route_request(1, 0.5)
        framework.record_delayed_outcome(request_id, 1.0)

    result = framework.compile_evidence()
    assert result is not None


def test_invalid_request_raises(framework):
    try:
        framework.record_delayed_outcome("invalid-id", 1.0)
    except ValueError:
        assert True
    else:
        assert False
