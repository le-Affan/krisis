"""Model adapters: resolve and invoke user-registered models.

Exactly two adapter types are supported.

  "http"
    `location` is a URL. Krisis POSTs the input features as JSON to that
    URL and expects back a JSON response containing a "prediction" field,
    e.g. {"prediction": 0.73}. Any other shape is treated as an error.
    Requests use a 5 second timeout by default.

  "python_callable"
    `location` is "module.path:function_name", importable from the SAME
    Python environment running Krisis. The function is called directly
    with the input features dict; its return value is the prediction.

    SECURITY: python_callable executes arbitrary local code at import and
    call time — there is no sandboxing. It is intended for local,
    single-user development only. Do NOT register python_callable models
    on a Krisis deployment reachable by untrusted users. Use the http
    adapter for any multi-tenant or publicly-reachable deployment.
"""

import importlib
from typing import Any, Callable, Dict

import httpx

VALID_ADAPTER_TYPES = {"http", "python_callable"}
HTTP_ADAPTER_TIMEOUT_SECONDS = 5.0


class ModelResolutionError(ValueError):
    """A model's adapter/location could not be resolved. Raised at
    registration time so bad models fail fast instead of at prediction time."""


class ModelInvocationError(Exception):
    """A resolved model failed while serving a prediction. Callers should
    treat this as a per-request failure (e.g. HTTP 502), not a service crash."""


def resolve_python_callable(location: str) -> Callable:
    if ":" not in location:
        raise ModelResolutionError(
            f"Invalid python_callable location '{location}': expected format "
            "'module.path:function_name'"
        )
    module_path, func_name = location.rsplit(":", 1)
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise ModelResolutionError(
            f"Cannot import module '{module_path}' for python_callable "
            f"'{location}': {e}"
        ) from e

    func = getattr(module, func_name, None)
    if func is None or not callable(func):
        raise ModelResolutionError(
            f"'{func_name}' not found or not callable in module '{module_path}'"
        )
    return func


def validate_adapter(adapter_type: str, location: str) -> None:
    """Fail-fast validation at registration time. Raises ModelResolutionError
    if adapter_type/location are invalid or, for python_callable, don't
    actually resolve."""
    if adapter_type not in VALID_ADAPTER_TYPES:
        raise ModelResolutionError(
            f"Invalid adapter_type '{adapter_type}'. Must be one of: "
            f"{sorted(VALID_ADAPTER_TYPES)}"
        )
    if adapter_type == "python_callable":
        resolve_python_callable(location)
    elif adapter_type == "http":
        if not (location.startswith("http://") or location.startswith("https://")):
            raise ModelResolutionError(
                f"Invalid http location '{location}': must start with "
                "http:// or https://"
            )


def invoke_model(
    adapter_type: str,
    location: str,
    features: Dict[str, Any],
    timeout: float = HTTP_ADAPTER_TIMEOUT_SECONDS,
) -> Any:
    """Call a registered model at prediction time. Raises ModelInvocationError
    on any failure."""
    if adapter_type == "http":
        return _invoke_http(location, features, timeout=timeout)
    elif adapter_type == "python_callable":
        return _invoke_python_callable(location, features)
    raise ModelInvocationError(f"Unknown adapter_type '{adapter_type}'")


def _invoke_http(location: str, features: Dict[str, Any], timeout: float) -> Any:
    try:
        response = httpx.post(location, json=features, timeout=timeout)
    except httpx.TimeoutException as e:
        raise ModelInvocationError(
            f"Model endpoint '{location}' timed out after {timeout}s: {e}"
        ) from e
    except httpx.RequestError as e:
        raise ModelInvocationError(
            f"Model endpoint '{location}' unreachable: {e}"
        ) from e

    if response.status_code != 200:
        raise ModelInvocationError(
            f"Model endpoint '{location}' returned HTTP {response.status_code}"
        )

    try:
        data = response.json()
    except ValueError as e:
        raise ModelInvocationError(
            f"Model endpoint '{location}' returned malformed JSON: {e}"
        ) from e

    if not isinstance(data, dict) or "prediction" not in data:
        raise ModelInvocationError(
            f"Model endpoint '{location}' response missing required "
            "'prediction' field"
        )
    return data["prediction"]


def _invoke_python_callable(location: str, features: Dict[str, Any]) -> Any:
    try:
        func = resolve_python_callable(location)
    except ModelResolutionError as e:
        raise ModelInvocationError(str(e)) from e

    try:
        return func(features)
    except Exception as e:
        raise ModelInvocationError(
            f"python_callable model '{location}' raised an exception: {e}"
        ) from e
