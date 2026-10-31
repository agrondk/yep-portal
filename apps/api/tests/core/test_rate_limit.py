import pytest

from app.core.errors import AppError
from app.core.rate_limit import RateLimiter


def test_rate_limiter_rejects_attempt_over_limit() -> None:
    limiter = RateLimiter()
    limiter.check("login:test", limit=2, window_seconds=60)
    limiter.check("login:test", limit=2, window_seconds=60)
    with pytest.raises(AppError) as error:
        limiter.check("login:test", limit=2, window_seconds=60)
    assert error.value.status_code == 429
