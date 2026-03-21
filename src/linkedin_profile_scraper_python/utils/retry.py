import random
import time
from typing import Callable, TypeVar


T = TypeVar("T")


class SessionExpiredError(Exception):
    pass


class RetryableRateLimitError(Exception):
    def __init__(self, message: str, retry_after_seconds: float = 0.0) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


def sleep_between(min_ms: int, max_ms: int) -> None:
    lower = max(1000, min(min_ms, max_ms))
    upper = max(lower, max(min_ms, max_ms))
    delay_ms = random.randint(lower, upper)
    time.sleep(delay_ms / 1000.0)


def with_retry(
    fn: Callable[[], T],
    max_attempts: int = 3,
    base_delay_seconds: float = 2.0,
    rate_limit_delay_seconds: float = 180.0,
) -> T:
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except SessionExpiredError:
            raise
        except RetryableRateLimitError as exc:
            last_error = exc
            if attempt >= max_attempts:
                raise
            delay_seconds = max(rate_limit_delay_seconds, exc.retry_after_seconds)
            time.sleep(delay_seconds)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= max_attempts:
                raise
            time.sleep(base_delay_seconds * (2 ** (attempt - 1)))

    if last_error is not None:
        raise last_error
    raise RuntimeError("Retry loop exited without result or error")
