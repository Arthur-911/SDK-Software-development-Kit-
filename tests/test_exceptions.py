"""Tests for exception hierarchy and string representations."""

from __future__ import annotations

from nasa_sdk.exceptions import (
    AuthenticationError,
    NasaAPIError,
    NasaError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)


def test_nasa_error_repr() -> None:
    err = NasaError("Something went wrong")
    assert repr(err) == "NasaError(message='Something went wrong')"
    assert str(err) == "Something went wrong"
    assert err.message == "Something went wrong"


def test_nasa_api_error_repr() -> None:
    err = NasaAPIError("Bad request", status_code=400, response_body={"error": "fail"})
    assert "status_code=400" in repr(err)
    assert "message='Bad request'" in repr(err)
    assert err.status_code == 400
    assert err.response_body == {"error": "fail"}


def test_rate_limit_error_repr() -> None:
    err = RateLimitError("Too Many Requests", retry_after=12.5)
    expected = "RateLimitError(status_code=429, retry_after=12.5, message='Too Many Requests')"
    assert repr(err) == expected
    assert err.retry_after == 12.5
    assert err.status_code == 429


def test_subclass_exceptions() -> None:
    auth_err = AuthenticationError("Unauthorized", status_code=401)
    assert isinstance(auth_err, NasaAPIError)
    assert isinstance(auth_err, NasaError)

    nf_err = NotFoundError("Not found", status_code=404)
    assert isinstance(nf_err, NasaAPIError)

    srv_err = ServerError("Server down", status_code=500)
    assert isinstance(srv_err, NasaAPIError)

    timeout_err = TimeoutError("Timed out")
    assert isinstance(timeout_err, NasaError)

    val_err = ValidationError("Invalid param")
    assert isinstance(val_err, NasaError)
