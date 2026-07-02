import socket
import time

import pytest

from src.adapters import (
    ModelInvocationError,
    ModelResolutionError,
    invoke_model,
    resolve_python_callable,
    validate_adapter,
)


# --- python_callable resolution ---


def test_resolve_python_callable_success():
    func = resolve_python_callable("tests.fixture_models:add_one")
    assert func({"x": 5}) == 6


def test_resolve_python_callable_bad_module():
    with pytest.raises(ModelResolutionError):
        resolve_python_callable("tests.does_not_exist:add_one")


def test_resolve_python_callable_bad_function():
    with pytest.raises(ModelResolutionError):
        resolve_python_callable("tests.fixture_models:does_not_exist")


def test_resolve_python_callable_bad_format():
    with pytest.raises(ModelResolutionError):
        resolve_python_callable("no_colon_here")


# --- registration-time validation ---


def test_validate_adapter_rejects_unknown_type():
    with pytest.raises(ModelResolutionError):
        validate_adapter("internal", "whatever")


def test_validate_adapter_rejects_non_url_http_location():
    with pytest.raises(ModelResolutionError):
        validate_adapter("http", "not-a-url")


def test_validate_adapter_accepts_valid_python_callable():
    validate_adapter("python_callable", "tests.fixture_models:add_one")  # no raise


def test_validate_adapter_rejects_unresolvable_python_callable():
    with pytest.raises(ModelResolutionError):
        validate_adapter("python_callable", "tests.fixture_models:does_not_exist")


# --- python_callable invocation ---


def test_invoke_python_callable_success():
    result = invoke_model("python_callable", "tests.fixture_models:double", {"x": 4})
    assert result == 8


def test_invoke_python_callable_raises_clean_error():
    with pytest.raises(ModelInvocationError, match="raised an exception"):
        invoke_model("python_callable", "tests.fixture_models:broken_model", {"x": 1})


# --- http invocation, against a real local server ---


def test_invoke_http_success(mock_model_server):
    url = mock_model_server(lambda f: (200, {"prediction": f["x"] + 1}))
    assert invoke_model("http", url, {"x": 5}) == 6


def test_invoke_http_missing_prediction_field(mock_model_server):
    url = mock_model_server(lambda f: (200, {"foo": "bar"}))
    with pytest.raises(ModelInvocationError, match="prediction"):
        invoke_model("http", url, {"x": 1})


def test_invoke_http_malformed_json(mock_model_server):
    url = mock_model_server(lambda f: (200, "not-json{"))
    with pytest.raises(ModelInvocationError):
        invoke_model("http", url, {"x": 1})


def test_invoke_http_non_200(mock_model_server):
    url = mock_model_server(lambda f: (500, {"error": "boom"}))
    with pytest.raises(ModelInvocationError, match="HTTP 500"):
        invoke_model("http", url, {"x": 1})


def test_invoke_http_unreachable():
    # Bind a free port then release it immediately — nothing is listening.
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()

    with pytest.raises(ModelInvocationError, match="unreachable"):
        invoke_model("http", f"http://127.0.0.1:{port}/predict", {"x": 1}, timeout=1.0)


def test_invoke_http_timeout(mock_model_server):
    def slow_handler(features):
        time.sleep(0.3)
        return (200, {"prediction": 1})

    url = mock_model_server(slow_handler)
    with pytest.raises(ModelInvocationError, match="timed out"):
        invoke_model("http", url, {"x": 1}, timeout=0.05)
