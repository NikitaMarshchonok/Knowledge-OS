from datetime import datetime, timedelta, timezone

TimeWindow = str


def resolve_time_window_start(time_window: TimeWindow) -> datetime | None:
    now = datetime.now(timezone.utc)
    if time_window == "24h":
        return now - timedelta(hours=24)
    if time_window == "7d":
        return now - timedelta(days=7)
    if time_window == "30d":
        return now - timedelta(days=30)
    return None
