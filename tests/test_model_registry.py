"""API-level tests for model registration, experiment/model validation, and
routing through real registered models — no more hardcoded model_a/model_b
stand-ins. Uses a real (migrated) SQLite file so experiments.py's own DB
session and framework.storage.get_model see the same data, matching how
STORAGE_BACKEND=database behaves in production."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app, get_framework
from src.core import ABTestFramework
from src.database import get_engine, get_session_factory, init_db
from src.storage import DatabaseStorage


@pytest.fixture
def registry_client(tmp_path, monkeypatch):
    db_file = tmp_path / "registry_test.db"
    db_url = f"sqlite:///{db_file}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    engine = get_engine(db_url)
    init_db(engine)
    session_factory = get_session_factory(engine)

    framework = ABTestFramework(storage_backend=DatabaseStorage(session_factory))
    app.dependency_overrides[get_framework] = lambda: framework

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()


def _register(client, model_id, adapter_type, location):
    return client.post(
        "/api/v1/models",
        json={"model_id": model_id, "adapter_type": adapter_type, "location": location},
    )


# --- registration ---


def test_register_python_callable_model(registry_client):
    resp = _register(registry_client, "local_add_one", "python_callable", "tests.fixture_models:add_one")
    assert resp.status_code == 201
    assert resp.json() == {
        "model_id": "local_add_one",
        "adapter_type": "python_callable",
        "location": "tests.fixture_models:add_one",
        "metadata": {},
    }


def test_register_http_model(registry_client, mock_model_server):
    url = mock_model_server(lambda f: (200, {"prediction": f["x"] * 10}))
    resp = _register(registry_client, "remote_model", "http", url)
    assert resp.status_code == 201


def test_get_registered_model(registry_client):
    _register(registry_client, "m1", "python_callable", "tests.fixture_models:add_one")
    resp = registry_client.get("/api/v1/models/m1")
    assert resp.status_code == 200
    assert resp.json()["model_id"] == "m1"


def test_get_unknown_model_404(registry_client):
    resp = registry_client.get("/api/v1/models/does-not-exist")
    assert resp.status_code == 404


def test_list_models(registry_client):
    _register(registry_client, "m1", "python_callable", "tests.fixture_models:add_one")
    _register(registry_client, "m2", "python_callable", "tests.fixture_models:double")
    resp = registry_client.get("/api/v1/models")
    assert resp.status_code == 200
    ids = {m["model_id"] for m in resp.json()}
    assert {"m1", "m2"}.issubset(ids)


# --- registration validation ---


def test_register_duplicate_model_id_rejected(registry_client):
    payload = {
        "model_id": "dup_model",
        "adapter_type": "python_callable",
        "location": "tests.fixture_models:add_one",
    }
    assert registry_client.post("/api/v1/models", json=payload).status_code == 201
    assert registry_client.post("/api/v1/models", json=payload).status_code == 409


def test_register_bad_adapter_type_rejected(registry_client):
    resp = _register(registry_client, "bad_type", "internal", "x")
    assert resp.status_code == 400


def test_register_unresolvable_python_callable_rejected(registry_client):
    resp = _register(registry_client, "broken_ref", "python_callable", "tests.fixture_models:does_not_exist")
    assert resp.status_code == 400


def test_register_http_without_url_scheme_rejected(registry_client):
    resp = _register(registry_client, "bad_url", "http", "not-a-url")
    assert resp.status_code == 400


# --- experiment <-> registry validation ---


def test_experiment_rejects_unregistered_model(registry_client):
    resp = registry_client.post(
        "/api/v1/experiments",
        json={"experiment_id": "exp_missing_model", "model_a_id": "ghost_a", "model_b_id": "ghost_b"},
    )
    assert resp.status_code == 400


def test_experiment_accepts_registered_models(registry_client):
    _register(registry_client, "ma", "python_callable", "tests.fixture_models:add_one")
    _register(registry_client, "mb", "python_callable", "tests.fixture_models:double")
    resp = registry_client.post(
        "/api/v1/experiments",
        json={"experiment_id": "exp_ok", "model_a_id": "ma", "model_b_id": "mb"},
    )
    assert resp.status_code == 200


# --- real end-to-end routing through the registry ---


def test_predict_uses_registered_python_callable_models(registry_client):
    _register(registry_client, "m_add_one", "python_callable", "tests.fixture_models:add_one")
    _register(registry_client, "m_double", "python_callable", "tests.fixture_models:double")
    registry_client.post(
        "/api/v1/experiments",
        json={
            "experiment_id": "real_registry_exp",
            "model_a_id": "m_add_one",
            "model_b_id": "m_double",
            "probability_split": 1.0,  # random.random() < 1.0 always -> forces variant A
        },
    )

    resp = registry_client.post(
        "/api/v1/predict", json={"experiment_id": "real_registry_exp", "features": {"x": 10}}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_variant"] == "A"
    assert body["prediction"] == 11  # add_one(10), not a hardcoded stand-in


def test_predict_uses_registered_http_model(registry_client, mock_model_server):
    url = mock_model_server(lambda f: (200, {"prediction": f["x"] * 100}))
    _register(registry_client, "m_http", "http", url)
    _register(registry_client, "m_local", "python_callable", "tests.fixture_models:add_one")
    registry_client.post(
        "/api/v1/experiments",
        json={
            "experiment_id": "http_exp",
            "model_a_id": "m_http",
            "model_b_id": "m_local",
            "probability_split": 1.0,
        },
    )

    resp = registry_client.post("/api/v1/predict", json={"experiment_id": "http_exp", "features": {"x": 3}})
    assert resp.status_code == 200
    assert resp.json()["prediction"] == 300


def test_broken_model_returns_clean_error_not_crash(registry_client):
    _register(registry_client, "m_broken", "python_callable", "tests.fixture_models:broken_model")
    _register(registry_client, "m_ok", "python_callable", "tests.fixture_models:add_one")
    registry_client.post(
        "/api/v1/experiments",
        json={
            "experiment_id": "broken_exp",
            "model_a_id": "m_broken",
            "model_b_id": "m_ok",
            "probability_split": 1.0,  # forces routing to the broken model
        },
    )

    resp = registry_client.post("/api/v1/predict", json={"experiment_id": "broken_exp", "features": {"x": 1}})
    assert resp.status_code == 502

    # the service itself must still be alive after a model exception
    health = registry_client.get("/health")
    assert health.status_code == 200


def test_predict_unknown_experiment_returns_404(registry_client):
    resp = registry_client.post(
        "/api/v1/predict", json={"experiment_id": "never_created", "features": {"x": 1}}
    )
    assert resp.status_code == 404
