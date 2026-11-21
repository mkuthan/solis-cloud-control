import pytest

from custom_components.solis_cloud_control.api.solis_api_error import (
    SolisCloudControlApiError,
    SolisCloudControlPermanentApiError,
    SolisCloudControlTransientApiError,
)


@pytest.mark.parametrize(
    "status_code",
    [408, 429, 500, 502, 503, 504, 599],
)
def test_create_transient_from_status_code(status_code: int) -> None:
    error = SolisCloudControlApiError.create("any message", status_code=status_code)

    assert type(error) is SolisCloudControlTransientApiError
    assert error.status_code == status_code
    assert error.response_code is None


@pytest.mark.parametrize(
    "response_code",
    ["S9999", "B0072", "B0119", "B0250", "B0115", "B0180"],
)
def test_create_transient_from_response_code(response_code: str) -> None:
    error = SolisCloudControlApiError.create("any message", response_code=response_code)

    assert type(error) is SolisCloudControlTransientApiError
    assert error.status_code is None
    assert error.response_code == response_code


@pytest.mark.parametrize(
    "status_code",
    [400, 401, 403, 404, 407, 499],
)
def test_create_permanent_from_status_code(status_code: int) -> None:
    error = SolisCloudControlApiError.create("any message", status_code=status_code)

    assert type(error) is SolisCloudControlPermanentApiError
    assert error.status_code == status_code
    assert error.response_code is None


@pytest.mark.parametrize(
    "response_code",
    ["Z0001", "I0000", "unknown"],
)
def test_create_permanent_from_response_code(response_code: str) -> None:
    error = SolisCloudControlApiError.create("any message", response_code=response_code)

    assert type(error) is SolisCloudControlPermanentApiError
    assert error.status_code is None
    assert error.response_code == response_code


def test_create_permanent_without_status_and_response_code() -> None:
    error = SolisCloudControlApiError.create("any message")

    assert type(error) is SolisCloudControlPermanentApiError


def test_create_transient_when_either_code_is_transient() -> None:
    error = SolisCloudControlApiError.create("any message", status_code=400, response_code="S9999")

    assert type(error) is SolisCloudControlTransientApiError


def test_create_formats_message() -> None:
    error = SolisCloudControlApiError.create("any message", status_code=503, response_code="S9999")

    assert str(error) == "any message (HTTP status code: 503) (API response code: S9999)"
