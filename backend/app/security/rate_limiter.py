from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from threading import Lock

from fastapi import HTTPException, Request, status

from app.config import settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._requests: dict[str, deque[datetime]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = datetime.now(tz=timezone.utc)
        cutoff = now - timedelta(seconds=window_seconds)

        with self._lock:
            bucket = self._requests[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded for AI endpoint. Try again in a minute.",
                )
            bucket.append(now)


rate_limiter = InMemoryRateLimiter()


def ai_rate_limit(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown-client"
    limit_key = f"{client_host}:ai"
    rate_limiter.check(limit_key, settings.ai_rate_limit_per_minute, 60)
