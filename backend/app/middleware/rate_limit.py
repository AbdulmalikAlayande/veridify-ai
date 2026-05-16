"""In-memory per-client rate limiter. Resets on server restart — acceptable for hackathon."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException

from app.config import get_settings
from app.db.models import Client
from app.middleware.auth import get_current_client

settings = get_settings()

_counters: dict[str, list[datetime]] = defaultdict(list)


async def rate_limit(client: Client = Depends(get_current_client)) -> Client:
    key = str(client.id)
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=1)
    timestamps = [t for t in _counters[key] if t > window_start]
    if len(timestamps) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": f"{settings.rate_limit_per_minute} requests per minute limit exceeded",
            },
        )
    timestamps.append(now)
    _counters[key] = timestamps
    return client
