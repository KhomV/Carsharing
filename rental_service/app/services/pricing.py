from datetime import datetime
from math import ceil


def calculate_rental_cost(
    started_at: datetime,
    finished_at: datetime,
    price_per_minute: int,
) -> int:
    duration_seconds = (finished_at - started_at).total_seconds()

    if duration_seconds < 0:
        raise ValueError("Время завершения раньше времени начала")

    minutes = max(1, ceil(duration_seconds / 60))

    return minutes * price_per_minute