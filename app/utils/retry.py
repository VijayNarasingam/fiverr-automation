"""Retry utilities built on tenacity for the browser automation service."""

from functools import wraps

from tenacity import retry as tenacity_retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_exponential


def retry_with_backoff(
    attempts: int = 3,
    multiplier: int = 1,
    min_wait: int = 2,
    max_wait: int = 30,
):
    """Decorator that retries an async function with exponential backoff.

    Defaults match the task specification:
        stop_after_attempt(3),
        wait_exponential(multiplier=1, min=2, max=30).
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retry = tenacity_retry(
                stop=stop_after_attempt(attempts),
                wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
                reraise=True,
            )
            return await retry(func)(*args, **kwargs)

        return wrapper

    return decorator
