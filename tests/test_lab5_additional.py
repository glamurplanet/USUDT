"""Пограничные проверки математического обеспечения ЛР5."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.analytics import hourly_intensity, queue_remainder, horizon_forecasts, compare_periods
from app.logic import weighted_delay


def test_intensity_and_invalid_period():
    assert hourly_intensity(12, 60) == 720
    with pytest.raises(ValueError):
        hourly_intensity(12, 0)


def test_queue_and_missing_service_estimate():
    assert queue_remainder(3, 5, 10) == 0
    with pytest.raises(ValueError):
        queue_remainder(3, 5, None)


def test_forecasts_for_three_horizons_with_unverified_history():
    start = datetime(2026, 11, 25, 10, tzinfo=timezone.utc)
    points = [
        SimpleNamespace(observed_at=start+timedelta(minutes=i),
                        vehicle_count=10+i, period_seconds=60)
        for i in range(5)
    ]
    result = horizon_forecasts(points)
    assert set(result) == {5, 10, 15}
    assert all(item["method"] == "moving_average_5_unverified"
               and item["validation_pairs"] == 0 for item in result.values())


def test_forecasts_with_broken_recent_window():
    start = datetime(2026, 11, 25, 10, tzinfo=timezone.utc)
    points = [
        SimpleNamespace(observed_at=start+timedelta(minutes=i),
                        vehicle_count=10, period_seconds=60)
        for i in (0, 1, 2, 4, 5)
    ]
    with pytest.raises(ValueError, match="пропуски"):
        horizon_forecasts(points)


def test_incomparable_conditions_and_public_weight():
    assert compare_periods([10]*5, [10]*5, "dry", "rain")["available"] is False
    criterion, public = weighted_delay(20, 8, 10, 12, 1, 1, 2)
    assert public == 10.5
    assert criterion == 17.15
