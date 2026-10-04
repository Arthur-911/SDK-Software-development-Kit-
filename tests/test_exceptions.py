"""Tests for exception hierarchy and string representations."""

from __future__ import annotations

from server_sdk.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ServerSDKError,
    TimeoutError,
    ValidationError,
)


def test_server_sdk_error_repr() -> None:
    err = ServerSDKError("Connection failed")
    assert repr(err) == "ServerSDKError(message='Connection failed')"
    assert str(err) == "Connection failed"
    assert err.message == "Connection failed"


def test_api_error_repr() -> None:
    err = APIError("Bad request", status_code=400, response_body={"detail": "fail"})
    assert "status_code=400" in repr(err)
    assert "message='Bad request'" in repr(err)
    assert err.status_code == 400
    assert err.response_body == {"detail": "fail"}


def test_rate_limit_error_repr() -> None:
    err = RateLimitError("Too Many Requests", retry_after=15.0)
    expected = "RateLimitError(status_code=429, retry_after=15.0, message='Too Many Requests')"
    assert repr(err) == expected
    assert err.retry_after == 15.0
    assert err.status_code == 429


def test_subclass_exceptions() -> None:
    auth_err = AuthenticationError("Unauthorized", status_code=401)
    assert isinstance(auth_err, APIError)
    assert isinstance(auth_err, ServerSDKError)

    nf_err = NotFoundError("Not found", status_code=404)
    assert isinstance(nf_err, APIError)

    srv_err = ServerError("Server down", status_code=500)
    assert isinstance(srv_err, APIError)

    timeout_err = TimeoutError("Timed out")
    assert isinstance(timeout_err, ServerSDKError)

    val_err = ValidationError("Invalid param")
    assert isinstance(val_err, ServerSDKError)
