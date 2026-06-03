import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

_LOGGER = logging.getLogger(__name__)


class MonotonicTimeProvider(Protocol):
    def __call__(self) -> float: ...


class SleepFunction(Protocol):
    def __call__(self, delay: float) -> Awaitable[None]: ...


class RetryPolicy:
    def __init__(
        self,
        retryable_exception: type[Exception],
        initial_delay_seconds: float = 1.0,
        delay_multiplier: float = 2.0,
        monotonic_time: MonotonicTimeProvider = time.monotonic,
        sleep: SleepFunction = asyncio.sleep,
    ) -> None:
        self._initial_delay_seconds = initial_delay_seconds
        self._delay_multiplier = delay_multiplier
        self._retryable_exception = retryable_exception
        self._monotonic_time = monotonic_time
        self._sleep = sleep

    async def __call__(
        self,
        operation_closure: Callable[[], Awaitable[Any]],
        max_retry_time: float,
    ) -> Any:  # noqa: ANN401
        start_time = self._monotonic_time()
        delay = self._initial_delay_seconds

        attempt = 0

        while True:
            try:
                return await operation_closure()
            except self._retryable_exception as err:
                elapsed_time = self._monotonic_time() - start_time

                if elapsed_time >= max_retry_time:
                    raise err

                attempt += 1
                _LOGGER.warning(
                    "Retrying due to error: %s (attempt %d, elapsed time: %.1fs)",
                    str(err),
                    attempt,
                    elapsed_time,
                )

                delay = min(delay, max_retry_time - elapsed_time)
                await self._sleep(delay)
                delay *= self._delay_multiplier
