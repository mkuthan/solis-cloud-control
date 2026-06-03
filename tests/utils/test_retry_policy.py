import pytest

from custom_components.solis_cloud_control.utils.retry_policy import MonotonicTimeProvider, RetryPolicy


class RetryableError(Exception):
    pass


class NotRetryableError(Exception):
    pass


@pytest.fixture
def any_monotonic_time_provider() -> MonotonicTimeProvider:
    return lambda: 0.0


@pytest.fixture
def any_max_retry_time() -> float:
    return 0.0


async def test_run_retry():
    sleep_delays: list[float] = []
    simulated_time = 0.0
    attempts = 0

    def fake_monotonic() -> float:
        return simulated_time

    async def fake_sleep(delay: float) -> None:
        nonlocal simulated_time
        sleep_delays.append(delay)
        simulated_time += delay

    retry_policy = RetryPolicy(
        retryable_exception=RetryableError,
        monotonic_time=fake_monotonic,
        sleep=fake_sleep,
    )

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        raise RetryableError("boom")

    with pytest.raises(RetryableError):
        await retry_policy(operation, max_retry_time=10.0)

    # First attempt + 4 retries fit within the 10-second budget.
    assert attempts == 5
    # Backoff doubles from 1s to 2s to 4s, then is capped to the remaining time (3s).
    assert sleep_delays == [1.0, 2.0, 4.0, 3.0]


async def test_run_returns_without_retry_on_success(
    any_monotonic_time_provider: MonotonicTimeProvider, any_max_retry_time: float
):
    sleep_delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_delays.append(delay)

    retry_policy = RetryPolicy(
        retryable_exception=RetryableError,
        monotonic_time=any_monotonic_time_provider,
        sleep=fake_sleep,
    )

    async def operation() -> str:
        return "ok"

    result = await retry_policy(operation, max_retry_time=any_max_retry_time)

    assert result == "ok"
    assert sleep_delays == []


async def test_run_does_not_retry_non_retryable_exception(
    any_monotonic_time_provider: MonotonicTimeProvider, any_max_retry_time: float
):
    sleep_delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_delays.append(delay)

    retry_policy = RetryPolicy(
        retryable_exception=RetryableError,
        monotonic_time=any_monotonic_time_provider,
        sleep=fake_sleep,
    )

    async def operation() -> str:
        raise NotRetryableError("not retryable")

    with pytest.raises(NotRetryableError):
        await retry_policy(operation, max_retry_time=any_max_retry_time)

    assert sleep_delays == []
